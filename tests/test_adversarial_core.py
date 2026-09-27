from __future__ import annotations

import json
from pathlib import Path

import pytest

import tools


ROOT = Path(__file__).resolve().parents[1]
PERIOD = "2025-01-01"


@pytest.fixture(autouse=True)
def real_data(monkeypatch):
    monkeypatch.setenv("GIPUZKOA360_DATA_DIR", str(ROOT / "datos_preparados"))
    tools.clear_analysis_cache()


@pytest.mark.parametrize(
    ("operation", "expected_code"),
    [
        (lambda: tools.obtener_resumen_territorial("NO EXISTE", PERIOD), "municipality_not_found"),
        (lambda: tools.obtener_resumen_territorial(None, PERIOD), "municipality_not_found"),
        (lambda: tools.analizar_envejecimiento("65", "percentage", "1900-01-01"), "period_not_found"),
        (lambda: tools.analizar_acceso_servicios("farmacia", 1.0, PERIOD), "service_category_not_found"),
        (lambda: tools.analizar_acceso_servicios("primary_care", 0, PERIOD), "invalid_threshold"),
        (lambda: tools.analizar_acceso_servicios("primary_care", 101, PERIOD), "invalid_threshold"),
        (lambda: tools.analizar_coincidencia("primary_care", "65", 1.0, PERIOD, 0.49), "invalid_quantile"),
        (lambda: tools.analizar_coincidencia("primary_care", "65", 1.0, PERIOD, 0.96), "invalid_quantile"),
        (
            lambda: tools.simular_escenario("añadir", "primary_care", 1.0, PERIOD),
            "invalid_coordinates",
        ),
        (
            lambda: tools.simular_escenario("eliminar", "primary_care", 1.0, PERIOD),
            "service_id_required",
        ),
        (
            lambda: tools.simular_escenario("cambiar umbral", "primary_care", 1.0, PERIOD),
            "threshold_required",
        ),
        (lambda: tools.simular_escenario(None, "primary_care", 1.0, PERIOD), "invalid_scenario"),
    ],
)
def test_bad_inputs_are_controlled_json(operation, expected_code: str):
    payload = json.loads(operation())
    assert payload["status"] == "error"
    assert payload["error_code"] == expected_code
    assert isinstance(payload["available_options"], list)


@pytest.mark.parametrize("quantile", [0.5, 0.75, 0.85, 0.95])
def test_allowed_quantile_edges_are_deterministic(quantile: float):
    first = tools.analizar_coincidencia("PRIMARY CARE", "≥65", 1.0, PERIOD, quantile)
    second = tools.analizar_coincidencia("atención primaria", "65+", 1.0, PERIOD, quantile)
    assert first == second
    assert json.loads(first)["status"] == "ok"


def test_real_eibar_mental_health_regression():
    result = json.loads(tools.analizar_acceso_servicios("SALUD MENTAL", 1.0, PERIOD, [" EIBAR "]))
    assert result["data"] == [
        {
            "municipality_code": "20030",
            "municipality_name": "Eibar",
            "nearest_distance_m": 1859.7,
            "nearest_service_id": "entity7809ADB5",
            "within_threshold": False,
        }
    ]


def test_real_aduna_zero_registered_services_is_not_missing_access():
    result = json.loads(tools.obtener_resumen_territorial("ADUNA", PERIOD))
    row = result["data"][0]
    assert row["services_in_municipality"] == {}
    assert all(
        indicator["registered_service_count"] == 0
        for indicator in row["service_indicators"].values()
    )
    assert row["service_indicators"]["primary_care"]["nearest_distance_m"] == 2756.2
    assert any("no acredita" in item for item in result["limitations"])


@pytest.mark.parametrize(
    ("quantile", "age_cut", "distance_cut", "highlighted"),
    [
        (0.75, 23.973, 2019.2, 7),
        (0.85, 25.3557, 2308.7, 2),
    ],
)
def test_real_coincidence_cut_regressions(
    quantile: float, age_cut: float, distance_cut: float, highlighted: int
):
    result = json.loads(tools.analizar_coincidencia("primary_care", "65", 1.0, PERIOD, quantile))
    assert result["summary"]["age_cut_percent"] == pytest.approx(age_cut)
    assert result["summary"]["distance_cut_m"] == pytest.approx(distance_cut)
    assert result["summary"]["joined_rows"] == 88
    assert result["summary"]["highlighted_count"] == highlighted
    assert len(result["data"]) == highlighted


def test_all_public_outputs_are_valid_json():
    calls = [
        lambda: tools.consultar_fuente("EUSTAT_EMH_2025"),
        lambda: tools.obtener_resumen_territorial("Aduna", PERIOD),
        lambda: tools.comparar_municipios(["Tolosa", "Beasain"], "75", "hospital", 1.0, PERIOD),
        lambda: tools.analizar_envejecimiento("75+", "percentage", PERIOD, 10),
        lambda: tools.analizar_acceso_servicios("other health", 1.0, PERIOD),
        lambda: tools.analizar_coincidencia("primary care", "65", 1.0, PERIOD, 0.75),
        lambda: tools.simular_escenario(
            "cambiar umbral", "primary care", 1.0, PERIOD, nuevo_umbral_km=2.0
        ),
    ]
    assert all(json.loads(operation())["status"] == "ok" for operation in calls)
