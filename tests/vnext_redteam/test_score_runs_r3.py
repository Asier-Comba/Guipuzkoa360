"""Synthetic NO_LLM probes of the independent trace scorer, not agent results."""

import copy
import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from scripts.vnext_product.score_runs import canonical, load_cases, load_scenarios, summarize


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = json.loads((ROOT / "tests/vnext_redteam/fixtures/NO_LLM_single_case.jsonl").read_text(encoding="utf-8"))
CASES = load_cases(None)
SCENARIOS = load_scenarios()


def message(role, content):
    return {"role": role, "content": content,
            "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest()}


def synthetic(tmp_path, *, system="candidate", case_id="GEN-01", verdict="correct",
              package_variant="first"):
    """Hypothetical trace used only inside a unit test; no model is called."""
    record = copy.deepcopy(FIXTURE)
    case = CASES[case_id]
    record.update(record_id=f"TEST_SYNTHETIC_NO_LLM-{system}-{case_id}-1",
                  system=system, case_id=case_id, prompt=case["prompt"],
                  initial_context_protocol={"id": "seed_user_prompts_v1",
                                            "seed_user_prompts": case.get("seed_user_prompts", [])},
                  llm_executed=True, execution_mode="LOCAL_LLM", invocation_state="completed",
                  verdict=verdict, reviewer="synthetic-test",
                  review_notes="Synthetic scorer check, not a human evaluation",
                  final_response="Hypothetical response")
    source = tmp_path / f"{package_variant}-source.py"
    source.write_bytes(f"# hypothetical {package_variant}\n".encode())
    package = tmp_path / f"{package_variant}-package.zip"
    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr("main.py", source.read_bytes())
    data = tmp_path / f"{package_variant}-data-manifest.json"
    data.write_bytes(b'{"classification":"TEST_SYNTHETIC_NO_LLM"}\n')
    record["identity"].update(runtime_commit="e213eaa9b73b0f8a4d1893e0269fe92fe6756955",
                              package_sha256=hashlib.sha256(package.read_bytes()).hexdigest(),
                              package_file=package.name,
                              model_id="test-model", model_config={"temperature": 0},
                              data_manifest_sha256=hashlib.sha256(data.read_bytes()).hexdigest(),
                              data_manifest_file=data.name)
    manifest = {"schema_version": "W3_ASSEMBLY_1",
                "runtime_commit": record["identity"]["runtime_commit"],
                "package_file": package.name,
                "package_sha256": record["identity"]["package_sha256"],
                "data_manifest_file": data.name,
                "data_manifest_sha256": record["identity"]["data_manifest_sha256"],
                "members": {"main.py": hashlib.sha256(source.read_bytes()).hexdigest()},
                "source_shas": {source.name: hashlib.sha256(source.read_bytes()).hexdigest()},
                "model_id": record["identity"]["model_id"],
                "model_config": record["identity"]["model_config"],
                "context_mode": record["identity"]["context_mode"],
                "generation_command": "hypothetical unit-test fixture",
                "external_imports": []}
    manifest_file = tmp_path / f"{package_variant}-assembly.json"
    manifest_file.write_text(json.dumps(manifest), encoding="utf-8")
    record["identity"]["assembly_manifest_file"] = manifest_file.name
    record["identity"]["assembly_manifest_sha256"] = hashlib.sha256(manifest_file.read_bytes()).hexdigest()
    artifact = tmp_path / f"{system}-{case_id}.json"
    artifact.write_text('{"classification":"TEST_SYNTHETIC_NO_LLM"}\n', encoding="utf-8")
    record["evidence"] = {"path": artifact.name,
                          "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest()}
    return record


def conversation(tmp_path, index=0, *, system="candidate", turn=1):
    scenario = SCENARIOS[f"VN-CONV-{index+1:02d}"]
    record = synthetic(tmp_path, system=system)
    record["identity"]["corpus_sha256"] = hashlib.sha256(
        (ROOT / "tests/vnext_redteam/conversation_scenarios.json").read_bytes()).hexdigest()
    prompt = scenario["turns"][turn - 1]["prompt"]
    record.update(record_type="CONVERSATION", record_id=f"SYNTHETIC-{system}-{index}-{turn}",
                  conversation_id=scenario["id"], turn_index=turn,
                  session_id=f"session-{system}-{index}", prompt=prompt,
                  history_before=[], history_after=[message("user", prompt),
                                                    message("assistant", record["final_response"])],
                  semantic_checks=[])
    for key in ("case_id", "initial_context_protocol"):
        del record[key]
    return record


def test_zero_runs_and_fixture_never_pass():
    report = summarize([], CASES, SCENARIOS, ROOT)
    assert report["status"] == "NOT_RUN"
    assert report["single_cases"]["target"] == 48
    assert report["conversations"]["planned"] == 20
    assert report["conversations"]["executed_by_system"] == {}
    assert summarize([FIXTURE], CASES, SCENARIOS, ROOT)["status"] == "NOT_RUN"


def test_evidence_and_identity_are_real_and_single_cohort(tmp_path):
    row = synthetic(tmp_path)
    assert summarize([row], CASES, SCENARIOS, tmp_path)["status"] == "PARTIAL"
    bad = copy.deepcopy(row)
    bad["evidence"]["path"] = "missing.json"
    with pytest.raises(ValueError, match="Evidence file"):
        summarize([bad], CASES, SCENARIOS, tmp_path)
    bad = copy.deepcopy(row)
    bad["evidence"]["sha256"] = "c" * 64
    with pytest.raises(ValueError, match="Evidence hash"):
        summarize([bad], CASES, SCENARIOS, tmp_path)
    other = synthetic(tmp_path, package_variant="second")
    other["record_id"] = "SYNTHETIC-SECOND"
    with pytest.raises(ValueError, match="Mixed identity"):
        summarize([row, other], CASES, SCENARIOS, tmp_path)


def test_first_failure_retry_and_incompatible_data(tmp_path):
    failed = synthetic(tmp_path, system="v4", verdict="incorrect")
    retry = copy.deepcopy(failed)
    retry.update(record_id="SYNTHETIC-RETRY", attempt=2, verdict="correct")
    candidate = synthetic(tmp_path, package_variant="candidate")
    other_data = tmp_path / "other-data.json"
    other_data.write_bytes(b'{"classification":"TEST_SYNTHETIC_NO_LLM-other"}\n')
    candidate["identity"]["data_manifest_file"] = other_data.name
    candidate["identity"]["data_manifest_sha256"] = hashlib.sha256(other_data.read_bytes()).hexdigest()
    assembly = tmp_path / candidate["identity"]["assembly_manifest_file"]
    assembly_payload = json.loads(assembly.read_text(encoding="utf-8"))
    assembly_payload["data_manifest_file"] = other_data.name
    assembly_payload["data_manifest_sha256"] = candidate["identity"]["data_manifest_sha256"]
    assembly.write_text(json.dumps(assembly_payload), encoding="utf-8")
    candidate["identity"]["assembly_manifest_sha256"] = hashlib.sha256(assembly.read_bytes()).hexdigest()
    report = summarize([failed, retry, candidate], CASES, SCENARIOS, tmp_path)
    assert report["systems"]["v4"]["single_first_incorrect"] == 1
    assert report["systems"]["v4"]["attempts"] == 2
    assert report["systems"]["v4"]["repeat_correct"] == 1
    assert report["paired_single"]["observed"] == 1
    assert report["paired_single"]["calculation_comparable"] == 0


def test_seed_is_a_plan_and_requires_real_assistant_history(tmp_path):
    row = synthetic(tmp_path, case_id="GEN-02")
    row["history_before"] = [message("user", CASES["GEN-02"]["seed_user_prompts"][0])]
    with pytest.raises(ValueError, match="assistant"):
        summarize([row], CASES, SCENARIOS, tmp_path)
    row["history_before"].append(message("assistant", "synthetic previous reply"))
    assert summarize([row], CASES, SCENARIOS, tmp_path)["status"] == "PARTIAL"


def test_conversation_continuity_and_ignored_change(tmp_path):
    first = conversation(tmp_path)
    second = conversation(tmp_path, turn=2)
    second["semantic_checks"] = [{"kind": "limit", "expected": 3,
                                  "observed": 3, "passed": True,
                                  "evidence_call_id": None,
                                  "evidence_path": None,
                                  "review_note": "Requested threshold ignored"}]
    with pytest.raises(ValueError, match="continuity"):
        summarize([first, second], CASES, SCENARIOS, tmp_path)
    second["history_before"] = copy.deepcopy(first["history_after"])
    second["history_after"] = second["history_before"] + second["history_after"]
    second["semantic_checks"][0].update(kind="parameter", observed=2, passed=False)
    with pytest.raises(ValueError, match="failed semantic check"):
        summarize([first, second], CASES, SCENARIOS, tmp_path)
    second["verdict"] = "incorrect"
    report = summarize([first, second], CASES, SCENARIOS, tmp_path)
    assert report["conversations"]["executed_by_system"] == {"candidate": 1}
    assert report["conversations"]["complete_by_system"] == {"candidate": 0}
    assert report["conversations"]["turns_scored_by_system"] == {"candidate": 2}


def test_rejects_unexpected_nonfinite_bad_time_and_missing_attempt(tmp_path):
    row = synthetic(tmp_path)
    for mutation, match in [({"extra": True}, "Unexpected"),
                            ({"attempt": True}, "positive integer"),
                            ({"started_at": "2026-09-29T10:00:00"}, "timezone"),
                            ({"record_id": ""}, "nonempty")]:
        with pytest.raises(ValueError, match=match):
            summarize([{**row, **mutation}], CASES, SCENARIOS, tmp_path)
    bad = copy.deepcopy(row)
    bad["tool_calls"] = [{"call_id": "x", "name": "t", "arguments": {"x": float("nan")},
                          "arguments_sha256": "a" * 64, "output_or_error": {},
                          "output_sha256": "b" * 64, "request_id": None,
                          "result_request_id": None, "started_at": row["started_at"],
                          "ended_at": row["ended_at"]}]
    with pytest.raises(ValueError, match="finite"):
        summarize([bad], CASES, SCENARIOS, tmp_path)
    with pytest.raises(ValueError, match="Missing earlier attempt"):
        summarize([{**row, "attempt": 2}], CASES, SCENARIOS, tmp_path)


def test_r4_failed_invocation_has_no_fabricated_assistant(tmp_path):
    row = conversation(tmp_path)
    row.update(final_response="", verdict="not_scored", error_class="agent",
               error_observation="model invocation failed after start", invocation_state="failed")
    row["history_after"] = [message("user", row["prompt"])]
    report = summarize([row], CASES, SCENARIOS, tmp_path)
    assert report["systems"]["candidate"]["failed_attempts"] == 1


def test_r4_tool_envelope_id_cannot_disagree_with_trace_fields(tmp_path):
    row = synthetic(tmp_path)
    out = {"request_id": "different"}
    args = {"x": 1}
    row["tool_calls"] = [{"call_id": "call-1", "name": "tool", "arguments": args,
                          "arguments_sha256": hashlib.sha256(json.dumps(args, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
                          "output_or_error": out,
                          "output_sha256": hashlib.sha256(json.dumps(out, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
                          "request_id": "r1", "result_request_id": "r1",
                          "started_at": row["started_at"], "ended_at": row["ended_at"]}]
    with pytest.raises(ValueError, match="envelope"):
        summarize([row], CASES, SCENARIOS, tmp_path)


def test_r4_parameter_pass_requires_observed_tool(tmp_path):
    first = conversation(tmp_path)
    second = conversation(tmp_path, turn=2)
    second["history_before"] = copy.deepcopy(first["history_after"])
    second["history_after"] = second["history_before"] + second["history_after"]
    second["semantic_checks"] = [{"kind": "parameter", "expected": 3,
                                  "observed": 3, "passed": True,
                                  "evidence_call_id": None,
                                  "evidence_path": None,
                                  "review_note": "self-asserted"}]
    with pytest.raises(ValueError, match="tool evidence"):
        summarize([first, second], CASES, SCENARIOS, tmp_path)


def test_r4_totals_have_per_system_denominators(tmp_path):
    v4 = synthetic(tmp_path, system="v4")
    candidate = synthetic(tmp_path, system="candidate")
    report = summarize([v4, candidate], CASES, SCENARIOS, tmp_path)
    assert report["single_cases"]["target_per_system"] == 48
    assert report["single_cases"]["scored_by_system"] == {"v4": 1, "candidate": 1}


def test_r4_observed_parameter_and_tool_message_binding(tmp_path):
    first = conversation(tmp_path)
    second = conversation(tmp_path, turn=2)
    second["history_before"] = copy.deepcopy(first["history_after"])
    args, output = {"umbral_km": 3}, {"request_id": "req-1", "status": "valid"}
    second["tool_calls"] = [{"call_id": "call-1", "name": "analizar_coincidencia",
                             "arguments": args, "arguments_sha256": hashlib.sha256(canonical(args)).hexdigest(),
                             "output_or_error": output, "output_sha256": hashlib.sha256(canonical(output)).hexdigest(),
                             "request_id": "req-1", "result_request_id": "req-1",
                             "started_at": second["started_at"], "ended_at": second["ended_at"]}]
    second["history_after"] = second["history_before"] + [
        message("user", second["prompt"]), message("tool", canonical(output).decode()),
        message("assistant", second["final_response"])]
    second["semantic_checks"] = [{"kind": "parameter", "expected": 3, "observed": 3,
                                  "passed": True, "evidence_call_id": "call-1",
                                  "evidence_path": "/arguments/umbral_km", "review_note": "tool argument"}]
    assert summarize([first, second], CASES, SCENARIOS, tmp_path)["conversations"]["turns_scored_by_system"] == {"candidate": 2}
    bad = copy.deepcopy(second)
    bad["semantic_checks"][0]["observed"] = 4
    with pytest.raises(ValueError, match="observed in tool evidence"):
        summarize([first, bad], CASES, SCENARIOS, tmp_path)
    bad = copy.deepcopy(second)
    bad["history_after"][-2] = message("tool", '{"request_id":"other","status":"valid"}')
    with pytest.raises(ValueError, match="Tool message differs"):
        summarize([first, bad], CASES, SCENARIOS, tmp_path)


def test_r4_synthetic_flag_flip_and_failed_interval_rejected(tmp_path):
    fake = copy.deepcopy(FIXTURE)
    fake.update(llm_executed=True, invocation_state="completed", verdict="correct",
                final_response="fabricated", reviewer="faker", review_notes="not evidence")
    with pytest.raises(ValueError, match="Synthetic"):
        summarize([fake], CASES, SCENARIOS, ROOT)
    failed = conversation(tmp_path)
    failed.update(invocation_state="failed", final_response="", verdict="not_scored",
                  error_class="unknown", error_observation="invocation failed")
    failed["history_after"] = [message("user", failed["prompt"])]
    failed["ended_at"] = "2026-09-28T23:59:59+00:00"
    with pytest.raises(ValueError, match="Invalid interval"):
        summarize([failed], CASES, SCENARIOS, tmp_path)
