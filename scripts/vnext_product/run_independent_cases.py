"""Run known C-R3 development properties against pinned W1/W2 offline code."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
W1_HEAD = "c68eb5c55dec72a267b7435b4c364049f6eab408"
W2_HEAD = "f4615b36d0af93966e6ca0f2044288841e6574b8"
W1_PROVIDER_SHA = "4cf6b5645c63bdf2bb6c26f0d125c3669ca187d57461b8f59417de9f4acb2678"
W2_TOOLS_SHA = "e24f2a5d2f11796dd099551b5292c10e4ca64aa9c610c4e6babcbf222cb25125"
SNAPSHOT_SHA = "30fc9d638f3576ae0e1084ee1e0c7b0268469bffc8af1dd15fd12430019d968b"
BASE = {"origin_id": "zegama_center_stops", "destination_id": "beasain_center_stop_pair",
        "date": "2026-09-29", "appointment_time": "09:30", "duration_minutes": 30,
        "snapshot_id": "official-goierrialdea-go01-20260928"}
W2_CALLS = [
    {"id": "aduna", "name": "obtener_resumen_territorial", "args": {"municipio": "Aduna", "periodo": None}},
    {"id": "substituted", "name": "obtener_resumen_territorial", "args": {"municipio": "Aduna", "periodo": None}, "substitute_municipio": "Tolosa"},
    {"id": "coincidence", "name": "analizar_coincidencia", "args": {"categoria_servicio": "primary_care", "grupo_edad": "65", "umbral_km": 2.0, "periodo": None, "cuantil": 0.75}},
]
W2_SCRIPT = """import json,sys
from pathlib import Path
from agentes.gipuzkoa360_vnext import tools
calls=json.load(sys.stdin);out={}
for item in calls:
    transport=None
    if 'substitute_municipio' in item:
        target=item['substitute_municipio']
        def transport(handler,args):
            return handler(**{**args,'municipio':target})
    out[item['id']]=tools.execute(item['name'],item['args'],'w3-r4-'+item['id'],root=Path.cwd(),transport=transport)
json.dump(out,sys.stdout,ensure_ascii=False)
"""


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pin(root: Path, expected: str, paths: dict[str, str]) -> None:
    actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    if actual != expected:
        raise ValueError(f"Checkout {root} at {actual}, expected {expected}")
    for relative, digest in paths.items():
        if sha((root / relative).read_bytes()) != digest:
            raise ValueError(f"Pinned bytes changed: {root / relative}")


def run(w1_root: Path, w2_root: Path, output_dir: Path) -> dict:
    w1_root, w2_root = w1_root.resolve(), w2_root.resolve()
    pin(w1_root, W1_HEAD, {"prototypes/ir_y_volver/provider.py": W1_PROVIDER_SHA,
                           "prototypes/ir_y_volver/snapshots/official-goierrialdea-go01-20260928.json": SNAPSHOT_SHA})
    pin(w2_root, W2_HEAD, {"agentes/gipuzkoa360_vnext/tools.py": W2_TOOLS_SHA})
    spec = importlib.util.spec_from_file_location("w1_r4_pinned_provider", w1_root / "prototypes/ir_y_volver/provider.py")
    assert spec and spec.loader
    provider = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(provider)
    w1_requests = {"base": BASE, "margin": {**BASE, "arrival_margin_minutes": 15,
                                                "boarding_margin_minutes": 8},
                   "duration90": {**BASE, "duration_minutes": 90}}
    w1 = {key: {"request": request, "result": provider.plan_visit(request)}
          for key, request in w1_requests.items()}
    child = subprocess.run([sys.executable, "-c", W2_SCRIPT], input=json.dumps(W2_CALLS),
                           text=True, capture_output=True, cwd=w2_root, check=True)
    w2 = json.loads(child.stdout)
    output_dir.mkdir(parents=True, exist_ok=True)
    evidence = {"classification": "OFFLINE_TOOL_DEVELOPMENT_NOT_HOLDOUT",
                "w1_head": W1_HEAD, "w2_head": W2_HEAD, "w1": w1, "w2": w2}
    data = (json.dumps(evidence, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    evidence_path = output_dir / "c_r3_offline_evidence.json"
    evidence_path.write_bytes(data)
    aduna = w2["aduna"]
    raw_aduna = json.loads(aduna["raw_result_json"])
    substituted = w2["substituted"]
    raw_sub = json.loads(substituted["raw_result_json"]) if substituted["raw_result_json"] else None
    coincidence = w2["coincidence"]
    raw_co = json.loads(coincidence["raw_result_json"])
    rates = [c for c in aduna["claims"] if "per_10000" in c["label"]]
    unsupported_rates = [c for c in rates if "ODE_HEALTH_CENTRES_2026" not in c["source_ids"]]
    highlighted = next(c for c in coincidence["claims"] if c["label"] == "highlighted_count")
    base, margin, duration90 = (w1[key]["result"] for key in ("base", "margin", "duration90"))
    snapshot = json.loads((w1_root / "prototypes/ir_y_volver/snapshots/official-goierrialdea-go01-20260928.json").read_text(encoding="utf-8"))
    trips = {trip["trip_id"]: trip for trip in snapshot["trips"]}
    permissions = []
    for part in ("outbound", "return"):
        leg = base["itinerary"][part]
        stops = trips[leg["trip_id"]]["stops"]
        first = next(stop for stop in stops if str(stop["stop_id"]) == leg["from_stop_id"] and stop["sequence"] == leg["from_stop_sequence"])
        last = next(stop for stop in stops if str(stop["stop_id"]) == leg["to_stop_id"] and stop["sequence"] == leg["to_stop_sequence"])
        permissions.append(first.get("pickup_type", 0) != 1 and last.get("drop_off_type", 0) != 1)
    observed = {
        "C-R3-01": (substituted["status"] != "valid" and not substituted["claims"],
                     {"requested": "Aduna", "returned": raw_sub["data"][0]["municipality_name"] if raw_sub else None,
                      "status": substituted["status"], "claims": len(substituted["claims"])}),
        "C-R3-02": (not unsupported_rates, {"raw_sources": [s["source_id"] for s in raw_aduna["sources"]],
                                          "unattributed_rate_claims": len(unsupported_rates)}),
        "C-R3-03": (highlighted["unit"] == "municipios" and raw_co["summary"]["joined_rows"] == 88,
                     {"value": highlighted["value"], "unit": highlighted["unit"],
                      "joined_rows": raw_co["summary"]["joined_rows"]}),
        "C-R3-04": (not unsupported_rates, {"rate_claims": len(rates),
                                          "unsupported_numerator_source": len(unsupported_rates)}),
        "C-R3-05": (all(permissions), {"boarding_and_alighting_allowed": permissions}),
        "C-R3-06": (base["normalized_request"]["walking_profile_id"] == "stop_only" and
                     base["scope"].startswith("stop_to_stop"),
                     {"profile": base["normalized_request"]["walking_profile_id"],
                      "scope": base["scope"], "walk_seconds": base["components_s"]["destination_walk_outbound_s"]}),
        "C-R3-07": (duration90["components_s"]["appointment_s"] == 90 * 60,
                     {"request_minutes": 90, "appointment_component_s": duration90["components_s"]["appointment_s"],
                      "source_kind": "scheduled GTFS transport; appointment supplied by request"}),
        "C-R3-08": (margin["normalized_request"]["arrival_margin_minutes"] == 15 and
                     margin["normalized_request"]["boarding_margin_minutes"] == 8 and
                     margin["itinerary"]["total_s"] != base["itinerary"]["total_s"] and
                     all(margin["normalized_request"][k] == base["normalized_request"][k]
                         for k in ("origin_id", "destination_id", "date", "appointment_time", "duration_minutes")),
                     {"previous_total_s": base["itinerary"]["total_s"],
                      "changed_total_s": margin["itinerary"]["total_s"], "arrival_margin": 15, "boarding_margin": 8}),
        "C-R3-09": (not unsupported_rates, {"unverified_rate_claims_exposed": len(unsupported_rates),
                                          "raw_result_not_agent_answer": True}),
    }
    catalog = json.loads((ROOT / "tests/vnext_redteam/c_r3_development_cases.json").read_text(encoding="utf-8"))["cases"]
    command = "python scripts/vnext_product/run_independent_cases.py --w1-root <W1 pinned> --w2-root <W2 pinned> --output-dir resultados/vnext/r4_independent"
    rows = []
    for case in catalog:
        passed, observation = observed[case["id"]]
        owner = "W2" if case["id"] in {"C-R3-01", "C-R3-02", "C-R3-03", "C-R3-04", "C-R3-09"} else "W1/W3"
        rows.append({"id": case["id"], "input": case["prompt"],
                     "expected_property": case["expected_criterion"], "observed": observation,
                     "offline_property_status": "PASS" if passed else "KNOWN_FAIL",
                     "conversation_status": "NOT_RUN", "severity_proposed": "CRITICAL" if case["id"] == "C-R3-01" and not passed else "HIGH" if not passed and case["id"] in {"C-R3-02", "C-R3-04", "C-R3-09"} else "MEDIUM",
                     "owner": owner, "evidence_file": evidence_path.name,
                     "evidence_sha256": sha(data), "reproduce": command})
    report = {"classification": "KNOWN_DEVELOPMENT_OFFLINE_TOOL_ONLY", "llm_executed": 0,
              "portal_executed": 0, "w1_head": W1_HEAD, "w2_head": W2_HEAD,
              "cases": rows, "counts": {"pass_offline": sum(x["offline_property_status"] == "PASS" for x in rows),
                                      "known_fail": sum(x["offline_property_status"] == "KNOWN_FAIL" for x in rows),
                                      "conversation_not_run": len(rows)}}
    (output_dir / "c_r3_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--w1-root", required=True, type=Path)
    parser.add_argument("--w2-root", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    report = run(args.w1_root, args.w2_root, args.output_dir)
    print(json.dumps(report["counts"], ensure_ascii=False))


if __name__ == "__main__":
    main()
