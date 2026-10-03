"""Reuse all R21 raw/oracle/malformed gates; only additive attribution is new."""
import argparse
import copy
import json
from pathlib import Path
from scripts.vnext_agent import verify_r21 as prior, build_r22 as build

def run(output):
    original = prior.run_worker
    observations = []
    def worker(root, cases):
        result = original(root, cases)
        if Path(root).name == "r21":
            # R21 verifier names the candidate root r21. Retain the exact new
            # public view while removing only the additive field from parity.
            observations.append((copy.deepcopy(result), {r["id"] for r in cases if r.get("route") != "internal"}))
            for record in result["records"].values():
                record["claims"] = [{k:v for k,v in c.items() if k != "source_attributions"} for c in record.get("claims", [])]
        return result
    prior.ZIP, prior.MANIFEST, prior.run_worker = build.ZIP, build.MANIFEST, worker
    result = prior.run(output)
    findings = list(result["findings"]); tested = 0
    for data, public_ids in observations:
        for key, record in data["records"].items():
            if record.get("status") != "valid" or key not in public_ids:
                continue
            for claim in record.get("claims", []):
                attrs = claim.get("source_attributions")
                if type(attrs) is not list or [r["source_id"] for r in attrs] != sorted(claim["source_ids"]):
                    findings.append({"id":key,"issues":["atomic_attribution_missing"]})
                tested += 1
    report = json.loads(output.read_bytes())
    report.update(generation="R22", base_r21=build.BASE, attribution_claims=tested,
                  findings=findings, status="FAIL" if findings else "PASS",
                  parity_policy="All raw/effective requests/claims unchanged; remove ONLY additive source_attributions before claim equality")
    output.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2)+"\n", encoding="utf-8", newline="\n")
    return {k:v for k,v in report.items() if k != "records"}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--output", type=Path, default=build.ROOT/"outputs/r22/offline-audit.json")
    result = run(parser.parse_args().output); print(json.dumps(result, sort_keys=True)); raise SystemExit(result["status"] != "PASS")
