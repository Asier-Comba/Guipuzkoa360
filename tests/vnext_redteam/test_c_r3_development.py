"""C-R3 is a known development suite, never the R2 hidden holdout."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_cr3_suite_is_distinct_and_actionable():
    data = json.loads((ROOT / "tests/vnext_redteam/c_r3_development_cases.json").read_text(encoding="utf-8"))
    cases = data["cases"]
    assert data["classification"] == "PROPOSAL_DEVELOPMENT_NOT_HOLDOUT"
    assert data["llm_executed"] is False
    assert len(cases) == 9 == len({item["id"] for item in cases})
    assert len({item["risk"] for item in cases}) == 9
    assert all(item["prompt"] and item["expected_criterion"] and item["evidence_needed"] for item in cases)
    frozen_ids = {item["id"] for item in json.loads((ROOT / "tests/vnext_redteam/development_cases.json").read_text(encoding="utf-8"))["cases"]}
    assert not frozen_ids.intersection(item["id"] for item in cases)
