"""Corpus and offline-provider integrity; no claim of a live agent run."""

import hashlib
import json
from pathlib import Path

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
    assert report["single_cases"]["target"] == 48
    assert report["conversations"]["planned"] == 20
    assert report["conversations"]["executed_by_system"] == {}


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
