from __future__ import annotations

import importlib.util
import ast
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PORTAL = ROOT / "agentes" / "gipuzkoa360" / "portal"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_generated_portal_bundle_is_self_contained(monkeypatch):
    subprocess.run([sys.executable, "scripts/agent/build_portal_sources.py"], cwd=ROOT, check=True)
    monkeypatch.syspath_prepend(str(PORTAL))
    bundled_tools = _load("portal_tools_test", PORTAL / "tools.py")
    assert "@tool" not in (PORTAL / "tools.py").read_text(encoding="utf-8")
    assert "TOOLS =" not in (PORTAL / "tools.py").read_text(encoding="utf-8")
    assert "importlib" not in (PORTAL / "tools.py").read_text(encoding="utf-8")
    assert "zipfile" not in (PORTAL / "tools.py").read_text(encoding="utf-8")
    assert "tempfile" not in (PORTAL / "tools.py").read_text(encoding="utf-8")
    monkeypatch.setenv("GIPUZKOA360_DATA_DIR", str(ROOT / "datos_preparados"))
    result = json.loads(bundled_tools.obtener_resumen_territorial("Aduna", "2025-01-01"))
    assert result["status"] == "ok"
    assert result["data"][0]["municipality_code"] == "20002"


def test_portal_main_build_agent_is_synchronous_and_has_no_local_path():
    source = (PORTAL / "main.py").read_text(encoding="utf-8")
    assert "async def build_agent" not in source
    assert "def build_agent(model):" in source
    assert "import tools as core" in source
    assert "zipfile" not in source
    assert "importlib" not in source
    assert "C:\\\\Users" not in source
    assert "STUDIO_INTERNET_ENABLED = False" in source


def test_portal_main_physically_declares_seven_unique_tools():
    source = (PORTAL / "main.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    decorated = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and any(isinstance(item, ast.Name) and item.id == "tool" for item in node.decorator_list)
    ]
    expected = {
        "obtener_resumen_territorial",
        "comparar_municipios",
        "analizar_envejecimiento",
        "analizar_acceso_servicios",
        "analizar_coincidencia",
        "simular_escenario",
        "consultar_fuente",
    }
    assert {node.name for node in decorated} == expected
    assert len(decorated) == len(expected) == 7


def test_release_package_manifest_and_context_are_coherent():
    subprocess.run([sys.executable, "scripts/agent/build_portal_package.py"], cwd=ROOT, check=True)
    package_manifest_path = ROOT / "dist" / "gipuzkoa360-urban-challenge-rc2-manifest.json"
    package_manifest = json.loads(package_manifest_path.read_text(encoding="utf-8"))
    package_path = ROOT / package_manifest["path"]
    assert package_path.stat().st_size == package_manifest["bytes"]
    assert hashlib.sha256(package_path.read_bytes()).hexdigest() == package_manifest["sha256"]

    with zipfile.ZipFile(package_path) as archive:
        packaged_files = sorted(archive.namelist())
        assert packaged_files == package_manifest["files"]
        assert len(packaged_files) == len(set(packaged_files))

    source = (ROOT / "agentes" / "gipuzkoa360" / "main.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    context_assignment = next(
        node for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "STUDIO_CONTEXT_FILES" for target in node.targets)
    )
    context_files = ast.literal_eval(context_assignment.value)
    assert set(context_files) <= set(packaged_files)
    assert all((ROOT / path).is_file() for path in context_files)

    runtime_manifest = json.loads(
        (ROOT / "datos_preparados" / "runtime_manifest.json").read_text(encoding="utf-8")
    )
    runtime_files = {item["path"] for item in runtime_manifest["files"]}
    packaged_runtime_data = {
        path for path in packaged_files
        if path.startswith("datos_preparados/") and path != "datos_preparados/runtime_manifest.json"
    }
    assert packaged_runtime_data <= runtime_files
    # La geometría es deliberadamente de Work 3 y no forma parte del runtime conversacional.
    assert "datos_preparados/runtime_municipios.geojson" in runtime_files
    assert "datos_preparados/runtime_municipios.geojson" not in packaged_files
