from __future__ import annotations

import json

import pytest

import tools
from schemas import DataContractError


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("atención primaria", "primary_care"),
        (" atencion   primaria ", "primary_care"),
        ("PRIMARY CARE", "primary_care"),
        ("primary_care", "primary_care"),
        ("salud mental", "mental_health"),
        ("MENTAL_HEALTH", "mental_health"),
        ("Hospital", "hospital"),
        ("OTHER HEALTH", "other_health"),
    ],
)
def test_service_category_aliases(value: str, expected: str):
    assert tools.normalize_service_category(value) == expected


@pytest.mark.parametrize("value", ["65", "65+", "65 o más", "65 O MAS", "≥65", ">=65", " 65 + "])
def test_age_65_aliases(value: str):
    assert tools.normalize_age_group(value) == "65"


@pytest.mark.parametrize("value", ["75", "75+", "75 o más", "75 O MAS", "≥75", ">=75", " 75 + "])
def test_age_75_aliases(value: str):
    assert tools.normalize_age_group(value) == "75"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("añadir", "add_service"),
        ("AGREGAR SERVICIO", "add_service"),
        ("add service", "add_service"),
        ("eliminar", "remove_service"),
        ("remove", "remove_service"),
        ("cambiar umbral", "change_threshold"),
        ("change_threshold", "change_threshold"),
    ],
)
def test_scenario_action_aliases(value: str, expected: str):
    assert tools.normalize_scenario_action(value) == expected


@pytest.mark.parametrize(
    ("normalizer", "value", "code", "options"),
    [
        (tools.normalize_service_category, "farmacia", "invalid_service_category", "primary_care"),
        (tools.normalize_service_category, None, "invalid_service_category", "mental_health"),
        (tools.normalize_age_group, "80+", "invalid_age_group", "75+"),
        (tools.normalize_age_group, None, "invalid_age_group", "65+"),
        (tools.normalize_scenario_action, "teletransportar", "invalid_scenario", "add_service"),
        (tools.normalize_scenario_action, None, "invalid_scenario", "change_threshold"),
    ],
)
def test_invalid_aliases_report_controlled_options(normalizer, value, code: str, options: str):
    with pytest.raises(DataContractError) as error:
        normalizer(value)
    assert error.value.code == code
    assert options in error.value.available_options


def test_public_tool_normalizes_human_service_and_age(monkeypatch):
    monkeypatch.setenv("GIPUZKOA360_DATA_DIR", str(tools.Path(__file__).parents[1] / "datos_preparados"))
    result = json.loads(tools.analizar_coincidencia(" ATENCIÓN_PRIMARIA ", "≥75", 1.0, "2025-01-01", 0.75))
    assert result["status"] == "ok"
    assert result["filters"]["service_category"] == "primary_care"
    assert result["filters"]["age_group"] == "75"


def test_public_tool_accepts_natural_age_phrase_from_g04(monkeypatch):
    monkeypatch.setenv("GIPUZKOA360_DATA_DIR", str(tools.Path(__file__).parents[1] / "datos_preparados"))
    result = json.loads(tools.analizar_coincidencia("atención primaria", "65 o más", 2.0, "2025-01-01", 0.75))
    assert result["status"] == "ok"
    assert result["filters"]["age_group"] == "65"
    assert result["rows_used"] == 88


def test_public_tool_rejects_unknown_category_as_json():
    result = json.loads(tools.analizar_acceso_servicios("farmacia"))
    assert result["status"] == "error"
    assert result["error_code"] == "service_category_not_found"
    assert set(result["available_options"]) == {"primary_care", "mental_health", "hospital", "other_health"}
