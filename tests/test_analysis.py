from __future__ import annotations

from pathlib import Path

import pytest

from data_access import DataRepository
from schemas import DataContractError
from tools import TerritorialAnalysis


FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture()
def analysis() -> TerritorialAnalysis:
    return TerritorialAnalysis(DataRepository(FIXTURES))


def test_age_65_and_75_recalculate(analysis: TerritorialAnalysis):
    age_65 = analysis.envejecimiento("65", "percentage", "2025", 4)
    age_75 = analysis.envejecimiento("75", "percentage", "2025", 4)
    assert age_65["metric"] == "pct_65_plus"
    assert age_75["metric"] == "pct_75_plus"
    assert age_65["data"][0]["value"] == 40.0
    assert age_75["data"][0]["value"] == 25.0


def test_count_measure(analysis: TerritorialAnalysis):
    result = analysis.envejecimiento("65", "count", "2025", 2)
    assert result["unit"] == "personas"
    assert result["data"][0]["municipality_name"] == "TEST_MUNICIPIO_C"


def test_service_category_filter_and_no_service_municipalities(analysis: TerritorialAnalysis):
    result = analysis.acceso("salud", 1.0, "2025")
    assert result["rows_used"] == 6
    assert {row["municipality_name"] for row in result["data"]} == {
        "TEST_MUNICIPIO_A", "TEST_MUNICIPIO_B", "TEST_MUNICIPIO_C", "TEST_MUNICIPIO_D"
    }
    assert next(row for row in result["data"] if row["municipality_name"] == "TEST_MUNICIPIO_D")["within_threshold"] is False


def test_unknown_category_is_controlled(analysis: TerritorialAnalysis):
    with pytest.raises(DataContractError) as error:
        analysis.acceso("inexistente", 1.0, "2025")
    assert error.value.code == "service_category_not_found"


def test_compare_two_and_several_municipalities(analysis: TerritorialAnalysis):
    pair = analysis.comparar(["TEST_MUNICIPIO_A", "TEST_MUNICIPIO_B"], "65", "salud", 1.0, "2025")
    group = analysis.comparar(["TEST_MUNICIPIO_A", "TEST_MUNICIPIO_B", "TEST_MUNICIPIO_C"], "75", None, 1.0, "2025")
    assert len(pair["data"]) == 2
    assert len(group["data"]) == 3


def test_unknown_municipality_does_not_fabricate(analysis: TerritorialAnalysis):
    with pytest.raises(DataContractError) as error:
        analysis.comparar(["TEST_MUNICIPIO_A", "NO_EXISTE"], period="2025")
    assert error.value.code == "municipality_not_found"


def test_coincidence_exposes_components_and_sources(analysis: TerritorialAnalysis):
    result = analysis.coincidencia("salud", "65", 1.0, "2025", 0.75)
    assert all("pct_65_plus" in row and "nearest_distance_m" in row for row in result["data"])
    assert all("highlighted" in row for row in result["data"])
    assert result["sources"]
    assert "no se usa una puntuación compuesta" in result["method"]


def test_change_threshold_scenario(analysis: TerritorialAnalysis):
    result = analysis.escenario("change_threshold", "salud", 1.0, "2025", new_threshold_km=20.0)
    assert result["scenario"]["changed_parameters"]["new_threshold_km"] == 20.0
    assert any(not row["baseline_within_threshold"] and row["scenario_within_threshold"] for row in result["data"])


def test_add_service_changes_distance(analysis: TerritorialAnalysis):
    result = analysis.escenario("add_service", "salud", 1.0, "2025", 43.2, -2.35)
    target = next(row for row in result["data"] if row["municipality_name"] == "TEST_MUNICIPIO_D")
    assert target["difference_absolute_m"] < 0
    assert "contrafactual" in " ".join(result["limitations"]).lower()


def test_invalid_scenario(analysis: TerritorialAnalysis):
    with pytest.raises(DataContractError) as error:
        analysis.escenario("predict_demand", "salud", period="2025")
    assert error.value.code == "invalid_scenario"


def test_traceability_on_every_numeric_result(analysis: TerritorialAnalysis):
    for result in (
        analysis.envejecimiento(period="2025"),
        analysis.acceso("salud", period="2025"),
        analysis.coincidencia("salud", period="2025"),
    ):
        assert result["rows_used"] > 0
        assert result["method"]
        assert result["sources"] or result["warnings"]


def test_missing_period_requires_choice(tmp_path: Path):
    for name in ("municipios.csv", "servicios.csv", "metadata_sources.json"):
        (tmp_path / name).write_bytes((FIXTURES / name).read_bytes())
    original = (FIXTURES / "demografia.csv").read_text(encoding="utf-8")
    extra = original.splitlines()[1].replace(",2025,", ",2024,")
    (tmp_path / "demografia.csv").write_text(original + "\n" + extra + "\n", encoding="utf-8")
    with pytest.raises(DataContractError) as error:
        TerritorialAnalysis(DataRepository(tmp_path)).envejecimiento(period=None)
    assert error.value.code == "period_required"
