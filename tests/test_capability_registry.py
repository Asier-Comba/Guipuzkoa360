from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import main


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "datos_preparados" / "capabilities.json"


def test_registry_is_reproducible_and_inputs_are_current():
    before = REGISTRY.read_bytes()
    subprocess.run([sys.executable, "scripts/data/09_build_capabilities.py"], cwd=ROOT, check=True)
    assert REGISTRY.read_bytes() == before
    payload = json.loads(before)
    for item in payload["registry_inputs"]:
        path = ROOT / item["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]


def test_registry_reflects_real_dimensions_categories_and_periods():
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    assert payload["dimensions"]["demography"]["supported_age_groups"] == ["65+", "75+"]
    assert payload["dimensions"]["services"]["categories"] == [
        "hospital", "mental_health", "other_health", "primary_care"
    ]
    assert payload["dimensions"]["time"]["available_demographic_periods"] == ["2025-01-01"]
    assert payload["dimensions"]["time"]["available_service_periods"] == ["2026-09-20"]
    assert payload["constraints"]["arbitrary_age_thresholds"] is False


def test_general_age_question_returns_capability_not_an_invented_value(monkeypatch):
    monkeypatch.setenv("GIPUZKOA360_DATA_DIR", str(ROOT / "datos_preparados"))
    result = json.loads(main.consultar_capacidades("¿Puedo calcular población de 50 o más?"))
    assert result["status"] == "ok"
    assert [item["dimension"] for item in result["data"]] == ["demography"]
    demographic = result["data"][0]
    assert demographic["supported_age_groups"] == ["65+", "75+"]
    assert "50" not in demographic["supported_age_groups"]
    assert "lacking its own cumulative count" in demographic["cannot_exactly_derive"]


def test_capability_tool_is_strict_json_and_exposes_all_operations(monkeypatch):
    monkeypatch.setenv("GIPUZKOA360_DATA_DIR", str(ROOT / "datos_preparados"))
    raw = main.consultar_capacidades()
    assert "NaN" not in raw and "Infinity" not in raw
    result = json.loads(raw)
    assert result["status"] == "ok"
    assert len(result["operations"]) == 8
    assert {item["name"] for item in result["operations"]} == {
        "obtener_resumen_territorial", "comparar_municipios", "analizar_envejecimiento",
        "analizar_acceso_servicios", "analizar_coincidencia", "simular_escenario",
        "consultar_fuente", "consultar_capacidades",
    }


def test_portal_generalization_plan_is_large_and_diverse():
    cases = json.loads((ROOT / "tests/portal_generalization_cases.json").read_text(encoding="utf-8"))
    assert len(cases) >= 30
    assert len({item["id"] for item in cases}) == len(cases)
    categories = {item["category"] for item in cases}
    assert {
        "supported_age", "unsupported_age", "multitool", "open_question",
        "scenario", "error_recovery", "out_of_domain", "impossible_derivation",
    } <= categories
    assert any(len(item["expected_tools"]) > 1 for item in cases)
    assert any(not item["expected_tools"] for item in cases)
