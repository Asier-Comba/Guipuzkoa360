import hashlib
import json
from pathlib import Path
import subprocess
import sys

import geopandas as gpd
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "datos_preparados"
CATEGORIES = ("primary_care", "hospital", "mental_health", "other_health")


def load_tables():
    municipalities = pd.read_csv(OUT / "municipios.csv", dtype={"municipality_code": str})
    demography = pd.read_csv(OUT / "demografia.csv", dtype={"municipality_code": str})
    services = pd.read_csv(OUT / "servicios.csv", dtype={"municipality_code": str, "service_id": str})
    return municipalities, demography, services


def test_machine_readable_contract_matches_schema_and_types():
    contract = json.loads((OUT / "data_contract.json").read_text(encoding="utf-8"))
    municipalities, _, _ = load_tables()
    required = contract["files"]["datos_preparados/municipios.csv"]["required_columns"]
    assert list(municipalities.columns) == list(required)
    assert municipalities.municipality_code.str.fullmatch(contract["municipality_key"]["pattern"]).all()
    assert municipalities.municipality_code.nunique() == contract["municipality_key"]["expected_unique_values"]
    integer_columns = [column for column, kind in required.items() if kind.startswith("integer")]
    assert all(pd.api.types.is_integer_dtype(municipalities[column]) for column in integer_columns)
    numeric_columns = [column for column, kind in required.items() if kind.startswith("number")]
    assert all(pd.api.types.is_numeric_dtype(municipalities[column]) for column in numeric_columns)


def test_no_nulls_duplicates_or_broken_foreign_keys():
    municipalities, demography, services = load_tables()
    boundaries = gpd.read_file(OUT / "municipios.geojson")
    assert municipalities.isna().sum().sum() == 0
    assert demography.isna().sum().sum() == 0
    assert services.isna().sum().sum() == 0
    assert municipalities.municipality_code.is_unique
    assert demography.municipality_code.is_unique
    assert services.service_id.is_unique
    assert set(municipalities.municipality_code) == set(demography.municipality_code) == set(boundaries.municipality_code)
    assert set(services.municipality_code) <= set(municipalities.municipality_code)


def test_service_points_are_inside_the_assigned_municipality():
    _, _, services = load_tables()
    boundaries = gpd.read_file(OUT / "municipios.geojson")[["municipality_code", "geometry"]]
    boundaries = boundaries.rename(columns={"municipality_code": "spatial_municipality_code"})
    points = gpd.GeoDataFrame(
        services[["service_id", "municipality_code"]],
        geometry=gpd.points_from_xy(services.longitude, services.latitude), crs=4326,
    )
    joined = gpd.sjoin(points, boundaries, how="left", predicate="within")
    assert joined.spatial_municipality_code.notna().all()
    assert joined.municipality_code.eq(joined.spatial_municipality_code).all()


def test_all_service_metrics_recompute_from_rows():
    municipalities, _, services = load_tables()
    counts = services.pivot_table(index="municipality_code", columns="service_category",
                                  values="service_id", aggfunc="count", fill_value=0)
    counts = counts.reindex(municipalities.municipality_code, fill_value=0)
    for category in CATEGORIES:
        expected_count = counts[category].to_numpy()
        assert np.array_equal(expected_count, municipalities[f"services_{category}"])
        for age in (65, 75):
            expected_rate = (expected_count / municipalities[f"population_{age}_plus"] * 10_000).round(3)
            assert np.allclose(expected_rate, municipalities[f"{category}_per_10000_{age}_plus"], atol=0.0005)
    assert municipalities.services_total.sum() == len(services) == 148
    assert np.array_equal(
        municipalities.services_total,
        municipalities[[f"services_{category}" for category in CATEGORIES]].sum(axis=1),
    )


def test_distances_recompute_in_epsg_25830():
    municipalities, _, services = load_tables()
    origins = gpd.GeoSeries(
        gpd.points_from_xy(municipalities.representative_point_longitude,
                           municipalities.representative_point_latitude), crs=4326,
    ).to_crs(25830)
    destinations = gpd.GeoDataFrame(
        services[["service_category"]],
        geometry=gpd.points_from_xy(services.longitude, services.latitude), crs=4326,
    ).to_crs(25830)
    origin_xy = np.array([[point.x, point.y] for point in origins])
    for category in CATEGORIES:
        category_xy = np.array([[point.x, point.y] for point in destinations.loc[
            destinations.service_category.eq(category), "geometry"]])
        expected = np.sqrt(((origin_xy[:, None, :] - category_xy[None, :, :]) ** 2).sum(axis=2)).min(axis=1).round(1)
        assert np.allclose(expected, municipalities[f"distance_to_nearest_{category}_m"], atol=0.2)


def test_periods_and_source_lineage_are_explicit():
    municipalities, demography, services = load_tables()
    boundaries = gpd.read_file(OUT / "municipios.geojson")
    sources = json.loads((OUT / "metadata_sources.json").read_text(encoding="utf-8"))
    by_id = {source["source_id"]: source for source in sources}
    assert set(demography.reference_period) == {"2025-01-01"}
    assert {str(value)[:10] for value in boundaries.reference_period} == {"2025-05-07"}
    assert set(services.reference_period) == {"2026-09-20"}
    assert set(municipalities.source_id) == {"G360_DERIVED_MUNICIPAL_METRICS_V1"}
    upstream = set(municipalities.source_ids.iloc[0].split("|"))
    assert all(set(value.split("|")) == upstream for value in municipalities.source_ids)
    assert upstream == set(by_id["G360_DERIVED_MUNICIPAL_METRICS_V1"]["upstream_source_ids"])
    assert upstream <= set(by_id)


def test_municipalities_without_registered_resources_remain_explicit():
    municipalities, _, services = load_tables()
    no_services = municipalities.loc[municipalities.services_total.eq(0), "municipality_code"].tolist()
    assert no_services == ["20002", "20006", "20007", "20012", "20028", "20037", "20041", "20048", "20077", "20905", "20906"]
    assert set(no_services).isdisjoint(set(services.municipality_code))
    assert (municipalities.loc[municipalities.municipality_code.isin(no_services),
                               [f"services_{category}" for category in CATEGORIES]] == 0).all().all()


def test_runtime_bundle_is_compact_and_hashes_match():
    manifest = json.loads((OUT / "runtime_manifest.json").read_text(encoding="utf-8"))
    assert manifest["within_portal_budget"] is True
    assert manifest["total_bytes"] < 1024 * 1024
    assert manifest["total_bytes"] == sum(item["bytes"] for item in manifest["files"])
    for item in manifest["files"]:
        path = ROOT / item["path"]
        assert path.stat().st_size == item["bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]


def test_original_download_snapshot_hashes_match():
    manifest = json.loads((ROOT / "datos_originales" / "download_manifest.json").read_text(encoding="utf-8"))
    assert len(manifest["files"]) == 4
    for item in manifest["files"]:
        path = ROOT / item["path"]
        assert path.stat().st_size == item["bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]


def test_golden_cases_against_fixed_source_snapshot():
    municipalities, demography, services = load_tables()
    fixture = json.loads((ROOT / "tests" / "fixtures" / "golden_cases.json").read_text(encoding="utf-8"))
    cases = {case["case_id"]: case for case in fixture["cases"]}

    donostia = demography.set_index("municipality_code").loc["20069"]
    expected = cases["GOLD-DEM-001"]["expected"]
    assert int(donostia.population_total) == expected["population_total"]
    assert int(donostia.population_65_plus) == expected["population_count"]
    assert float(donostia.pct_65_plus) == expected["percentage"]

    for expected_row in cases["GOLD-DEM-002"]["expected"]["rows"]:
        row = demography.set_index("municipality_code").loc[expected_row["municipality_code"]]
        assert int(row.population_75_plus) == expected_row["population_count"]
        assert float(row.pct_75_plus) == expected_row["percentage"]

    by_code = municipalities.set_index("municipality_code")
    aduna_expected = cases["GOLD-SVC-001"]["expected"]
    assert int(by_code.loc["20002", "services_primary_care"]) == aduna_expected["registered_service_count"]
    assert float(by_code.loc["20002", "distance_to_nearest_primary_care_m"]) == aduna_expected["distance_m"]
    nearest = services.loc[services.service_id.eq(aduna_expected["nearest_service_id"])].iloc[0]
    assert nearest.municipality_code == aduna_expected["nearest_service_municipality_code"]

    eibar_expected = cases["GOLD-SVC-002"]["expected"]
    assert int(by_code.loc["20030", "services_mental_health"]) == eibar_expected["registered_service_count"]
    assert float(by_code.loc["20030", "distance_to_nearest_mental_health_m"]) == eibar_expected["distance_m"]
    assert services.service_id.eq(eibar_expected["nearest_service_id"]).any()

    scenario = cases["GOLD-SCN-001"]
    observed = float(by_code.loc[scenario["inputs"]["municipality_code"], "distance_to_nearest_primary_care_m"])
    assert observed == scenario["expected"]["observed_distance_m"]
    assert scenario["expected"]["scenario_distance_m"] - observed == scenario["expected"]["distance_delta_m"]


def test_work3_v1_mapping_has_no_implicit_unit_or_null_conversion():
    municipalities, _, _ = load_tables()
    contract = json.loads((OUT / "data_contract.json").read_text(encoding="utf-8"))
    mapping = contract["work3_mapping"]
    selected_category = "primary_care"
    row = municipalities.set_index("municipality_code").loc["20069"]
    output = {
        "unit_id": "20069",
        "name": row[mapping["name"]],
        "population": int(row[mapping["population"]]),
        "age_65_count": int(row[mapping["age_65_count"]]),
        "age_75_count": int(row[mapping["age_75_count"]]),
        "service_count": int(row[mapping["service_count"].replace("<selected_category>", selected_category)]),
        "service_distance_km": float(row[
            mapping["service_distance_km"].split(" / ")[0].replace("<selected_category>", selected_category)
        ]) / 1000,
        "period": row[mapping["period"]],
        "source_ids": row.source_ids.split("|"),
    }
    assert output == {
        "unit_id": "20069", "name": "Donostia / San Sebastián", "population": 183388,
        "age_65_count": 48832, "age_75_count": 24884, "service_count": 18,
        "service_distance_km": 0.3231,
        "period": "demography=2025-01-01;services=2026-09-20;geography=2025-05-07",
        "source_ids": ["EUSTAT_EMH_2025", "ODE_HEALTH_CENTRES_2026", "GEOEUSKADI_MUNICIPIOS_2025"],
    }


def test_work3_smoke_export_is_real_but_explicitly_not_an_agent_run(tmp_path):
    output = tmp_path / "work3-smoke.json"
    process = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "data" / "export_work3_smoke_result.py"), str(output)],
        capture_output=True, text=True,
    )
    assert process.returncode == 0, process.stderr
    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["schema_version"] == "1.0.0"
    assert result["data_mode"] == "real"
    assert len(result["comparison"]) == 3
    assert result["scenario"] is None
    assert result["trace"]["agent_version"] == "data-contract-smoke-not-agent"
    assert "no es una respuesta producida por el agente" in result["summary"]
    source_ids = {source["source_id"] for source in result["sources"]}
    assert all(source["url"].startswith("https://") for source in result["sources"])
    assert set(result["trace"]["data_refs"]) == source_ids
    assert all(set(row["source_ids"]) <= source_ids for row in result["comparison"])
