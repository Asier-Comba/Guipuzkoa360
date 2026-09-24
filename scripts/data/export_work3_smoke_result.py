"""Exporta un resultado real determinista para probar el contrato de Work 3.

No representa una ejecución del agente. Solo demuestra que la capa de datos se
puede adaptar sin perder claves, periodos, unidades ni fuentes.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "datos_preparados"
COMPARISON_CODES = ("20069", "20030", "20071")
SOURCE_IDS = ("EUSTAT_EMH_2025", "ODE_HEALTH_CENTRES_2026", "GEOEUSKADI_MUNICIPIOS_2025")


def build_result() -> dict[str, object]:
    municipalities = pd.read_csv(OUT / "municipios.csv", dtype={"municipality_code": str}).set_index(
        "municipality_code"
    )
    source_catalog = {
        source["source_id"]: source
        for source in json.loads((OUT / "metadata_sources.json").read_text(encoding="utf-8"))
    }
    rows = []
    for code in COMPARISON_CODES:
        row = municipalities.loc[code]
        rows.append({
            "unit_id": code,
            "name": row.municipality_name,
            "population": int(row.population_total),
            "age_65_count": int(row.population_65_plus),
            "age_75_count": int(row.population_75_plus),
            "service_distance_km": float(row.distance_to_nearest_primary_care_m) / 1000,
            "service_count": int(row.services_primary_care),
            "period": row.metrics_reference_period,
            "source_ids": list(SOURCE_IDS),
        })
    sources = []
    for source_id in SOURCE_IDS:
        source = source_catalog[source_id]
        sources.append({
            "source_id": source_id,
            "title": source["title"],
            "url": source["url"],
            "period": source["reference_period"],
            "unit": source["unit"],
            "license": source["license"],
            "method": source["method"],
        })
    period = "demography=2025-01-01;services=2026-09-20;geography=2025-05-07"
    return {
        "schema_version": "1.0.0",
        "data_mode": "real",
        "title": "Prueba de integración territorial con datos reales",
        "question": "Compara población mayor y atención primaria en Donostia / San Sebastián, Eibar y Tolosa.",
        "summary": "Fixture determinista de QA para validar el adaptador de datos; no es una respuesta producida por el agente.",
        "generated_at": "2026-09-24T00:00:00+02:00",
        "period": period,
        "geography": "Municipios de Gipuzkoa",
        "parameters": {"age_group": "65+", "service": "primary_care", "distance_threshold_km": 2},
        "metrics": [
            {"id": "population_total", "label": "Población total comparada",
             "value": sum(row["population"] for row in rows), "unit": "personas",
             "period": "2025-01-01", "source_ids": ["EUSTAT_EMH_2025"]},
            {"id": "population_65_plus", "label": "Población de 65 años o más comparada",
             "value": sum(row["age_65_count"] for row in rows), "unit": "personas",
             "period": "2025-01-01", "source_ids": ["EUSTAT_EMH_2025"]},
        ],
        "comparison": rows,
        "map_layers": [
            {"id": "older_share", "label": "Población de 65 años o más",
             "metric": "age_65_count / population * 100", "unit": "%", "period": "2025-01-01",
             "source_ids": ["EUSTAT_EMH_2025"]},
            {"id": "primary_care_distance", "label": "Distancia geométrica a atención primaria",
             "metric": "service_distance_km", "unit": "km", "period": period,
             "source_ids": list(SOURCE_IDS)},
        ],
        "scenario": None,
        "sources": sources,
        "method": (
            "Porcentaje = población de 65+ / población total × 100. Distancia geométrica = mínima distancia "
            "euclídea desde el punto representativo municipal, calculada en EPSG:25830 y convertida de m a km."
        ),
        "limitations": [
            "Fixture de integración de datos; no acredita una ejecución del agente.",
            "La distancia geométrica no equivale a tiempo de viaje ni acceso individual.",
            "Los conteos de centros no miden capacidad, citas, calidad u horario.",
            "Los periodos de demografía, servicios y geometría no son simultáneos.",
        ],
        "trace": {
            "question_id": "DATA-QA-SMOKE-001",
            "agent_version": "data-contract-smoke-not-agent",
            "tool_calls": [{
                "tool": "export_work3_smoke_result",
                "arguments": {"municipality_codes": list(COMPARISON_CODES), "service_category": "primary_care"},
                "output_ref": "DATA-QA-SMOKE-RESULT-001",
            }],
            "data_refs": list(SOURCE_IDS),
            "result_ref": "DATA-QA-SMOKE-RESULT-001",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path, help="Ruta JSON de salida")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(build_result(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Resultado smoke Work 3 escrito en {args.output}")


if __name__ == "__main__":
    main()
