"""Genera ejemplos reales reproducibles para Work 3 sin invocar un LLM."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AGENT_DIR = ROOT / "agentes" / "gipuzkoa360"
sys.path.insert(0, str(AGENT_DIR))

from data_access import DataRepository  # noqa: E402
from tools import TerritorialAnalysis  # noqa: E402


def write(name: str, value: dict) -> None:
    output = ROOT / "docs" / "examples" / name
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    repository = DataRepository(ROOT / "datos_preparados")
    analysis = TerritorialAnalysis(repository)
    write(
        "comparison_tolosa_beasain_azpeitia.json",
        analysis.comparar(
            ["Tolosa", "Beasain", "Azpeitia"],
            "65",
            "primary_care",
            1.0,
            "2025-01-01",
        ),
    )
    write(
        "coincidence_primary_care_65.json",
        analysis.coincidencia("primary_care", "65", 1.0, "2025-01-01", 0.75),
    )
    beasain = repository.municipality_lookup("Beasain")
    write(
        "scenario_add_primary_care_beasain.json",
        analysis.escenario(
            "add_service",
            "primary_care",
            1.0,
            "2025-01-01",
            beasain["latitude"],
            beasain["longitude"],
            "HYPOTHETICAL_BEASAIN",
        ),
    )


if __name__ == "__main__":
    main()
