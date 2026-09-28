"""Genera un registro compacto de capacidades a partir del runtime y sus contratos."""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "datos_preparados"
OUTPUT = DATA / "capabilities.json"
INPUT_FILES = (
    DATA / "data_contract.json",
    DATA / "metadata_sources.json",
    DATA / "municipios.csv",
    DATA / "demografia.csv",
    DATA / "runtime_municipality_points.csv",
    DATA / "runtime_servicios.csv",
    ROOT / "agentes/gipuzkoa360/main.py",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def csv_profile(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    columns = list(rows[0]) if rows else []
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "rows": len(rows),
        "columns": columns,
        "reference_periods": sorted({row.get("reference_period", "") for row in rows if row.get("reference_period")}),
        "service_categories": sorted({row.get("service_category", "") for row in rows if row.get("service_category")}),
        "sha256": sha256(path),
    }


def tool_operations(path: Path) -> list[dict[str, Any]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=path.as_posix())
    operations: list[dict[str, Any]] = []
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        if not any(isinstance(item, ast.Name) and item.id == "tool" for item in node.decorator_list):
            continue
        operations.append(
            {
                "name": node.name,
                "inputs": [argument.arg for argument in node.args.args],
                "purpose": ast.get_docstring(node) or "",
            }
        )
    return operations


def update_manifest() -> None:
    path = DATA / "runtime_manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    entry = {
        "path": OUTPUT.relative_to(ROOT).as_posix(),
        "bytes": OUTPUT.stat().st_size,
        "sha256": sha256(OUTPUT),
    }
    files = [item for item in manifest["files"] if item["path"] != entry["path"]]
    files.append(entry)
    files.sort(key=lambda item: item["path"])
    manifest["files"] = files
    manifest["total_bytes"] = sum(item["bytes"] for item in files)
    manifest["within_portal_budget"] = manifest["total_bytes"] < manifest["portal_budget_bytes"]
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    for path in INPUT_FILES:
        if not path.is_file():
            raise SystemExit(f"Falta entrada del registro de capacidades: {path.relative_to(ROOT).as_posix()}")

    contract = json.loads((DATA / "data_contract.json").read_text(encoding="utf-8"))
    metadata = json.loads((DATA / "metadata_sources.json").read_text(encoding="utf-8"))
    profiles = {path.stem: csv_profile(path) for path in INPUT_FILES if path.suffix == ".csv"}
    municipality_columns = profiles["municipios"]["columns"]
    demography_columns = profiles["demografia"]["columns"]
    age_groups = sorted(
        {match.group(1) + "+" for name in demography_columns if (match := re.fullmatch(r"population_(\d+)_plus", name))},
        key=lambda value: int(value[:-1]),
    )
    category_values = profiles["runtime_servicios"]["service_categories"]
    source_ids = sorted(str(item["source_id"]) for item in metadata)

    exact_demographic_fields = [
        name for name in demography_columns
        if name == "population_total" or re.fullmatch(r"(?:population|pct)_\d+_plus", name)
    ]
    transformations = [
        {
            "id": "share_of_population",
            "exact_when": "the requested cumulative age group has both population_<age>_plus and population_total",
            "formula": "population_<age>_plus / population_total * 100",
        },
        {
            "id": "service_rate_per_10000",
            "exact_when": "the selected service count and requested supported age denominator are present",
            "formula": "services_<category> / population_<age>_plus * 10000",
        },
        {
            "id": "nearest_service_distance",
            "exact_when": "municipality representative point and service coordinates exist in EPSG:25830",
            "formula": "euclidean distance in metres",
        },
        {
            "id": "quantile_coincidence",
            "exact_when": "supported age metric, service category and quantile are supplied",
            "formula": "municipality reaches both independently computed quantile cuts",
        },
    ]
    semantic_limits = sorted(
        {
            *[limit for item in metadata for limit in item.get("limitations", [])],
            "Los grupos agregados no permiten reconstruir exactamente umbrales de edad distintos de los campos acumulados disponibles.",
            "Los periodos de demografía, geografía y servicios no forman una fotografía temporal homogénea.",
            "Una comparación o coincidencia territorial no demuestra causalidad ni constituye una recomendación.",
        }
    )

    registry = {
        "registry_version": "1.0.0",
        "generated_from_contract_version": contract["contract_version"],
        "datasets": [profiles[name] for name in ("municipios", "demografia", "runtime_municipality_points", "runtime_servicios")],
        "dimensions": {
            "demography": {
                "granularity": "one row per municipality and reference period",
                "supported_age_groups": age_groups,
                "direct_fields": exact_demographic_fields,
                "exact_derivations": [item for item in transformations if item["id"] in {"share_of_population", "service_rate_per_10000"}],
                "cannot_exactly_derive": "any age threshold lacking its own cumulative count or finer-grained source rows",
                "search_terms": ["edad", "años", "población", "envejecimiento", "age", "population"],
            },
            "services": {
                "granularity": "one row per public health-service record",
                "categories": category_values,
                "available_metrics": sorted(
                    [name for name in municipality_columns if name.startswith("services_") or name.startswith("distance_to_nearest_")]
                ),
                "exact_derivations": [item for item in transformations if item["id"] in {"service_rate_per_10000", "nearest_service_distance"}],
                "search_terms": ["servicio", "salud", "centro", "hospital", "distancia", "access", "health"],
            },
            "geography": {
                "granularity": contract["geographic_unit"],
                "key": contract["municipality_key"],
                "coverage": profiles["municipios"]["rows"],
                "calculation_crs": contract["calculation_crs"],
                "publication_crs": contract["publication_crs"],
                "search_terms": ["municipio", "territorio", "coordenada", "mapa", "geografía", "location"],
            },
            "time": {
                "periods": contract["periods"],
                "available_demographic_periods": profiles["demografia"]["reference_periods"],
                "available_service_periods": profiles["runtime_servicios"]["reference_periods"],
                "search_terms": ["periodo", "fecha", "año", "evolución", "futuro", "time", "year"],
            },
            "sources": {
                "source_ids": source_ids,
                "search_terms": ["fuente", "origen", "licencia", "procedencia", "source"],
            },
        },
        "metrics_derivable": transformations,
        "operations": tool_operations(ROOT / "agentes/gipuzkoa360/main.py"),
        "relations": {
            "municipality_join_key": contract["municipality_key"]["field"],
            "service_foreign_key": contract["files"]["datos_preparados/servicios.csv"]["foreign_key"],
            "source_lineage_separator": contract["source_id_separator"],
        },
        "constraints": {
            "internet_required": False,
            "external_live_lookup": False,
            "arbitrary_age_thresholds": False,
            "prediction_models": False,
            "travel_time_or_routes": False,
            "capacity_appointments_staff": False,
            "valid_transformations": [item["id"] for item in transformations],
        },
        "semantic_limits": semantic_limits,
        "provenance": [
            {
                "source_id": item["source_id"],
                "title": item["title"],
                "institution": item["institution"],
                "reference_period": item["reference_period"],
            }
            for item in metadata
        ],
        "registry_inputs": [
            {"path": path.relative_to(ROOT).as_posix(), "sha256": sha256(path)} for path in INPUT_FILES
        ],
    }
    OUTPUT.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    update_manifest()
    print(f"{OUTPUT.relative_to(ROOT).as_posix()} · {OUTPUT.stat().st_size} bytes · {sha256(OUTPUT)}")


if __name__ == "__main__":
    main()
