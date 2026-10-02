"""R22 source-attribution-only delta from the immutable tested R21 package."""
import ast
import io
import json
import subprocess
import zipfile
from scripts.vnext_agent.build_r21 import ROOT, PUBLIC_TOOLS, sha

BASE = "b0096e9aeda533ed0a43f56bf98975becf4022d8"
BASE_ZIP = "scripts/vnext_agent/dist/r21/gipuzkoa360-r21-final-agent.zip"
BASE_MANIFEST = "scripts/vnext_agent/dist/r21/gipuzkoa360-r21-final-agent-manifest.json"
BASE_HASH = "a714bac1fa91caebe3e8ef6fb65259c4f11447120479ecf51dce4813cfba5dc2"
BASE_MANIFEST_HASH = "6d425d3e194e6fea016ae4a4b685ae2e50af978897278539d17b7bb03fad31b9"
OUT = ROOT / "scripts/vnext_agent/dist/r22"
ZIP = OUT / "gipuzkoa360-r22-final-agent.zip"
MANIFEST = OUT / "gipuzkoa360-r22-final-agent-manifest.json"
PORTAL = ROOT / "agentes/gipuzkoa360_vnext/portal_r22"
DELTA = ROOT / "scripts/vnext_agent/r22_attribution.py"
ATTRIBUTION_PRINCIPLE = "Cuando cites procedencia temporal, usa cada source_attributions como unidad indivisible: fuente, función, fecha e institución. Nunca reasignes una fecha a otra fuente ni reconstruyas el emparejamiento desde el campo period."
OLD_COMMUNICATION = "Responde primero a lo preguntado, breve y humano: cifras importantes con unidades, fechas y fuentes legibles."
COMMUNICATION = "Responde primero y solo a lo preguntado, breve y humano, con cifras y unidades. No enumeres fechas exactas de fuentes salvo que el usuario las pida, sean necesarias para interpretar una comparación o exista una discrepancia temporal material que deba advertirse. Conserva la trazabilidad disponible; puedes explicar brevemente qué tipos de fuentes combina el cálculo."

def blob(path):
    return subprocess.check_output(["git", "show", f"{BASE}:{path}"], cwd=ROOT)

def generated_main(data):
    text = data.decode("utf-8")
    node = next(n for n in ast.parse(text).body if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", None) == "SYSTEM_PROMPT")
    prompt = ast.literal_eval(node.value)
    assert prompt.count(OLD_COMMUNICATION) == 1
    prompt = prompt.replace(OLD_COMMUNICATION, COMMUNICATION).replace("\n\nTOOL SELECTION", "\n" + ATTRIBUTION_PRINCIPLE + "\n\nTOOL SELECTION", 1)
    lines = text.splitlines(keepends=True)
    lines[node.lineno - 1:node.end_lineno] = ["SYSTEM_PROMPT = " + repr(prompt) + "\n"]
    result = "".join(lines).encode("utf-8")
    ast.parse(result)
    return result

def build():
    baseline, metadata = blob(BASE_ZIP), blob(BASE_MANIFEST)
    assert sha(baseline) == BASE_HASH and sha(metadata) == BASE_MANIFEST_HASH
    prior = json.loads(metadata)
    OUT.mkdir(parents=True, exist_ok=True); PORTAL.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(baseline)) as old, zipfile.ZipFile(ZIP, "w") as new:
        overrides = {"main.py": generated_main(old.read("main.py")),
                     "tools.py": old.read("tools.py") + b"\n\n" + DELTA.read_bytes().replace(b"\r\n", b"\n")}
        members, changed = {}, []
        for info in old.infolist():
            original = old.read(info.filename); data = overrides.get(info.filename, original)
            new.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            members[info.filename] = {"bytes": len(data), "sha256": sha(data)}
            if data != original: changed.append(info.filename)
    assert changed == ["main.py", "tools.py"] and len(members) == 25
    for name, data in overrides.items():
        ast.parse(data); (PORTAL / name).write_bytes(data)
    report = {"package": "GIPUZKOA360_R22_final_agent", "base_r21_tested_runtime": BASE,
              "base_r21_zip_sha256": BASE_HASH, "base_r21_manifest_sha256": BASE_MANIFEST_HASH,
              "sha256": sha(ZIP.read_bytes()), "bytes": ZIP.stat().st_size, "members": members,
              "members_count": len(members), "changed_members": changed,
              "context_paths": prior["context_paths"], "context_assets_changed": [],
              "uncompressed_bytes": sum(x["bytes"] for x in members.values()),
              "limit_bytes": prior["limit_bytes"], "public_tools": PUBLIC_TOOLS,
              "w1_runtime_changed": False, "v4_changed": False,
              "source_delta_sha256": sha(DELTA.read_bytes().replace(b"\r\n", b"\n")),
              "runtime_delta": "Atomic public source attribution and communication principle only; complete R21 tools prefix and 23 other members unchanged",
              "portal_real_agent": "NOT_RUN"}
    assert report["bytes"] < report["limit_bytes"]
    MANIFEST.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    return {"zip_sha256": report["sha256"], "manifest_sha256": sha(MANIFEST.read_bytes()), "bytes": report["bytes"]}

if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
