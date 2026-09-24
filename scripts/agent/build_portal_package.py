"""Construye el paquete mínimo reproducible para el runtime del portal."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "dist" / "gipuzkoa360-portal.zip"
MAX_BYTES = 24 * 1024 * 1024

FILES = [
    "agentes/gipuzkoa360/__init__.py",
    "agentes/gipuzkoa360/main.py",
    "agentes/gipuzkoa360/tools.py",
    "agentes/gipuzkoa360/schemas.py",
    "agentes/gipuzkoa360/data_access.py",
    "agentes/gipuzkoa360/metrics.py",
    "agentes/gipuzkoa360/requirements.txt",
    "agentes/gipuzkoa360/README.md",
    "FUENTES.md",
    "docs/METODOLOGIA.md",
    "docs/RESULT_SCHEMA.md",
    "datos_preparados/municipios.csv",
    "datos_preparados/demografia.csv",
    "datos_preparados/runtime_municipality_points.csv",
    "datos_preparados/runtime_servicios.csv",
    "datos_preparados/metadata_sources.json",
]


def main() -> None:
    missing = [name for name in FILES if not (ROOT / name).is_file()]
    if missing:
        raise SystemExit("Faltan archivos del paquete: " + ", ".join(missing))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in FILES:
            archive.write(ROOT / name, name)
    size = OUTPUT.stat().st_size
    if size > MAX_BYTES:
        raise SystemExit(f"Paquete de {size} bytes supera el límite de {MAX_BYTES}.")
    digest = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    report = {
        "path": str(OUTPUT.relative_to(ROOT)),
        "bytes": size,
        "limit_bytes": MAX_BYTES,
        "sha256": digest,
        "files": FILES,
    }
    (OUTPUT.parent / "gipuzkoa360-portal-manifest.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
