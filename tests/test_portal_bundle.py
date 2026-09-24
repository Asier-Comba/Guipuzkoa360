from __future__ import annotations

import importlib.util
import ast
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


def test_rc2_zip_extracts_and_executes_a_real_smoke_case(tmp_path):
    subprocess.run([sys.executable, "scripts/agent/build_portal_sources.py"], cwd=ROOT, check=True)
    subprocess.run([sys.executable, "scripts/agent/build_portal_package.py"], cwd=ROOT, check=True)
    archive_path = ROOT / "dist" / "gipuzkoa360-urban-challenge-rc2.zip"
    with zipfile.ZipFile(archive_path) as archive:
        assert set(archive.namelist()) == {
            "FUENTES.md",
            "docs/METODOLOGIA.md",
            "docs/PORTAL_DEPLOYMENT.md",
            "docs/RESULT_SCHEMA.md",
            "main.py",
            "requirements.txt",
            "tools.py",
            "datos_preparados/data_contract.json",
            "datos_preparados/demografia.csv",
            "datos_preparados/metadata_sources.json",
            "datos_preparados/municipios.csv",
            "datos_preparados/runtime_manifest.json",
            "datos_preparados/runtime_municipality_points.csv",
            "datos_preparados/runtime_servicios.csv",
        }
        archive.extractall(tmp_path)
    smoke = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import json, main; "
                "r=json.loads(main.analizar_coincidencia('atención primaria','65+',2,'2025-01-01',.75)); "
                "assert r['status']=='ok'; assert r['summary']['highlighted_count']==7; "
                "assert r['summary']['joined_rows']==88; print('ZIP_SMOKE_PASS')"
            ),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert smoke.returncode == 0, smoke.stderr
    assert "ZIP_SMOKE_PASS" in smoke.stdout
