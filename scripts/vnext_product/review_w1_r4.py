"""Repeat W1-owned C-R3 properties against the pinned 0.2.0 provider offline."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HEAD = "725a7b73ae0381092cd80edc41b8a25432d75fcd"
PROVIDER_SHA = "c97842617f3077c2eec1892653361b4471a18e1c64f8127b808b9968401cb834"
SNAPSHOT_SHA = "62e00c04edb96ccde0a5ce4fe81574452ddcacdb4c173b030ca49b000f5a084b"
SNAPSHOT_NAME = "official-goierrialdea-go01-r4-20260929.json"
BASE = {"origin_id": "zegama_center_stops", "destination_id": "beasain_center_stop_pair",
        "date": "2026-09-29", "appointment_time": "09:30", "duration_minutes": 30,
        "snapshot_id": "official-goierrialdea-go01-r4-20260929"}
CHILD = """import json,sys
from prototypes.ir_y_volver import plan_visit
requests=json.load(sys.stdin)
json.dump({k:plan_visit(v) for k,v in requests.items()},sys.stdout,ensure_ascii=False)
"""


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def review(root: Path) -> dict:
    root = root.resolve()
    provider = root / "prototypes/ir_y_volver/provider.py"
    snapshot = root / "prototypes/ir_y_volver/snapshots" / SNAPSHOT_NAME
    if digest(provider) != PROVIDER_SHA or digest(snapshot) != SNAPSHOT_SHA:
        raise ValueError("W1 R4 provider/snapshot bytes differ from published pin")
    requests = {"base": BASE,
                "duration90": {**BASE, "duration_minutes": 90},
                "margin": {**BASE, "arrival_margin_minutes": 15,
                           "boarding_margin_minutes": 8}}
    proc = subprocess.run([sys.executable, "-c", CHILD], cwd=root,
                          input=json.dumps(requests), text=True, capture_output=True,
                          check=True)
    results = json.loads(proc.stdout)
    base, duration, margin = (results[k] for k in ("base", "duration90", "margin"))
    legs = [base["itinerary"][part] for part in ("outbound", "return")]
    checks = {
        "C-R3-05": all(leg["pickup_type"] == 0 and leg["drop_off_type"] == 0 for leg in legs),
        "C-R3-06": (base["scenario_kind"] == "stop_only" and
                     base["normalized_request"]["walking_profile_id"] == "stop_only" and
                     base["components_s"]["destination_walk_outbound_s"] == 0),
        "C-R3-07": duration["components_s"]["appointment_s"] == 5400,
        "C-R3-08": (margin["normalized_request"]["arrival_margin_minutes"] == 15 and
                     margin["normalized_request"]["boarding_margin_minutes"] == 8 and
                     margin["itinerary"]["total_s"] != base["itinerary"]["total_s"]),
    }
    return {"classification": "OFFLINE_W1_R4_PROPERTY_REVIEW_NOT_W2_OR_PORTAL",
            "w1_head": HEAD, "provider_sha256": PROVIDER_SHA,
            "snapshot_sha256": SNAPSHOT_SHA, "w2_adapter": "NOT_RUN_INCOMPATIBLE_0.1.0",
            "llm_executed": 0, "portal_executed": 0,
            "checks": {k: "PASS" if v else "KNOWN_FAIL" for k, v in checks.items()},
            "requests": requests, "results": results,
            "observed": {"base_status": base["status"],
                         "base_total_s": base["itinerary"]["total_s"],
                         "duration90_appointment_s": duration["components_s"]["appointment_s"],
                         "margin_total_s": margin["itinerary"]["total_s"],
                         "return_slack_s": base["itinerary"]["return_slack_s"],
                         "leg_permissions": [{"pickup_type": x["pickup_type"],
                                             "drop_off_type": x["drop_off_type"]} for x in legs]},
            "limitations": ["Permissions of selected legs only; W1 raw oracle covers broader GTFS rows.",
                            "Stop-only destination; no validated healthcare walking route.",
                            "R2 W2 adapter does not consume W1 contract 0.2.0."]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--w1-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = review(args.w1_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["checks"]))


if __name__ == "__main__":
    main()
