"""Audita contratos cruzados y genera un manifiesto mínimo de ejecución."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "datos_preparados"
ANALYSIS = ROOT / "analisis"
CATEGORIES = ("primary_care", "hospital", "mental_health", "other_health")
RUNTIME_FILES = (
    "datos_preparados/municipios.csv",
    "datos_preparados/runtime_servicios.csv",
    "datos_preparados/runtime_municipios.geojson",
    "datos_preparados/metadata_sources.json",
    "datos_preparados/data_contract.json",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def nearest_distance(origins: gpd.GeoSeries, destinations: gpd.GeoSeries) -> np.ndarray:
    destination_xy = np.array([[point.x, point.y] for point in destinations])
    return np.array([
        float(np.sqrt(((destination_xy - np.array([origin.x, origin.y])) ** 2).sum(axis=1)).min())
        for origin in origins
    ])


def main() -> None:
    demography = pd.read_csv(OUT / "demografia.csv", dtype={"municipality_code": str})
    municipalities = pd.read_csv(OUT / "municipios.csv", dtype={"municipality_code": str})
    boundaries = gpd.read_file(OUT / "municipios.geojson")
    runtime_geo = gpd.read_file(OUT / "runtime_municipios.geojson")
    services = pd.read_csv(OUT / "servicios.csv", dtype={"municipality_code": str, "service_id": str})
    runtime_services = pd.read_csv(
        OUT / "runtime_servicios.csv", dtype={"municipality_code": str, "service_id": str}
    )
    sources = json.loads((OUT / "metadata_sources.json").read_text(encoding="utf-8"))
    contract = json.loads((OUT / "data_contract.json").read_text(encoding="utf-8"))

    checks: list[dict[str, object]] = []

    def check(check_id: str, condition: bool, detail: object) -> None:
        checks.append({"check_id": check_id, "status": "PASS" if condition else "FAIL", "detail": detail})

    code_sets = {
        "demography": set(demography.municipality_code),
        "municipalities": set(municipalities.municipality_code),
        "boundaries": set(boundaries.municipality_code.astype(str)),
        "runtime_geo": set(runtime_geo.municipality_code.astype(str)),
    }
    check("coverage_88_all_municipal_files", all(len(values) == 88 for values in code_sets.values()),
          {name: len(values) for name, values in code_sets.items()})
    check("municipality_key_sets_equal", len({frozenset(values) for values in code_sets.values()}) == 1,
          {name: sorted(values) for name, values in code_sets.items() if values != code_sets["municipalities"]})
    check("municipality_code_format", municipalities.municipality_code.str.fullmatch(r"20\d{3}").all(),
          "^20[0-9]{3}$")
    check("municipality_keys_unique", all(frame.municipality_code.is_unique for frame in (demography, municipalities)),
          {"demography_duplicates": int(demography.municipality_code.duplicated().sum()),
           "municipalities_duplicates": int(municipalities.municipality_code.duplicated().sum())})

    nulls = {
        "demografia.csv": int(demography.isna().sum().sum()),
        "municipios.csv": int(municipalities.isna().sum().sum()),
        "servicios.csv": int(services.isna().sum().sum()),
        "runtime_servicios.csv": int(runtime_services.isna().sum().sum()),
    }
    check("no_nulls_prepared_tables", sum(nulls.values()) == 0, nulls)
    check("population_hierarchy",
          ((municipalities.population_75_plus <= municipalities.population_65_plus)
           & (municipalities.population_65_plus <= municipalities.population_total)
           & (municipalities.population_total > 0)).all(),
          "0 < 75+ <= 65+ <= total")
    for age in (65, 75):
        expected = (municipalities[f"population_{age}_plus"] / municipalities.population_total * 100).round(3)
        check(f"pct_{age}_formula", np.allclose(expected, municipalities[f"pct_{age}_plus"], atol=0.0005),
              "count / total * 100; 3 decimals")

    check("service_ids_unique", services.service_id.is_unique and runtime_services.service_id.is_unique,
          {"rows": len(services), "duplicates": int(services.service_id.duplicated().sum())})
    check("service_foreign_keys", set(services.municipality_code) <= code_sets["municipalities"],
          sorted(set(services.municipality_code) - code_sets["municipalities"]))
    check("service_categories", set(services.service_category) == set(CATEGORIES),
          services.service_category.value_counts().sort_index().to_dict())
    check("service_coordinates_bounds",
          services.latitude.between(42.8, 43.5).all() and services.longitude.between(-2.7, -1.7).all(),
          {"latitude": [float(services.latitude.min()), float(services.latitude.max())],
           "longitude": [float(services.longitude.min()), float(services.longitude.max())]})

    service_points = gpd.GeoDataFrame(
        services[["service_id", "municipality_code", "service_category"]].copy(),
        geometry=gpd.points_from_xy(services.longitude, services.latitude), crs=4326,
    )
    containment = gpd.sjoin(
        service_points, boundaries[["municipality_code", "geometry"]].rename(
            columns={"municipality_code": "spatial_municipality_code"}),
        how="left", predicate="within",
    )
    check("service_spatial_assignment",
          containment.spatial_municipality_code.notna().all()
          and containment.municipality_code.eq(containment.spatial_municipality_code).all(),
          {"unmatched": int(containment.spatial_municipality_code.isna().sum()),
           "mismatched": int((containment.municipality_code != containment.spatial_municipality_code).sum())})
    check("geometry_crs", boundaries.crs.to_epsg() == 4326 and runtime_geo.crs.to_epsg() == 4326,
          {"master": str(boundaries.crs), "runtime": str(runtime_geo.crs), "calculation": "EPSG:25830"})
    check("geometry_valid", boundaries.geometry.is_valid.all() and runtime_geo.geometry.is_valid.all(),
          {"master_invalid": int((~boundaries.geometry.is_valid).sum()),
           "runtime_invalid": int((~runtime_geo.geometry.is_valid).sum())})
    check("geometry_types", set(runtime_geo.geometry.geom_type) <= {"Polygon", "MultiPolygon"},
          runtime_geo.geometry.geom_type.value_counts().to_dict())

    counts = services.pivot_table(index="municipality_code", columns="service_category",
                                  values="service_id", aggfunc="count", fill_value=0)
    counts = counts.reindex(municipalities.municipality_code, fill_value=0)
    for category in CATEGORIES:
        expected_count = counts.get(category, pd.Series(0, index=counts.index)).to_numpy()
        check(f"service_count_{category}",
              np.array_equal(expected_count, municipalities[f"services_{category}"].to_numpy()),
              int(expected_count.sum()))
        for age in (65, 75):
            expected_rate = (expected_count / municipalities[f"population_{age}_plus"] * 10_000).round(3)
            check(f"rate_{category}_{age}_formula",
                  np.allclose(expected_rate, municipalities[f"{category}_per_10000_{age}_plus"], atol=0.0005),
                  "count / population * 10000; 3 decimals")
    expected_total = municipalities[[f"services_{category}" for category in CATEGORIES]].sum(axis=1)
    check("services_total_formula", np.array_equal(expected_total, municipalities.services_total),
          int(expected_total.sum()))

    representative = gpd.GeoSeries(
        gpd.points_from_xy(municipalities.representative_point_longitude,
                           municipalities.representative_point_latitude), crs=4326,
    ).to_crs(25830)
    service_points_metric = service_points.to_crs(25830)
    for category in CATEGORIES:
        expected_distance = nearest_distance(
            representative, service_points_metric.loc[service_points_metric.service_category.eq(category), "geometry"]
        ).round(1)
        check(f"distance_{category}_formula",
              np.allclose(expected_distance, municipalities[f"distance_to_nearest_{category}_m"], atol=0.2),
              "Euclidean metres in EPSG:25830; rounded to 0.1 m")

    expected_runtime_columns = [
        "service_id", "service_name", "service_category", "municipality_code", "latitude", "longitude"
    ]
    check("runtime_services_exact_view",
          runtime_services.equals(services[expected_runtime_columns].reset_index(drop=True)), expected_runtime_columns)
    critical_columns = ["municipality_code", "population_total", "population_65_plus", "population_75_plus",
                        "services_total", "distance_to_nearest_primary_care_m"]
    left = municipalities[critical_columns].sort_values("municipality_code").reset_index(drop=True)
    right = pd.DataFrame(runtime_geo.drop(columns="geometry"))[critical_columns].sort_values(
        "municipality_code").reset_index(drop=True)
    check("runtime_geo_attributes_match",
          left.astype({column: "int64" for column in critical_columns[1:-1]}).equals(
              right.astype({column: "int64" for column in critical_columns[1:-1]})
          ), critical_columns)

    source_ids = {source["source_id"] for source in sources}
    referenced_source_ids = set(municipalities.source_id) | set(services.source_id) | set(boundaries.source_id)
    referenced_source_ids |= {
        source_id for value in municipalities.source_ids for source_id in value.split("|")
    }
    check("all_source_ids_registered", referenced_source_ids <= source_ids,
          sorted(referenced_source_ids - source_ids))
    derived = next(source for source in sources if source["source_id"] == "G360_DERIVED_MUNICIPAL_METRICS_V1")
    check("derived_lineage_complete", set(derived["upstream_source_ids"]) <= source_ids,
          derived["upstream_source_ids"])
    expected_periods = contract["periods"]
    period_detail = {
        "demography": sorted(str(value)[:10] for value in demography.reference_period.unique()),
        "geography": sorted(str(value)[:10] for value in boundaries.reference_period.unique()),
        "services": sorted(str(value)[:10] for value in services.reference_period.unique()),
    }
    check("reference_periods_exact",
          period_detail == {name: [expected_periods[name]] for name in ("demography", "geography", "services")},
          period_detail)

    no_services = municipalities.loc[municipalities.services_total.eq(0),
                                     ["municipality_code", "municipality_name", "population_total"]]
    duplicate_coordinates = int(services.duplicated(["latitude", "longitude"]).sum())
    report = {
        "status": "PASS" if all(item["status"] == "PASS" for item in checks) else "FAIL",
        "contract_version": contract["contract_version"],
        "source_snapshot_date": "2026-09-24",
        "checks": checks,
        "coverage": {"municipalities": len(municipalities), "services": len(services)},
        "service_category_totals": services.service_category.value_counts().sort_index().to_dict(),
        "municipalities_without_registered_services": no_services.to_dict("records"),
        "municipalities_without_registered_services_count": len(no_services),
        "shared_service_coordinates": duplicate_coordinates,
        "shared_service_coordinates_note": (
            "Varios registros oficiales pueden compartir edificio/coordenada y representar tipos de servicio distintos; "
            "no se deduplican por ubicación."
        ),
        "extremes": {
            "highest_pct_65_plus": municipalities.nlargest(5, "pct_65_plus")[[
                "municipality_code", "municipality_name", "pct_65_plus"]].to_dict("records"),
            "largest_primary_care_distance_m": municipalities.nlargest(
                5, "distance_to_nearest_primary_care_m")[[
                    "municipality_code", "municipality_name", "distance_to_nearest_primary_care_m",
                    "services_primary_care"]].to_dict("records"),
        },
        "temporal_compatibility": {
            **expected_periods,
            "interpretation": "Comparación exploratoria; los periodos no son simultáneos."
        },
    }
    (ANALYSIS / "data_quality_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )

    manifest_files = []
    for relative in RUNTIME_FILES:
        path = ROOT / relative
        manifest_files.append({"path": relative, "bytes": path.stat().st_size, "sha256": sha256(path)})
    manifest = {
        "manifest_version": "1.0.0",
        "source_snapshot_date": "2026-09-24",
        "files": manifest_files,
        "total_bytes": sum(item["bytes"] for item in manifest_files),
        "portal_budget_bytes": 24 * 1024 * 1024,
        "within_portal_budget": sum(item["bytes"] for item in manifest_files) < 24 * 1024 * 1024,
        "exclude_from_runtime": ["datos_originales/", "analisis/", "resultados/metricas_municipales.csv",
                                 "datos_preparados/municipios.geojson", "datos_preparados/demografia.csv",
                                 "datos_preparados/servicios.csv"],
    }
    (OUT / "runtime_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    if report["status"] != "PASS":
        failed = [item["check_id"] for item in checks if item["status"] == "FAIL"]
        raise AssertionError(f"Controles QA fallidos: {failed}")
    print(f"QA exhaustivo: {len(checks)} controles PASS; runtime {manifest['total_bytes']} bytes.")


if __name__ == "__main__":
    main()
