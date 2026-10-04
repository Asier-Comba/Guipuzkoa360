from __future__ import annotations

import json
from pathlib import Path

from scripts.vnext_agent import record_offline


def test_offline_recorder_preserves_observations_without_model(tmp_path: Path):
    report = record_offline.record(tmp_path)
    assert report["records"] == 8
    assert report["llm_executed"] == 0 and report["w3_scorer_run"] is False
    rows = [json.loads(line) for line in (tmp_path / "offline_tools.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 8
    assert all(row["execution_mode"] == "OFFLINE_TOOL" and row["final_response"] is None and not row["scoring_eligible"] for row in rows)
    assert {row["observed_status"] for row in rows} >= {"valid", "error"}
    assert any(any(item["status"] == "unknown" for item in row["outcomes"]) for row in rows)
    assert all(record_offline.sha((tmp_path / row["evidence"]["path"]).read_bytes()) == row["evidence"]["sha256"] for row in rows)
