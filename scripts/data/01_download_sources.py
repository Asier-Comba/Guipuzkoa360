"""Descarga reproducible de las fuentes oficiales de GIPUZKOA 360."""
from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from datetime import date
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "datos_originales"
RAW.mkdir(parents=True, exist_ok=True)

HEALTH_URL = (
    "https://opendata.euskadi.eus/contenidos/ds_localizaciones/"
    "centros_salud_en_euskadi/opendata/centros-salud.xlsx"
)
BOUNDARIES_URL = (
    "https://www.geo.euskadi.eus/cartografia/DatosDescarga/Limites/"
    "MUNICIPIOS_5000_ETRS89.zip"
)
PX_65_URL = (
    "https://www.eustat.eus/bankupx/api/v1/es/DB/"
    "PX_010154_cepv1_ep06b.px"
)
PX_BIRTH_URL = (
    "https://www.eustat.eus/bankupx/api/v1/es/DB/"
    "PX_010154_cepv1_ep10b.px"
)


def get(url: str) -> requests.Response:
    response = requests.get(url, timeout=90)
    response.raise_for_status()
    return response


def download(url: str, target: Path) -> None:
    target.write_bytes(get(url).content)


def post_px(url: str, query: dict, target: Path) -> None:
    response = requests.post(url, json=query, timeout=120)
    response.raise_for_status()
    target.write_bytes(response.content)


def item(code: str, values: list[str]) -> dict:
    return {"code": code, "selection": {"filter": "item", "values": values}}


def checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    download(HEALTH_URL, RAW / "centros-salud.xlsx")
    download(BOUNDARIES_URL, RAW / "MUNICIPIOS_5000_ETRS89.zip")
    with zipfile.ZipFile(RAW / "MUNICIPIOS_5000_ETRS89.zip") as archive:
        archive.extractall(RAW / "municipios_etrs89")

    meta_65 = get(PX_65_URL).json()
    meta_birth = get(PX_BIRTH_URL).json()
    (RAW / "eustat_ep06b_metadata.json").write_text(
        json.dumps(meta_65, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n"
    )
    (RAW / "eustat_ep10b_metadata.json").write_text(
        json.dumps(meta_birth, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n"
    )

    territorial = meta_65["variables"][0]
    municipality_codes = [
        code for code in territorial["values"] if len(code) == 5 and code.startswith("20")
    ]
    if len(municipality_codes) != 88:
        raise RuntimeError(f"Se esperaban 88 municipios de Gipuzkoa; API devolvió {len(municipality_codes)}")

    query_65 = {
        "query": [
            item("ámbitos territoriales", municipality_codes),
            {"code": "grandes grupos de edad cumplida", "selection": {"filter": "all", "values": ["*"]}},
            item("sexo", ["10"]),
            item("periodo", ["20250101"]),
        ],
        "response": {"format": "csv"},
    }
    post_px(PX_65_URL, query_65, RAW / "eustat_demografia_2025.csv")

    birth_vars = {variable["code"]: variable for variable in meta_birth["variables"]}
    birth_year_codes = [
        code
        for code, label in zip(
            birth_vars["año de nacimiento"]["values"],
            birth_vars["año de nacimiento"]["valueTexts"],
        )
        if label.startswith("<=") or (label.isdigit() and int(label) <= 1949)
    ]
    query_birth = {
        "query": [
            item("ámbitos territoriales", municipality_codes),
            item("año de nacimiento", birth_year_codes),
            item("sexo", ["10"]),
            item("periodo", ["20250101"]),
        ],
        "response": {"format": "csv"},
    }
    post_px(PX_BIRTH_URL, query_birth, RAW / "eustat_nacimientos_hasta_1949_2025.csv")

    tracked = [
        RAW / "centros-salud.xlsx",
        RAW / "MUNICIPIOS_5000_ETRS89.zip",
        RAW / "eustat_demografia_2025.csv",
        RAW / "eustat_nacimientos_hasta_1949_2025.csv",
    ]
    manifest = {
        "download_date": date.today().isoformat(),
        "python": sys.version,
        "files": [
            {"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": checksum(path)}
            for path in tracked
        ],
    }
    (RAW / "download_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n"
    )
    print(f"Descargadas 4 fuentes/consultas; {len(municipality_codes)} municipios Eustat.")


if __name__ == "__main__":
    main()
