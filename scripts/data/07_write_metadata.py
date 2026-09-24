"""Genera el registro canónico de fuentes y el informe de tamaños."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "datos_preparados"


def main() -> None:
    sources = [
        {
            "source_id": "EUSTAT_EMH_2025",
            "title": "Población de la C.A. de Euskadi por ámbitos territoriales, edad y sexo",
            "institution": "Eustat - Instituto Vasco de Estadística",
            "url": "https://www.eustat.eus/bankupx/api/v1/es/DB/PX_010154_cepv1_ep06b.px",
            "download_date": "2026-09-24",
            "reference_period": "2025-01-01",
            "territory": "Gipuzkoa, 88 municipios",
            "license": "Creative Commons (según ficha Eustat de la operación 010154)",
            "original_file": "datos_originales/eustat_demografia_2025.csv",
            "prepared_files": ["datos_preparados/demografia.csv", "datos_preparados/municipios.csv"],
            "notes": ["Códigos municipales Eustat/INE de cinco caracteres conservados como texto."],
            "limitations": ["75+ se deriva de año de nacimiento <=1949 a 2025-01-01."],
        },
        {
            "source_id": "ODE_HEALTH_CENTRES_2026",
            "title": "Centros de salud, ambulatorios y hospitales públicos de Euskadi",
            "institution": "Gobierno Vasco - Departamento de Salud",
            "url": "https://opendata.euskadi.eus/catalogo/-/centros-de-salud-publicos-en-euskadi/",
            "download_date": "2026-09-24",
            "reference_period": "2026-09-20",
            "territory": "Euskadi; filtrado a Gipuzkoa",
            "license": "Licencia abierta indicada por Open Data Euskadi; atribución y fecha obligatorias",
            "original_file": "datos_originales/centros-salud.xlsx",
            "prepared_files": ["datos_preparados/servicios.csv", "datos_preparados/runtime_servicios.csv"],
            "notes": ["Asignación municipal por punto dentro de polígono oficial."],
            "limitations": ["La presencia de un centro no mide capacidad, disponibilidad de citas ni calidad."],
        },
        {
            "source_id": "GEOEUSKADI_MUNICIPIOS_2025",
            "title": "Límites Administrativos del País Vasco - Municipios 1:5.000",
            "institution": "Gobierno Vasco - geoEuskadi",
            "url": "https://www.geo.euskadi.eus/limites-administrativos-del-pais-vasco/webgeo00-dataset/es/",
            "download_date": "2026-09-24",
            "reference_period": "2025-05-07",
            "territory": "Euskadi; filtrado a Gipuzkoa",
            "license": "Uso permitido citando Eusko Jaurlaritza / Gobierno Vasco",
            "original_file": "datos_originales/MUNICIPIOS_5000_ETRS89.zip",
            "prepared_files": ["datos_preparados/municipios.geojson", "datos_preparados/runtime_municipios.geojson"],
            "notes": ["CRS original y de cálculo: EPSG:25830; publicación runtime: EPSG:4326."],
            "limitations": ["El propio catálogo advierte que no es cartografía oficial conforme a Ley 7/1986 y RD 1545/2007."],
        },
        {
            "source_id": "G360_DERIVED_MUNICIPAL_METRICS_V1",
            "title": "Métricas municipales derivadas de GIPUZKOA 360",
            "institution": "DeustoAI Labs",
            "url": None,
            "download_date": "2026-09-24",
            "reference_period": "demography=2025-01-01;services=2026-09-20;geography=2025-05-07",
            "territory": "Gipuzkoa, 88 municipios",
            "license": "Hereda las condiciones de las fuentes de entrada",
            "original_file": None,
            "prepared_files": [
                "datos_preparados/municipios.csv",
                "datos_preparados/runtime_municipality_points.csv"
            ],
            "input_source_ids": [
                "EUSTAT_EMH_2025", "ODE_HEALTH_CENTRES_2026", "GEOEUSKADI_MUNICIPIOS_2025"
            ],
            "notes": [
                "Distancia euclídea EPSG:25830 desde representative_point() municipal al servicio más cercano."
            ],
            "limitations": [
                "El punto representativo no está ponderado por población.",
                "La distancia no es viaria, peatonal ni tiempo de viaje."
            ]
        },
    ]
    (OUT / "metadata_sources.json").write_text(
        json.dumps(sources, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    rows = []
    for path in sorted(OUT.glob("*")):
        if path.is_file():
            rows.append((str(path.relative_to(ROOT)), path.stat().st_size))
    lines = [
        "# Informe de tamaño del runtime",
        "",
        "El runtime recomendado usa `runtime_municipios.geojson` y `runtime_servicios.csv`.",
        "La geometría runtime se simplifica a 25 m en EPSG:25830 conservando topología; el maestro no se modifica.",
        "",
        "| Archivo | Bytes | Papel |",
        "|---|---:|---|",
    ]
    for path, size in rows:
        role = "runtime" if "runtime_" in path else "maestro/auditoría"
        lines.append(f"| `{path}` | {size:,} | {role} |")
    (ROOT / "analisis" / "runtime_size_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Metadatos e informe de tamaño generados.")


if __name__ == "__main__":
    main()

