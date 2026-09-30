from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from agentes.gipuzkoa360_vnext import tools
from agentes.gipuzkoa360_vnext.session import CandidateSession


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).with_name("fixtures")


def registry():
    return tools._registry(ROOT)


def test_synthetic_evidence_and_capability_contracts():
    evidence = json.loads((FIXTURES / "TEST_SYNTHETIC_evidence_valid.json").read_text(encoding="utf-8"))
    tools.validate_evidence(evidence, {"TEST_SOURCE": {"reference_period": "TEST_PERIOD"}})
    capability = json.loads((FIXTURES / "TEST_SYNTHETIC_capability.json").read_text(encoding="utf-8"))
    assert capability["id"].startswith("TEST_")
    assert evidence["claims"][0]["value"] == 0


def test_registry_is_valid_and_does_not_enable_mobility_without_binding():
    entries = registry()
    assert len({item["id"] for item in entries}) == len(entries)
    assert {item["id"] for item in entries if item["enabled"]} == tools.TERRITORIAL_HANDLERS | tools.LOCAL_HANDLERS
    assert not next(item for item in entries if item["id"] == "plan_visit")["enabled"]


@pytest.mark.parametrize("mutation", ["top", "nested", "semantic_limits", "wrong_type", "bad_hash", "false_source", "missing_handler", "handler_schema", "false_coverage"])
def test_corrupt_capability_rejected(mutation):
    cap = copy.deepcopy(registry()[0])
    if mutation == "top":
        del cap["id"]
    elif mutation == "nested":
        del cap["coverage"]["periods"]
    elif mutation == "semantic_limits":
        del cap["semantic_limits"]
    elif mutation == "wrong_type":
        cap["coverage"]["entities"] = True
    elif mutation == "bad_hash":
        cap["required_data"][0]["sha256"] = "0" * 64
    elif mutation == "false_source":
        cap["source_ids"] = ["TEST_FALSE_SOURCE"]
    elif mutation == "missing_handler":
        cap["handler"] = "not_a_handler"
    elif mutation == "handler_schema":
        cap["input_fields"].append({"name": "TEST_UNKNOWN", "type": "string", "required": False, "allowed_values": []})
    elif mutation == "false_coverage":
        cap["coverage"]["entities"] = 89
    with pytest.raises(tools.ContractViolation):
        tools.validate_capability(cap, ROOT, tools._catalog(ROOT))


@pytest.mark.parametrize("raw", ['{"a":1,"a":2}', '{"x":NaN}', '{"x":Infinity}', '{"x":1e999}'])
def test_strict_json_rejects_duplicates_and_nonfinite(raw):
    with pytest.raises(tools.ContractViolation):
        tools.strict_loads(raw)


@pytest.mark.parametrize("mutation", ["request", "arguments", "value", "source", "period", "unit", "missing_denominator", "extra_key"])
def test_evidence_tampering_rejected(mutation):
    item = json.loads((FIXTURES / "TEST_SYNTHETIC_evidence_valid.json").read_text(encoding="utf-8"))
    catalog = {"TEST_SOURCE": {"reference_period": "TEST_PERIOD"}}
    if mutation == "request":
        item["execution"]["request_id"] = "other"
    elif mutation == "arguments":
        item["normalized_input"]["arguments"]["municipio"] = "other"
    elif mutation == "value":
        item["claims"][0]["value"] = 1
    elif mutation == "source":
        item["claims"][0]["source_ids"] = ["FALSE"]
    elif mutation == "period":
        item["claims"][0]["period"] = "OTHER_PERIOD"
    elif mutation == "unit":
        item["claims"][0]["evidence_path"] = "/data/0/distance_m"
        item["raw_result_json"] = '{"data":[{"distance_m":0}]}'
        item["raw_result_sha256"] = tools.digest(item["raw_result_json"])
    elif mutation == "missing_denominator":
        item["claims"][0]["label"] = "rate_per_10000_65_plus"
        item["claims"][0]["evidence_path"] = "/data/0/rate_per_10000_65_plus"
        item["raw_result_json"] = '{"data":[{"rate_per_10000_65_plus":0}]}'
        item["raw_result_sha256"] = tools.digest(item["raw_result_json"])
    elif mutation == "extra_key":
        item["unexpected"] = 1
    with pytest.raises(tools.ContractViolation):
        tools.validate_evidence(item, catalog)


def test_canonical_coincidence_recomputes_7_4_2():
    session = CandidateSession()
    first = session.ask("analizar_coincidencia", {"categoria_servicio": "primary_care", "grupo_edad": "65", "cuantil": 0.75, "umbral_km": 2.0})
    second = session.ask("seguimiento", {"grupo_edad": "75", "cuantil": 0.80, "umbral_km": 3.0})
    third = session.ask("seguimiento", {"grupo_edad": "65", "cuantil": 0.85, "umbral_km": 2.0})
    assert [item["status"] for item in (first, second, third)] == ["valid"] * 3
    assert [tools.strict_loads(item["raw_result_json"])["summary"]["highlighted_count"] for item in (first, second, third)] == [7, 4, 2]
    assert len({item["request_id"] for item in (first, second, third)}) == 3
    assert len({item["raw_result_sha256"] for item in (first, second, third)}) == 3


@pytest.mark.parametrize("name,args", [
    ("obtener_resumen_territorial", {"municipio": "Aduna"}),
    ("comparar_municipios", {"municipios": ["Eibar", "Tolosa"], "grupo_edad": "75", "categoria_servicio": "primary_care"}),
    ("analizar_envejecimiento", {"grupo_edad": "75", "top_n": 5}),
    ("analizar_acceso_servicios", {"categoria_servicio": "primary_care", "municipios": ["Aduna"]}),
    ("simular_escenario", {"accion": "change_threshold", "categoria_servicio": "primary_care", "nuevo_umbral_km": 2.0}),
    ("consultar_fuente", {"source_id": "EUSTAT_EMH_2025"}),
    ("consultar_capacidades", {}),
])
def test_every_enabled_handler_executes(name, args):
    result = tools.execute(name, args, "TEST_HANDLER")
    assert result["status"] == "valid", result.get("error")
    assert result["normalized_input"]["tool"] == name


def test_sessions_are_isolated():
    one, two = CandidateSession(), CandidateSession()
    first = one.ask("analizar_envejecimiento", {"grupo_edad": "65"})
    assert first["status"] == "valid"
    assert one.session_id != two.session_id
    with pytest.raises(tools.ContractViolation, match="followup_without_previous_request"):
        two.ask("seguimiento", {"grupo_edad": "75"})


@pytest.mark.parametrize("age", ["50", "70"])
def test_unsupported_age_has_no_claims(age):
    result = tools.execute("analizar_envejecimiento", {"grupo_edad": age}, "TEST_AGE")
    assert result["status"] == "error"
    assert result["claims"] == []
    assert result["error"]["origin"] == "domain"


def test_unknown_category_and_source_have_no_numbers():
    for name, args in [
        ("analizar_acceso_servicios", {"categoria_servicio": "farmacia"}),
        ("consultar_fuente", {"source_id": "TEST_FALSE_SOURCE"}),
    ]:
        result = tools.execute(name, args, "TEST_UNKNOWN")
        assert result["status"] in {"error", "unsupported"}
        assert result["claims"] == []
        assert result["error"] is not None


def test_only_explicit_equivalent_alias_is_repaired_once_and_disclosed():
    repaired = tools.execute("analizar_acceso_servicios", {"categoria_servicio": "atención primaria", "municipios": ["Aduna"]}, "TEST_REPAIR")
    assert repaired["status"] == "valid"
    assert repaired["normalized_input"]["arguments"]["categoria_servicio"] == "primary_care"
    assert len(repaired["assumptions"]) == 1 and "atención primaria" in repaired["assumptions"][0]
    unrelated = tools.execute("analizar_acceso_servicios", {"categoria_servicio": "farmacia"}, "TEST_NO_REPAIR")
    assert unrelated["claims"] == [] and unrelated["status"] != "valid"


def test_result_cannot_cite_catalog_only_source():
    result = tools.execute("obtener_resumen_territorial", {"municipio": "Aduna"}, "TEST_SOURCE_ATTRIBUTION")
    raw = tools.strict_loads(result["raw_result_json"])
    observed_sources = {item["source_id"] for item in raw["sources"]}
    assert result["status"] == "valid"
    assert all(set(claim["source_ids"]) <= observed_sources for claim in result["claims"])
    assert any("carecen de atribución" in note for note in result["limitations"])


def test_invalid_nonfinite_input_is_controlled():
    result = tools.execute("analizar_coincidencia", {"categoria_servicio": "primary_care", "cuantil": float("nan")}, "TEST_NAN")
    assert result["claims"] == []
    assert result["error"]["code"] == "invalid_arguments"
    assert result["normalized_input"]["arguments"] == {}


def test_domain_transport_and_unknown_failures_remain_distinct():
    domain = tools.execute("consultar_fuente", {"source_id": "TEST_FALSE_SOURCE"}, "TEST_DOMAIN")

    def transport(_handler, _args):
        raise tools.ObservedTransportError("HTTP 504 observado en transporte simulado")

    def unknown(_handler, _args):
        raise RuntimeError("private diagnostic")

    transmitted = tools.execute("consultar_fuente", {}, "TEST_TRANSPORT", transport=transport)
    unverified = tools.execute("consultar_fuente", {}, "TEST_UNKNOWN", transport=unknown)
    assert domain["error"]["origin"] == "domain"
    assert transmitted["error"]["origin"] == "transport"
    assert unverified["error"] == {
        "origin": "unknown", "code": "unverified_result", "message": "No se ha podido verificar el resultado.",
        "available_options": [], "safe_next_action": "Revisar los valores disponibles; si el fallo persiste, no usar el resultado.",
    }
    assert all(not item["claims"] for item in (domain, transmitted, unverified))


def test_result_source_and_period_contract_failure_blocks_all_claims():
    def fake(handler, kwargs):
        raw = tools.strict_loads(handler(**kwargs))
        raw["sources"] = [{"source_id": "TEST_FALSE_SOURCE"}]
        return tools.canonical(raw)

    result = tools.execute("analizar_envejecimiento", {}, "TEST_FALSE", transport=fake)
    assert result["error"]["code"] == "contract_violation"
    assert result["claims"] == []


def test_result_from_other_request_is_rejected():
    def substituted(handler, kwargs):
        wrong = dict(kwargs)
        wrong["cuantil"] = 0.85
        return handler(**wrong)

    result = tools.execute("analizar_coincidencia", {"categoria_servicio": "primary_care", "cuantil": 0.75}, "TEST_REQUEST_BIND", transport=substituted)
    assert result["error"]["code"] == "contract_violation"
    assert "request_mismatch" in result["error"]["message"]
    assert result["claims"] == []


def test_payload_over_limit_is_explicit_and_untruncated(monkeypatch):
    monkeypatch.setattr(tools, "MAX_EVIDENCE_BYTES", 100)
    result = tools.execute("analizar_coincidencia", {"categoria_servicio": "primary_care"}, "TEST_SIZE")
    assert result["error"]["code"] == "payload_too_large"
    assert result["raw_result_json"] is None
    assert result["claims"] == []
