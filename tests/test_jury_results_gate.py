from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "verify_jury_results", ROOT / "scripts" / "benchmark" / "verify_jury_results.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_three_jury_coincidence_lists_are_exact():
    cases = MODULE.compute_cases()
    assert [item["highlighted_count"] for item in cases] == [7, 4, 2]
    assert all(item["status"] == "PASS" for item in cases)


def test_jury_results_use_requested_quantiles_not_fixed_quartile():
    result = MODULE.verify_quantile_sensitivity(MODULE.compute_cases())
    assert result["status"] == "PASS"
