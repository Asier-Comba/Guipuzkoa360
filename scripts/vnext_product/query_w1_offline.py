"""Export an arbitrary allowed W1 stop-to-stop query for offline visual review."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

PINNED_W1 = "c68eb5c55dec72a267b7435b4c364049f6eab408"
PINNED_PROVIDER_SHA256 = "4cf6b5645c63bdf2bb6c26f0d125c3669ca187d57461b8f59417de9f4acb2678"
ALLOWED = {"origin_id", "destination_id", "date", "appointment_time",
           "duration_minutes", "arrival_margin_minutes", "boarding_margin_minutes",
           "walking_profile_id", "snapshot_id"}
REQUIRED = {"origin_id", "destination_id", "date", "appointment_time",
            "duration_minutes"}
SNAPSHOT_NAME = "official-goierrialdea-go01-20260928.json"


def request_from_bytes(raw: bytes) -> dict:
    request = json.loads(raw)
    if type(request) is not dict or REQUIRED - request.keys() or request.keys() - ALLOWED:
        raise ValueError("Request must contain exactly W1 allowed fields with all required fields")
    for key in ("origin_id", "destination_id", "date", "appointment_time"):
        if type(request[key]) is not str or not request[key]:
            raise ValueError(f"{key} must be nonempty text")
    for key in ("duration_minutes", "arrival_margin_minutes", "boarding_margin_minutes"):
        if key in request and type(request[key]) is not int:
            raise ValueError(f"{key} must be an integer")
    for key in ("walking_profile_id", "snapshot_id"):
        if key in request and (type(request[key]) is not str or not request[key]):
            raise ValueError(f"{key} must be nonempty text")
    return request


def export(w1_root: Path, request: dict) -> dict:
    w1_root = w1_root.resolve()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=w1_root, text=True).strip()
    if head != PINNED_W1:
        raise ValueError(f"W1 checkout must be pinned to {PINNED_W1}; got {head}")
    provider_file = w1_root / "prototypes/ir_y_volver/provider.py"
    snapshot = w1_root / "prototypes/ir_y_volver/snapshots" / SNAPSHOT_NAME
    if not provider_file.is_file() or not snapshot.is_file():
        raise ValueError("Pinned W1 provider or snapshot is missing")
    if hashlib.sha256(provider_file.read_bytes()).hexdigest() != PINNED_PROVIDER_SHA256:
        raise ValueError("W1 provider bytes changed")
    snapshot_hash = hashlib.sha256(snapshot.read_bytes()).hexdigest()
    if snapshot_hash != "30fc9d638f3576ae0e1084ee1e0c7b0268469bffc8af1dd15fd12430019d968b":
        raise ValueError("W1 snapshot bytes changed")
    spec = importlib.util.spec_from_file_location("pinned_w1_provider_query", provider_file)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.plan_visit(request)
    if result.get("schema_version") != "0.1.0" or result.get("status") not in {
            "ok", "no_feasible_journey", "unsupported", "unknown", "error"}:
        raise ValueError("Unexpected W1 result contract")
    if result["status"] == "ok":
        if sum(result["components_s"].values()) != result["itinerary"]["total_s"]:
            raise ValueError("Provider component/total mismatch")
    elif result["itinerary"] is not None or result["components_s"] is not None:
        raise ValueError("Non-ok result includes a numeric itinerary")
    return {"schema_version": "W3-PROVIDER-QUERY-1",
            "classification": "OFFLINE_DETERMINISTIC_PROVIDER_OUTPUT",
            "provider_head": head, "snapshot_sha256": snapshot_hash,
            "output": {"id": "local_query", "title": "Consulta local importada",
                       "source_case_id": None, "changed_request_fields": None,
                       "request": request, "result": result}}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--w1-root", required=True, type=Path)
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    request = request_from_bytes(args.request.read_bytes())
    payload = export(args.w1_root, request)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    args.output.write_bytes(data)
    print(json.dumps({"output": str(args.output), "status": payload["output"]["result"]["status"],
                      "sha256": hashlib.sha256(data).hexdigest()}))


if __name__ == "__main__":
    main()
