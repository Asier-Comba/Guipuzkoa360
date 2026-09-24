"""Benchmark reproducible de carga, cálculo y serialización de las siete tools."""

from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[2]
AGENT_DIR = ROOT / "agentes" / "gipuzkoa360"
sys.path.insert(0, str(AGENT_DIR))

import main as agent_main  # noqa: E402
import tools as core  # noqa: E402


OUTPUT = ROOT / "analisis" / "runtime_benchmark_rc2.json"


def _seconds(callback: Callable[[], Any]) -> tuple[float, Any]:
    start = time.perf_counter()
    value = callback()
    return time.perf_counter() - start, value


def _invoke(function: Callable[..., str], *args: Any) -> dict[str, Any]:
    return json.loads(function(*args))


def build_report(repeats: int = 5) -> dict[str, Any]:
    core.clear_runtime_cache()
    repository = core.DataRepository(ROOT / "datos_preparados")
    load_seconds, _ = _seconds(lambda: (repository.municipalities(), repository.demography(), repository.services(), repository.metadata()))
    analysis = core.TerritorialAnalysis(repository)
    calculations = {
        "obtener_resumen_territorial": lambda: analysis.resumen("Eibar", "2025-01-01"),
        "comparar_municipios": lambda: analysis.comparar(["Eibar", "Tolosa"], "75+", "atención primaria", 2, "2025-01-01"),
        "analizar_envejecimiento": lambda: analysis.envejecimiento("65+", "percentage", "2025-01-01", 10),
        "analizar_acceso_servicios": lambda: analysis.acceso("hospitales", 5, "2025-01-01", ["Tolosa"]),
        "analizar_coincidencia": lambda: analysis.coincidencia("primary care", "65+", 2, "2025-01-01", 0.75),
        "simular_escenario": lambda: analysis.escenario("cambiar umbral", "atención primaria", 2, "2025-01-01", new_threshold_km=3),
        "consultar_fuente": lambda: analysis.fuente("EUSTAT_EMH_2025"),
    }
    wrappers = {
        "obtener_resumen_territorial": lambda: _invoke(agent_main.obtener_resumen_territorial, "Eibar", "2025-01-01"),
        "comparar_municipios": lambda: _invoke(agent_main.comparar_municipios, ["Eibar", "Tolosa"], "75+", "atención primaria", 2, "2025-01-01"),
        "analizar_envejecimiento": lambda: _invoke(agent_main.analizar_envejecimiento, "65+", "percentage", "2025-01-01", 10),
        "analizar_acceso_servicios": lambda: _invoke(agent_main.analizar_acceso_servicios, "hospitales", 5, "2025-01-01", ["Tolosa"]),
        "analizar_coincidencia": lambda: _invoke(agent_main.analizar_coincidencia, "primary care", "65+", 2, "2025-01-01", 0.75),
        "simular_escenario": lambda: _invoke(agent_main.simular_escenario, "cambiar umbral", "atención primaria", 2, "2025-01-01", None, None, None, 3),
        "consultar_fuente": lambda: _invoke(agent_main.consultar_fuente, "EUSTAT_EMH_2025"),
    }
    rows = []
    for name in calculations:
        calc_times, serialization_times, wrapper_times = [], [], []
        result = None
        for _ in range(repeats):
            elapsed, result = _seconds(calculations[name])
            calc_times.append(elapsed)
            elapsed, _ = _seconds(lambda: json.dumps(result, ensure_ascii=False, sort_keys=True))
            serialization_times.append(elapsed)
            elapsed, wrapped = _seconds(wrappers[name])
            wrapper_times.append(elapsed)
            assert wrapped["status"] == "ok"
        rows.append({
            "tool": name,
            "calculation_ms_median": round(statistics.median(calc_times) * 1000, 3),
            "serialization_ms_median": round(statistics.median(serialization_times) * 1000, 3),
            "wrapper_ms_median": round(statistics.median(wrapper_times) * 1000, 3),
        })
    maximum = max(row["wrapper_ms_median"] for row in rows)
    return {
        "release": "urban-challenge-rc2", "repeats": repeats,
        "cold_data_load_ms": round(load_seconds * 1000, 3), "tools": rows,
        "max_wrapper_ms_median": maximum, "status": "PASS" if maximum < 1000 else "FAIL",
    }


def main() -> None:
    report = build_report()
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
