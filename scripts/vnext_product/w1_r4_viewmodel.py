"""Project observed W1 0.2.0 output to display components without routing math."""

from __future__ import annotations

import json
from pathlib import Path

KINDS = ["initial_wait", "outbound_vehicle", "destination_walk_outbound",
         "pre_appointment_wait", "appointment", "destination_walk_return",
         "return_wait", "return_vehicle"]


def viewmodel(result: dict) -> dict:
    if result.get("schema_version") != "0.2.0" or result.get("scenario_kind") != "stop_only":
        raise ValueError("Only W1 0.2.0 stop-only output is supported")
    status = result.get("status")
    if status not in {"ok", "no_feasible_journey", "unsupported", "unknown", "error"}:
        raise ValueError("Unknown W1 state")
    common = {"status": status, "scope": result.get("scope"),
              "time_basis": result.get("time_basis"), "sources": result.get("sources"),
              "assumptions": result.get("assumptions"), "limitations": result.get("limitations")}
    if status != "ok":
        if (result.get("itinerary") is not None or result.get("components") is not None
                or result.get("components_s") is not None):
            raise ValueError("Non-viable result contains an invented itinerary")
        return {**common, "timeline": None, "total_s": None,
                "return_slack_s": None, "error": result.get("error")}
    itinerary = result["itinerary"]
    components = result["components"]
    totals = result["components_s"]
    if [part.get("kind") for part in components] != KINDS:
        raise ValueError("Unexpected component order")
    current = itinerary["start_s"]
    for part in components:
        key = part["kind"] + "_s"
        if (part["start_s"] != current or part["end_s"] - current != part["seconds"]
                or totals[key] != part["seconds"] or part["seconds"] < 0):
            raise ValueError("Intervals and durations differ")
        current = part["end_s"]
    if (current != itinerary["end_s"] or current - itinerary["start_s"] != itinerary["total_s"]
            or not isinstance(itinerary["return_slack_s"], int)):
        raise ValueError("Timeline does not reconcile with provider total")
    if not result.get("sources") or any(not source.get("source_id") for source in result["sources"]):
        raise ValueError("Successful itinerary has no source ID")
    return {**common, "timeline": components,
            "outbound": itinerary["outbound"], "return": itinerary["return"],
            "total_s": itinerary["total_s"],
            "return_slack_s": itinerary["return_slack_s"],
            "return_slack_kind": "provider_value_not_appointment_availability",
            "origin_stop_id": itinerary["origin_stop_id"],
            "return_stop_id": itinerary["return_stop_id"]}


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    report = json.loads((root / "resultados/vnext/r4_independent/w1_r4_followup.json").read_text(encoding="utf-8"))
    output = {"classification": "OFFLINE_W1_R4_COMPONENT_PROJECTION_NOT_AGENT",
              "w1_head": report["w1_head"], "views": {k: viewmodel(v) for k, v in report["results"].items()}}
    path = root / "resultados/vnext/r4_independent/w1_r4_product_components.json"
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
