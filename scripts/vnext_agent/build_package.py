"""Generate an isolated two-editor Studio bundle and reproducible vNext ZIP."""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
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
LIMIT = 24 * 1024 * 1024  # Local safety limit; not an observed portal limit.
PIN_FILE = ROOT / "scripts/vnext_agent/w1_pin.json"
FILES = {
    PORTAL / "main.py": "main.py",
    PORTAL / "tools.py": "tools.py",
    PORTAL / "mobility_adapter.py": "mobility_adapter.py",
    ROOT / "FUENTES.md": "FUENTES.md",
    ROOT / "docs/METODOLOGIA.md": "docs/METODOLOGIA.md",
    ROOT / "contracts/vnext/evidence-v1.schema.json": "contracts/vnext/evidence-v1.schema.json",
    ROOT / "contracts/vnext/evidence-v1.1.schema.json": "contracts/vnext/evidence-v1.1.schema.json",
    ROOT / "contracts/vnext/capability-v1.schema.json": "contracts/vnext/capability-v1.schema.json",
    ROOT / "contracts/vnext/capability-v1.1.schema.json": "contracts/vnext/capability-v1.1.schema.json",
    ROOT / "tests/vnext_agent/test_contracts.py": "tests/vnext_agent/test_contracts.py",
    ROOT / "datos_preparados/vnext/capabilities.json": "datos_preparados/vnext/capabilities.json",
    ROOT / "datos_preparados/vnext/mobility_sources.json": "datos_preparados/vnext/mobility_sources.json",
    PIN_FILE: "scripts/vnext_agent/w1_pin.json",
    ROOT / "tests/vnext_agent/test_mobility_binding.py": "tests/vnext_agent/test_mobility_binding.py",
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
    DataRepository=DataRepository,
    TerritorialAnalysis=TerritorialAnalysis,
    normalize_service_category=normalize_service_category,
    normalize_age_group=normalize_age_group,
    normalize_scenario_action=normalize_scenario_action,
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
    (PORTAL / "mobility_adapter.py").write_text((NEXT / "mobility_adapter.py").read_text(encoding="utf-8"), encoding="utf-8", newline="\n")


def _w1_blobs() -> tuple[dict[str, bytes], dict]:
    pin = json.loads(PIN_FILE.read_text(encoding="utf-8"))
    if pin["commit"] != "725a7b73ae0381092cd80edc41b8a25432d75fcd" or pin["contract_version"] != "0.2.0" or pin["health_destination_go"] is not False:
        raise SystemExit("W1 pin is not the approved stop-only contract")
    blobs = {}
    for item in pin["files"]:
        path = item["path"]
        if not path.startswith("prototypes/") or ".." in Path(path).parts:
            raise SystemExit("W1 pin has unsafe path")
        data = subprocess.check_output(["git", "show", f"{pin['commit']}:{path}"], cwd=ROOT)
        if len(data) != item["bytes"] or sha(data) != item["sha256"]:
            raise SystemExit(f"W1 pinned blob mismatch: {path}")
        blobs[path] = data
    if len(blobs) != len(pin["files"]):
        raise SystemExit("Duplicate W1 pin path")
    return blobs, pin


def _combined_registry(pin: dict) -> bytes:
    registry = json.loads((ROOT / "datos_preparados/vnext/capabilities.json").read_text(encoding="utf-8"))
    mobility = next(item for item in registry["capabilities"] if item["id"] == "plan_visit")
    if mobility["enabled"] or mobility["validation_status"] != "pending":
        raise SystemExit("Source registry must leave mobility pending")
    test_file = ROOT / "tests/vnext_agent/test_mobility_binding.py"
    mobility.update({
        "description": "Viaje GO01 programado entre paradas y comparación 2–32, no visita sanitaria",
        "enabled": True, "validation_status": "tested", "handler": "plan_visit",
        "input_fields": [{"name": "request", "type": "object_or_array", "required": True, "allowed_values": []}],
        "required_data": [{"path": item["path"], "sha256": item["sha256"]} for item in pin["files"]],
        "coverage": {"territory": "Goierrialdea", "periods": ["2026-09-29"], "entities": 1, "scope": "scheduled; stop_only; origin_stop_presence_to_return_stop_arrival"},
        "source_ids": ["W1_GTFS@2026-09-29", "W2_USER@2026-09-29", "W1_MODEL@2026-09-29", "W1_DERIVED@2026-09-29"],
        "allowed_transformations": ["direct_pair_search", "contiguous_component_sum", "bounded_comparison"],
        "preconditions": ["Proveedor, allowlist, validator y snapshot coinciden con el pin W1 publicado.", "Solo stop_only con fecha validada; ningún acceso sanitario acreditado."],
        "precondition_checks": ["required_data_sha256", "handler_signature", "source_catalog", "coverage_count"],
        "validation_evidence": [{"test_file": "tests/vnext_agent/test_mobility_binding.py", "test_name": "test_published_w1_020_is_pinned_and_role_attributed", "sha256": sha(test_file.read_bytes())}],
        "restrictions": ["Solo parada a parada; no Ambulatorio de Beasain, puerta a puerta, transbordo o realtime."],
        "semantic_limits": ["Horarios programados y walking stop_only modelado no son observaciones de llegada real.", "Unknown no significa ausencia de transporte; no viable no es fallo de red."],
    })
    return (json.dumps(registry, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def main() -> None:
    build_portal()
    missing = [str(path.relative_to(ROOT)) for path in FILES if not path.is_file()]
    if missing:
        raise SystemExit("Missing package files: " + ", ".join(missing))
    DIST.mkdir(parents=True, exist_ok=True)
    w1_blobs, pin = _w1_blobs()
    package_files = {destination: source.read_bytes().replace(b"\r\n", b"\n") for source, destination in FILES.items()}
    package_files.update(w1_blobs)
    package_files["datos_preparados/vnext/capabilities.json"] = _combined_registry(pin)
    members = {}
    with zipfile.ZipFile(ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for destination, data in sorted(package_files.items()):
            data.decode("utf-8")
            info = zipfile.ZipInfo(destination, STAMP)
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            members[destination] = {"bytes": len(data), "sha256": sha(data)}
    size = ZIP.stat().st_size
    if size > LIMIT:
        raise SystemExit(f"Package exceeds {LIMIT} bytes")
    main_tree = ast.parse(package_files["main.py"].decode("utf-8"))
    constants = {
        node.targets[0].id: ast.literal_eval(node.value)
        for node in main_tree.body
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id in {"AGENT_NAME", "SYSTEM_PROMPT", "STUDIO_CONTEXT_FILES"}
    }
    tool_count = sum(
        isinstance(node, ast.FunctionDef) and any(isinstance(decorator, ast.Name) and decorator.id == "tool" for decorator in node.decorator_list)
        for node in main_tree.body
    )
    context_paths = constants["STUDIO_CONTEXT_FILES"]
    if tool_count > 10 or not 2 <= len(constants["AGENT_NAME"]) <= 80 or not 10 <= len(constants["SYSTEM_PROMPT"]) <= 8000:
        raise SystemExit("Observed portal tool/name/instruction limits exceeded")
    if len(set(context_paths)) != len(context_paths) or any(path not in package_files for path in context_paths):
        raise SystemExit("Missing or duplicated context file")
    report = {
        "package": "GIPUZKOA360_vNext_W2_candidate", "entrypoint": "main.py:build_agent",
        "bytes": size, "sha256": sha(ZIP.read_bytes()), "limit_bytes": LIMIT,
        "limit_provenance": "local_safety_limit_not_portal_rule",
        "uncompressed_bytes": sum(item["bytes"] for item in members.values()),
        "w1_pin": pin["commit"], "w1_contract": pin["contract_version"], "health_destination_go": False,
        "tool_count": tool_count,
        "agent_name_chars": len(constants["AGENT_NAME"]),
        "instruction_chars": len(constants["SYSTEM_PROMPT"]),
        "context_file_count": len(context_paths),
        "context_bytes": sum(len(package_files[path]) for path in context_paths),
        "context_paths": context_paths,
        "runtime_dependencies": ["Python 3.12 standard library", "portal-provided studio.tool", "portal-provided langchain.agents.create_agent"],
        "members": members, "canonicalization": "UTF-8 and LF; sorted names; fixed ZIP metadata",
        "mobility_binding": "PINNED_STOP_ONLY_0.2.0; W1 source and snapshot bytes verified at build time",
    }
    MANIFEST.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"zip": ZIP.relative_to(ROOT).as_posix(), "bytes": size, "sha256": report["sha256"]}))


if __name__ == "__main__":
    main()
