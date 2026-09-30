"""Independent known-development retest using exact published W2 ZIP bytes."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from scripts.vnext_product.package_review import review_zip

W2_PIN = "8272988566f5bca2d65d3119732bf831d11382dc"
PACKAGE_SHA = "366cdc7d160ee6743cb125c6709f57e48f6ddfb91ead812a92eb881570233357"
CHILD = '''import json
from pathlib import Path
import tools
calls={}
for name in ("Aduna","Tolosa"):
    result=tools.execute("obtener_resumen_territorial",{"municipio":name,"periodo":None},"r10-"+name,root=Path.cwd())
    calls[name]={"evidence":result,"public_result":json.loads(tools.public_result(result))}
def substituted(handler,args):
    return handler(**{**args,"municipio":"Tolosa"})
result=tools.execute("obtener_resumen_territorial",{"municipio":"Aduna","periodo":None},"r10-substitution",root=Path.cwd(),transport=substituted)
calls["substitution"]={"evidence":result,"public_result":json.loads(tools.public_result(result))}
result=tools.execute("analizar_coincidencia",{"categoria_servicio":"primary_care","grupo_edad":"65","umbral_km":2.0,"periodo":None,"cuantil":0.75},"r10-coincidence",root=Path.cwd())
calls["coincidence"]={"evidence":result,"public_result":json.loads(tools.public_result(result))}
json.dump(calls,__import__("sys").stdout,ensure_ascii=False)
'''


def run(package: Path, manifest_path: Path, output: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    package_hash = hashlib.sha256(package.read_bytes()).hexdigest()
    if package_hash != PACKAGE_SHA or manifest["sha256"] != PACKAGE_SHA:
        raise ValueError("W2 R10 baseline package pin mismatch")
    hashes = {name: item["sha256"] for name, item in manifest["members"].items()}
    # Bundled source tests import repository-only modules; they are not runtime.
    with zipfile.ZipFile(package) as archive:
        for name in archive.namelist():
            if name.endswith(".py") and not name.startswith("tests/"):
                tree = ast.parse(archive.read(name).decode("utf-8"))
                for node in ast.walk(tree):
                    names = ([a.name.split(".")[0] for a in node.names] if isinstance(node,ast.Import)
                             else [node.module.split(".")[0]] if isinstance(node,ast.ImportFrom) and node.module else [])
                    if set(names) & {"pytest", "agentes"}:
                        raise ValueError("Repository-only test dependency reachable in runtime member")
    static = review_zip(package, hashes, ["studio", "langchain", "pytest", "agentes"])
    static["test_only_imports_not_declared_as_runtime"] = ["pytest", "agentes"]
    static["bundled_source_tests_executable_as_packaged"] = False
    with tempfile.TemporaryDirectory(prefix="g360-w3-r10-w2-") as directory:
        with zipfile.ZipFile(package) as archive:
            archive.extractall(directory)  # paths and member types validated above
        child = subprocess.run([sys.executable, "-X", "utf8", "-c", CHILD], cwd=directory,
                               text=True, encoding="utf-8", capture_output=True, check=True)
        calls = json.loads(child.stdout)
    output.mkdir(parents=True, exist_ok=True)
    raw_bytes = (json.dumps(calls, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
    evidence_file = output / "w2_retest_evidence.json"
    evidence_file.write_bytes(raw_bytes)
    aduna, tolosa, substituted, coincidence = (calls[k] for k in ("Aduna", "Tolosa", "substitution", "coincidence"))
    def rates(record, field):
        return [claim for claim in record[field]["claims"] if "per_10000" in claim["label"]]
    legitimate = all(record["evidence"]["status"] == "valid" and record["public_result"]["claims"]
                     for record in (aduna, tolosa, coincidence))
    rejected = (substituted["evidence"]["status"] == "error" and
                not substituted["evidence"]["claims"] and not substituted["public_result"]["claims"])
    lineage = (not rates(aduna, "evidence") and not rates(aduna, "public_result") and
               bool(rates(tolosa, "public_result")))
    highlighted = next(claim for claim in coincidence["public_result"]["claims"]
                       if claim["label"] == "highlighted_count")
    unit = highlighted["value"] == 7 and highlighted["unit"] == "municipios"
    public_safe = (not rates(aduna, "public_result") and
                   "raw_result_json" not in aduna["public_result"])
    checks = {"C-R3-01": rejected and legitimate, "C-R3-02": lineage,
              "C-R3-04": lineage, "C-R3-03": unit, "C-R3-09": public_safe}
    roots = {"municipality_binding": checks["C-R3-01"],
             "rate_lineage_and_model_leak": lineage and public_safe,
             "municipality_unit": unit}
    report = {"classification": "OFFLINE_TOOL_KNOWN_DEVELOPMENT_NOT_CONVERSATION",
              "w2_pin": W2_PIN, "package_sha256": package_hash,
              "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
              "static_package_review": static, "legitimate_results_valid": legitimate,
              "checks": {key: "PASS" if value else "FAIL" for key, value in checks.items()},
              "root_defects": {key: "FIXED_INDEPENDENTLY_VERIFIED" if value else "STILL_FAILING"
                               for key, value in roots.items()},
              "observed": {"aduna_public_rate_count": len(rates(aduna,"public_result")),
                           "tolosa_public_rate_count": len(rates(tolosa,"public_result")),
                           "substitution_error": substituted["public_result"]["error"],
                           "highlighted_claim": highlighted},
              "evidence_file": evidence_file.name,
              "evidence_sha256": hashlib.sha256(raw_bytes).hexdigest(),
              "llm_executed": 0, "portal_executed": 0,
              "health_contract": "NOT_IN_THIS_0.2.0_PACKAGE"}
    (output / "w2_retest_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n",encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.package,args.manifest,args.output_dir)["root_defects"]))


if __name__ == "__main__":
    main()
