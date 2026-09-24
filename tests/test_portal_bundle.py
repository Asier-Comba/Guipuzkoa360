from __future__ import annotations

import importlib.util
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
    assert len(bundled_tools.TOOLS) == 7
    monkeypatch.setenv("GIPUZKOA360_DATA_DIR", str(ROOT / "datos_preparados"))
    result = json.loads(bundled_tools.obtener_resumen_territorial("Aduna", "2025-01-01"))
    assert result["status"] == "ok"
    assert result["data"][0]["municipality_code"] == "20002"


def test_portal_main_build_agent_is_synchronous_and_has_no_local_path():
    source = (PORTAL / "main.py").read_text(encoding="utf-8")
    assert "async def build_agent" not in source
    assert "def build_agent(model):" in source
    assert "from tools import TOOLS" in source
    assert "C:\\\\Users" not in source
    assert "STUDIO_INTERNET_ENABLED = False" in source
