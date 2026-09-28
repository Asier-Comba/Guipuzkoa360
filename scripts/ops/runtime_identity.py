"""Identidad reproducible del runtime actual, independiente del nombre de rama."""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path


def runtime_files(root: Path) -> list[str]:
    main_path = root / "agentes/gipuzkoa360/portal/main.py"
    tree = ast.parse(main_path.read_text(encoding="utf-8"))
    assignment = next(
        node for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "STUDIO_CONTEXT_FILES" for target in node.targets)
    )
    context = ast.literal_eval(assignment.value)
    return [
        "agentes/gipuzkoa360/portal/main.py",
        "agentes/gipuzkoa360/portal/tools.py",
        "agentes/gipuzkoa360/requirements.txt",
        *context,
    ]


def compute_runtime_sha(root: Path) -> str:
    digest = hashlib.sha256()
    for relative in runtime_files(root):
        path = root / relative
        if not path.is_file():
            raise FileNotFoundError(relative)
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()
