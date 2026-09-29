"""Synthetic NO_LLM probes of the independent trace scorer, not agent results."""

import copy
import hashlib
import json
from pathlib import Path

import pytest

from scripts.vnext_product.score_runs import load_cases, load_scenarios, summarize


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = json.loads((ROOT / "tests/vnext_redteam/fixtures/NO_LLM_single_case.jsonl").read_text(encoding="utf-8"))
CASES = load_cases(None)
SCENARIOS = load_scenarios()


def message(role, content):
    return {"role": role, "content": content,
            "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest()}


def synthetic(tmp_path, *, system="candidate", case_id="GEN-01", verdict="correct"):
    """Hypothetical trace used only inside a unit test; no model is called."""
    record = copy.deepcopy(FIXTURE)
    case = CASES[case_id]
    record.update(record_id=f"TEST_SYNTHETIC_NO_LLM-{system}-{case_id}-1",
                  system=system, case_id=case_id, prompt=case["prompt"],
                  initial_context_protocol={"id": "seed_user_prompts_v1",
                                            "seed_user_prompts": case.get("seed_user_prompts", [])},
                  llm_executed=True, verdict=verdict, reviewer="synthetic-test",
                  review_notes="Synthetic scorer check, not a human evaluation",
                  final_response="Hypothetical response")
    package = tmp_path / "package.bin"
    package.write_bytes(b"TEST_SYNTHETIC_NO_LLM package")
    data = tmp_path / "data-manifest.json"
    data.write_bytes(b'{"classification":"TEST_SYNTHETIC_NO_LLM"}\n')
    record["identity"].update(runtime_commit="e213eaa9b73b0f8a4d1893e0269fe92fe6756955",
                              package_sha256=hashlib.sha256(package.read_bytes()).hexdigest(),
                              package_file=package.name,
                              model_id="test-model", model_config={"temperature": 0},
                              data_manifest_sha256=hashlib.sha256(data.read_bytes()).hexdigest(),
                              data_manifest_file=data.name)
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
    assert report["conversations"]["executed"] == 0
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
    other = copy.deepcopy(row)
    other["record_id"] = "SYNTHETIC-SECOND"
    second_package = tmp_path / "second-package.bin"
    second_package.write_bytes(b"another synthetic package")
    other["identity"]["package_file"] = second_package.name
    other["identity"]["package_sha256"] = hashlib.sha256(second_package.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="Mixed identity"):
        summarize([row, other], CASES, SCENARIOS, tmp_path)


def test_first_failure_retry_and_incompatible_data(tmp_path):
    failed = synthetic(tmp_path, system="v4", verdict="incorrect")
    retry = copy.deepcopy(failed)
    retry.update(record_id="SYNTHETIC-RETRY", attempt=2, verdict="correct")
    candidate = synthetic(tmp_path)
    other_data = tmp_path / "other-data.json"
    other_data.write_bytes(b'{"classification":"TEST_SYNTHETIC_NO_LLM-other"}\n')
    candidate["identity"]["data_manifest_file"] = other_data.name
    candidate["identity"]["data_manifest_sha256"] = hashlib.sha256(other_data.read_bytes()).hexdigest()
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
    second["semantic_checks"] = [{"kind": "parameter", "expected": 3,
                                  "observed": 3, "passed": True,
                                  "evidence_call_id": None,
                                  "review_note": "Requested threshold ignored"}]
    with pytest.raises(ValueError, match="continuity"):
        summarize([first, second], CASES, SCENARIOS, tmp_path)
    second["history_before"] = copy.deepcopy(first["history_after"])
    second["history_after"] = second["history_before"] + second["history_after"]
    second["semantic_checks"][0].update(observed=2, passed=False)
    with pytest.raises(ValueError, match="failed semantic check"):
        summarize([first, second], CASES, SCENARIOS, tmp_path)
    second["verdict"] = "incorrect"
    report = summarize([first, second], CASES, SCENARIOS, tmp_path)
    assert report["conversations"]["executed"] == 1
    assert report["conversations"]["complete"] == 0
    assert report["conversations"]["turns_scored"] == 2


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
