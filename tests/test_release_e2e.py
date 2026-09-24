from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "release_e2e", ROOT / "scripts" / "agent" / "run_release_e2e.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_release_acceptance_matrix_passes_all_eight_cases():
    report = MODULE.build_report()
    assert report["status"] == "PASS"
    assert report["cases_total"] == report["cases_passed"] == 8
    assert report["cases_failed"] == 0


def test_hallucination_guards_are_visible_in_final_answers():
    report = MODULE.build_report()
    answers = {case["case_id"]: case["final_answer"].casefold() for case in report["cases"]}
    assert "no significa que no exista atención sanitaria" in answers["E"]
    assert "no capacidad" in answers["F"]
    assert "no predice" in answers["G"]
    assert "no voy a inventar" in answers["H"]
    assert report["cases"][-1]["tool_calls"] == []


def test_every_supported_case_has_trace_and_units():
    report = MODULE.build_report()
    for case in report["cases"][:-1]:
        assert case["tool_calls"]
        assert case["data_rows_used"]
        assert case["unit"]
        assert case["period"]
        assert case["sources"]
