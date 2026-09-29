"""Integrity gates for W3 artifacts; these do not certify a live agent."""

import hashlib
import json
from pathlib import Path

import pytest

from scripts.vnext_product.score_runs import load_cases, summarize


ROOT = Path(__file__).resolve().parents[2]
DEV = ROOT / "tests/vnext_redteam/development_cases.json"
CONVERSATIONS = ROOT / "tests/vnext_redteam/conversation_scenarios.json"
EVIDENCE = ROOT / "resultados/vnext/provider_evidence.json"
HTML = ROOT / "resultados/vnext/index.html"


def test_frozen_development_and_conversation_counts():
    cases = json.loads(DEV.read_text(encoding="utf-8"))["cases"]
    scenarios = json.loads(CONVERSATIONS.read_text(encoding="utf-8"))["scenarios"]
    assert len(cases) == 48 == len({item["id"] for item in cases})
    assert len(scenarios) == 20 == len({item["id"] for item in scenarios})
    assert all(3 <= len(item["turns"]) <= 6 for item in scenarios)
    original_projection = [[item["id"], item["prompt"], item["expected_criterion"],
                            item.get("expected_tools_reference")] for item in cases[:36]]
    digest = hashlib.sha256(json.dumps(original_projection, ensure_ascii=False,
                                       separators=(",", ":")).encode()).hexdigest()
    assert digest == "a4804e669abc5162167873555873b962888d5f9aa4475d0cda104a61b7b56cf2"


def test_empty_evaluation_is_not_a_pass():
    report = summarize([], load_cases(None))
    assert report["status"] == "NOT_RUN"
    assert report["llm_executed"] == 0
    assert report["target_cases"] == 48


def test_score_rejects_unfrozen_prompt_and_missing_attempt():
    cases = load_cases(None)
    case = cases["GEN-01"]
    base = {"case_id": "GEN-01", "system": "candidate", "attempt": 1,
            "version": "candidate-pin", "package_hash": "abc", "model_config": {"id": "same"},
            "data_identity": "fixed", "prompt": case["prompt"], "context": [], "tool_calls": [],
            "final_response": "observed", "started_at": "2026-09-29T10:00:00Z",
            "ended_at": "2026-09-29T10:00:01Z", "error_class": None,
            "verdict": "correct", "reviewer": "human", "evidence_path": "private/evidence/1.json",
            "llm_executed": True}
    report = summarize([base], cases)
    assert report["status"] == "PARTIAL"
    assert report["systems"]["candidate"]["unique_cases_scored"] == 1
    with pytest.raises(ValueError, match="prompt differs"):
        summarize([{**base, "prompt": "altered after freeze"}], cases)
    with pytest.raises(ValueError, match="Missing earlier attempt"):
        summarize([{**base, "attempt": 2}], cases)
    with pytest.raises(ValueError, match="positive integer"):
        summarize([{**base, "attempt": True}], cases)
    with pytest.raises(ValueError, match="model_config"):
        summarize([{**base, "model_config": {}}], cases)
    with pytest.raises(ValueError, match="outside attempt interval"):
        summarize([{**base, "tool_calls": [{"name": "test", "arguments": {},
            "started_at": "2026-09-29T09:59:59Z", "ended_at": "2026-09-29T10:00:00Z",
            "output_or_error": "output"}]}], cases)


def test_score_keeps_first_failure_and_rejects_incomparable_data():
    cases = load_cases(None)
    case = cases["GEN-01"]
    common = {"case_id": "GEN-01", "attempt": 1, "version": "pinned",
              "package_hash": "pin", "model_config": {"id": "same"},
              "data_identity": "data-A", "prompt": case["prompt"], "context": [],
              "tool_calls": [], "final_response": "observed",
              "started_at": "2026-09-29T10:00:00Z", "ended_at": "2026-09-29T10:00:01Z",
              "error_class": "agent", "verdict": "incorrect", "reviewer": "human",
              "evidence_path": "private/evidence/1.json", "llm_executed": True}
    v4 = {**common, "system": "v4"}
    retry = {**common, "system": "v4", "attempt": 2, "verdict": "correct",
             "error_class": None, "evidence_path": "private/evidence/2.json"}
    candidate = {**common, "system": "candidate", "verdict": "correct",
                 "error_class": None, "data_identity": "data-B"}
    report = summarize([v4, retry, candidate], cases)
    assert report["systems"]["v4"]["first_attempt_incorrect"] == 1
    assert report["systems"]["v4"]["attempts"] == 2
    assert report["paired"]["observed"] == 1
    assert report["paired"]["comparable"] == 0
    assert report["paired"]["candidate_additional_correct"] == 0


def test_offline_provider_evidence_preserves_non_ok_states():
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    assert evidence["classification"] == "OFFLINE_DETERMINISTIC_PROVIDER_OUTPUT"
    assert evidence["provider_head"] == "c68eb5c55dec72a267b7435b4c364049f6eab408"
    outputs = {item["id"]: item["result"] for item in evidence["outputs"]}
    assert outputs["segura_1900_30"]["status"] == "ok"
    assert outputs["segura_1900_180"]["status"] == "no_feasible_journey"
    assert outputs["zegama_unvalidated"]["status"] == "unknown"
    for result in outputs.values():
        if result["status"] == "ok":
            assert sum(result["components_s"].values()) == result["itinerary"]["total_s"]
            assert result["sources"] and result["sources"][0]["source_sha256"]
        else:
            assert result["itinerary"] is None and result["components_s"] is None
    html = HTML.read_text(encoding="utf-8")
    assert evidence["snapshot_sha256"] in html
    assert "Evidencia offline guardada" in html
    assert "No ejecuta una conversación con el agente" in html
