"""Genera los dos únicos archivos Python editables por el agente del portal."""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "agentes" / "gipuzkoa360"
OUTPUT = SOURCE / "portal"
INTERNAL_MODULES = {"schemas", "metrics", "data_access", ".schemas", ".metrics", ".data_access"}


def _is_internal_import(node: ast.AST) -> bool:
    if isinstance(node, ast.ImportFrom):
        dotted = "." * node.level + (node.module or "")
        return dotted in INTERNAL_MODULES or (node.module or "") in INTERNAL_MODULES
    return False


def _module_nodes(path: Path) -> list[ast.stmt]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=path.as_posix())
    nodes: list[ast.stmt] = []
    for index, node in enumerate(tree.body):
        if index == 0 and isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            continue
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            continue
        if _is_internal_import(node):
            continue
        if isinstance(node, ast.Try):
            imports = [item for branch in [node.body, *[handler.body for handler in node.handlers]] for item in branch]
            if imports and all(_is_internal_import(item) for item in imports):
                continue
        nodes.append(node)
    return nodes


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    body: list[ast.stmt] = [ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0)]
    for filename in ("schemas.py", "metrics.py", "data_access.py", "tools.py"):
        body.extend(_module_nodes(SOURCE / filename))
    bundled = ast.unparse(ast.fix_missing_locations(ast.Module(body=body, type_ignores=[])))
    (OUTPUT / "tools.py").write_text(
        '"""Bundle autocontenido generado; editar los módulos fuente, no este archivo."""\n\n'
        + bundled + "\n",
        encoding="utf-8",
        newline="\n",
    )
    main_source = (SOURCE / "main.py").read_text(encoding="utf-8")
    (OUTPUT / "main.py").write_text(main_source, encoding="utf-8", newline="\n")
    print("agentes/gipuzkoa360/portal/main.py")
    print("agentes/gipuzkoa360/portal/tools.py")


if __name__ == "__main__":
    main()
