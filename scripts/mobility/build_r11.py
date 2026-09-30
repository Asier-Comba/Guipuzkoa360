"""Build R11 consumer-gate evidence without changing frozen runtime R6."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from prototypes.ir_y_volver import provider_r6


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/vnext/w1"
OUT = DOC / "integration_r11"
R10 = DOC / "integration_r10/W1_HANDSHAKE_R10.json"
RUNTIME_PIN = "cb061a97e78d6b5c967104fef6b935132fdc450f"
PACKAGE_SHA = "c66d44af702eb3410fcea05ae8711f537214f675e83a7fda38c39c3b39a1b910"
BASE = {
    "origin_id": "zegama_center_stops",
    "destination_id": "beasain_official_centre_anchor",
    "date": "2026-09-29",
    "appointment_time": "09:45",
    "duration_minutes": 20,
}


def encoded(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def dump(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded(value))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(path: Path, role: str) -> dict:
    raw = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix(), "role": role, "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(), "hash_basis": "exact_bytes"}


def requirement(identifier: str, applicability: str, source_path: str, fact: str,
                projection: list[str], omission: str, severity: str,
                *, expected_value: object | None = None, semantic_match_any: list[str] | None = None) -> dict:
    row = {"requirement_id": identifier, "applicability": applicability, "source_path": source_path,
           "semantic_fact": fact, "allowed_projection": projection, "forbidden_omission": omission,
           "severity": severity}
    if expected_value is not None:
        row["expected_value"] = expected_value
    if semantic_match_any:
        row["semantic_match_any"] = semantic_match_any
    return row


def build_requirements() -> dict:
    raw = provider_r6.plan_visit(BASE)
    old = json.loads((ROOT / "prototypes/ir_y_volver/snapshots/official-goierrialdea-go01-r4-20260929.json").read_text(encoding="utf-8"))
    labels = {key: old["stops"][key]["name"] for key in ("8305", "7219", "7218", "8309")}
    rows = [
        requirement("MV-STATUS", "all", "/status", "producer status", ["status", "outcomes.status"], "status absent", "critical", expected_value=raw["status"]),
        requirement("MV-EFFECTIVE", "all", "/normalized_request", "effective request and defaults", ["effective_request", "normalized_request"], "effective request absent", "critical", expected_value=raw["normalized_request"]),
        requirement("MV-OUT-TRIP", "ok", "/itinerary/outbound/trip_id", "outbound trip identity", ["outbound.trip_id", "claims.value"], "trip identity absent", "critical", expected_value=raw["itinerary"]["outbound"]["trip_id"]),
        requirement("MV-OUT-ROUTE", "ok", "/itinerary/outbound/route_id", "outbound route identity and public GO01 label", ["outbound.route_id", "route_id", "route_label"], "route identity absent", "critical", expected_value=raw["itinerary"]["outbound"]["route_id"]),
        requirement("MV-OUT-ROUTE-LABEL", "ok", "/sources/0/transformation", "public route label GO01", ["route_label", "method", "sources.transformation"], "route label absent", "high", expected_value="GO01"),
        requirement("MV-OUT-FROM-ID", "ok", "/itinerary/outbound/from_stop_id", "outbound boarding stop id", ["outbound.from_stop_id", "claims.value"], "boarding stop id absent", "critical", expected_value=raw["itinerary"]["outbound"]["from_stop_id"]),
        requirement("MV-OUT-FROM-LABEL", "ok", "snapshot:/stops/8305/name", "outbound boarding stop label", ["outbound.from_stop_label", "stop_label", "claims.entity_label"], "boarding stop label absent", "high", expected_value=labels["8305"]),
        requirement("MV-OUT-TO-ID", "ok", "/itinerary/outbound/to_stop_id", "outbound arrival stop id", ["outbound.to_stop_id", "claims.value"], "arrival stop id absent", "critical", expected_value=raw["itinerary"]["outbound"]["to_stop_id"]),
        requirement("MV-OUT-TO-LABEL", "ok", "snapshot:/stops/7219/name", "outbound arrival stop label", ["outbound.to_stop_label", "stop_label", "claims.entity_label"], "arrival stop label absent", "high", expected_value=labels["7219"]),
        requirement("MV-OUT-DEP", "ok", "/itinerary/outbound/departure_time", "scheduled outbound departure", ["outbound.departure_time", "claims.value"], "departure absent", "critical", expected_value=raw["itinerary"]["outbound"]["departure_time"]),
        requirement("MV-OUT-ARR", "ok", "/itinerary/outbound/arrival_time", "scheduled outbound arrival", ["outbound.arrival_time", "claims.value"], "arrival absent", "critical", expected_value=raw["itinerary"]["outbound"]["arrival_time"]),
        requirement("MV-WALK-OUT-M", "ok", "/walking/outbound/total_metres", "outbound walking metres", ["walking.outbound.total_metres", "claims.value"], "walking distance absent", "high", expected_value=raw["walking"]["outbound"]["total_metres"]),
        requirement("MV-WALK-OUT-S", "ok", "/walking/outbound/seconds", "outbound walking seconds", ["walking.outbound.seconds", "claims.value"], "walking time absent", "high", expected_value=raw["walking"]["outbound"]["seconds"]),
        requirement("MV-WALK-PROFILE", "ok", "/normalized_request/walking_profile_id", "walking profile/model", ["walking_profile_id", "method", "assumptions"], "walking model absent", "high", expected_value=raw["normalized_request"]["walking_profile_id"]),
        requirement("MV-APPT-TIME", "ok", "/normalized_request/appointment_time", "appointment time", ["appointment_time", "claims.value"], "appointment time absent", "high", expected_value=raw["normalized_request"]["appointment_time"]),
        requirement("MV-APPT-DURATION", "ok", "/components_s/appointment_s", "appointment duration seconds", ["appointment_s", "claims.value"], "appointment duration absent", "high", expected_value=raw["components_s"]["appointment_s"]),
        requirement("MV-PRE-WAIT", "ok", "/components_s/pre_appointment_wait_s", "pre-appointment wait seconds", ["pre_appointment_wait_s", "claims.value"], "pre-wait absent", "high", expected_value=raw["components_s"]["pre_appointment_wait_s"]),
        requirement("MV-RET-TRIP", "ok", "/itinerary/return/trip_id", "return trip identity", ["return.trip_id", "claims.value"], "return trip absent", "critical", expected_value=raw["itinerary"]["return"]["trip_id"]),
        requirement("MV-RET-FROM-ID", "ok", "/itinerary/return/from_stop_id", "return boarding stop id", ["return.from_stop_id", "claims.value"], "return boarding id absent", "critical", expected_value=raw["itinerary"]["return"]["from_stop_id"]),
        requirement("MV-RET-FROM-LABEL", "ok", "snapshot:/stops/7218/name", "return boarding stop label", ["return.from_stop_label", "stop_label", "claims.entity_label"], "return boarding label absent", "high", expected_value=labels["7218"]),
        requirement("MV-RET-TO-ID", "ok", "/itinerary/return/to_stop_id", "return arrival stop id", ["return.to_stop_id", "claims.value"], "return arrival id absent", "critical", expected_value=raw["itinerary"]["return"]["to_stop_id"]),
        requirement("MV-RET-TO-LABEL", "ok", "snapshot:/stops/8309/name", "return arrival stop label", ["return.to_stop_label", "stop_label", "claims.entity_label"], "return arrival label absent", "high", expected_value=labels["8309"]),
        requirement("MV-RET-DEP", "ok", "/itinerary/return/departure_time", "scheduled return departure", ["return.departure_time", "claims.value"], "return departure absent", "critical", expected_value=raw["itinerary"]["return"]["departure_time"]),
        requirement("MV-RET-ARR", "ok", "/itinerary/return/arrival_time", "scheduled return arrival", ["return.arrival_time", "claims.value"], "return arrival absent", "critical", expected_value=raw["itinerary"]["return"]["arrival_time"]),
        requirement("MV-RET-WALK-S", "ok", "/components_s/destination_walk_return_s", "return walk seconds", ["destination_walk_return_s", "claims.value"], "return walk absent", "high", expected_value=raw["components_s"]["destination_walk_return_s"]),
        requirement("MV-RET-WAIT", "ok", "/components_s/return_wait_s", "return wait seconds", ["return_wait_s", "claims.value"], "return wait absent", "high", expected_value=raw["components_s"]["return_wait_s"]),
        requirement("MV-RET-SLACK", "ok", "/itinerary/return_slack_s", "return slack seconds", ["return_slack_s", "claims.value"], "return slack absent", "high", expected_value=raw["itinerary"]["return_slack_s"]),
        requirement("MV-TOTAL", "ok", "/itinerary/total_s", "whole journey total seconds", ["total_s", "claims.value"], "total absent", "critical", expected_value=raw["itinerary"]["total_s"]),
        requirement("MV-CENTRE-ID", "ok", "/health_destination/centre_id", "health centre identity", ["centre_id", "claims.entity_id"], "centre id absent", "critical", expected_value=raw["health_destination"]["centre_id"]),
        requirement("MV-CENTRE-LABEL", "ok", "/health_destination/name", "health centre label", ["health_destination.name", "centre_label", "claims.entity_label"], "centre label absent", "critical", expected_value=raw["health_destination"]["name"]),
        requirement("MV-MODELLED-ACCESS", "ok", "/health_destination/modelled_access", "access is modelled", ["health_destination.modelled_access", "limitations", "method"], "modelled nature absent", "critical", expected_value=True),
        requirement("MV-ENTRANCE", "ok", "/health_destination/entrance_verified", "physical entrance is not verified", ["health_destination.entrance_verified", "limitations"], "entrance caveat absent", "critical", expected_value=False),
        requirement("MV-SCOPE", "ok", "/scope", "stop-presence to return-stop-arrival scope", ["scope", "limitations"], "scope absent", "critical", expected_value=raw["scope"]),
        requirement("MV-SOURCES", "ok", "/sources", "readable sources and source identities", ["sources", "source_ids", "source_refs"], "source identity absent", "critical", expected_value=[row["source_id"] for row in raw["sources"]]),
        requirement("MV-ASSUMPTIONS", "all", "/assumptions", "producer assumptions", ["assumptions"], "assumptions absent", "high", expected_value=raw["assumptions"]),
        requirement("MV-LIMITATIONS", "all", "/limitations", "producer limitations", ["limitations"], "limitations absent", "critical", expected_value=raw["limitations"]),
        requirement("MV-PROVENANCE", "ok", "/parameter_provenance", "caller-supplied versus default-applied provenance", ["parameter_provenance", "effective_request.defaults_applied", "normalized_input.arguments"], "caller provenance absent", "critical", expected_value=raw["parameter_provenance"]),
        requirement("MV-TIMEPOINT", "ok", "/itinerary/outbound/from_timepoint", "timepoint zero is approximate/interpolated scheduled time", ["timepoint", "limitations", "method"], "timepoint approximation absent", "critical", semantic_match_any=["aproxim", "interpol"]),
    ]
    return {"version": "r11.0", "runtime_changed": False, "derived_from": "provider_r6 canonical case plus frozen R4/R5 snapshots",
            "case_request": BASE, "requirements": rows}


def build_gold() -> dict:
    cases = [
        ("GOLD-R11-DEFAULTS", BASE),
        ("GOLD-R11-EXPLICIT-SAME", {**BASE, "boarding_margin_minutes": 3}),
        ("GOLD-R11-CALLER-CHANGED", {**BASE, "boarding_margin_minutes": 8}),
        ("GOLD-R11-FOLLOWUP-75MIN", {**BASE, "appointment_time": "10:15", "duration_minutes": 75}),
        ("GOLD-R11-UNKNOWN-DATE", {**BASE, "date": "2026-09-30"}),
        ("GOLD-R11-NO-FEASIBLE", {**BASE, "appointment_time": "07:00"}),
    ]
    rows = []
    for case_id, request in cases:
        result = provider_r6.plan_visit(request)
        critical = {"status": result["status"], "error_code": (result.get("error") or {}).get("code")}
        if result["status"] == "ok":
            critical.update({"total_s": result["itinerary"]["total_s"],
                             "outbound_trip_id": result["itinerary"]["outbound"]["trip_id"],
                             "return_trip_id": result["itinerary"]["return"]["trip_id"],
                             "centre_id": result["health_destination"]["centre_id"],
                             "entrance_verified": result["health_destination"]["entrance_verified"]})
        rows.append({"case_id": case_id, "request": request, "expected_status": result["status"],
                     "critical_facts": critical,
                     "forbidden_claims": ["real-time journey", "verified physical entrance", "appointment availability", "human-authored caller parameters"],
                     "source_refs": [row["source_id"] for row in result.get("sources", [])]})
    return {"version": "r11.0", "classification": "DETERMINISTIC_PUBLIC_GOLD_NOT_HOLDOUT",
            "contains_final_answer_wording": False, "runtime_changed": False, "cases": rows}


def build() -> dict:
    requirements = build_requirements()
    dump(DOC / "MODEL_VIEW_REQUIREMENTS_R11.json", requirements)
    gold = build_gold()
    dump(DOC / "DETERMINISTIC_GOLD_R11.json", gold)
    handshake = copy.deepcopy(json.loads(R10.read_text(encoding="utf-8")))
    handshake["handshake_version"] = "r11.0-support"
    handshake["support_patch"] = {"supersedes_handshake_version": "r10.0-support", "runtime_changed": False,
                                  "reason": "Remove the remaining top-level unknown=date ambiguity and bind the real consumer model view."}
    for row in handshake["status_semantics"]:
        if row["status"] == "unknown":
            row["meaning"] = "La evidencia no permite verificar el resultado; la causa concreta depende de status+error.code."
            row["forbidden"] = "Atribuir fecha, red, HTTP o ausencia de transporte sin el error observado."
    handshake["model_view_requirements_ref"] = ref(DOC / "MODEL_VIEW_REQUIREMENTS_R11.json", "model_view_oracle")
    handshake["deterministic_gold_ref"] = ref(DOC / "DETERMINISTIC_GOLD_R11.json", "public_deterministic_gold")
    handshake["consumer_gate"] = {"command": "python scripts/mobility/intake_candidate_r11.py", "model_view": "candidate tools.public_result(envelope)",
                                  "diagnostic_not_run_exit": 0, "strict_not_run_exit": "nonzero"}
    dump(OUT / "W1_HANDSHAKE_R11.json", handshake)
    manifest = {"manifest_version": "r11.0", "runtime_inclusion": False, "runtime_tested_pin": RUNTIME_PIN,
                "runtime_package_sha256": PACKAGE_SHA,
                "files": [ref(OUT / "W1_HANDSHAKE_R11.json", "handshake"),
                          ref(DOC / "MODEL_VIEW_REQUIREMENTS_R11.json", "model_view_oracle"),
                          ref(DOC / "DETERMINISTIC_GOLD_R11.json", "public_deterministic_gold"),
                          ref(ROOT / "scripts/mobility/intake_candidate_r11.py", "candidate_intake")]}
    dump(OUT / "INTEGRATION_MANIFEST_R11.json", manifest)
    (OUT / "README.md").write_text("# W1 integration R11\n\nConsumer-only gate for the exact W2 public model view. Runtime R6 is unchanged. R10 remains historical.\n", encoding="utf-8", newline="\n")
    return {"handshake_sha256": sha(OUT / "W1_HANDSHAKE_R11.json"),
            "requirements": len(requirements["requirements"]), "gold_cases": len(gold["cases"]), "runtime_changed": False}


if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False, allow_nan=False))
