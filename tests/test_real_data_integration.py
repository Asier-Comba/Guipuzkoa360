from __future__ import annotations

import csv
from pathlib import Path

import pytest

from data_access import DataRepository
from metrics import wgs84_to_utm30
from tools import TerritorialAnalysis


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "datos_preparados"


@pytest.fixture(scope="module")
def repository() -> DataRepository:
    return DataRepository(DATA)


@pytest.fixture(scope="module")
def analysis(repository: DataRepository) -> TerritorialAnalysis:
    return TerritorialAnalysis(repository)


def test_real_files_load_with_expected_coverage(repository: DataRepository):
    municipalities = repository.municipalities()
    demography = repository.demography()
    services = repository.services()
    assert len(municipalities) == 88
    assert len(demography) == 88
    assert len(services) == 148
    assert all(len(row["municipality_code"]) == 5 for row in municipalities)
    assert all(row.get("easting_m") is not None and row.get("northing_m") is not None for row in municipalities)
    assert all(row.get("easting_m") is not None and row.get("northing_m") is not None for row in services)


def test_official_donostia_population_matches_raw_and_prepared(repository: DataRepository):
    prepared = repository.municipality_lookup("Donostia / San Sebastián")
    with (ROOT / "datos_originales" / "eustat_demografia_2025.csv").open(
        "r", encoding="latin-1", newline=""
    ) as handle:
        rows = list(csv.DictReader(handle))
    raw = next(
        row for row in rows
        if row["ámbitos territoriales"] == "Donostia / San Sebastián"
        and row["grandes grupos de edad cumplida"] == "Total"
        and row["sexo"] == "Total"
    )
    assert int(raw["2025/01/01"]) == 183_388
    assert prepared["population_total"] == 183_388


@pytest.mark.parametrize(
    ("category", "prepared_field"),
    [
        ("primary_care", "distance_to_nearest_primary_care_m"),
        ("hospital", "distance_to_nearest_hospital_m"),
    ],
)
def test_agent_distance_reproduces_work1_metrics(
    repository: DataRepository,
    analysis: TerritorialAnalysis,
    category: str,
    prepared_field: str,
):
    result = analysis.acceso(category, 1.0, "2025-01-01")
    calculated = {row["municipality_code"]: row["nearest_distance_m"] for row in result["data"]}
    for municipality in repository.municipalities():
        assert calculated[municipality["municipality_code"]] == pytest.approx(
            municipality[prepared_field], abs=0.1
        )
    assert result["unit"] == "m"
    assert "EPSG:25830" in result["method"]


def test_real_comparison_is_reproducible(analysis: TerritorialAnalysis):
    result = analysis.comparar(
        ["Tolosa", "Beasain", "Azpeitia"], "65", "primary_care", 1.0, "2025-01-01"
    )
    by_name = {row["municipality_name"]: row for row in result["data"]}
    assert by_name["Tolosa"]["population_total"] == 20_048
    assert by_name["Tolosa"]["pct_65_plus"] == pytest.approx(23.534)
    assert by_name["Beasain"]["nearest_distance_m"] == pytest.approx(3617.3, abs=0.1)
    assert {source["source_id"] for source in result["sources"]} == {
        "EUSTAT_EMH_2025", "ODE_HEALTH_CENTRES_2026", "GEOEUSKADI_MUNICIPIOS_2025"
    }


def test_real_hypothetical_point_recalculates_same_metric(
    repository: DataRepository, analysis: TerritorialAnalysis
):
    target = repository.municipality_lookup("Beasain")
    result = analysis.escenario(
        "add_service",
        "primary_care",
        1.0,
        "2025-01-01",
        target["latitude"],
        target["longitude"],
        "HYPOTHETICAL_BEASAIN",
    )
    row = next(item for item in result["data"] if item["municipality_name"] == "Beasain")
    assert row["baseline_distance_m"] == pytest.approx(3617.3, abs=0.1)
    assert row["scenario_distance_m"] == pytest.approx(0.0, abs=0.2)
    assert row["difference_absolute_m"] < 0
    assert "contrafactual" in " ".join(result["limitations"]).casefold()


def test_runtime_wgs84_conversion_matches_export(repository: DataRepository):
    tolosa = repository.municipality_lookup("Tolosa")
    easting, northing = wgs84_to_utm30(tolosa["latitude"], tolosa["longitude"])
    assert easting == pytest.approx(tolosa["easting_m"], abs=0.1)
    assert northing == pytest.approx(tolosa["northing_m"], abs=0.1)


def test_derived_source_metadata_is_present(repository: DataRepository):
    details = repository.source_details(["G360_DERIVED_MUNICIPAL_METRICS_V1"])[0]
    assert details["institution"] == "DeustoAI Labs"
    assert set(details["input_source_ids"]) == {
        "EUSTAT_EMH_2025", "ODE_HEALTH_CENTRES_2026", "GEOEUSKADI_MUNICIPIOS_2025"
    }
