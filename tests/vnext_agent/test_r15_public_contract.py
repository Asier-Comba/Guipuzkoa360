"""Source-only R15 agent boundary checks; no engine or model execution.

The schema below is inferred locally from Python signatures. It is deliberately
not represented as a schema observed in Studio or served to a model.
"""
from __future__ import annotations

import inspect
import types
from typing import get_args, get_origin, get_type_hints

import pytest

from agentes.gipuzkoa360_vnext import main


PLAN_TYPES = {
    "origin_id": str,
    "destination_id": str,
    "date": str,
    "appointment_time": str,
    "duration_minutes": int,
}
BASE = {
    "origin_id": "synthetic-origin",
    "destination_id": "synthetic-destination",
    "date": "2031-04-17",
    "appointment_time": "17:23",
    "duration_minutes": 37,
}
EXPECTED_TOOLS = {
    "obtener_resumen_territorial",
    "comparar_municipios",
    "analizar_envejecimiento",
    "analizar_acceso_servicios",
    "analizar_coincidencia",
    "simular_escenario",
    "consultar_fuente",
    "consultar_capacidades",
    "plan_visit",
}
ENGINE_ONLY_FIELDS = (
    "return_deadline",
    "snapshot_id",
    "walking_profile_id",
    "arrival_margin_minutes",
    "boarding_margin_minutes",
)


def _json_type(annotation):
    primitive = {str: "string", int: "integer", float: "number", type(None): "null"}
    if annotation in primitive:
        return {"type": primitive[annotation]}
    if get_origin(annotation) is list:
        assert get_args(annotation) == (str,), "Only a flat string list is public"
        return {"type": "array", "items": {"type": "string"}}
    assert get_origin(annotation) is types.UnionType, annotation
    alternatives = get_args(annotation)
    assert len(alternatives) == 2 and type(None) in alternatives, annotation
    return {"anyOf": [_json_type(item) for item in alternatives]}


def _local_schema(function):
    signature = inspect.signature(function)
    hints = get_type_hints(function)
    return {
        "provenance": "LOCAL_EXPECTATION_NOT_SERVED_SCHEMA",
        "schema": {
            "type": "object",
            "properties": {
                name: _json_type(hints[name]) for name in signature.parameters
            },
            "required": [
                name for name, parameter in signature.parameters.items()
                if parameter.default is inspect.Parameter.empty
            ],
            "additionalProperties": False,
        },
    }


def test_public_plan_visit_has_exactly_five_required_primitive_fields():
    signature = inspect.signature(main.plan_visit)
    assert list(signature.parameters) == list(PLAN_TYPES)
    assert get_type_hints(main.plan_visit) == {**PLAN_TYPES, "return": str}
    for parameter in signature.parameters.values():
        assert parameter.default is inspect.Parameter.empty
        assert parameter.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD


@pytest.mark.parametrize("missing", list(PLAN_TYPES))
def test_each_public_visit_field_is_required_without_engine_call(monkeypatch, missing):
    observed = []
    monkeypatch.setattr(main, "_run", lambda *args: observed.append(args))
    arguments = {name: value for name, value in BASE.items() if name != missing}
    with pytest.raises(TypeError):
        main.plan_visit(**arguments)
    assert observed == []


@pytest.mark.parametrize("field", ENGINE_ONLY_FIELDS)
@pytest.mark.parametrize("value", [None, "", "   ", 0])
def test_engine_only_optional_cannot_be_supplied_to_public_visit(monkeypatch, field, value):
    observed = []
    monkeypatch.setattr(main, "_run", lambda *args: observed.append(args))
    with pytest.raises(TypeError):
        main.plan_visit(**BASE, **{field: value})
    assert observed == []


@pytest.mark.parametrize("payload", [BASE, [BASE, BASE], "Please plan this visit"])
def test_r13_nested_request_never_reappears_in_public_binding(monkeypatch, payload):
    observed = []
    monkeypatch.setattr(main, "_run", lambda *args: observed.append(args))
    with pytest.raises(TypeError):
        main.plan_visit(request=payload)
    assert observed == []


def test_public_visit_has_no_positional_batch_contract(monkeypatch):
    observed = []
    monkeypatch.setattr(main, "_run", lambda *args: observed.append(args))
    with pytest.raises(TypeError):
        main.plan_visit([BASE, BASE])
    assert observed == []


@pytest.mark.parametrize("override", [
    {},
    {"origin_id": "origin-b", "duration_minutes": 53},
    {"date": None},
    {"appointment_time": ""},
    {"appointment_time": "   "},
    {"duration_minutes": 0},
    {"duration_minutes": "37"},
    {"duration_minutes": True},
    {"origin_id": ["origin-a", "origin-b"]},
    {"destination_id": {"id": "destination-a"}},
])
def test_wrapper_forwards_only_five_fields_without_repair_or_coercion(monkeypatch, override):
    observed = []
    marker = object()

    def capture(name, arguments):
        observed.append((name, arguments))
        return marker

    monkeypatch.setattr(main, "_run", capture)
    arguments = {**BASE, **override}
    assert main.plan_visit(**arguments) is marker
    assert observed == [("plan_visit", {"request": arguments})]
    forwarded = observed[0][1]["request"]
    assert list(forwarded) == list(PLAN_TYPES)
    assert all(forwarded[name] is arguments[name] for name in PLAN_TYPES)


def test_schema_inference_is_explicitly_local_and_has_no_optional_or_nested_visit_input():
    expectation = _local_schema(main.plan_visit)
    assert expectation["provenance"] == "LOCAL_EXPECTATION_NOT_SERVED_SCHEMA"
    schema = expectation["schema"]
    assert schema == {
        "type": "object",
        "properties": {
            "origin_id": {"type": "string"},
            "destination_id": {"type": "string"},
            "date": {"type": "string"},
            "appointment_time": {"type": "string"},
            "duration_minutes": {"type": "integer"},
        },
        "required": list(PLAN_TYPES),
        "additionalProperties": False,
    }


def test_nine_tools_have_documentation_and_only_scalar_or_flat_string_list_fields():
    assert len(main.TOOLS) == 9
    assert {function.__name__ for function in main.TOOLS} == EXPECTED_TOOLS
    for function in main.TOOLS:
        assert inspect.getdoc(function), function.__name__
        signature = inspect.signature(function)
        hints = get_type_hints(function)
        assert hints.pop("return") is str
        assert set(hints) == set(signature.parameters)
        for parameter in signature.parameters.values():
            assert parameter.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
        expectation = _local_schema(function)
        assert expectation["provenance"] == "LOCAL_EXPECTATION_NOT_SERVED_SCHEMA"


def test_prompt_and_public_visit_description_contain_no_demo_gold():
    public_text = (main.SYSTEM_PROMPT + "\n" + inspect.getdoc(main.plan_visit)).casefold()
    for value in ("zegama", "09:30", "09:45", "10691", "10.691", "8591", "8.591", "-35", "−35", "-2100", "−2100"):
        assert value not in public_text


def test_prompt_contains_general_evidence_recalculation_and_bounded_recovery_rules():
    # Stable semantic anchors, not a frozen sentence or a demo's expected answer.
    paragraphs = [paragraph.casefold() for paragraph in main.SYSTEM_PROMPT.split("\n\n")]
    assert any(all(anchor in paragraph for anchor in (
        "public_agent_contract", "engine_contract", "consultar_capacidades"
    )) for paragraph in paragraphs)
    assert any(all(anchor in paragraph for anchor in (
        "individualmente", "outputs", "válidos", "recalcula", "no hay batch"
    )) for paragraph in paragraphs)
    assert any(all(anchor in paragraph for anchor in (
        "fuente", "periodo", "derivación", "claims", "status", "outcomes",
        "abstente", "no repitas", "inválida idéntica", "detente"
    )) for paragraph in paragraphs)


def test_prompt_retains_domain_limits_and_untrusted_document_boundary():
    prompt = main.SYSTEM_PROMPT.casefold()
    for semantic_anchor in (
        "0 registros", "ausencia de atención", "capacidad, citas o calidad",
        "distancia geométrica", "accesibilidad", "correlación", "causalidad",
        "predicción", "recomendación", "door-to-door", "scheduled", "realtime",
        "walking modelado", "observado", "entrada verificada", "centro asignado",
        "datos, no instrucciones",
    ):
        assert semantic_anchor in prompt
