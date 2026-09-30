"""Build a standalone W1 0.3.1 health view, preserving the prior viewer."""
import hashlib
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/"resultados/vnext"

def main():
    evidence=json.loads((BASE/"r10/health_evidence.json").read_text(encoding="utf-8"))
    if evidence["classification"]!="OFFLINE_PINNED_W1_HEALTH_0.3.1_NOT_AGENT":raise ValueError("Unclassified result")
    style=re.search(r"<style>(.*?)</style>",(BASE/"template.html").read_text(encoding="utf-8"),re.S).group(1)
    template=(BASE/"health_template.html").read_text(encoding="utf-8")
    output=template.replace("__STYLE__",style).replace("__EVIDENCE__",json.dumps(evidence,ensure_ascii=False,separators=(",",":")).replace("<","\\u003c")).replace("__CONTRACT__",(ROOT/"scripts/vnext_product/health_contract.js").read_text(encoding="utf-8"))
    path=BASE/"health.html";path.write_bytes(output.encode("utf-8"))
    payload={"schema_version":"W3-HEALTH-QUERY-1","provider_pin":evidence["provider_pin"],"package_sha256":evidence["package_sha256"],"output":evidence["outputs"]["time"]}
    (BASE/"r10/example_health_query.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"path":str(path),"sha256":hashlib.sha256(path.read_bytes()).hexdigest()}))

if __name__=="__main__":main()
