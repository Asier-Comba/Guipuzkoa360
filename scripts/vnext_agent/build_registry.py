"""Generate only the isolated W2 capability registry from verified local inputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "datos_preparados/vnext/capabilities.json"
DATA = "datos_preparados/"
SOURCES = {
    "demography": ["EUSTAT_EMH_2025"],
    "services": ["ODE_HEALTH_CENTRES_2026", "GEOEUSKADI_MUNICIPIOS_2025"],
    "combined": ["EUSTAT_EMH_2025", "ODE_HEALTH_CENTRES_2026", "GEOEUSKADI_MUNICIPIOS_2025"],
    "all": ["EUSTAT_EMH_2025", "ODE_HEALTH_CENTRES_2026", "GEOEUSKADI_MUNICIPIOS_2025", "G360_DERIVED_MUNICIPAL_METRICS_V1"],
}


def field(name: str, kind: str = "string", required: bool = False, options: list[str] | None = None) -> dict:
    return {"name": name, "type": kind, "required": required, "allowed_values": options or []}


AGE = field("grupo_edad", options=["65", "75"])
CATEGORY = field("categoria_servicio", required=True, options=["primary_care", "hospital", "mental_health", "other_health"])
THRESHOLD = field("umbral_km", "number")
PERIOD = field("periodo")

SPECS = [
    ("obtener_resumen_territorial", "Resumen municipal observado", "direct", [field("municipio", required=True), PERIOD], ["demografia.csv", "municipios.csv", "runtime_servicios.csv", "metadata_sources.json"], "combined"),
    ("comparar_municipios", "Comparación municipal con criterios explícitos", "derived_exact", [field("municipios", "string_array", True), AGE, field("categoria_servicio", options=CATEGORY["allowed_values"]), THRESHOLD, PERIOD], ["demografia.csv", "municipios.csv", "runtime_servicios.csv", "runtime_municipality_points.csv", "metadata_sources.json"], "combined"),
    ("analizar_envejecimiento", "Ranking demográfico 65+ o 75+", "derived_exact", [AGE, field("medida", options=["percentage", "count"]), PERIOD, field("top_n", "integer")], ["demografia.csv", "metadata_sources.json"], "demography"),
    ("analizar_acceso_servicios", "Distancia geométrica desde punto representativo", "derived_exact", [CATEGORY, THRESHOLD, PERIOD, field("municipios", "string_array")], ["demografia.csv", "municipios.csv", "runtime_servicios.csv", "runtime_municipality_points.csv", "metadata_sources.json"], "services"),
    ("analizar_coincidencia", "Cruce descriptivo de envejecimiento y distancia", "derived_exact", [CATEGORY, AGE, THRESHOLD, PERIOD, field("cuantil", "number")], ["demografia.csv", "municipios.csv", "runtime_servicios.csv", "runtime_municipality_points.csv", "metadata_sources.json"], "combined"),
    ("simular_escenario", "Contrafactual geométrico hipotético", "estimated_with_assumptions", [field("accion", required=True, options=["add_service", "remove_service", "change_threshold"]), CATEGORY, THRESHOLD, PERIOD, field("latitud", "number"), field("longitud", "number"), field("service_id"), field("nuevo_umbral_km", "number")], ["demografia.csv", "municipios.csv", "runtime_servicios.csv", "runtime_municipality_points.csv", "metadata_sources.json"], "services"),
    ("consultar_fuente", "Ficha de procedencia versionada", "direct", [field("source_id")], ["metadata_sources.json"], "all"),
    ("consultar_capacidades", "Inspección de operaciones habilitadas y límites", "direct", [field("pregunta_o_dimension")], ["metadata_sources.json"], "all"),
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    capabilities = []
    for name, description, derivation, fields, files, source_kind in SPECS:
        capabilities.append({
            "schema_version": "1.0.0", "id": name, "description": description,
            "derivation": derivation, "enabled": True, "validation_status": "tested",
            "handler": name, "input_fields": fields,
            "required_data": [
                {"path": DATA + filename, "sha256": sha(ROOT / DATA / filename)} for filename in files
            ],
            "coverage": {"territory": "Gipuzkoa", "periods": ["2025-01-01", "2025-05-07", "2026-09-20"], "entities": 88, "scope": "88 municipios; 148 registros sanitarios"},
            "source_ids": SOURCES[source_kind],
            "allowed_transformations": ["lookup", "recount", "ratio", "quantile", "euclidean_distance"] if derivation != "direct" else ["lookup"],
            "preconditions": ["Los archivos requeridos coinciden con SHA-256 versionados.", "El handler existe y ha superado pruebas locales."],
            "restrictions": ["Solo 65+ y 75+; sin rutas, citas, capacidad ni predicción."],
            "semantic_limits": ["Los periodos no forman una fotografía temporal homogénea.", "Distancia geométrica no mide acceso real; coincidencia no demuestra causa."],
        })
    capabilities.append({
        "schema_version": "1.0.0", "id": "plan_visit", "description": "Piloto W1 GO01, vinculación pendiente en W2",
        "derivation": "estimated_with_assumptions", "enabled": False, "validation_status": "pending",
        "handler": None, "input_fields": [], "required_data": [],
        "coverage": {"territory": "Goierrialdea", "periods": ["2026-09-29"], "entities": 0, "scope": "scheduled; stop_to_stop_with_destination_walk"},
        "source_ids": [], "allowed_transformations": [],
        "preconditions": ["Integración por SHA del proveedor W1 y pruebas conjuntas pendientes."],
        "restrictions": ["Solo GO01 y destinos catalogados; realtime y puerta a puerta deshabilitados."],
        "semantic_limits": ["Un horario programado no es una llegada observada.", "unknown no significa ausencia de servicio."],
    })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"schema_version": "1.0.0", "capabilities": capabilities}, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"{OUT.relative_to(ROOT).as_posix()} {OUT.stat().st_size} bytes sha256={sha(OUT)}")


if __name__ == "__main__":
    main()
