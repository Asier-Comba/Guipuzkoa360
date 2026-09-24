"""Repite una tool real de Work 2 con otro cuantil para la demo de producto."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "agentes" / "gipuzkoa360"))

from data_access import DataRepository  # noqa: E402
from tools import TerritorialAnalysis, obtener_resumen_territorial  # noqa: E402


def main() -> None:
    repository = DataRepository(ROOT / "datos_preparados")
    result = TerritorialAnalysis(repository).coincidencia(
        "primary_care", "65", 1.0, "2025-01-01", 0.85
    )
    output = ROOT / "docs" / "examples" / "coincidence_primary_care_65_q85.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{output}: {sum(row['highlighted'] for row in result['data'])} municipios destacados")
    error = json.loads(obtener_resumen_territorial("MUNICIPIO_INEXISTENTE"))
    if error.get("status") != "error":
        raise RuntimeError("Se esperaba un error controlado para municipio inexistente")
    error_path = ROOT / "docs" / "examples" / "error_unknown_municipality.json"
    error_path.write_text(json.dumps(error, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{error_path}: {error['error_code']}")


if __name__ == "__main__":
    main()
