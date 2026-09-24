from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "work3_adapter", ROOT / "scripts" / "agent" / "build_work3_result.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_work3_adapter_uses_real_agent_tool_trace():
    result = MODULE.build_result()
    assert result["data_mode"] == "real"
    assert result["trace"]["tool_calls"][0]["tool"] == "comparar_municipios"
    assert result["trace"]["tool_calls"][0]["output_ref"] == result["trace"]["result_ref"]
    assert {row["unit_id"] for row in result["comparison"]} == {"20069", "20030", "20071"}
    assert all(row["source_ids"] == MODULE.SOURCE_IDS for row in result["comparison"])
