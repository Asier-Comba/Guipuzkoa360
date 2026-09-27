from __future__ import annotations

import json
from pathlib import Path

import tools


ROOT = Path(__file__).resolve().parents[1]


def test_analysis_cache_reuses_repository_per_resolved_path(monkeypatch):
    monkeypatch.setenv("GIPUZKOA360_DATA_DIR", str(ROOT / "datos_preparados"))
    tools.clear_analysis_cache()
    first = tools._analysis()
    second = tools._analysis()
    assert first is second
    assert first.repo is second.repo


def test_repeated_tool_call_is_byte_deterministic(monkeypatch):
    monkeypatch.setenv("GIPUZKOA360_DATA_DIR", str(ROOT / "datos_preparados"))
    tools.clear_analysis_cache()
    first = tools.analizar_coincidencia("atención primaria", "≥65", 1.0, "2025-01-01", 0.75)
    second = tools.analizar_coincidencia("primary_care", "65", 1.0, "2025-01-01", 0.75)
    assert first == second


def test_compact_general_outputs_stay_bounded(monkeypatch):
    monkeypatch.setenv("GIPUZKOA360_DATA_DIR", str(ROOT / "datos_preparados"))
    tools.clear_analysis_cache()
    outputs = {
        "access": tools.analizar_acceso_servicios("primary_care", 1.0, "2025-01-01"),
        "coincidence": tools.analizar_coincidencia("primary_care", "65", 1.0, "2025-01-01", 0.75),
        "scenario": tools.simular_escenario(
            "change_threshold", "primary_care", 1.0, "2025-01-01", nuevo_umbral_km=2.0
        ),
    }
    assert len(outputs["access"]) < 8_000
    assert len(outputs["coincidence"]) < 10_000
    assert len(outputs["scenario"]) < 16_000
    assert all(json.loads(value)["detail_level"] == "compact" for value in outputs.values())
