from __future__ import annotations

import json
from pathlib import Path

import tools


def test_public_tool_converts_missing_data_to_json(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("GIPUZKOA360_DATA_DIR", str(tmp_path))
    result = json.loads(tools.obtener_resumen_territorial("TEST_MUNICIPIO_A"))
    assert result["status"] == "error"
    assert result["error_code"] == "missing_file"


def test_public_tool_returns_structured_json(monkeypatch):
    fixtures = Path(__file__).parent / "fixtures"
    monkeypatch.setenv("GIPUZKOA360_DATA_DIR", str(fixtures))
    result = json.loads(tools.analizar_envejecimiento("65", "percentage", "2025", 3))
    assert result["status"] == "ok"
    assert result["rows_used"] == 4
    assert len(result["data"]) == 3
