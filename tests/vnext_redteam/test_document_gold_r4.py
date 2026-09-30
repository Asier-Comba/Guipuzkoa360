"""Check the independent public-document gold before any retrieval run."""

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GOLD = ROOT / "docs/vnext/w3/DOCUMENT_GOLD_R4.json"


def test_document_gold_has_reviewed_scope_and_unique_cases():
    data = json.loads(GOLD.read_text(encoding="utf-8"))
    assert data["status"] == "PROPOSED_NOT_RUN"
    assert data["source_ids"] == ["S1", "S2", "S3"]
    cases = data["cases"]
    assert len(cases) == 30
    assert len({case["id"] for case in cases}) == 30
    assert Counter(case["class"] for case in cases) == {
        "answerable": 18, "unanswerable": 6, "adversarial": 6
    }
    for case in cases:
        assert case["question"] and case["expected"]
        assert isinstance(case["fragments"], list)
        if case["class"] == "answerable":
            assert case["fragments"]
        elif case["class"] == "unanswerable":
            assert not case["fragments"]
        for fragment in case["fragments"]:
            assert fragment.split(":", 1)[0] in data["source_ids"]
