"""Ejecuta el pipeline completo en orden y detiene ante cualquier error."""
from __future__ import annotations

import subprocess
import sys
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


def main() -> None:
    for step in STEPS:
        print(f"\n== {step} ==")
        subprocess.run([sys.executable, str(HERE / step)], check=True)


if __name__ == "__main__":
    main()
