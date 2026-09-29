from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ZIP = ROOT / "scripts/vnext_agent/dist/gipuzkoa360-vnext-w2.zip"
MANIFEST = ROOT / "scripts/vnext_agent/dist/gipuzkoa360-vnext-w2-manifest.json"


def build():
    subprocess.run([sys.executable, "-m", "scripts.vnext_agent.build_package"], cwd=ROOT, check=True, capture_output=True, text=True)
    return ZIP.read_bytes()


def test_double_build_manifest_context_and_offline_execution(tmp_path):
    first = build()
    second = build()
    assert first == second
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["sha256"] == hashlib.sha256(first).hexdigest()
    assert manifest["bytes"] < manifest["limit_bytes"]
    with zipfile.ZipFile(ZIP) as archive:
        assert set(archive.namelist()) == set(manifest["members"])
        tree = ast.parse(archive.read("main.py").decode("utf-8"))
        context = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "STUDIO_CONTEXT_FILES" for target in node.targets))
        assert set(context) <= set(archive.namelist())
        assert len(context) <= 20
        prompt = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "SYSTEM_PROMPT" for target in node.targets))
        assert 10 <= len(prompt) <= 8000
        archive.extractall(tmp_path)
    check = "import json,main; r=json.loads(main.analizar_coincidencia('primary_care', umbral_km=2.0, cuantil=0.75)); assert r['status']=='valid',r; raw=json.loads(r['raw_result_json']); assert raw['summary']['highlighted_count']==7"
    subprocess.run([sys.executable, "-c", check], cwd=tmp_path, check=True, capture_output=True, text=True)
