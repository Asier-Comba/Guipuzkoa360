"""Adapta una salida real del tool de comparación al contrato de Work 3."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
AGENT_DIR = ROOT / "agentes" / "gipuzkoa360"
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

from data_access import DataRepository  # noqa: E402
from tools import TerritorialAnalysis  # noqa: E402


NAMES = ["Donostia / San Sebastián", "Eibar", "Tolosa"]
PERIOD = "2025-01-01"
SOURCE_IDS = ["EUSTAT_EMH_2025", "ODE_HEALTH_CENTRES_2026", "GEOEUSKADI_MUNICIPIOS_2025"]


def _source(source: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_id": source["source_id"],
        "title": source["title"],
        "url": source["url"],
        "period": source["reference_period"],
        "unit": source["unit"],
        "license": source["license"],
        "method": source["method"],
    }


def build_result() -> dict[str, Any]:
    repository = DataRepository(ROOT / "datos_preparados")
    analysis = TerritorialAnalysis(repository)
    raw = analysis.comparar(NAMES, "65", "primary_care", 2.0, PERIOD)
    raw_by_code = {row["municipality_code"]: row for row in raw["data"]}
    comparison = []
    for name in NAMES:
        municipality = repository.municipality_lookup(name)
        row = raw_by_code[municipality["municipality_code"]]
        comparison.append({
            "unit_id": row["municipality_code"],
            "name": row["municipality_name"],
            "population": municipality["population_total"],
            "age_65_count": municipality["population_65_plus"],
            "age_75_count": municipality["population_75_plus"],
            "service_distance_km": row["nearest_distance_m"] / 1000,
            "service_count": municipality["services_primary_care"],
            "period": municipality["metrics_reference_period"],
            "source_ids": SOURCE_IDS,
        })
    catalog = {item["source_id"]: item for item in repository.metadata()["sources"]}
    combined_period = "demography=2025-01-01;services=2026-09-20;geography=2025-05-07"
    result_ref = "RC1-COMPARE-20069-20030-20071"
    return {
        "schema_version": "1.0.0",
        "data_mode": "real",
        "title": "Comparación territorial reproducible",
        "question": "Compara envejecimiento y distancia geométrica a atención primaria en Donostia, Eibar y Tolosa.",
        "summary": (
            "Resultado construido directamente desde la salida real de comparar_municipios; las cifras "
            "conservan claves, unidades, periodos y fuentes del runtime del agente."
        ),
        "generated_at": "2026-09-24T00:00:00+02:00",
        "period": combined_period,
        "geography": "Municipios de Gipuzkoa",
        "parameters": {"age_group": "65+", "service": "primary_care", "distance_threshold_km": 2},
        "metrics": [
            {"id": "population_total", "label": "Población total comparada",
             "value": sum(row["population"] for row in comparison), "unit": "personas",
             "period": PERIOD, "source_ids": ["EUSTAT_EMH_2025"]},
            {"id": "population_65_plus", "label": "Población de 65 años o más comparada",
             "value": sum(row["age_65_count"] for row in comparison), "unit": "personas",
             "period": PERIOD, "source_ids": ["EUSTAT_EMH_2025"]},
        ],
        "comparison": comparison,
        "map_layers": [
            {"id": "older_share", "label": "Población de 65 años o más",
             "metric": "age_65_count / population * 100", "unit": "%", "period": PERIOD,
             "source_ids": ["EUSTAT_EMH_2025"]},
            {"id": "primary_care_distance", "label": "Distancia geométrica a atención primaria",
             "metric": "service_distance_km", "unit": "km", "period": combined_period,
             "source_ids": SOURCE_IDS},
        ],
        "scenario": None,
        "sources": [_source(catalog[source_id]) for source_id in SOURCE_IDS],
        "method": raw["method"] + " Distancias convertidas de metros a kilómetros para la visualización.",
        "limitations": list(dict.fromkeys(raw["limitations"] + [
            "Los periodos de demografía, servicios y geometría no son simultáneos.",
            "El recuento registrado no mide capacidad, citas, horario ni disponibilidad.",
        ])),
        "trace": {
            "execution_mode": "local_tool",
            "question_id": "RC1-WORK3-COMPARE-001",
            "agent_version": "urban-challenge-rc1",
            "tool_calls": [{
                "tool": "comparar_municipios",
                "arguments": {"municipios": NAMES, "grupo_edad": "65", "categoria_servicio": "primary_care",
                              "umbral_km": 2.0, "periodo": PERIOD},
                "output_ref": result_ref,
            }],
            "data_refs": SOURCE_IDS,
            "result_ref": result_ref,
        },
    }


def main() -> None:
    output = ROOT / "analisis" / "work3_agent_result.json"
    output.write_text(json.dumps(build_result(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(output.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
