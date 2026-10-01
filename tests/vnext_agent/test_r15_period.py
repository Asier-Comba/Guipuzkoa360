"""R15 public validation regressions; unchanged territorial calculations."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentes.gipuzkoa360_vnext import main, tools


ROOT = Path(__file__).resolve().parents[2]
PERIOD_CASES = [
    ("obtener_resumen_territorial", {"municipio": "Aduna"}),
    ("comparar_municipios", {"municipios": ["Eibar", "Tolosa"]}),
    ("analizar_envejecimiento", {"top_n": 2}),
    ("analizar_acceso_servicios", {"categoria_servicio": "primary_care", "municipios": ["Aduna"]}),
    ("analizar_coincidencia", {"categoria_servicio": "primary_care"}),
    ("simular_escenario", {"accion": "change_threshold", "categoria_servicio": "primary_care", "nuevo_umbral_km": 2.0}),
]
SOURCE_PERIOD_TOOLS = {"analizar_acceso_servicios", "simular_escenario"}


def assert_safe_input_error(result):
    assert result["status"] == "error"
    assert result["error"]["origin"] == "domain"
    assert result["error"]["code"] == "invalid_arguments"
    assert result["claims"] == []
    assert result["outcomes"] == []
    if "raw_result_json" in result:
        assert result["raw_result_json"] is None
        assert result["raw_result_sha256"] is None


@pytest.mark.parametrize("name,args", PERIOD_CASES)
@pytest.mark.parametrize("period", ["", "   ", "\t\n", 2025, False, [], {}, "2099-01-01"])
def test_invalid_explicit_period_never_produces_authoritative_numbers(name, args, period):
    request = {**args, "periodo": period}
    evidence = tools.execute(name, request, "R15_PERIOD_INVALID", root=ROOT)
    assert_safe_input_error(evidence)
    public = json.loads(getattr(main, name)(**request))
    assert_safe_input_error(public)


@pytest.mark.parametrize("name,args", PERIOD_CASES)
@pytest.mark.parametrize("mode", ["omitted", "none", "supported"])
def test_omitted_nullable_and_supported_period_preserve_engine_result(name, args, mode):
    request = dict(args)
    if mode == "none":
        request["periodo"] = None
    elif mode == "supported":
        if name in SOURCE_PERIOD_TOOLS:
            capability = next(cap for cap in tools._registry(ROOT) if cap["id"] == name)
            request["periodo"] = capability["coverage"]["periods"][0]
        else:
            request["periodo"] = tools.territorial.DataRepository(ROOT / "datos_preparados").available_periods()[0]
    evidence = tools.execute(name, request, "R15_PERIOD_VALID", root=ROOT)
    assert evidence["status"] == "valid", evidence["error"]
    expected = tools._territorial_handler(name, ROOT)(**request, detalle=True)
    assert tools.strict_loads(evidence["raw_result_json"]) == tools.strict_loads(expected)
    public = json.loads(getattr(main, name)(**request))
    assert public["status"] == "valid", public["error"]
    assert public["claims"]
    assert evidence["normalized_input"]["arguments"] == request


@pytest.mark.parametrize("name,args", [case for case in PERIOD_CASES if case[0] in SOURCE_PERIOD_TOOLS])
def test_source_period_validation_uses_own_coverage_not_demographic_default(name, args):
    capability = next(cap for cap in tools._registry(ROOT) if cap["id"] == name)
    demographic = tools.territorial.DataRepository(ROOT / "datos_preparados").available_periods()[0]
    assert demographic not in capability["coverage"]["periods"]
    assert_safe_input_error(tools.execute(name, {**args, "periodo": demographic}, "R15_NOT_THIS_SOURCE", root=ROOT))
    for period in capability["coverage"]["periods"]:
        result = tools.execute(name, {**args, "periodo": period}, "R15_SOURCE_PERIOD", root=ROOT)
        assert result["status"] == "valid", result["error"]
        assert result["effective_request"]["parameters"]["periodo"] == period
        assert tools.strict_loads(result["raw_result_json"]) == tools.strict_loads(
            tools._territorial_handler(name, ROOT)(**args, periodo=period, detalle=True))


@pytest.mark.parametrize("name,args", [case for case in PERIOD_CASES if case[0] not in SOURCE_PERIOD_TOOLS])
def test_demographic_period_does_not_accept_unrelated_source_date(name, args):
    result = tools.execute(name, {**args, "periodo": "2026-09-20"}, "R15_DEMOGRAPHIC_PERIOD", root=ROOT)
    assert_safe_input_error(result)
    assert "period_not_found" in result["error"]["message"]


@pytest.mark.parametrize("name,args", [
    ("obtener_resumen_territorial", {"municipio": "   "}),
    ("comparar_municipios", {"municipios": ["Eibar", "   "]}),
    ("analizar_envejecimiento", {"grupo_edad": "   "}),
    ("analizar_acceso_servicios", {"categoria_servicio": "primary_care", "municipios": ["   "]}),
    ("analizar_coincidencia", {"categoria_servicio": "   "}),
    ("simular_escenario", {"accion": "add_service", "categoria_servicio": "primary_care", "latitud": 43, "longitud": -2, "service_id": "   "}),
    ("consultar_fuente", {"source_id": "   "}),
    ("consultar_capacidades", {"pregunta_o_dimension": "   "}),
])
def test_whitespace_is_rejected_without_coercion_or_defaults(name, args):
    evidence = tools.execute(name, args, "R15_WHITESPACE", root=ROOT)
    assert_safe_input_error(evidence)
    assert evidence["normalized_input"]["arguments"] == args


@pytest.mark.parametrize("action,values", [
    ("add_service", {"latitud": 43, "longitud": -2, "nuevo_umbral_km": 2}),
    ("remove_service", {"service_id": "TEST_SERVICE", "latitud": 43}),
    ("remove_service", {"service_id": "TEST_SERVICE", "longitud": -2}),
    ("remove_service", {"service_id": "TEST_SERVICE", "nuevo_umbral_km": 2}),
    ("change_threshold", {"nuevo_umbral_km": 2, "latitud": 43, "longitud": -2}),
    ("change_threshold", {"nuevo_umbral_km": 2, "latitud": 999, "longitud": -999}),
    ("change_threshold", {"nuevo_umbral_km": 2, "service_id": "TEST_SERVICE"}),
    ("add_service", {}),
    ("remove_service", {}),
    ("change_threshold", {}),
])
def test_scenario_parameters_must_belong_to_selected_action(action, values):
    args = {"accion": action, "categoria_servicio": "primary_care", **values}
    evidence = tools.execute("simular_escenario", args, "R15_ACTION_FIELDS", root=ROOT)
    assert_safe_input_error(evidence)
    assert "arguments:accion:" in evidence["error"]["message"]


@pytest.mark.parametrize("action", ["change_threshold", "cambiar umbral"])
def test_scenario_alias_and_null_unused_fields_preserve_supported_engine_result(action):
    args = {"accion": action, "categoria_servicio": "primary_care", "nuevo_umbral_km": 2,
            "latitud": None, "longitud": None, "service_id": None}
    evidence = tools.execute("simular_escenario", args, "R15_ACTION_ALIAS", root=ROOT)
    assert evidence["status"] == "valid", evidence["error"]
    expected = tools._territorial_handler("simular_escenario", ROOT)(**args, detalle=True)
    assert tools.strict_loads(evidence["raw_result_json"]) == tools.strict_loads(expected)


@pytest.mark.parametrize("threshold", [None, 0, -1, 101])
@pytest.mark.parametrize("category", [None, "primary_care"])
def test_comparison_never_accepts_invalid_threshold_even_without_service_category(threshold, category):
    args = {"municipios": ["Beasain", "Ordizia"], "umbral_km": threshold, "categoria_servicio": category}
    assert_safe_input_error(tools.execute("comparar_municipios", args, "R15_THRESHOLD", root=ROOT))
    assert_safe_input_error(json.loads(main.comparar_municipios(**args)))


@pytest.mark.parametrize("name,args", [
    ("analizar_envejecimiento", {"grupo_edad": None}),
    ("analizar_envejecimiento", {"medida": None}),
    ("analizar_envejecimiento", {"top_n": None}),
    ("analizar_envejecimiento", {"top_n": 0}),
    ("analizar_envejecimiento", {"top_n": 101}),
    ("analizar_coincidencia", {"categoria_servicio": "primary_care", "cuantil": None}),
    ("analizar_coincidencia", {"categoria_servicio": "primary_care", "cuantil": 0.49}),
    ("analizar_coincidencia", {"categoria_servicio": "primary_care", "cuantil": 0.96}),
    ("simular_escenario", {"accion": "change_threshold", "categoria_servicio": "primary_care", "nuevo_umbral_km": 0}),
    ("simular_escenario", {"accion": "change_threshold", "categoria_servicio": "primary_care", "nuevo_umbral_km": 101}),
])
def test_nonnullable_and_existing_numeric_engine_limits_are_public_input_contract(name, args):
    assert_safe_input_error(tools.execute(name, args, "R15_NON_NULLABLE", root=ROOT))


@pytest.mark.parametrize("name,args", [
    ("comparar_municipios", {"municipios": ["Beasain", "Ordizia"], "umbral_km": 100}),
    ("analizar_envejecimiento", {"top_n": 1}),
    ("analizar_envejecimiento", {"top_n": 100}),
    ("analizar_coincidencia", {"categoria_servicio": "primary_care", "cuantil": 0.5}),
    ("analizar_coincidencia", {"categoria_servicio": "primary_care", "cuantil": 0.95}),
    ("simular_escenario", {"accion": "change_threshold", "categoria_servicio": "primary_care", "nuevo_umbral_km": 100}),
])
def test_existing_inclusive_numeric_limits_remain_usable(name, args):
    result = tools.execute(name, args, "R15_NUMERIC_BOUNDARY", root=ROOT)
    assert result["status"] == "valid", result["error"]


def test_source_lookup_preserves_existing_general_derivation_method_and_limits():
    source_id = "EUSTAT_EMH_2025"
    evidence = tools.execute("consultar_fuente", {"source_id": source_id}, "R15_SOURCE_METHOD", root=ROOT)
    before = tools.canonical(evidence)
    public = json.loads(tools.public_result(evidence, root=ROOT))
    source = next(item for item in public["source_metadata"] if item["source_id"] == source_id)
    catalog = tools._catalog(ROOT)[source_id]
    assert source["method"] == catalog["method"]
    assert source["limitations"] == catalog["limitations"]
    assert source["reference_period"] == catalog["reference_period"]
    assert "1949" in source["method"]
    assert tools.canonical(evidence) == before


@pytest.mark.parametrize("name,args", PERIOD_CASES)
def test_public_period_allowed_values_match_actual_selector_without_changing_source_coverage(name, args):
    evidence = tools.execute("consultar_capacidades", {"pregunta_o_dimension": name}, "R15_PERIOD_POLICY", root=ROOT)
    before = tools.canonical(evidence)
    public = json.loads(tools.public_result(evidence, root=ROOT))
    capability = next(item for item in public["capabilities"] if item["id"] == name)
    original = next(item for item in tools._registry(ROOT) if item["id"] == name)
    expected = original["coverage"]["periods"] if name in SOURCE_PERIOD_TOOLS else tools.territorial.DataRepository(ROOT / "datos_preparados").available_periods()
    field = next(item for item in capability["input_fields"] if item["name"] == "periodo")
    assert field["allowed_values"] == expected
    assert field["required"] is False
    assert field["nullable"] is True
    policy = capability["period_policy"]
    assert policy["allowed_values"] == expected
    assert policy["meaning"] == ("source_reference_only_not_historical_filter" if name in SOURCE_PERIOD_TOOLS else "demographic_selector")
    assert policy["omitted_or_null"] == ("current_sources_with_their_distinct_periods" if name in SOURCE_PERIOD_TOOLS else "single_available_period_else_request_period")
    assert policy["explicit_invalid"] == "reject_without_numeric_claims"
    assert capability["coverage"]["periods"] == original["coverage"]["periods"]
    assert tools.canonical(evidence) == before
    for period in expected:
        result = tools.execute(name, {**args, "periodo": period}, "R15_ADVERTISED_PERIOD", root=ROOT)
        assert result["status"] == "valid", result["error"]


@pytest.mark.parametrize("name,args", [case for case in PERIOD_CASES if case[0] not in SOURCE_PERIOD_TOOLS])
def test_multiple_demographic_periods_require_selection_never_choose_latest(monkeypatch, name, args):
    existing = tools.territorial.DataRepository(ROOT / "datos_preparados").available_periods()
    monkeypatch.setattr(tools.territorial.DataRepository, "available_periods", lambda self: existing + ["TEST_OTHER_PERIOD"])
    for request in (args, {**args, "periodo": None}):
        result = tools.execute(name, request, "R15_MULTIPLE_PERIODS", root=ROOT)
        assert_safe_input_error(result)
        assert "period_required" in result["error"]["message"]
