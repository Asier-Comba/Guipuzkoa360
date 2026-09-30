"""Build a standalone W1 0.3.1 health view, preserving the prior viewer."""
import argparse
import hashlib
import html
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/"resultados/vnext"

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--evidence",type=Path,default=BASE/"r13/health_evidence.json");parser.add_argument("--output",type=Path,default=BASE/"health.html")
    args=parser.parse_args()
    evidence=json.loads(args.evidence.read_text(encoding="utf-8"))
    if evidence["classification"] not in {"OFFLINE_PINNED_W1_HEALTH_0.3.1_NOT_AGENT","OFFLINE_W2_EXACT_PACKAGE_R12_NOT_AGENT","OFFLINE_W2_EXACT_PACKAGE_R13_NOT_AGENT"}:raise ValueError("Unclassified result")
    style=re.search(r"<style>(.*?)</style>",(BASE/"template.html").read_text(encoding="utf-8"),re.S).group(1)
    template=(BASE/"health_template.html").read_text(encoding="utf-8")
    portal_note='Studio R13: la pregunta sanitaria falló por argumentos incompatibles; lote detenido en 4/12 mensajes. Estas cifras proceden del cálculo offline aceptado de patch3, no de esa respuesta del agente.' if evidence.get('portal_health_status')=='BLOCKED_REQUEST_BINDING_R13_M04' else ''
    output=template.replace("__STYLE__",style).replace("__PORTAL_NOTE__",html.escape(portal_note)).replace("__EVIDENCE__",json.dumps(evidence,ensure_ascii=False,separators=(",",":")).replace("<","\\u003c")).replace("__CONTRACT__",(ROOT/"scripts/vnext_product/health_contract.js").read_text(encoding="utf-8"))
    path=args.output;path.write_bytes(output.encode("utf-8"))
    payload={"schema_version":"W3-HEALTH-QUERY-1","provider_pin":evidence["provider_pin"],"package_sha256":evidence["package_sha256"],"output":evidence["outputs"]["time"]}
    (args.evidence.parent/"example_health_query.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps({"path":str(path),"sha256":hashlib.sha256(path.read_bytes()).hexdigest()}))

if __name__=="__main__":main()
