"""Embed pinned provider evidence into a standalone, offline product review HTML."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "resultados/vnext"


def main() -> None:
    evidence = json.loads((BASE / "provider_evidence.json").read_text(encoding="utf-8"))
    if evidence.get("classification") != "OFFLINE_DETERMINISTIC_PROVIDER_OUTPUT":
        raise SystemExit("Refusing to render unclassified evidence")
    if len(evidence.get("outputs", [])) != 5:
        raise SystemExit("Expected five pinned examples")
    template = (BASE / "template.html").read_text(encoding="utf-8")
    marker = "__EMBEDDED_EVIDENCE__"
    if template.count(marker) != 1:
        raise SystemExit("Template marker missing or duplicated")
    embedded = json.dumps(evidence, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    output = template.replace(marker, embedded).encode("utf-8")
    path = BASE / "index.html"
    path.write_bytes(output)
    print(json.dumps({"path": str(path), "bytes": len(output),
                      "sha256": hashlib.sha256(output).hexdigest()}))


if __name__ == "__main__":
    main()
