from __future__ import annotations

import importlib.util
import ast
import json
import subprocess
import sys
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
