"""Construye el paquete mínimo reproducible para el runtime del portal."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RELEASE_VERSION = "urban-challenge-rc2"
OUTPUT = ROOT / "dist" / f"gipuzkoa360-{RELEASE_VERSION}.zip"
MAX_BYTES = 24 * 1024 * 1024
FIXED_ZIP_TIME = (2026, 9, 24, 0, 0, 0)

FILES = {
    "agentes/gipuzkoa360/portal/main.py": "main.py",
    "agentes/gipuzkoa360/portal/tools.py": "tools.py",
    "agentes/gipuzkoa360/requirements.txt": "requirements.txt",
    "FUENTES.md": "FUENTES.md",
    "docs/METODOLOGIA.md": "docs/METODOLOGIA.md",
    "docs/RESULT_SCHEMA.md": "docs/RESULT_SCHEMA.md",
    "docs/PORTAL_DEPLOYMENT.md": "docs/PORTAL_DEPLOYMENT.md",
    "datos_preparados/municipios.csv": "datos_preparados/municipios.csv",
    "datos_preparados/demografia.csv": "datos_preparados/demografia.csv",
    "datos_preparados/runtime_municipality_points.csv": "datos_preparados/runtime_municipality_points.csv",
    "datos_preparados/runtime_servicios.csv": "datos_preparados/runtime_servicios.csv",
    "datos_preparados/metadata_sources.json": "datos_preparados/metadata_sources.json",
    "datos_preparados/data_contract.json": "datos_preparados/data_contract.json",
    "datos_preparados/runtime_manifest.json": "datos_preparados/runtime_manifest.json",
}


def canonical_bytes(path: Path) -> bytes:
    """UTF-8/LF packaging only; never rewrite the source or portal deployment."""
    data = path.read_bytes()
    data.decode('utf-8')  # Reject unknown encodings rather than silently transcoding.
    return data.replace(b'\r\n', b'\n')


def main() -> None:
    missing = [name for name in FILES if not (ROOT / name).is_file()]
    if missing:
        raise SystemExit("Faltan archivos del paquete: " + ", ".join(missing))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for source_name, archive_name in sorted(FILES.items(), key=lambda item: item[1]):
            info = zipfile.ZipInfo(archive_name, FIXED_ZIP_TIME)
            info.create_system = 3
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(
                info, canonical_bytes(ROOT / source_name), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9
            )
    size = OUTPUT.stat().st_size
    if size > MAX_BYTES:
        raise SystemExit(f"Paquete de {size} bytes supera el límite de {MAX_BYTES}.")
    digest = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    report = {
        "release_version": RELEASE_VERSION,
        "path": OUTPUT.relative_to(ROOT).as_posix(),
        "entrypoint": "main.py:build_agent",
        "bytes": size,
        "limit_bytes": MAX_BYTES,
        "sha256": digest,
        "files": sorted(FILES.values()),
        "canonicalization": "UTF-8 validated; CRLF to LF; no other whitespace or source changes",
        "zip_metadata": "sorted names; 2026-09-24 00:00:00; Unix create_system=3; regular file 0644; deflate level 9",
        "members": {
            destination: {"bytes": len(canonical_bytes(ROOT / source)),
                          "sha256": hashlib.sha256(canonical_bytes(ROOT / source)).hexdigest()}
            for source, destination in sorted(FILES.items(), key=lambda pair: pair[1])
        },
    }
    (OUTPUT.parent / f"gipuzkoa360-{RELEASE_VERSION}-manifest.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
