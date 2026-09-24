from __future__ import annotations

import json
from pathlib import Path

from main import SYSTEM_PROMPT


def test_ten_golden_cases_are_declared():
    cases = json.loads((Path(__file__).parent / "golden_cases.json").read_text(encoding="utf-8"))
    assert [case["id"] for case in cases] == [f"T{i}" for i in range(1, 11)]


def test_prompt_enforces_non_hallucination_and_limits():
    normalized = SYSTEM_PROMPT.casefold()
    for concept in ("herramienta", "no inventes", "ausencia", "causalidad", "periodo", "unidad", "fuentes", "fuera"):
        assert concept in normalized
    assert "fixtures test_*" in normalized
