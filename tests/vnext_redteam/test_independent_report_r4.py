"""Guard against turning pinned offline property findings into agent acceptance."""

import hashlib
import json
from pathlib import Path


BASE = Path(__file__).resolve().parents[2] / "resultados/vnext/r4_independent"


def test_pinned_c_r3_report_retains_failures_and_evidence():
    report = json.loads((BASE / "c_r3_report.json").read_text(encoding="utf-8"))
    evidence = (BASE / "c_r3_offline_evidence.json").read_bytes()
    assert report["classification"] == "KNOWN_DEVELOPMENT_OFFLINE_TOOL_ONLY"
    assert report["counts"] == {"pass_offline": 4, "known_fail": 5, "conversation_not_run": 9}
    assert report["llm_executed"] == report["portal_executed"] == 0
    assert len(report["cases"]) == 9
    assert all(case["conversation_status"] == "NOT_RUN" for case in report["cases"])
    assert all(case["evidence_sha256"] == hashlib.sha256(evidence).hexdigest()
               for case in report["cases"])
    assert {case["id"] for case in report["cases"] if case["offline_property_status"] == "KNOWN_FAIL"} == {
        "C-R3-01", "C-R3-02", "C-R3-03", "C-R3-04", "C-R3-09"}
