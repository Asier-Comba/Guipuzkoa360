"""Inventory tracked baseline files and every development-language occurrence."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = "488f46db7047d9393d4d4a489a869ab246c215b9"
HISTORY = {
    "DEMO_QUERIES.md", "JURY_READINESS.md", "INTEGRATION_PLAYBOOK.md",
    "INTEGRATION_STATUS_2026-09-24.md", "PR3_RECOVERY_AUDIT.md",
    "REAL_DATA_INTEGRATION.md", "RC2_FINAL_STATUS.md", "PORTAL_EVIDENCE_RC2.md",
}
UPDATE = {
    "README.md", "datos_preparados/README.md", "docs/JURY_TEST_PLAN.md",
    "docs/RELEASE_CANDIDATE.md", "docs/RUBRIC_TRACEABILITY.md",
    "docs/SUBMISSION_CHECKLIST.md", "docs/RUNTIME_PACKAGE.md",
}
PATTERN = re.compile(
    r"Work\s*[123]|RC[12]|\bv[123]\b|mock|fixture|synthetic|sint[eé]tic[oa]s?|"
    r"\bLLM\b|ChatGPT|OpenAI|handoff|pending|pendiente|\bTODO\b|\bFIXME\b", re.I
)


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def classification(path: str) -> tuple[str, str, str]:
    name = Path(path).name
    if path == "datos_preparados/README.md":
        return "OBSOLETE", "UPDATE", "Placeholder incompatible con datos ya disponibles."
    if path == "README.md":
        return "PUBLIC", "UPDATE", "Nueva entrada canónica del producto."
    if path in {"FUENTES.md", "docs/METODOLOGIA.md"}:
        return "PUBLIC", "KEEP", "Contexto congelado: conservar bytes y trazabilidad."
    if path == "docs/PORTAL_DEPLOYMENT.md":
        return "HISTORICAL", "UPDATE", "Archivar guía y corregir rutas; solo cambia un miembro documental del ZIP, no el contexto."
    if path.startswith("docs/") and (name.startswith("HANDOFF_") or name in HISTORY):
        return "HISTORICAL", "MOVE_TO_INTERNAL", "Conservar evidencia fechada, no presentarla como estado actual."
    if path in UPDATE:
        return "TECHNICAL", "UPDATE", "Reemplazar claims por enlaces a evidencia actual."
    if path.startswith("resultados/") and path.endswith(".html"):
        return "HISTORICAL", "REMOVE_FROM_PUBLIC_NAVIGATION", "Vista local de tres municipios; no equivale a coincidencia provincial."
    if path.startswith(("tests/", "analisis/")):
        return "INTERNAL", "KEEP", "Tests, controles negativos o evidencia; no convertirlos en resultados de portal."
    return "TECHNICAL", "KEEP", "Contrato, código, fuente o recurso de ingeniería; términos internos justificados."


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ref", default=BASE)
    args = parser.parse_args()
    paths = git("ls-tree", "-r", "--name-only", args.ref).decode().splitlines()
    files, occurrences = [], []
    for path in paths:
        blob = git("show", f"{args.ref}:{path}")
        category, action, reason = classification(path)
        files.append({"path": path, "category": category, "decision": action,
                      "reason": reason, "bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest()})
        if path.endswith((".zip", ".xlsx")):
            continue
        for number, line in enumerate(blob.decode("utf-8-sig", errors="replace").splitlines(), 1):
            for match in PATTERN.finditer(line):
                occurrences.append({"path": path, "line": number, "column": match.start() + 1,
                                    "term": match.group(), "decision": action, "reason": reason,
                                    "context": line[max(0, match.start()-55):match.end()+80]})
    report = {"baseline": args.ref, "files_total": len(files),
              "categories": dict(Counter(f["category"] for f in files)),
              "occurrences_total": len(occurrences), "files": files, "occurrences": occurrences}
    out = ROOT / "docs/internal/release/repository-audit.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in report.items() if k not in {"files", "occurrences"}}))


if __name__ == "__main__":
    main()
