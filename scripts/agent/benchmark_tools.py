"""Benchmark reproducible del core: carga fría, llamada caliente, serialización y salida."""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[2]
AGENT = ROOT / "agentes" / "gipuzkoa360"
sys.path.insert(0, str(AGENT))
os.environ.setdefault("GIPUZKOA360_DATA_DIR", str(ROOT / "datos_preparados"))

import tools  # noqa: E402


Case = tuple[str, str, Callable[[Any], dict[str, Any]]]


CASES: list[Case] = [
    ("consultar_fuente", "source", lambda analysis: analysis.fuente()),
    ("obtener_resumen_territorial", "summary", lambda analysis: analysis.resumen("Eibar", "2025-01-01")),
    (
        "comparar_municipios",
        "comparison",
        lambda analysis: analysis.comparar(
            ["Tolosa", "Beasain", "Azpeitia"], "65", "primary_care", 1.0, "2025-01-01"
        ),
    ),
    (
        "analizar_envejecimiento",
        "aging",
        lambda analysis: analysis.envejecimiento("65", "percentage", "2025-01-01", 10),
    ),
    (
        "analizar_acceso_servicios",
        "access",
        lambda analysis: analysis.acceso("primary_care", 1.0, "2025-01-01"),
    ),
    (
        "analizar_coincidencia",
        "coincidence",
        lambda analysis: analysis.coincidencia("primary_care", "65", 1.0, "2025-01-01", 0.75),
    ),
    (
        "simular_escenario",
        "scenario",
        lambda analysis: analysis.escenario(
            "change_threshold", "primary_care", 1.0, "2025-01-01", new_threshold_km=2.0
        ),
    ),
]


def _milliseconds(operation: Callable[[], Any]) -> tuple[float, Any]:
    started = time.perf_counter()
    value = operation()
    return (time.perf_counter() - started) * 1000, value


def benchmark(warm_repetitions: int = 7) -> dict[str, Any]:
    rows = []
    for name, result_kind, operation in CASES:
        tools.clear_analysis_cache()
        cold_ms, full = _milliseconds(lambda: operation(tools._analysis()))
        warm_times = []
        for _ in range(warm_repetitions):
            warm_ms, repeated = _milliseconds(lambda: operation(tools._analysis()))
            assert repeated == full
            warm_times.append(warm_ms)
        serialization_ms, full_json = _milliseconds(
            lambda: json.dumps({**full, "detail_level": "full"}, ensure_ascii=False, sort_keys=True)
        )
        compact_json = json.dumps(
            tools.compact_result(full, result_kind), ensure_ascii=False, sort_keys=True
        )
        rows.append(
            {
                "tool": name,
                "cold_ms": round(cold_ms, 3),
                "warm_median_ms": round(statistics.median(warm_times), 3),
                "serialization_ms": round(serialization_ms, 3),
                "full_chars": len(full_json),
                "compact_chars": len(compact_json),
                "reduction_percent": round(100 * (1 - len(compact_json) / len(full_json)), 1),
                "rows_used": full.get("rows_used"),
                "result_rows": len(full.get("data", [])),
            }
        )
    resolved_data_dir = Path(os.environ["GIPUZKOA360_DATA_DIR"]).resolve()
    try:
        displayed_data_dir = resolved_data_dir.relative_to(ROOT).as_posix()
    except ValueError:
        displayed_data_dir = str(resolved_data_dir)
    return {
        "data_dir": displayed_data_dir,
        "warm_repetitions": warm_repetitions,
        "tools": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--warm-repetitions", type=int, default=7)
    args = parser.parse_args()
    report = benchmark(args.warm_repetitions)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
