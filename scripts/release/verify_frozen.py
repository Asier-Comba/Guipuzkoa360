"""Fail closed on any byte change to the portal-validated runtime/context."""
from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNTIME_SHA = "195b4980fa5998b096c308296a55e452380b0371"


def frozen_paths() -> list[str]:
    source = subprocess.check_output([
        "git", "show", f"{RUNTIME_SHA}:agentes/gipuzkoa360/portal/main.py"
    ], cwd=ROOT).decode("utf-8")
    tree = ast.parse(source)
    context = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == "STUDIO_CONTEXT_FILES" for t in node.targets))
    return ["agentes/gipuzkoa360/portal/main.py", "agentes/gipuzkoa360/portal/tools.py", *context]


def verify() -> dict:
    checks = []
    for path in frozen_paths():
        expected = subprocess.check_output(["git", "show", f"{RUNTIME_SHA}:{path}"], cwd=ROOT)
        actual = (ROOT / path).read_bytes()
        checks.append({"path": path, "bytes": len(actual), "sha256": hashlib.sha256(actual).hexdigest(),
                       "status": "PASS" if actual == expected else "FAIL"})
    manifest = json.loads((ROOT / "datos_preparados/runtime_manifest.json").read_text(encoding="utf-8"))
    entries = []
    for entry in manifest["files"]:
        actual = (ROOT / entry["path"]).read_bytes()
        entries.append({**entry, "status": "PASS" if len(actual) == entry["bytes"] and
                        hashlib.sha256(actual).hexdigest() == entry["sha256"] else "FAIL"})
    total_ok = sum(e["bytes"] for e in entries) == manifest["total_bytes"]
    return {"runtime_sha": RUNTIME_SHA, "frozen": checks, "manifest": entries,
            "manifest_total_bytes": manifest["total_bytes"],
            "status": "PASS" if total_ok and all(e["status"] == "PASS" for e in checks + entries) else "FAIL"}


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["status"] == "PASS" else 1)
