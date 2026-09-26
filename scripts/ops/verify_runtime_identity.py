"""Byte identity gate: derive the frozen list from Git, never the current declaration."""
from __future__ import annotations
import ast
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = "195b4980fa5998b096c308296a55e452380b0371"

def frozen_files(root=ROOT):
    blob = subprocess.check_output(["git", "show", f"{RUNTIME}:agentes/gipuzkoa360/portal/main.py"], cwd=root)
    tree = ast.parse(blob.decode("utf-8"))
    contexts = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == "STUDIO_CONTEXT_FILES" for t in n.targets))
    return ["agentes/gipuzkoa360/main.py", "agentes/gipuzkoa360/tools.py",
            "agentes/gipuzkoa360/portal/main.py", "agentes/gipuzkoa360/portal/tools.py", *contexts]

def audit(root=ROOT):
    rows = []
    for path in frozen_files(root):
        expected = subprocess.check_output(["git", "show", f"{RUNTIME}:{path}"], cwd=root)
        actual = (root/path).read_bytes() if (root/path).is_file() else b""
        rows.append({"path": path, "matches": actual == expected,
                     "sha256": hashlib.sha256(actual).hexdigest()})
    return {"runtime": RUNTIME, "status": "PASS" if all(r["matches"] for r in rows) else "FAIL", "files": rows}

if __name__ == "__main__":
    report = audit()
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["status"] == "PASS" else 1)
