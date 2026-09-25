"""Ejecuta el pipeline completo en orden y detiene ante cualquier error."""
from __future__ import annotations

import subprocess
import sys
import argparse
import hashlib
import json
import zipfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
STEPS = [
    "01_download_sources.py",
    "02_prepare_geography.py",
    "03_prepare_demography.py",
    "04_prepare_services.py",
    "05_build_metrics.py",
    "06_validate_data.py",
    "07_write_metadata.py",
    "08_build_qa_assets.py",
]


def verify_snapshot(root: Path) -> None:
    """Verify committed source bytes; do not refresh today's live endpoints."""
    manifest = json.loads((root / "datos_originales/download_manifest.json").read_text(encoding="utf-8"))
    for entry in manifest["files"]:
        path = (root / entry["path"].replace("\\", "/")).resolve()
        if not path.is_relative_to(root.resolve() / "datos_originales"):
            raise ValueError("Ruta fuera del snapshot")
        data = path.read_bytes()
        if len(data) != entry["bytes"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise ValueError(f"Snapshot alterado: {entry['path']}")
    target = (root / "datos_originales/municipios_etrs89").resolve()
    with zipfile.ZipFile(root / "datos_originales/MUNICIPIOS_5000_ETRS89.zip") as archive:
        for name in archive.namelist():
            if not (target / name).resolve().is_relative_to(target):
                raise ValueError("Ruta insegura en archivo de geometría")
        archive.extractall(target)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", help="Regenerar desde el snapshot versionado y verificado, sin descargar")
    args = parser.parse_args()
    if args.offline:
        verify_snapshot(HERE.parents[1])
    for step in (STEPS[1:] if args.offline else STEPS):
        print(f"\n== {step} ==")
        subprocess.run([sys.executable, str(HERE / step)], check=True)


if __name__ == "__main__":
    main()
