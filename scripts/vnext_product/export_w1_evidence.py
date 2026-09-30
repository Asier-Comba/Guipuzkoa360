"""Export pinned offline provider outputs for product review, never LLM goldens."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PINNED_W1 = "c68eb5c55dec72a267b7435b4c364049f6eab408"
TARGET = ROOT / "resultados/vnext/provider_evidence.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--w1-root", type=Path, required=True)
    args = parser.parse_args()
    w1 = args.w1_root.resolve()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=w1, text=True).strip()
    if head != PINNED_W1:
        raise SystemExit(f"W1 checkout must be pinned to {PINNED_W1}, got {head}")
    provider_path = w1 / "prototypes/ir_y_volver/provider.py"
    spec = importlib.util.spec_from_file_location("pinned_w1_provider", provider_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    real = json.loads((w1 / "docs/vnext/w1/REAL_CASES.json").read_text(encoding="utf-8"))
    by_id = {case["case_id"]: case for case in real["cases"]}
    snapshot = w1 / "prototypes/ir_y_volver/snapshots/official-goierrialdea-go01-20260928.json"
    snapshot_hash = hashlib.sha256(snapshot.read_bytes()).hexdigest()
    if snapshot_hash != real["snapshot_sha256"]:
        raise SystemExit("W1 snapshot hash does not match REAL_CASES")

    variants = [
        ("zegama_0930", "Zegama · cita 09:30 · 30 min", "W1-RC-01", {}),
        ("zegama_1000", "Zegama · cita 10:00 · 30 min", "W1-RC-02", {}),
        ("segura_1900_30", "Segura · cita 19:00 · 30 min", "W1-RC-07", {}),
        ("segura_1900_180", "Segura · cita 19:00 · 180 min", "W1-RC-07", {"duration_minutes": 180}),
        ("zegama_unvalidated", "Zegama · fecha aún no validada", "W1-RC-01", {"date": "2026-10-04"}),
    ]
    outputs = []
    for key, title, source_case, changes in variants:
        request = {**by_id[source_case]["request"], **changes}
        result = module.plan_visit(request)
        if result.get("schema_version") != "0.1.0":
            raise SystemExit(f"Unexpected result schema for {key}")
        if result["status"] == "ok":
            if sum(result["components_s"].values()) != result["itinerary"]["total_s"]:
                raise SystemExit(f"Component/total mismatch for {key}")
        elif result["itinerary"] is not None or result["components_s"] is not None:
            raise SystemExit(f"Non-ok result leaked an itinerary or components for {key}")
        outputs.append({"id": key, "title": title, "source_case_id": source_case,
                        "changed_request_fields": changes, "request": request, "result": result})
    payload = {
        "schema_version": "W3-PROVIDER-EVIDENCE-1",
        "classification": "OFFLINE_DETERMINISTIC_PROVIDER_OUTPUT",
        "disclaimer": "Resultados guardados de un proveedor determinista de W1; no son respuestas del agente W2 ni consultas live.",
        "provider_head": head, "provider_contract_version": "0.1.0",
        "snapshot_sha256": snapshot_hash,
        "outputs": outputs,
        "appointment_comparison": module.compare_visits([
            by_id["W1-RC-01"]["request"], by_id["W1-RC-02"]["request"]]),
    }
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    TARGET.write_bytes(data)
    print(json.dumps({"path": str(TARGET), "outputs": len(outputs),
                      "statuses": [item["result"]["status"] for item in outputs],
                      "sha256": hashlib.sha256(data).hexdigest()}))


if __name__ == "__main__":
    main()
