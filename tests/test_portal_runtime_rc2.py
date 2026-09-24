from __future__ import annotations

import ast
import inspect
import json
import math
from pathlib import Path

import main
import tools


ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "obtener_resumen_territorial", "comparar_municipios", "analizar_envejecimiento",
    "analizar_acceso_servicios", "analizar_coincidencia", "simular_escenario", "consultar_fuente",
}


def _tool_name(item):
    return getattr(item, "name", getattr(item, "__name__", None))


def test_seven_decorated_wrappers_are_physical_and_unique_in_main():
    tree = ast.parse((ROOT / "agentes/gipuzkoa360/main.py").read_text(encoding="utf-8"))
    decorated = {
        node.name for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and any(isinstance(decorator, ast.Name) and decorator.id == "tool" for decorator in node.decorator_list)
    }
    assert decorated == EXPECTED
    names = [_tool_name(item) for item in main.TOOLS]
    assert len(names) == len(set(names)) == 7
    assert set(names) == EXPECTED


def test_tools_core_has_no_decorators_or_registration_list():
    source = (ROOT / "agentes/gipuzkoa360/tools.py").read_text(encoding="utf-8")
    assert "@tool" not in source
    assert "TOOLS = [" not in source


def test_studio_wrappers_do_not_expose_full_detail_payload():
    assert all("detalle" not in inspect.signature(item).parameters for item in main.TOOLS)


def test_core_full_payload_remains_available_offline(monkeypatch):
    monkeypatch.setenv("GIPUZKOA360_DATA_DIR", str(ROOT / "datos_preparados"))
    result = json.loads(tools.analizar_coincidencia(
        "primary_care", "65", 2, "2025-01-01", 0.75, detalle=True
    ))
    assert result["detail_level"] == "full"
    assert len(result["data"]) == result["rows_used"] == 88


def test_service_age_and_action_aliases():
    for value in ("atención primaria", "atencion primaria", "primary care", "primary_care"):
        assert tools.normalize_service_category(value) == "primary_care"
    for value in ("salud mental", "mental health", "mental_health"):
        assert tools.normalize_service_category(value) == "mental_health"
    for value in ("hospital", "hospitales"):
        assert tools.normalize_service_category(value) == "hospital"
    for value in ("otros", "otros servicios sanitarios", "other health", "other_health"):
        assert tools.normalize_service_category(value) == "other_health"
    for value in ("65", "65+", "≥65", ">=65"):
        assert tools.normalize_age_group(value) == "65"
    for value in ("75", "75+", "≥75", ">=75"):
        assert tools.normalize_age_group(value) == "75"
    assert tools.normalize_scenario_action("añadir servicio") == "add_service"
    assert tools.normalize_scenario_action("quitar servicio") == "remove_service"
    assert tools.normalize_scenario_action("cambiar umbral") == "change_threshold"


def test_unknown_alias_is_controlled_json(monkeypatch):
    monkeypatch.setenv("GIPUZKOA360_DATA_DIR", str(ROOT / "datos_preparados"))
    result = json.loads(main.analizar_acceso_servicios("farmacia", 1, "2025-01-01", ["Eibar"]))
    assert result["status"] == "error"
    assert result["error_code"] == "service_category_not_found"
    assert set(result["available_options"]) == {"hospital", "mental_health", "other_health", "primary_care"}


def test_compact_coincidence_matches_full_core(monkeypatch):
    monkeypatch.setenv("GIPUZKOA360_DATA_DIR", str(ROOT / "datos_preparados"))
    tools.clear_analysis_cache()
    full = tools._analysis().coincidencia("primary_care", "65+", 2, "2025-01-01", 0.75)
    compact = json.loads(main.analizar_coincidencia("atención primaria", "65+", 2, "2025-01-01", 0.75))
    full_highlighted = [row for row in full["data"] if row["highlighted"]]
    compact_highlighted = [row for row in compact["data"] if row["highlighted"]]
    assert compact["summary"]["joined_rows"] == len(full["data"]) == 88
    assert compact["summary"]["highlighted_count"] == len(full_highlighted) == 7
    assert compact_highlighted == full_highlighted
    assert len(compact["data"]) == 7
    assert len(json.dumps(compact, ensure_ascii=False)) < 12_000
    for field in ("period", "unit", "sources", "limitations"):
        assert compact[field]


def test_compact_scenario_only_returns_changed_municipalities(monkeypatch):
    monkeypatch.setenv("GIPUZKOA360_DATA_DIR", str(ROOT / "datos_preparados"))
    tools.clear_analysis_cache()
    aduna = tools._analysis().repo.municipality_lookup("Aduna")
    compact = json.loads(main.simular_escenario(
        "añadir servicio", "atención primaria", 2, "2025-01-01",
        aduna["latitude"], aduna["longitude"], "HYPOTHETICAL_ADUNA"
    ))
    assert compact["summary"]["total_result_rows"] == 88
    assert compact["summary"]["affected_rows"] >= 1
    assert any(row["municipality_name"] == "Aduna" for row in compact["data"])
    assert all(
        abs(row["difference_absolute_m"]) > 0.05
        or row["baseline_within_threshold"] != row["scenario_within_threshold"]
        for row in compact["data"]
    )
    assert compact["scenario"]["baseline"]["service_count"] == 148
    assert compact["scenario"]["scenario"]["service_count"] == 149
    assert all("baseline_distance_m" in row and "scenario_distance_m" in row for row in compact["data"])


def test_scenario_does_not_contaminate_next_normal_query(monkeypatch):
    monkeypatch.setenv("GIPUZKOA360_DATA_DIR", str(ROOT / "datos_preparados"))
    tools.clear_analysis_cache()
    before = main.analizar_acceso_servicios("primary_care", 2, "2025-01-01", ["Aduna"])
    aduna = tools._analysis().repo.municipality_lookup("Aduna")
    main.simular_escenario(
        "añadir servicio", "primary_care", 2, "2025-01-01",
        aduna["latitude"], aduna["longitude"], "TEMP_AUDIT",
    )
    after = main.analizar_acceso_servicios("primary_care", 2, "2025-01-01", ["Aduna"])
    assert after == before
    assert all(item["service_id"] != "TEMP_AUDIT" for item in tools._analysis().repo.services())


def test_non_finite_threshold_is_controlled_strict_json(monkeypatch):
    monkeypatch.setenv("GIPUZKOA360_DATA_DIR", str(ROOT / "datos_preparados"))
    raw = main.simular_escenario(
        "cambiar umbral", "primary_care", 1, "2025-01-01",
        nuevo_umbral_km=math.nan,
    )
    assert "NaN" not in raw
    result = json.loads(raw)
    assert result["status"] == "error"
    assert result["error_code"] == "invalid_threshold"


def test_scenario_numeric_inputs_never_leak_python_exceptions(monkeypatch):
    monkeypatch.setenv("GIPUZKOA360_DATA_DIR", str(ROOT / "datos_preparados"))
    invalid_threshold = json.loads(main.simular_escenario(
        "cambiar umbral", "primary_care", 1, "2025-01-01", nuevo_umbral_km="no-numérico"
    ))
    invalid_coordinates = json.loads(main.simular_escenario(
        "añadir servicio", "primary_care", 1, "2025-01-01", latitud="NaN", longitud=-2.0
    ))
    assert invalid_threshold["error_code"] == "invalid_threshold"
    assert invalid_coordinates["error_code"] == "invalid_coordinates"
    assert "could not convert" not in invalid_threshold["message"]
    assert "not supported" not in invalid_coordinates["message"]


def test_compact_output_never_suggests_hidden_detail_parameter(monkeypatch):
    monkeypatch.setenv("GIPUZKOA360_DATA_DIR", str(ROOT / "datos_preparados"))
    raw = main.analizar_acceso_servicios("primary_care", 2, "2025-01-01")
    assert "detalle" not in raw.casefold()


def test_context_paths_exist_and_runtime_has_no_forbidden_mechanisms():
    assert all((ROOT / path).is_file() for path in main.STUDIO_CONTEXT_FILES)
    source = (ROOT / "agentes/gipuzkoa360/portal/main.py").read_text(encoding="utf-8")
    core = (ROOT / "agentes/gipuzkoa360/portal/tools.py").read_text(encoding="utf-8")
    combined = source + core
    for forbidden in ("zipfile", "extractall", "TemporaryDirectory", "importlib", "requests", "urllib", "httpx", "C:\\\\Users"):
        assert forbidden not in combined


def test_follow_up_age_recalculation_changes_effective_filter(monkeypatch):
    monkeypatch.setenv("GIPUZKOA360_DATA_DIR", str(ROOT / "datos_preparados"))
    a = json.loads(main.analizar_coincidencia("primary care", "65+", 2, "2025-01-01", 0.75))
    b = json.loads(main.analizar_coincidencia("atención primaria", "75+", 3, "2025-01-01", 0.80))
    assert a["filters"]["age_group"] == "65"
    assert b["filters"]["age_group"] == "75"
    assert a["summary"]["highlighted_count"] == 7
    assert b["summary"]["highlighted_count"] == 4
