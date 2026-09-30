"""R4 adversarial results supplied through the real execute boundary."""

from __future__ import annotations

import pytest

from agentes.gipuzkoa360_vnext import tools
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def substituted(changes):
    def transport(handler, call_args):
        return handler(**{**call_args, **changes})
    return transport


def mutated(change):
    def transport(handler, call_args):
        raw = tools.strict_loads(handler(**call_args))
        change(raw)
        return tools.canonical(raw)
    return transport


@pytest.mark.parametrize("name,args,transport", [
    ("obtener_resumen_territorial", {"municipio": "Eibar"}, substituted({"municipio": "Tolosa"})),
    ("comparar_municipios", {"municipios": ["Eibar", "Tolosa"], "grupo_edad": "65"}, substituted({"municipios": ["Eibar", "Aduna"]})),
    ("analizar_acceso_servicios", {"categoria_servicio": "primary_care", "municipios": ["Eibar", "Tolosa"]}, substituted({"municipios": ["Eibar", "Aduna"]})),
    ("simular_escenario", {"accion": "add_service", "categoria_servicio": "primary_care", "latitud": 43.0, "longitud": -2.0, "service_id": "TEST_HYPOTHETICAL"}, substituted({"latitud": 43.1})),
    ("simular_escenario", {"accion": "add_service", "categoria_servicio": "primary_care", "latitud": 43.0, "longitud": -2.0, "service_id": "TEST_HYPOTHETICAL"}, substituted({"service_id": "TEST_OTHER"})),
    ("simular_escenario", {"accion": "change_threshold", "categoria_servicio": "primary_care", "nuevo_umbral_km": 2.0}, substituted({"nuevo_umbral_km": 3.0})),
    ("analizar_envejecimiento", {"grupo_edad": "65"}, mutated(lambda raw: raw["filters"].pop("age_group"))),
    ("analizar_envejecimiento", {}, substituted({"grupo_edad": "75"})),
    ("analizar_envejecimiento", {"periodo": "2025-01-01"}, mutated(lambda raw: raw["filters"].update(period="2024-01-01"))),
    ("analizar_coincidencia", {"categoria_servicio": "primary_care", "umbral_km": 2.0, "cuantil": 0.75}, mutated(lambda raw: raw["filters"].update(threshold_km=0.75, quantile_threshold=2.0))),
])
def test_substituted_request_cannot_produce_claims(name, args, transport):
    result = tools.execute(name, args, "TEST_R4_BINDING", transport=transport)
    assert result["status"] != "valid"
    assert result["claims"] == []
    assert result["error"]["code"] == "contract_violation"


def test_w3_highlighted_count_is_municipalities():
    result = tools.execute("analizar_coincidencia", {"categoria_servicio": "primary_care", "grupo_edad": "65", "umbral_km": 2.0, "cuantil": 0.75}, "TEST_W3_UNIT")
    claim = next(item for item in result["claims"] if item["label"] == "highlighted_count")
    assert claim["value"] == 7
    assert claim["unit"] == "municipios"


def test_w3_rate_without_numerator_source_is_not_a_claim():
    result = tools.execute("obtener_resumen_territorial", {"municipio": "Aduna"}, "TEST_W3_RATE")
    raw = tools.strict_loads(result["raw_result_json"])
    assert {source["source_id"] for source in raw["sources"]} == {"EUSTAT_EMH_2025"}
    assert all("rate_per_10000" not in claim["evidence_path"] for claim in result["claims"])


def test_reordered_same_municipalities_are_allowed():
    result = tools.execute("comparar_municipios", {"municipios": ["Eibar", "Tolosa"]}, "TEST_R4_ORDER", transport=substituted({"municipios": ["Tolosa", "Eibar"]}))
    assert result["status"] == "valid", result.get("error")


@pytest.mark.parametrize("mutation", ["numerator", "denominator", "entity", "unit", "period", "source_role", "rounding"])
def test_rate_lineage_mutations_are_rejected(mutation):
    result = tools.execute("obtener_resumen_territorial", {"municipio": "Eibar"}, "TEST_R4_RATE")
    assert result["status"] == "valid"
    claim = next(item for item in result["claims"] if "per_10000" in item["metric_id"])
    if mutation == "numerator":
        claim["numerator"]["value"] += 1
    elif mutation == "denominator":
        claim["denominator"]["value"] += 1
    elif mutation == "entity":
        claim["entity_id"] = "20071"
    elif mutation == "unit":
        claim["unit"] = "personas"
    elif mutation == "period":
        claim["reference_periods"][0]["period"] = "2099-01-01"
    elif mutation == "source_role":
        claim["source_refs"][1]["role"] = "denominator"
    elif mutation == "rounding":
        claim["value"] += 0.01
    with pytest.raises(tools.ContractViolation):
        tools.validate_evidence(result, tools._catalog(ROOT))


@pytest.mark.parametrize("mutation", ["numerator", "denominator", "entity", "period", "source", "rounding", "field", "hash", "missing_ref"])
def test_percentage_lineage_mutations_are_rejected(mutation):
    result = tools.execute("analizar_envejecimiento", {"grupo_edad": "65", "medida": "percentage"}, "TEST_R4_PERCENT")
    assert result["status"] == "valid"
    claim = next(item for item in result["claims"] if item["metric_id"] == "value")
    assert claim["numerator"]["data_ref"]
    if mutation == "numerator":
        claim["numerator"]["value"] += 1
    elif mutation == "denominator":
        claim["denominator"]["value"] += 1
    elif mutation == "entity":
        claim["entity_id"] = "20071"
    elif mutation == "period":
        claim["numerator"]["period"] = "2099-01-01"
    elif mutation == "source":
        claim["numerator"]["source_id"] = "ODE_HEALTH_CENTRES_2026"
    elif mutation == "rounding":
        claim["value"] += 0.01
    elif mutation == "field":
        claim["numerator"]["data_ref"]["field"] = "population_total"
    elif mutation == "hash":
        claim["numerator"]["data_ref"]["sha256"] = "0" * 64
    elif mutation == "missing_ref":
        claim["numerator"]["data_ref"] = None
    with pytest.raises(tools.ContractViolation):
        tools.validate_evidence(result, tools._catalog(ROOT))


def test_model_view_excludes_unattributed_raw_numbers():
    evidence = tools.execute("obtener_resumen_territorial", {"municipio": "Aduna"}, "TEST_VIEW_ADUNA")
    assert "rate_per_10000" in evidence["raw_result_json"]
    view = tools.strict_loads(tools.public_result(evidence))
    assert "raw_result_json" not in view
    assert all("rate_per_10000" not in claim["evidence_path"] for claim in view["claims"])
    assert view["selection"]["total_entities"] == view["selection"]["returned_entities"] == 1


def test_model_view_keeps_explicit_comparison_complete():
    evidence = tools.execute("comparar_municipios", {"municipios": ["Eibar", "Tolosa"], "categoria_servicio": "primary_care"}, "TEST_VIEW_COMPARE")
    view = tools.strict_loads(tools.public_result(evidence))
    assert view["status"] == "valid"
    assert view["selection"]["total_entities"] == 2
    assert view["selection"]["returned_entities"] == 2
    assert {claim["entity_label"] for claim in view["claims"] if claim["entity_type"] == "municipality"} == {"Eibar", "Tolosa"}


def test_model_view_broad_query_declares_selection_and_bounded_bytes():
    evidence = tools.execute("analizar_acceso_servicios", {"categoria_servicio": "primary_care"}, "TEST_VIEW_BROAD")
    rendered = tools.public_result(evidence)
    view = tools.strict_loads(rendered)
    assert view["selection"]["total_entities"] == 88
    assert view["selection"]["returned_entities"] == 10
    assert view["selection"]["omitted_entities"] == 78
    assert len(rendered.encode("utf-8")) <= tools.MAX_PUBLIC_BYTES


def test_model_view_payload_over_limit_fails_without_partial_claims(monkeypatch):
    evidence = tools.execute("analizar_coincidencia", {"categoria_servicio": "primary_care"}, "TEST_VIEW_LIMIT")
    monkeypatch.setattr(tools, "MAX_PUBLIC_BYTES", 100)
    view = tools.strict_loads(tools.public_result(evidence))
    assert view["status"] == "error"
    assert view["claims"] == []
    assert view.get("error", {}).get("code", view.get("code")) == "public_payload_too_large"
    assert len(tools.public_result(evidence).encode("utf-8")) <= 100
