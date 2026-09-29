"""Generate an isolated two-editor Studio bundle and reproducible vNext ZIP."""

from __future__ import annotations

import ast
import hashlib
import json
import zipfile
from pathlib import Path

from scripts.agent.build_portal_sources import _module_nodes


ROOT = Path(__file__).resolve().parents[2]
V4 = ROOT / "agentes/gipuzkoa360"
NEXT = ROOT / "agentes/gipuzkoa360_vnext"
PORTAL = NEXT / "portal"
DIST = ROOT / "scripts/vnext_agent/dist"
ZIP = DIST / "gipuzkoa360-vnext-w2.zip"
MANIFEST = DIST / "gipuzkoa360-vnext-w2-manifest.json"
STAMP = (2026, 9, 29, 0, 0, 0)
LIMIT = 24 * 1024 * 1024
FILES = {
    PORTAL / "main.py": "main.py",
    PORTAL / "tools.py": "tools.py",
    ROOT / "FUENTES.md": "FUENTES.md",
    ROOT / "docs/METODOLOGIA.md": "docs/METODOLOGIA.md",
    ROOT / "contracts/vnext/evidence-v1.schema.json": "contracts/vnext/evidence-v1.schema.json",
    ROOT / "contracts/vnext/capability-v1.schema.json": "contracts/vnext/capability-v1.schema.json",
    ROOT / "datos_preparados/vnext/capabilities.json": "datos_preparados/vnext/capabilities.json",
    ROOT / "datos_preparados/municipios.csv": "datos_preparados/municipios.csv",
    ROOT / "datos_preparados/demografia.csv": "datos_preparados/demografia.csv",
    ROOT / "datos_preparados/runtime_municipality_points.csv": "datos_preparados/runtime_municipality_points.csv",
    ROOT / "datos_preparados/runtime_servicios.csv": "datos_preparados/runtime_servicios.csv",
    ROOT / "datos_preparados/metadata_sources.json": "datos_preparados/metadata_sources.json",
    ROOT / "datos_preparados/data_contract.json": "datos_preparados/data_contract.json",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _candidate_nodes() -> list[ast.stmt]:
    tree = ast.parse((NEXT / "tools.py").read_text(encoding="utf-8"))
    nodes = []
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and type(node.value.value) is str:
            continue
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            continue
        if isinstance(node, ast.Try) and any(
            isinstance(child, ast.ImportFrom) and child.module == "agentes.gipuzkoa360"
            for child in node.body
        ):
            continue
        nodes.append(node)
    return nodes


def build_portal() -> None:
    PORTAL.mkdir(parents=True, exist_ok=True)
    body: list[ast.stmt] = [ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0)]
    for filename in ("schemas.py", "metrics.py", "data_access.py", "tools.py"):
        body.extend(_module_nodes(V4 / filename))
    alias = """from types import SimpleNamespace
territorial = SimpleNamespace(
    obtener_resumen_territorial=obtener_resumen_territorial,
    comparar_municipios=comparar_municipios,
    analizar_envejecimiento=analizar_envejecimiento,
    analizar_acceso_servicios=analizar_acceso_servicios,
    analizar_coincidencia=analizar_coincidencia,
    simular_escenario=simular_escenario,
    consultar_fuente=consultar_fuente,
)"""
    body.extend(ast.parse(alias).body)
    body.extend(_candidate_nodes())
    bundled = ast.unparse(ast.fix_missing_locations(ast.Module(body=body, type_ignores=[])))
    (PORTAL / "tools.py").write_text(
        '"""Generated vNext Studio tool bundle. Edit source modules, not this file."""\n\n' + bundled + "\n",
        encoding="utf-8", newline="\n",
    )
    main = (NEXT / "main.py").read_text(encoding="utf-8")
    package_import = "try:\n    from . import tools as evidence\nexcept ImportError:\n    import tools as evidence"
    if main.count(package_import) != 1:
        raise SystemExit("Candidate main import boundary changed")
    (PORTAL / "main.py").write_text(main.replace(package_import, "import tools as evidence"), encoding="utf-8", newline="\n")


def main() -> None:
    build_portal()
    missing = [str(path.relative_to(ROOT)) for path in FILES if not path.is_file()]
    if missing:
        raise SystemExit("Missing package files: " + ", ".join(missing))
    DIST.mkdir(parents=True, exist_ok=True)
    members = {}
    with zipfile.ZipFile(ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for source, destination in sorted(FILES.items(), key=lambda item: item[1]):
            data = source.read_bytes()
            data.decode("utf-8")
            data = data.replace(b"\r\n", b"\n")
            info = zipfile.ZipInfo(destination, STAMP)
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            members[destination] = {"bytes": len(data), "sha256": sha(data)}
    size = ZIP.stat().st_size
    if size > LIMIT:
        raise SystemExit(f"Package exceeds {LIMIT} bytes")
    report = {
        "package": "GIPUZKOA360_vNext_W2_candidate", "entrypoint": "main.py:build_agent",
        "bytes": size, "sha256": sha(ZIP.read_bytes()), "limit_bytes": LIMIT,
        "members": members, "canonicalization": "UTF-8 and LF; sorted names; fixed ZIP metadata",
        "mobility_binding": "PENDING; no mock or W1 snapshot bundled",
    }
    MANIFEST.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"zip": ZIP.relative_to(ROOT).as_posix(), "bytes": size, "sha256": report["sha256"]}))


if __name__ == "__main__":
    main()
