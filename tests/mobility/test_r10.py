import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from scripts.mobility import build_r9, build_r10, verify_candidate_parity_r10 as parity


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/vnext/w1"


def load(path):
    return json.loads((DOC / path).read_text(encoding="utf-8"))


def test_r9_historical_evidence_is_preserved_but_generator_is_corrected():
    historical = DOC / "integration_r9/W1_HANDSHAKE_R9.json"
    assert hashlib.sha256(historical.read_bytes()).hexdigest() == "090335ab9e18b76a0dea311408aeff2a913289c7368f0801ac02a70031f056d6"
    assert load("integration_r9/W1_HANDSHAKE_R9.json")["boundaries"]["available_capability_count"] == 20
    answerability = load("MOBILITY_ANSWERABILITY_R8.json")["capabilities"]
    counts = build_r9.capability_status_counts(answerability)
    assert counts["described_entry_count"] == 25
    assert counts["available_entry_count"] == 9
    assert counts["unavailable_entry_count"] == 11
    assert counts["out_of_scope_entry_count"] == 5
    assert counts["executable_tool_count"] is None


def test_r10_handshake_is_compact_schema_valid_and_hash_bound():
    handshake_path = DOC / "integration_r10/W1_HANDSHAKE_R10.json"
    handshake = json.loads(handshake_path.read_text(encoding="utf-8"))
    schema = load("integration_r10/W1_HANDSHAKE_R10.schema.json")
    assert set(schema["required"]) <= set(handshake)
    assert set(handshake) <= set(schema["properties"])
    assert handshake["handshake_version"] == schema["properties"]["handshake_version"]["const"]
    assert handshake_path.stat().st_size < 30_000
    assert handshake["handshake_version"] == "r10.0-support"
    assert "available_capability_count" not in handshake["boundaries"]
    answerability = handshake["boundaries"]["answerability"]
    assert (answerability["available_entry_count"], answerability["unavailable_entry_count"], answerability["out_of_scope_entry_count"]) == (9, 11, 5)
    assert handshake["boundaries"]["producer_interfaces"]["count"] == 3
    assert handshake["runtime"]["package_sha256"] == build_r10.PACKAGE_SHA
    for item in handshake["refs"] + [handshake["capability_descriptor_ref"], handshake["status_error_semantics_ref"], handshake["caller_provenance_ref"]]:
        target = ROOT / item["path"]
        assert target.stat().st_size == item["bytes"]
        assert hashlib.sha256(target.read_bytes()).hexdigest() == item["sha256"]


def test_status_error_mapping_uses_observed_code_and_safe_generic_unknown():
    report = load("STATUS_ERROR_SEMANTICS_R10.json")
    observed = {(row["status"], row["technical_code_preserved"]): row for row in report["cases"]}
    required = {("unknown", "date_not_validated"), ("unknown", "invalid_health_snapshot"),
                ("unsupported", "catalog_scope"), ("unsupported", "cross_day_appointment"),
                ("error", "invalid_request"), ("no_feasible_journey", "no_pair_in_complete_direct_search")}
    assert required <= set(observed)
    generic = observed[("unknown", "future_unknown_code")]["user_facing"].casefold()
    assert all(word not in generic for word in ("fecha", "http", "red", "autobús"))
    assert "evidencia" in generic


def test_caller_provenance_does_not_claim_human_authorship():
    report = load("CALLER_PROVENANCE_R10.json")
    rows = {row["case_id"]: row for row in report["cases"]}
    omitted = rows["default_omitted"]
    explicit = rows["default_explicit_same_value"]
    changed = rows["explicit_distinct_value"]
    assert omitted["total_s"] == explicit["total_s"]
    assert omitted["boarding_margin_origin"] == "model_default"
    assert explicit["boarding_margin_origin"] == changed["boarding_margin_origin"] == "human_explicit"
    assert changed["initial_wait_s"] != omitted["initial_wait_s"]
    assert "caller" in report["rule"] and "does not prove human authorship" in report["rule"]


def make_package(tmp_path, adapter, *, contract="0.3.1", pin=parity.RUNTIME_PIN):
    package = tmp_path / "candidate.zip"
    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr("mobility_adapter.py", adapter)
    raw = package.read_bytes()
    member = adapter.encode()
    manifest = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "w1_pin": pin,
                "w1_contract": contract, "members": {"mobility_adapter.py": {"bytes": len(member), "sha256": hashlib.sha256(member).hexdigest()}}}
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return package, path


FAKE_ADAPTER = '''import json
def _claims(raw):
    if raw["status"] != "ok": return []
    rows=[{"evidence_path":"/itinerary/total_s","value":raw["itinerary"]["total_s"]}]
    rows += [{"evidence_path":"/components_s/"+k,"value":v} for k,v in raw["components_s"].items()]
    return rows
def consume_plan_visit(provider, request, request_id):
    raw=provider.plan_visit(request)
    return {"raw_result_json":json.dumps(raw,ensure_ascii=False),"outcomes":[{"status":raw["status"]}],"claims":_claims(raw),"limitations":raw["limitations"],"assumptions":raw["assumptions"]}
def consume_compare_visits(provider, requests, request_id):
    raw=provider.compare_visits(requests)
    return {"raw_result_json":json.dumps(raw,ensure_ascii=False),"outcomes":[{"status":x["status"]} for x in raw["results"]],"claims":[],"limitations":[],"assumptions":[]}
'''


def test_parity_runner_passes_semantically_complete_projection(tmp_path):
    package, manifest = make_package(tmp_path, FAKE_ADAPTER)
    report = parity.run(package, manifest, parity.RUNTIME_PIN)
    assert report["status"] == "PASS"
    assert report["candidate_package_tested"] is True
    assert report["classifications"]["WRONG_VALUE"] == 0
    assert len(report["cases"]) == 14


def test_parity_runner_returns_not_run_for_pre_r6_candidate(tmp_path):
    package, manifest = make_package(tmp_path, FAKE_ADAPTER, contract="0.2.0", pin="725a7b73ae0381092cd80edc41b8a25432d75fcd")
    report = parity.run(package, manifest, parity.RUNTIME_PIN)
    assert report["status"] == "NOT_RUN"
    assert report["candidate_package_tested"] is False


def test_parity_runner_fails_closed_on_package_manifest_mismatch(tmp_path):
    package, manifest = make_package(tmp_path, FAKE_ADAPTER)
    data = json.loads(manifest.read_text())
    data["sha256"] = "0" * 64
    manifest.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="bytes/hash"):
        parity.run(package, manifest, parity.RUNTIME_PIN)


def test_r10_manifest_references_exact_files_and_runtime_stays_frozen():
    manifest = load("integration_r10/INTEGRATION_MANIFEST_R10.json")
    for item in manifest["files"]:
        path = ROOT / item["path"]
        assert path.stat().st_size == item["bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
    assert hashlib.sha256((ROOT / "prototypes/ir_y_volver/provider_r6.py").read_bytes()).hexdigest() == "c9fe7e4c8078ba7f9bf2eb2a51e050b729d9f01e6021dbcc6909f951d2e936e8"
