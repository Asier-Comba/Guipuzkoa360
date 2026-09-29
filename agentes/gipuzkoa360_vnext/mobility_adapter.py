"""Optional W1 consumer. This module is not exposed in the portal package yet."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import tools


W1_VERSION = "0.1.0"
SNAPSHOT_ID = "official-goierrialdea-go01-20260928"
SNAPSHOT_SHA256 = "30fc9d638f3576ae0e1084ee1e0c7b0268469bffc8af1dd15fd12430019d968b"
GTFS_SHA256 = "3276fcae7bfa5002a39a2a094fef6637603de2e50648a46a436b314db27832a4"
SOURCE_ID = "MOVEUSKADI_GOIERRIALDEA_GO01_20260928"
REQUEST_FIELDS = {
    "origin_id", "destination_id", "date", "appointment_time", "duration_minutes",
    "arrival_margin_minutes", "boarding_margin_minutes", "walking_profile_id", "snapshot_id",
}
REQUIRED = {"origin_id", "destination_id", "date", "appointment_time", "duration_minutes"}
RESULT_FIELDS = {
    "schema_version", "normalized_request", "status", "time_basis", "scope", "snapshot_id",
    "itinerary", "components_s", "sources", "assumptions", "limitations", "error",
}


def _request(request: Any) -> dict[str, Any]:
    if type(request) is not dict or REQUIRED - set(request) or set(request) - REQUEST_FIELDS:
        raise tools.ContractViolation("mobility:invalid_request_fields")
    for field in ("origin_id", "destination_id", "date", "appointment_time"):
        tools._text(request[field], f"mobility.{field}")
    for field in ("duration_minutes", "arrival_margin_minutes", "boarding_margin_minutes"):
        if field in request and type(request[field]) is not int:
            raise tools.ContractViolation(f"mobility:{field}:expected_integer")
    for field in ("walking_profile_id", "snapshot_id"):
        if field in request:
            tools._text(request[field], f"mobility.{field}")
    if request.get("snapshot_id", SNAPSHOT_ID) != SNAPSHOT_ID:
        raise tools.ContractViolation("mobility:unverified_requested_snapshot")
    tools._finite(request)
    return dict(request)


def _snapshot(provider: Any) -> tuple[str, str]:
    source = Path(provider.__file__).resolve()
    snapshot = source.with_name("snapshots") / f"{SNAPSHOT_ID}.json"
    if not snapshot.is_file() or tools.digest(snapshot.read_bytes()) != SNAPSHOT_SHA256:
        raise tools.ContractViolation("mobility:unverified_snapshot")
    return tools.digest(source.read_bytes()), tools.digest(snapshot.read_bytes())


def _validate_result(raw: Any, request: dict[str, Any]) -> dict[str, Any]:
    tools._keys(raw, RESULT_FIELDS, "mobility_result")
    if raw["schema_version"] != W1_VERSION or raw["status"] not in {"ok", "no_feasible_journey", "unsupported", "unknown", "error"}:
        raise tools.ContractViolation("mobility:version_or_status")
    if raw["time_basis"] != "scheduled" or raw["scope"] != "stop_to_stop_with_destination_walk":
        raise tools.ContractViolation("mobility:false_scope")
    if raw["snapshot_id"] != request.get("snapshot_id", SNAPSHOT_ID):
        raise tools.ContractViolation("mobility:snapshot_mismatch")
    normalized = raw["normalized_request"]
    if raw["status"] == "ok":
        if type(normalized) is not dict or type(raw["itinerary"]) is not dict or type(raw["components_s"]) is not dict or raw["error"] is not None:
            raise tools.ContractViolation("mobility:success_shape")
        for field in REQUIRED - {"appointment_time"}:
            if normalized.get(field) != request[field]:
                raise tools.ContractViolation(f"mobility:request_mismatch:{field}")
        if not str(normalized.get("appointment_time", "")).startswith(request["appointment_time"]):
            raise tools.ContractViolation("mobility:request_mismatch:appointment_time")
        components = raw["components_s"]
        total = raw["itinerary"].get("total_s")
        if type(total) is not int or any(type(value) is not int or value < 0 for value in components.values()) or sum(components.values()) != total:
            raise tools.ContractViolation("mobility:component_total")
        if type(raw["sources"]) is not list or not raw["sources"] or any(source.get("source_sha256") != GTFS_SHA256 for source in raw["sources"]):
            raise tools.ContractViolation("mobility:false_source")
    else:
        if raw["itinerary"] is not None or raw["components_s"] is not None or type(raw["error"]) is not dict:
            raise tools.ContractViolation("mobility:error_shape")
    tools._strings(raw["assumptions"], "mobility.assumptions")
    tools._strings(raw["limitations"], "mobility.limitations")
    tools._finite(raw)
    return raw


def consume_plan_visit(provider: Any, request: dict[str, Any], request_id: str) -> dict[str, Any]:
    """Use the published W1 provider by explicit injection, never a mock at runtime."""
    normalized = _request(request)
    capabilities = provider.get_capabilities()
    if type(capabilities) is not dict or capabilities.get("schema_version") != W1_VERSION or capabilities.get("time_basis") != "scheduled" or capabilities.get("scope") != "stop_to_stop_with_destination_walk" or not any(item.get("snapshot_id") == SNAPSHOT_ID and item.get("fixture_kind") != "SYNTHETIC_TEST_ONLY" for item in capabilities.get("snapshots", [])):
        raise tools.ContractViolation("mobility:provider_capability_not_verified")
    code_hash, data_hash = _snapshot(provider)
    raw = _validate_result(provider.plan_visit(normalized), normalized)
    raw_json = tools.canonical(raw)
    if len(raw_json.encode("utf-8")) > tools.MAX_EVIDENCE_BYTES:
        raise tools.ContractViolation("mobility:payload_too_large")
    status = {"ok": "valid", "no_feasible_journey": "no_data", "unsupported": "unsupported", "unknown": "error", "error": "error"}[raw["status"]]
    claims = []
    catalog = {SOURCE_ID: {"reference_period": normalized["date"]}}
    if status == "valid":
        for pointer, label, value in [
            ("/itinerary/total_s", "scheduled_total_s", raw["itinerary"]["total_s"]),
            *((f"/components_s/{key}", key, value) for key, value in raw["components_s"].items()),
        ]:
            claims.append({"id": f"claim-{len(claims) + 1}", "label": label, "value": value, "unit": "s", "period": normalized["date"], "denominator": None, "source_ids": [SOURCE_ID], "evidence_path": pointer})
    error = None
    if status != "valid":
        observed = raw["error"]
        origin = "domain" if raw["status"] in {"no_feasible_journey", "unsupported", "error"} else "data"
        error = {"origin": origin, "code": observed["code"], "message": observed["message"], "available_options": [], "safe_next_action": "Revise el catálogo y la fecha validada; no infiera que no existe transporte."}
    result = {
        "schema_version": tools.VERSION, "request_id": request_id, "capability_id": "plan_visit",
        "normalized_input": {"tool": "plan_visit", "arguments": normalized},
        "execution": {"request_id": request_id, "tool": "plan_visit", "arguments_sha256": tools.digest(tools.canonical(normalized)), "snapshot_id": raw["snapshot_id"]},
        "status": status, "claims": claims, "method": "Búsqueda W1 de viajes directos sobre GTFS estático programado.",
        "assumptions": raw["assumptions"], "limitations": raw["limitations"], "error": error,
        "versions": {"data_sha256": data_hash, "code_sha256": code_hash, "contract_sha256": tools.digest((tools._workspace_root() / "contracts/vnext/evidence-v1.schema.json").read_bytes())},
        "raw_result_json": raw_json, "raw_result_sha256": tools.digest(raw_json),
    }
    tools.validate_evidence(result, catalog)
    return result


def consume_compare_visits(provider: Any, requests: list[dict[str, Any]]) -> dict[str, Any]:
    """Preserve every W1 outcome, including nonviable cases, in comparison."""
    if type(requests) is not list or not 2 <= len(requests) <= 32:
        raise tools.ContractViolation("mobility:comparison_requires_2_to_32")
    normalized = [_request(request) for request in requests]
    _snapshot(provider)
    raw = provider.compare_visits(normalized)
    tools._keys(raw, {"schema_version", "status", "results", "differences_s", "error"}, "mobility_comparison")
    if raw["schema_version"] != W1_VERSION or raw["status"] != "ok" or type(raw["results"]) is not list or len(raw["results"]) != len(normalized):
        raise tools.ContractViolation("mobility:comparison_result")
    for item, request in zip(raw["results"], normalized):
        _validate_result(item, request)
    if type(raw["differences_s"]) is not list:
        raise tools.ContractViolation("mobility:comparison_differences")
    for difference in raw["differences_s"]:
        tools._keys(difference, {"left_index", "right_index", "total_difference_s"}, "mobility.difference")
        left, right = difference["left_index"], difference["right_index"]
        if type(left) is not int or type(right) is not int or not 0 <= left < right < len(normalized):
            raise tools.ContractViolation("mobility:comparison_index")
        a, b = raw["results"][left], raw["results"][right]
        if a["status"] != "ok" or b["status"] != "ok" or a["snapshot_id"] != b["snapshot_id"] or a["normalized_request"]["date"] != b["normalized_request"]["date"] or type(difference["total_difference_s"]) is not int or difference["total_difference_s"] != b["itinerary"]["total_s"] - a["itinerary"]["total_s"]:
            raise tools.ContractViolation("mobility:comparison_value")
    tools._finite(raw)
    return raw
