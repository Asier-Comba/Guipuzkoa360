"""Captura o verifica que la identidad del runtime actual no cambie durante un gate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from runtime_identity import compute_runtime_sha, runtime_files


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", type=Path)
    parser.add_argument("--expected-file", type=Path)
    args = parser.parse_args()
    identity = compute_runtime_sha(ROOT)
    if args.expected_file:
        expected = args.expected_file.read_text(encoding="utf-8").strip()
        if identity != expected:
            raise SystemExit(f"Runtime cambió durante la validación: {expected} -> {identity}")
    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(identity + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": "PASS", "runtime_sha256": identity, "files": runtime_files(ROOT)}, indent=2))


if __name__ == "__main__":
    main()
