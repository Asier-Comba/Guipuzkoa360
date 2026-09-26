from __future__ import annotations

import json

import pytest

import tools


def _result(call, *args, **kwargs):
    return json.loads(call(*args, **kwargs))


def test_coincidence_compact_keeps_all_highlights_and_audit_fields():
    compact = _result(tools.analizar_coincidencia, "primary care", "65+", 1.0, "2025-01-01", 0.75)
    full = _result(tools.analizar_coincidencia, "primary_care", "65", 1.0, "2025-01-01", 0.75, True)
    full_highlights = [row for row in full["data"] if row["highlighted"]]

    assert compact["data"] == full_highlights
    assert compact["summary"]["age_cut_percent"] == full["summary"]["age_cut_percent"]
    assert compact["summary"]["distance_cut_m"] == full["summary"]["distance_cut_m"]
    assert compact["summary"]["joined_rows"] == len(full["data"]) == 88
    assert compact["rows_used"] == full["rows_used"]
    for field in ("period", "unit", "method", "warnings", "limitations"):
        assert compact[field] == full[field]
    assert {item["source_id"] for item in compact["sources"]} == {
        item["source_id"] for item in full["sources"]
    }
    assert len(json.dumps(compact, ensure_ascii=False)) < len(json.dumps(full, ensure_ascii=False)) * 0.5


def test_access_compact_keeps_summary_and_top_exceptions():
    compact = _result(tools.analizar_acceso_servicios, "atención primaria", 1.0, "2025-01-01")
    full = _result(tools.analizar_acceso_servicios, "primary_care", 1.0, "2025-01-01", None, True)

    assert compact["data"] == full["data"][:10]
    assert compact["summary"]["total_result_rows"] == len(full["data"]) == 88
    assert compact["summary"]["within_threshold_count"] == sum(row["within_threshold"] for row in full["data"])
    assert compact["summary"]["outside_threshold_count"] == sum(
        not row["within_threshold"] for row in full["data"]
    )
    assert compact["summary"]["maximum_distance_m"] == full["data"][0]["nearest_distance_m"]
    assert compact["rows_used"] == full["rows_used"]


@pytest.mark.parametrize(
    ("action", "new_threshold"),
    [("cambiar umbral", 2.0), ("change_threshold", 0.5)],
)
def test_scenario_compact_keeps_exact_changed_rows(action: str, new_threshold: float):
    compact = _result(
        tools.simular_escenario,
        action,
        "primary care",
        1.0,
        "2025-01-01",
        None,
        None,
        None,
        new_threshold,
    )
    full = _result(
        tools.simular_escenario,
        "change_threshold",
        "primary_care",
        1.0,
        "2025-01-01",
        None,
        None,
        None,
        new_threshold,
        True,
    )
    expected = [
        row
        for row in full["data"]
        if row["difference_absolute_m"] != 0
        or row["baseline_within_threshold"] != row["scenario_within_threshold"]
    ]
    assert compact["data"] == expected
    assert compact["summary"]["affected_rows"] == len(expected)
    assert compact["scenario"] == full["scenario"]
    assert compact["rows_used"] == full["rows_used"]


def test_full_output_is_repeatable_and_explicit():
    first = tools.analizar_coincidencia("primary_care", "75", 1.0, "2025-01-01", 0.85, True)
    second = tools.analizar_coincidencia("primary_care", "75", 1.0, "2025-01-01", 0.85, True)
    assert first == second
    assert json.loads(first)["detail_level"] == "full"
