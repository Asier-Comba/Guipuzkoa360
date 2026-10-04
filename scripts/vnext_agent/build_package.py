"""Generate an isolated two-editor Studio bundle and reproducible vNext ZIP."""

from __future__ import annotations

import ast
import hashlib
import json
import zipfile
from pathlib import Path

from scripts.agent.build_portal_sources import _module_nodes
from scripts.vnext_agent.w1_r6_bundle import (
    LABELS_PATH, PACKAGE_SHA256 as W1_R6_PACKAGE_SHA256,
    SUPPORT_PIN, TESTED_RUNTIME_COMMIT, blob as w1_blob,
    published_runtime,
)


ROOT = Path(__file__).resolve().parents[2]
V4 = ROOT / "agentes/gipuzkoa360"
NEXT = ROOT / "agentes/gipuzkoa360_vnext"
PORTAL = NEXT / "portal"
DIST = ROOT / "scripts/vnext_agent/dist"
ZIP = DIST / "gipuzkoa360-vnext-w2.zip"
MANIFEST = DIST / "gipuzkoa360-vnext-w2-manifest.json"
STAMP = (2026, 9, 29, 0, 0, 0)
LIMIT = 24 * 1024 * 1024  # Conservative local guard; portal says 24 MB, basis/unit unspecified.
PIN_FILE = ROOT / "scripts/vnext_agent/w1_pin.json"
W1_PACKAGE_PATH = "datos_preparados/vnext/w1_r6_runtime.zip"
W1_CATALOG_PATH = "datos_preparados/vnext/operational_catalog_r6.json"
W1_LABELS_PATH = "datos_preparados/vnext/consumer_labels_r7.json"
W1_CONFORMANCE_PATH = "datos_preparados/vnext/w1_conformance_r7.json"
FILES = {
    PORTAL / "main.py": "main.py",
    PORTAL / "tools.py": "tools.py",
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
    ROOT / "tests/vnext_agent/test_health_r10.py": "tests/vnext_agent/test_health_r10.py",
    ROOT / "tests/vnext_agent/test_r12_generated.py": "tests/vnext_agent/test_r12_generated.py",
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
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "_DEFAULT_WORKSPACE_ROOT" for target in node.targets):
            node.value = ast.parse("Path(__file__).resolve().parents[2] if Path(__file__).resolve().parent.parent.name == 'agentes' else Path(__file__).resolve().parent", mode="eval").body
        nodes.append(node)
    return nodes


def _bootstrap_source() -> str:
    helpers = {
        name: (NEXT / f"{name}.py").read_text(encoding="utf-8")
        for name in ("mobility_adapter", "health_adapter")
    }
    return f'''
import sys as _w1_sys
import tempfile as _w1_tempfile
import types as _w1_types
import zipfile as _w1_zipfile
from pathlib import PurePosixPath as _W1PurePath

_W1_PACKAGE_SHA256 = {W1_R6_PACKAGE_SHA256!r}
_W1_HELPERS = {helpers!r}
_W1_TEMPDIR = None
_W1_BOUND_ROOT = None

def _ensure_w1_runtime(root):
    global _W1_TEMPDIR, _W1_BOUND_ROOT
    archive_path = root / {W1_PACKAGE_PATH!r}
    if not archive_path.is_file():
        raise ContractViolation("mobility:pinned_package_missing")
    raw = archive_path.read_bytes()
    if digest(raw) != _W1_PACKAGE_SHA256:
        raise ContractViolation("mobility:pinned_package_sha_mismatch")
    if _W1_TEMPDIR is not None:
        if root != _W1_BOUND_ROOT:
            raise ContractViolation("mobility:runtime_root_changed")
        return
    existing = _w1_sys.modules.get("prototypes")
    if existing is not None:
        raise ContractViolation("mobility:unverified_preloaded_provider")
    temp = _w1_tempfile.TemporaryDirectory(prefix="g360-w1-r6-")
    with _w1_zipfile.ZipFile(archive_path) as archive:
        members = archive.infolist()
        if sum(item.file_size for item in members) > 2_000_000:
            raise ContractViolation("mobility:archive_too_large")
        for item in members:
            part = _W1PurePath(item.filename)
            if part.is_absolute() or ".." in part.parts or "\\\\" in item.filename:
                raise ContractViolation("mobility:unsafe_archive_path")
        archive.extractall(temp.name)
    _w1_sys.path.insert(0, temp.name)
    for name, source in _W1_HELPERS.items():
        module = _w1_types.ModuleType(name)
        module.__file__ = "<verified W2 bundled " + name + ">"
        _w1_sys.modules[name] = module
        exec(compile(source, module.__file__, "exec"), module.__dict__)
    _W1_TEMPDIR = temp
    _W1_BOUND_ROOT = root
'''


def build_portal() -> None:
    PORTAL.mkdir(parents=True, exist_ok=True)
    body: list[ast.stmt] = [ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0)]
    for filename in ("schemas.py", "metrics.py", "data_access.py", "tools.py"):
        body.extend(_module_nodes(V4 / filename))
    alias = """from types import SimpleNamespace
territorial = SimpleNamespace(
    DataRepository=DataRepository,
    TerritorialAnalysis=TerritorialAnalysis,
    _safe=_safe,
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
    # Runtime freeze must not require mounting test sources/gold as LLM context.
    # Carry only an index of the exact reviewed test bytes and actual function names.
    proof_index = {}
    for source, destination in FILES.items():
        if destination.startswith("tests/vnext_agent/"):
            test_source = source.read_bytes()
            test_tree = ast.parse(test_source.decode("utf-8"))
            proof_index[destination] = {"sha256": sha(test_source), "test_names": sorted(node.name for node in test_tree.body if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"))}
    body.extend(ast.parse("_BUNDLED_VALIDATION_INDEX = " + repr(proof_index)).body)
    bundled = ast.unparse(ast.fix_missing_locations(ast.Module(body=body, type_ignores=[])))
    (PORTAL / "tools.py").write_text(
        '"""Generated two-editor Studio tool bundle. Edit source modules, not this file."""\n\n' + bundled + "\n" + _bootstrap_source(),
        encoding="utf-8", newline="\n",
    )
    main = (NEXT / "main.py").read_text(encoding="utf-8")
    package_import = "try:\n    from . import tools as evidence\nexcept ImportError:\n    import tools as evidence"
    if main.count(package_import) != 1:
        raise SystemExit("Candidate main import boundary changed")
    (PORTAL / "main.py").write_text(main.replace(package_import, "import tools as evidence"), encoding="utf-8", newline="\n")
    # The historical generated helper is retained for audit; only main.py and
    # tools.py are executable editors in the combined package.
    (PORTAL / "mobility_adapter.py").write_text((NEXT / "mobility_adapter.py").read_text(encoding="utf-8"), encoding="utf-8", newline="\n")


def _combined_registry(w1_package_sha: str, w1_catalog_sha: str, w1_labels_sha: str) -> bytes:
    registry = json.loads((ROOT / "datos_preparados/vnext/capabilities.json").read_text(encoding="utf-8"))
    mobility = next(item for item in registry["capabilities"] if item["id"] == "plan_visit")
    if mobility["enabled"] or mobility["validation_status"] != "pending":
        raise SystemExit("Source registry must leave mobility pending")
    test_file = ROOT / "tests/vnext_agent/test_health_r10.py"
    sources = ["GTFS", "HEALTH_REGISTRY", "HEALTH_PAGE", "PADI_2026", "OSM", "MODEL", "USER", "MODEL_DEFAULTS", "DERIVED"]
    source_metadata = {item["source_id"]: item for item in json.loads((ROOT / "datos_preparados/vnext/mobility_sources.json").read_text(encoding="utf-8"))}
    periods = list(dict.fromkeys(source_metadata[source]["reference_period"] for source in sources))
    mobility.update({
        "description": "Visita sanitaria GO01 programada a punto oficial modelado del Ambulatorio de Beasain; opción legacy stop_only explícita; comparación 2–4",
        "enabled": True, "validation_status": "tested", "handler": "plan_visit",
        "input_fields": [{"name": "request", "type": "object_or_array", "required": True, "allowed_values": []}],
        "required_data": [{"path": W1_PACKAGE_PATH, "sha256": w1_package_sha}, {"path": W1_CATALOG_PATH, "sha256": w1_catalog_sha}, {"path": W1_LABELS_PATH, "sha256": w1_labels_sha}],
        "coverage": {"territory": "Goierrialdea", "periods": periods, "entities": 3, "scope": "2026-09-29 only; health_visit modelled; stop_only explicit; origin_stop_presence_to_return_stop_arrival"},
        "source_ids": sources,
        "allowed_transformations": ["direct_pair_search", "pinned_walking_formula", "contiguous_component_sum", "bounded_comparison"],
        "preconditions": ["W1 R6 package, catalog, snapshot and schemas match published hashes.", "Health destination is modelled to an official centre point, not a verified entrance."],
        "precondition_checks": ["required_data_sha256", "handler_signature", "source_catalog", "coverage_count"],
        "validation_evidence": [{"test_file": "tests/vnext_agent/test_health_r10.py", "test_name": "test_health_provider_and_model_view", "sha256": sha(test_file.read_bytes())}, {"test_file": "tests/vnext_agent/test_r12_generated.py", "test_name": "test_generated_r12_end_to_end", "sha256": sha((ROOT / "tests/vnext_agent/test_r12_generated.py").read_bytes())}],
        "restrictions": ["Fecha validada 2026-09-29; tres orígenes y GO01 directa; no puerta física, domicilio, citas, realtime ni accesibilidad garantizada."],
        "semantic_limits": ["Paseo modelado y tiempo GTFS programado, no llegada real.", "Unknown no significa ausencia de transporte; no viable no es fallo de red.", "Los argumentos de la tool no acreditan autoría humana."],
    })
    return (json.dumps(registry, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def main() -> None:
    build_portal()
    missing = [str(path.relative_to(ROOT)) for path in FILES if not path.is_file()]
    if missing:
        raise SystemExit("Missing package files: " + ", ".join(missing))
    DIST.mkdir(parents=True, exist_ok=True)
    w1_package, w1_manifest = published_runtime()
    w1_catalog = w1_blob("datos_preparados/movilidad/operational_catalog_r6.json")
    w1_labels = w1_blob(LABELS_PATH)
    w1_conformance = w1_blob("docs/vnext/w1/CONSUMER_CONFORMANCE_R7.json")
    package_files = {destination: source.read_bytes().replace(b"\r\n", b"\n") for source, destination in FILES.items()}
    package_files[W1_PACKAGE_PATH] = w1_package
    package_files[W1_CATALOG_PATH] = w1_catalog
    package_files[W1_LABELS_PATH] = w1_labels
    package_files[W1_CONFORMANCE_PATH] = w1_conformance
    package_files["datos_preparados/vnext/capabilities.json"] = _combined_registry(sha(w1_package), sha(w1_catalog), sha(w1_labels))
    members = {}
    with zipfile.ZipFile(ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for destination, data in sorted(package_files.items()):
            if not destination.endswith(".zip"):
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
        "limit_provenance": "W3 read-only portal help reports 24 MB total agent package; compressed/uncompressed basis and MB unit unspecified; builder uses conservative 24 MiB local guard",
        "uncompressed_bytes": sum(item["bytes"] for item in members.values()),
        "w1_support_pin": SUPPORT_PIN, "w1_runtime_commit_observed": TESTED_RUNTIME_COMMIT,
        "w1_contract": "0.3.1", "w1_legacy_contract": "0.2.0", "health_destination_modelled": True,
        "health_entrance_verified": False, "w1_package_sha256": W1_R6_PACKAGE_SHA256,
        "w1_source_files": w1_manifest["files"],
        "deployment_mode": "two Python editors (main.py, tools.py) plus static workspace assets including a pinned W1 ZIP; tools.py verifies and extracts that ZIP to a temporary runtime directory",
        "root_policy": "explicit root, else GIPUZKOA360_VNEXT_ROOT if present, else module-anchored layout: flat tools.py directory or workspace root for agentes/<candidate>/tools.py; invalid root rejects without search; cwd and GIPUZKOA360_DATA_DIR do not select data",
        "tool_count": tool_count,
        "agent_name_chars": len(constants["AGENT_NAME"]),
        "instruction_chars": len(constants["SYSTEM_PROMPT"]),
        "context_file_count": len(context_paths),
        "context_bytes": sum(len(package_files[path]) for path in context_paths),
        "context_paths": context_paths,
        "freeze_paths": ["main.py", "tools.py", *context_paths],
        "validation_proof_mode": "exact test source SHA and AST function-name index embedded in tools.py; full tests remain ZIP audit-only, never context/gold for the model",
        "runtime_dependencies": ["Python 3.12 standard library", "portal-provided studio.tool", "portal-provided langchain.agents.create_agent"],
        "members": members, "canonicalization": "UTF-8 and LF; sorted names; fixed ZIP metadata",
        "mobility_binding": "PINNED_HEALTH_0.3.1_AND_EXPLICIT_STOP_ONLY_0.2.0; W1 package, source and snapshot bytes verified at build time and runtime",
    }
    MANIFEST.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"zip": ZIP.relative_to(ROOT).as_posix(), "bytes": size, "sha256": report["sha256"]}))


if __name__ == "__main__":
    main()
