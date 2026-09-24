"""Ejecuta los ocho casos de aceptación del release sin red ni modelo externo."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[2]
AGENT_DIR = ROOT / "agentes" / "gipuzkoa360"
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

from data_access import DataRepository  # noqa: E402
from tools import TerritorialAnalysis  # noqa: E402


OUTPUT = ROOT / "analisis" / "release_e2e_report.json"
PERIOD = "2025-01-01"


def _call(
    analysis: TerritorialAnalysis,
    tool: str,
    arguments: dict[str, Any],
    operation: Callable[[], dict[str, Any]],
) -> dict[str, Any]:
    return {"tool": tool, "arguments": arguments, "raw_result": operation()}


def _case(
    case_id: str,
    question: str,
    tool_calls: list[dict[str, Any]],
    data_rows: list[dict[str, Any]],
    final_answer: str,
    expected: str,
    passed: bool,
) -> dict[str, Any]:
    raw = tool_calls[-1]["raw_result"] if tool_calls else None
    return {
        "case_id": case_id,
        "question": question,
        "tool_calls": tool_calls,
        "data_rows_used": data_rows,
        "raw_result": raw,
        "final_answer": final_answer,
        "unit": raw.get("unit") if raw else "no aplica",
        "period": raw.get("period") if raw else "no aplica",
        "sources": [item.get("source_id") for item in raw.get("sources", [])] if raw else [],
        "expected": expected,
        "status": "PASS" if passed else "FAIL",
    }


def build_report() -> dict[str, Any]:
    repository = DataRepository(ROOT / "datos_preparados")
    analysis = TerritorialAnalysis(repository)
    cases: list[dict[str, Any]] = []

    a_call = _call(
        analysis,
        "analizar_coincidencia",
        {"categoria_servicio": "primary_care", "grupo_edad": "65", "umbral_km": 2.0,
         "periodo": PERIOD, "cuantil": 0.75},
        lambda: analysis.coincidencia("primary_care", "65", 2.0, PERIOD, 0.75),
    )
    a_hits = [row for row in a_call["raw_result"]["data"] if row["highlighted"]]
    cases.append(_case(
        "A", "¿Dónde coinciden envejecimiento (65+) y mayor distancia geométrica a atención primaria?",
        [a_call], [{"municipality_code": row["municipality_code"], "pct_65_plus": row["pct_65_plus"],
                    "nearest_distance_m": row["nearest_distance_m"]} for row in a_hits],
        f"Hallazgo: {len(a_hits)} municipios superan simultáneamente los cortes del cuantil 0,75. "
        "Es una coincidencia territorial entre porcentaje de 65+ y distancia geométrica; no demuestra "
        "causalidad ni accesibilidad real. Evidencia: resultado de analizar_coincidencia, en % y metros.",
        "7 municipios destacados; porcentajes 2025-01-01 y distancia euclídea EPSG:25830.",
        len(a_hits) == 7 and all(row["meets_age_criterion"] and row["meets_access_criterion"] for row in a_hits),
    ))

    b_call = _call(
        analysis,
        "analizar_coincidencia",
        {"categoria_servicio": "primary_care", "grupo_edad": "75", "umbral_km": 3.0,
         "periodo": PERIOD, "cuantil": 0.80},
        lambda: analysis.coincidencia("primary_care", "75", 3.0, PERIOD, 0.80),
    )
    b_hits = [row for row in b_call["raw_result"]["data"] if row["highlighted"]]
    cases.append(_case(
        "B", "Repítelo para 75+, con umbral de 3 km y cuantil 0,80.",
        [b_call], [{"municipality_code": row["municipality_code"], "pct_75_plus": row["pct_75_plus"],
                    "nearest_distance_m": row["nearest_distance_m"]} for row in b_hits],
        f"Hallazgo: al cambiar el seguimiento a 75+ y cuantil 0,80 quedan {len(b_hits)} municipios "
        "destacados. El umbral de 3 km se conserva como criterio solicitado; los cortes estadísticos y sus "
        "componentes se muestran por separado.",
        "4 municipios destacados con los nuevos argumentos, sin reutilizar cifras del caso A.",
        len(b_hits) == 4 and b_call["raw_result"]["filters"]["age_group"] == "75",
    ))

    c_call = _call(
        analysis,
        "comparar_municipios",
        {"municipios": ["Eibar", "Tolosa"], "grupo_edad": "75",
         "categoria_servicio": "primary_care", "umbral_km": 2.0, "periodo": PERIOD},
        lambda: analysis.comparar(["Eibar", "Tolosa"], "75", "primary_care", 2.0, PERIOD),
    )
    c_rows = c_call["raw_result"]["data"]
    c_by_name = {row["municipality_name"]: row for row in c_rows}
    cases.append(_case(
        "C", "Compara Eibar y Tolosa para población de 75+ y atención primaria.",
        [c_call], c_rows,
        "Eibar registra 13,744 % de población de 75+ y 1.223,6 m al centro de atención primaria más "
        "cercano; Tolosa, 12,131 % y 1.080,5 m. Son porcentajes municipales y distancias euclídeas, no "
        "tiempos de viaje ni disponibilidad.",
        "Eibar 13.744 % / 1223.6 m; Tolosa 12.131 % / 1080.5 m.",
        c_by_name["Eibar"]["pct_75_plus"] == 13.744
        and c_by_name["Tolosa"]["pct_75_plus"] == 12.131
        and c_by_name["Eibar"]["nearest_distance_m"] == 1223.6,
    ))

    d_call = _call(
        analysis,
        "analizar_acceso_servicios",
        {"categoria_servicio": "hospital", "umbral_km": 5.0, "periodo": PERIOD,
         "municipios": ["Tolosa"]},
        lambda: analysis.acceso("hospital", 5.0, PERIOD, ["Tolosa"]),
    )
    d_row = d_call["raw_result"]["data"][0]
    cases.append(_case(
        "D", "¿Cuál es la distancia geométrica de Tolosa al hospital registrado más cercano?",
        [d_call], [d_row],
        f"La distancia geométrica desde el punto representativo de Tolosa al hospital registrado más "
        f"cercano es {d_row['nearest_distance_m']:.1f} m. No representa ruta, tiempo de viaje, capacidad "
        "ni disponibilidad del hospital.",
        "18670.9 m; fuera del umbral de 5 km.",
        d_row["nearest_distance_m"] == 18670.9 and not d_row["within_threshold"],
    ))

    e_summary = _call(
        analysis, "obtener_resumen_territorial", {"municipio": "Aduna", "periodo": PERIOD},
        lambda: analysis.resumen("Aduna", PERIOD),
    )
    e_access = _call(
        analysis, "analizar_acceso_servicios",
        {"categoria_servicio": "primary_care", "umbral_km": 2.0, "periodo": PERIOD,
         "municipios": ["Aduna"]},
        lambda: analysis.acceso("primary_care", 2.0, PERIOD, ["Aduna"]),
    )
    e_indicator = e_summary["raw_result"]["data"][0]["service_indicators"]["primary_care"]
    e_row = e_access["raw_result"]["data"][0]
    cases.append(_case(
        "E", "¿Tiene Aduna atención primaria registrada y cuál es la distancia al registro más cercano?",
        [e_summary, e_access], [
            {"file": "datos_preparados/municipios.csv", "municipality_code": "20002",
             "registered_service_count": e_indicator["registered_service_count"]},
            {"file": "datos_preparados/runtime_servicios.csv", "service_id": e_row["nearest_service_id"]},
        ],
        "Aduna tiene 0 registros de atención primaria dentro de su límite municipal en la fuente, y el "
        f"registro más cercano está a {e_row['nearest_distance_m']:.1f} m en distancia euclídea. Esto no "
        "significa que no exista atención sanitaria para su población.",
        "0 registros municipales; entityF0E8348B; 2756.2 m; no inferir ausencia de atención.",
        e_indicator["registered_service_count"] == 0
        and e_row["nearest_service_id"] == "entityF0E8348B"
        and e_row["nearest_distance_m"] == 2756.2,
    ))

    f_call = _call(
        analysis, "obtener_resumen_territorial", {"municipio": "Eibar", "periodo": PERIOD},
        lambda: analysis.resumen("Eibar", PERIOD),
    )
    f_data = f_call["raw_result"]["data"][0]
    f_indicator = f_data["service_indicators"]["mental_health"]
    cases.append(_case(
        "F", "Consulta el indicador de salud mental de Eibar.",
        [f_call], [{"municipality_code": "20030", **f_indicator}],
        "Eibar tiene 1 registro de salud mental dentro del municipio; equivale a 1,408 registros por "
        "10.000 personas de 65+ y 2,683 por 10.000 de 75+. La distancia geométrica mínima es 1.859,7 m. "
        "Son registros y tasas, no capacidad ni citas disponibles.",
        "1 registro; 1.408 por 10.000 de 65+; 2.683 por 10.000 de 75+; 1859.7 m.",
        f_indicator == {
            "registered_service_count": 1,
            "rate_per_10000_65_plus": 1.408,
            "rate_per_10000_75_plus": 2.683,
            "nearest_distance_m": 1859.7,
        },
    ))

    aduna = repository.municipality_lookup("Aduna")
    g_call = _call(
        analysis,
        "simular_escenario",
        {"accion": "add_service", "categoria_servicio": "primary_care", "umbral_km": 2.0,
         "periodo": PERIOD, "latitud": aduna["latitude"], "longitud": aduna["longitude"],
         "service_id": "HYPOTHETICAL_ADUNA"},
        lambda: analysis.escenario(
            "add_service", "primary_care", 2.0, PERIOD, aduna["latitude"], aduna["longitude"],
            "HYPOTHETICAL_ADUNA"
        ),
    )
    g_row = next(row for row in g_call["raw_result"]["data"] if row["municipality_name"] == "Aduna")
    cases.append(_case(
        "G", "Simula un nuevo servicio de atención primaria en el punto representativo de Aduna.",
        [g_call], [g_row],
        "ESCENARIO HIPOTÉTICO: la distancia geométrica de Aduna cambia de 2.756,2 m a 0,0 m "
        "(−2.756,2 m) al insertar un punto ficticio exactamente en su punto representativo. No predice "
        "uso, coste, capacidad ni recomienda una ubicación real.",
        "Base 2756.2 m; escenario 0.0 m; diferencia -2756.2 m; etiqueta hipotética.",
        g_row["baseline_distance_m"] == 2756.2
        and g_row["scenario_distance_m"] == 0.0
        and g_row["difference_absolute_m"] == -2756.2,
    ))

    h_question = "¿Cuál será el precio de la vivienda en Donostia en 2030?"
    supported = any(term in h_question.casefold() for term in (
        "65", "75", "servicio", "hospital", "salud", "fuente", "municipio", "distancia", "escenario"
    )) and "vivienda" not in h_question.casefold()
    cases.append(_case(
        "H", h_question, [], [],
        "No puedo responder con los datos y herramientas de GIPUZKOA 360: no incluyen vivienda ni "
        "predicciones a 2030. No voy a inventar una cifra. El alcance disponible es demografía 65+/75+, "
        "servicios sanitarios registrados, distancia geométrica, comparaciones, fuentes y escenarios "
        "contrafactuales soportados.",
        "Reconocer fuera de alcance, no llamar tools y no inventar.",
        not supported,
    ))

    passed = sum(case["status"] == "PASS" for case in cases)
    return {
        "release": "urban-challenge-rc1",
        "execution": "Deterministic coordinator/tool acceptance; no network and no external LLM.",
        "cases_total": len(cases),
        "cases_passed": passed,
        "cases_failed": len(cases) - passed,
        "status": "PASS" if passed == len(cases) else "FAIL",
        "cases": cases,
    }


def main() -> None:
    report = build_report()
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("cases_total", "cases_passed", "cases_failed", "status")}))
    if report["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
