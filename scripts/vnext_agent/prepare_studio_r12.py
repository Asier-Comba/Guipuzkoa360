"""Export exact deployment closure and EXPECTED (not Studio-served) tool schemas."""
from __future__ import annotations

import ast
import importlib.metadata
import importlib.util
import inspect
import io
import json
import platform
import types
import typing
import zipfile

from agentes.gipuzkoa360_vnext import main as agent
from scripts.agent.build_portal_sources import _module_nodes
from scripts.vnext_agent.build_package import MANIFEST, ROOT, V4, ZIP, _candidate_nodes, sha

OUT = ROOT / "docs/vnext/w2/STUDIO_DEPLOYMENT_R12.json"


def schema(annotation):
    origin = typing.get_origin(annotation)
    args = typing.get_args(annotation)
    if origin is typing.NotRequired:
        return schema(args[0])
    if origin in (typing.Union, types.UnionType):
        return {"anyOf": [schema(item) for item in args]}
    if origin is list:
        return {"type": "array", "items": schema(args[0])}
    if typing.is_typeddict(annotation):
        hints = typing.get_type_hints(annotation, include_extras=True)
        return {"type": "object", "properties": {key: schema(value) for key, value in hints.items()},
                "required": [key for key, value in hints.items() if typing.get_origin(value) is not typing.NotRequired],
                "additionalProperties": False}
    return {"type": {str: "string", int: "integer", float: "number", bool: "boolean", type(None): "null"}[annotation]}


def names(nodes):
    result = set()
    for node in nodes:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            result.add(node.name)
        elif isinstance(node, ast.Assign):
            result.update(target.id for target in node.targets if isinstance(target, ast.Name))
    return result


def main():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert sha(ZIP.read_bytes()) == manifest["sha256"]
    with zipfile.ZipFile(ZIP) as archive:
        for path, expected in manifest["members"].items():
            content = archive.read(path)
            assert len(content) == expected["bytes"] and sha(content) == expected["sha256"]
        with zipfile.ZipFile(io.BytesIO(archive.read("datos_preparados/vnext/w1_r6_runtime.zip"))) as runtime:
            runtime_expanded = sum(item.file_size for item in runtime.infolist())
    core_nodes = [node for filename in ("schemas.py", "metrics.py", "data_access.py", "tools.py") for node in _module_nodes(V4 / filename)]
    collisions = sorted(names(core_nodes) & names(_candidate_nodes()))
    assert collisions == ["consultar_fuente"], collisions
    tool_schemas = {}
    for name in ("obtener_resumen_territorial", "comparar_municipios", "analizar_envejecimiento", "analizar_acceso_servicios", "analizar_coincidencia", "simular_escenario", "consultar_fuente", "consultar_capacidades", "plan_visit"):
        function = getattr(agent, name)
        signature = inspect.signature(function)
        hints = typing.get_type_hints(function, include_extras=True)
        tool_schemas[name] = {"type": "object", "properties": {key: schema(hints[key]) for key in signature.parameters},
                              "required": [key for key, parameter in signature.parameters.items() if parameter.default is inspect.Parameter.empty],
                              "additionalProperties": False}
    # Runtime bounds remain authoritative; record them explicitly in the expected schema.
    request_variants = tool_schemas["plan_visit"]["properties"]["request"]["anyOf"]
    next(item for item in request_variants if item["type"] == "array").update(minItems=2, maxItems=4)
    visit = next(item for item in request_variants if item["type"] == "object")
    assert visit["required"] == ["origin_id", "destination_id", "date", "appointment_time", "duration_minutes"]
    versions = {}
    for name in ("studio", "langchain", "langchain-core"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = "NOT_INSTALLED_LOCALLY"
    payload = {
        "status": "EXPECTED_SCHEMA_ONLY_STUDIO_SERVED_SCHEMA_NOT_RUN",
        "package_sha256": manifest["sha256"], "compressed_bytes": manifest["bytes"],
        "extracted_workspace_bytes": manifest["uncompressed_bytes"], "nested_w1_expanded_bytes": runtime_expanded,
        "runtime_static_closure": manifest["members"], "context_paths": manifest["context_paths"],
        "runtime_dependencies": manifest["runtime_dependencies"], "local_python": platform.python_version(),
        "local_dependency_versions": versions, "typing_check": "get_type_hints(include_extras=True) resolves TypedDict and NotRequired on the installed Python",
        "required_visit_fields": visit["required"], "expected_tool_schemas": tool_schemas,
        "generated_global_collisions": collisions,
        "collision_resolution": "consultar_fuente is intentionally replaced after saving the unchanged core handler and _safe in territorial SimpleNamespace; all calculations use a root-bound repository",
        "root_policy": manifest["root_policy"], "bootstrap": "verify pinned W1 ZIP SHA, safely extract into writable tempfile, import only that runtime, embed W2 adapters in tools.py; cached runtime remains bound to the same root",
        "load_order": ["verify immutable package+manifest hashes", "explicitly extract locally; do not assume portal ZIP extraction", "verify common v4 assets are byte-identical before reuse", "mount every listed workspace member under its exact relative path beside generated tools.py", "load tools.py then main.py in the two editors", "set name/instructions/configuration from main.py; no new model", "W3 captures actual served schema, import closure and real conversation trace before acceptance"],
        "portal_asset_mount_verified": False, "studio_schema_verified": False,
        "llm_executed": 0, "portal_writes_by_w2": 0,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"output": OUT.relative_to(ROOT).as_posix(), "sha256": sha(OUT.read_bytes()), "collisions": collisions, "dependencies": versions}))


if __name__ == "__main__":
    main()
