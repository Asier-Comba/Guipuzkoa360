"""Pinned, read-only consumer of W1 0.2.0 stop-only provider.

The approved W1 blobs are assembled at build time, never fetched at runtime.
No health-centre visit or realtime journey is exposed by this adapter.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any

try:
    from . import tools
except ImportError:  # Generated standalone Studio module.
    import tools


W1_PIN = "725a7b73ae0381092cd80edc41b8a25432d75fcd"
W1_VERSION = "0.2.0"
SNAPSHOT_ID = "official-goierrialdea-go01-r4-20260929"
PROVIDER_SHA256 = "c97842617f3077c2eec1892653361b4471a18e1c64f8127b808b9968401cb834"
VALIDATOR_SHA256 = "0773a1a612b366f59ea01f80ea1dc4fc0a4650ebbd339f6b99869c4061a16d42"
ALLOWLIST_SHA256 = "80d67a0a10da8f4aa6f7d3a30629a35dd861da9e419ede2e7fd5c907b8217cff"
SNAPSHOT_SHA256 = "62e00c04edb96ccde0a5ce4fe81574452ddcacdb4c173b030ca49b000f5a084b"
GTFS_SHA256 = "3276fcae7bfa5002a39a2a094fef6637603de2e50648a46a436b314db27832a4"
REQUEST_FIELDS = {"origin_id", "destination_id", "date", "appointment_time", "duration_minutes", "arrival_margin_minutes", "boarding_margin_minutes", "walking_profile_id", "snapshot_id", "return_deadline"}
REQUIRED = {"origin_id", "destination_id", "date", "appointment_time", "duration_minutes"}
RESULT_FIELDS = {"schema_version", "normalized_request", "status", "scenario_kind", "time_basis", "scope", "snapshot_id", "itinerary", "components_s", "components", "sources", "assumptions", "limitations", "error"}
COMPONENTS = ("initial_wait_s", "outbound_vehicle_s", "destination_walk_outbound_s", "pre_appointment_wait_s", "appointment_s", "destination_walk_return_s", "return_wait_s", "return_vehicle_s")
SCOPE = "origin_stop_presence_to_return_stop_arrival"


def _clock(value: str) -> str:
    if type(value) is not str or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d(?::[0-5]\d)?", value):
        raise tools.ContractViolation("mobility:invalid_clock")
    return value if len(value) == 8 else value + ":00"


def _request(request: Any) -> dict[str, Any]:
    if type(request) is not dict or REQUIRED - set(request) or set(request) - REQUEST_FIELDS:
        raise tools.ContractViolation("mobility:invalid_request_fields")
    for field in ("origin_id", "destination_id", "date", "appointment_time"):
        tools._text(request[field], f"mobility.{field}")
    try:
        if date.fromisoformat(request["date"]).isoformat() != request["date"]:
            raise ValueError("noncanonical date")
    except ValueError as exc:
        raise tools.ContractViolation("mobility:invalid_date") from exc
    _clock(request["appointment_time"])
    for field in ("duration_minutes", "arrival_margin_minutes", "boarding_margin_minutes"):
        if field in request and type(request[field]) is not int:
            raise tools.ContractViolation(f"mobility:{field}:expected_integer")
    for field in ("walking_profile_id", "snapshot_id"):
        if field in request:
            tools._text(request[field], f"mobility.{field}")
    if request.get("return_deadline") is not None:
        _clock(request["return_deadline"])
    if request.get("snapshot_id", SNAPSHOT_ID) != SNAPSHOT_ID:
        raise tools.ContractViolation("mobility:unverified_requested_snapshot")
    tools._finite(request)
    return dict(request)


def _pinned_blobs(provider: Any) -> None:
    source = Path(provider.__file__).resolve()
    expected = {
        source: PROVIDER_SHA256,
        source.with_name("snapshot_validation.py"): VALIDATOR_SHA256,
        source.with_name("snapshots") / "allowlist.json": ALLOWLIST_SHA256,
        source.with_name("snapshots") / f"{SNAPSHOT_ID}.json": SNAPSHOT_SHA256,
    }
    for path, sha in expected.items():
        if not path.is_file() or tools.digest(path.read_bytes()) != sha:
            raise tools.ContractViolation(f"mobility:unverified_pinned_blob:{path.name}")


def _capabilities(provider: Any) -> dict[str, Any]:
    _pinned_blobs(provider)
    capability = provider.get_capabilities()
    if type(capability) is not dict or capability.get("schema_version") != W1_VERSION or capability.get("provider_id") != "ir_y_volver" or capability.get("time_basis") != "scheduled" or capability.get("scope") != SCOPE:
        raise tools.ContractViolation("mobility:provider_capability_not_verified")
    snapshots = capability.get("snapshots")
    if type(snapshots) is not list:
        raise tools.ContractViolation("mobility:provider_snapshot_list")
    matching = [item for item in snapshots if type(item) is dict and item.get("snapshot_id") == SNAPSHOT_ID and item.get("scenario_kind") == "stop_only" and item.get("fixture_kind") != "SYNTHETIC_TEST_ONLY"]
    if len(matching) != 1 or type(matching[0].get("defaults")) is not dict or type(matching[0].get("walking_profiles")) is not dict:
        raise tools.ContractViolation("mobility:provider_snapshot_not_verified")
    return matching[0]


def _expected_normalized(request: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
    defaults = snapshot["defaults"]
    return {
        "origin_id": request["origin_id"], "destination_id": request["destination_id"], "date": request["date"],
        "appointment_time": _clock(request["appointment_time"]), "duration_minutes": request["duration_minutes"],
        "arrival_margin_minutes": request.get("arrival_margin_minutes", defaults["arrival_margin_minutes"]),
        "boarding_margin_minutes": request.get("boarding_margin_minutes", defaults["boarding_margin_minutes"]),
        "walking_profile_id": request.get("walking_profile_id", defaults["walking_profile_id"]),
        "snapshot_id": SNAPSHOT_ID, "timezone": "Europe/Madrid",
        "return_deadline": _clock(request["return_deadline"]) if request.get("return_deadline") is not None else None,
    }


def _validate_result(raw: Any, request: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
    tools._keys(raw, RESULT_FIELDS, "mobility_result")
    if raw["schema_version"] != W1_VERSION or raw["status"] not in {"ok", "no_feasible_journey", "unsupported", "unknown", "error"}:
        raise tools.ContractViolation("mobility:version_or_status")
    if raw["time_basis"] != "scheduled" or raw["scope"] != SCOPE or raw["scenario_kind"] != "stop_only" or raw["snapshot_id"] != SNAPSHOT_ID:
        raise tools.ContractViolation("mobility:false_scope_or_snapshot")
    normalized = raw["normalized_request"]
    if normalized is not None and normalized != _expected_normalized(request, snapshot):
        raise tools.ContractViolation("mobility:request_mismatch")
    if raw["status"] == "ok" and normalized is None:
        raise tools.ContractViolation("mobility:missing_normalized_request")
    if type(raw["sources"]) is not list or not any(type(source) is dict and source.get("source_sha256") == GTFS_SHA256 for source in raw["sources"]):
        raise tools.ContractViolation("mobility:official_schedule_source_missing")
    tools._strings(raw["assumptions"], "mobility.assumptions")
    tools._strings(raw["limitations"], "mobility.limitations")
    if raw["status"] == "ok":
        itinerary, components = raw["itinerary"], raw["components_s"]
        if type(itinerary) is not dict or type(components) is not dict or set(components) != set(COMPONENTS) or type(raw["components"]) is not list or len(raw["components"]) != len(COMPONENTS) or raw["error"] is not None:
            raise tools.ContractViolation("mobility:success_shape")
        if any(type(components[key]) is not int or components[key] < 0 for key in COMPONENTS) or type(itinerary.get("total_s")) is not int or sum(components.values()) != itinerary["total_s"]:
            raise tools.ContractViolation("mobility:component_total")
        if type(itinerary.get("start_s")) is not int or type(itinerary.get("end_s")) is not int or itinerary["end_s"] - itinerary["start_s"] != itinerary["total_s"]:
            raise tools.ContractViolation("mobility:interval_total")
        cursor = itinerary["start_s"]
        for name, item in zip(COMPONENTS, raw["components"]):
            tools._keys(item, {"kind", "start_s", "end_s", "seconds", "basis", "derivation"}, "mobility.component")
            if item["kind"] != name.removesuffix("_s") or item["start_s"] != cursor or item["end_s"] - item["start_s"] != item["seconds"] or item["seconds"] != components[name]:
                raise tools.ContractViolation("mobility:component_interval")
            cursor = item["end_s"]
        if cursor != itinerary["end_s"] or components["appointment_s"] != normalized["duration_minutes"] * 60 or components["initial_wait_s"] != normalized["boarding_margin_minutes"] * 60 or components["destination_walk_outbound_s"] != 0 or components["destination_walk_return_s"] != 0:
            raise tools.ContractViolation("mobility:parameter_or_stop_only_mismatch")
    elif raw["itinerary"] is not None or raw["components_s"] is not None or raw["components"] is not None or type(raw["error"]) is not dict:
        raise tools.ContractViolation("mobility:error_shape")
    tools._finite(raw)
    return raw


def _catalog(date_text: str) -> dict[str, dict[str, str]]:
    return {f"{prefix}@{date_text}": {"reference_period": date_text} for prefix in ("W1_GTFS", "W2_USER", "W1_MODEL", "W1_DERIVED")}


def _ids(date_text: str, component: str) -> list[str]:
    roles = {
        "outbound_vehicle_s": ("W1_GTFS",), "return_vehicle_s": ("W1_GTFS",),
        "appointment_s": ("W2_USER",),
        "initial_wait_s": ("W2_USER", "W1_MODEL"),
        "destination_walk_outbound_s": ("W1_MODEL",), "destination_walk_return_s": ("W1_MODEL",),
    }
    return [f"{prefix}@{date_text}" for prefix in roles.get(component, ("W1_GTFS", "W2_USER", "W1_MODEL", "W1_DERIVED"))]


def _claim(raw: dict[str, Any], pointer: str, value: int, date_text: str, claims: list[dict[str, Any]], component: str, *, explicit_boarding_margin: bool = False) -> None:
    sources = [f"W2_USER@{date_text}"] if component == "initial_wait_s" and explicit_boarding_margin else [f"W1_MODEL@{date_text}"] if component == "initial_wait_s" else _ids(date_text, component)
    entity_type, entity_id, entity_label = tools._claim_entity(raw, pointer)
    claims.append({
        "id": f"claim-{len(claims) + 1}", "label": component, "metric_id": component,
        "value": value, "unit": "s", "period": date_text, "numerator": None, "denominator": None,
        "source_ids": sources, "source_refs": tools._source_roles(component, sources),
        "reference_periods": [{"source_id": source, "period": date_text} for source in sources],
        "evidence_path": pointer, "entity_type": entity_type, "entity_id": entity_id,
        "entity_label": entity_label, "derivation": "estimated_with_assumptions", "assumptions": ["Horario programado y alcance stop_only; no duración real observada."],
    })


def _envelope(raw: dict[str, Any], original_args: dict[str, Any], effective_parameters: dict[str, Any], defaults_applied: list[str], request_id: str, claims: list[dict[str, Any]], outcomes: list[dict[str, Any]], status: str, error: dict[str, Any] | None, catalog: dict[str, Any]) -> dict[str, Any]:
    raw_json = tools.canonical(raw)
    if len(raw_json.encode("utf-8")) > tools.MAX_EVIDENCE_BYTES:
        raise tools.ContractViolation("mobility:payload_too_large")
    date_text = effective_parameters.get("date") if type(effective_parameters.get("date")) is str else None
    result = {
        "schema_version": tools.VERSION, "request_id": request_id, "capability_id": "plan_visit",
        "normalized_input": {"tool": "plan_visit", "arguments": original_args},
        "effective_request": {"operation": "plan_visit", "municipality_codes": [], "municipality_labels": [], "effective_period": date_text, "parameters": effective_parameters, "defaults_applied": defaults_applied, "snapshot_id": SNAPSHOT_ID, "contracts": {"evidence": tools.VERSION, "capability": tools.CAPABILITY_VERSION, "mobility": W1_VERSION}},
        "execution": {"request_id": request_id, "tool": "plan_visit", "arguments_sha256": tools.digest(tools.canonical(original_args)), "snapshot_id": SNAPSHOT_ID, "state": "completed"},
        "status": status, "outcomes": outcomes, "claims": claims,
        "method": "W1 0.2.0: búsqueda completa de pares directos programados entre paradas; tiempos modelados y parámetros humanos diferenciados.",
        "assumptions": ["Horario programado, no observado en tiempo real.", "El destino es una parada; no acredita entrada ni visita a centro sanitario."],
        "limitations": ["Solo fecha GO01 validada y scope stop_only; no puerta a puerta, transbordos ni acceso sanitario acreditado."],
        "error": error,
        "versions": {"data_sha256": SNAPSHOT_SHA256, "code_sha256": PROVIDER_SHA256, "contract_sha256": tools.digest((tools._workspace_root() / "contracts/vnext/evidence-v1.1.schema.json").read_bytes())},
        "raw_result_json": raw_json, "raw_result_sha256": tools.digest(raw_json),
    }
    tools.validate_evidence(result, catalog)
    return result


def _outcome(index: int, raw: dict[str, Any]) -> dict[str, Any]:
    return {"index": index, "status": raw["status"], "error": raw["error"]}


def consume_plan_visit(provider: Any, request: dict[str, Any], request_id: str) -> dict[str, Any]:
    normalized_input = _request(request)
    snapshot = _capabilities(provider)
    raw = _validate_result(provider.plan_visit(normalized_input), normalized_input, snapshot)
    expected = _expected_normalized(normalized_input, snapshot)
    claims: list[dict[str, Any]] = []
    status = {"ok": "valid", "no_feasible_journey": "no_data", "unsupported": "unsupported", "unknown": "error", "error": "error"}[raw["status"]]
    if status == "valid":
        _claim(raw, "/itinerary/total_s", raw["itinerary"]["total_s"], expected["date"], claims, "total_s")
        for component in COMPONENTS:
            _claim(raw, f"/components_s/{component}", raw["components_s"][component], expected["date"], claims, component, explicit_boarding_margin="boarding_margin_minutes" in normalized_input)
    error = None if status == "valid" else {
        "origin": "data" if raw["status"] == "unknown" else "domain",
        "code": raw["error"]["code"], "message": raw["error"]["message"],
        "available_options": [], "safe_next_action": "Revise el catálogo y la fecha validada; unknown no demuestra ausencia de transporte.",
    }
    return _envelope(raw, normalized_input, expected if raw["normalized_request"] is not None else normalized_input, sorted(set(expected if raw["normalized_request"] is not None else normalized_input) - set(normalized_input)), request_id, claims, [_outcome(0, raw)], status, error, _catalog(expected["date"]))


def consume_compare_visits(provider: Any, requests: list[dict[str, Any]], request_id: str) -> dict[str, Any]:
    if type(requests) is not list or not 2 <= len(requests) <= 32:
        raise tools.ContractViolation("mobility:comparison_requires_2_to_32")
    normalized = [_request(request) for request in requests]
    snapshot = _capabilities(provider)
    raw = provider.compare_visits(normalized)
    tools._keys(raw, {"schema_version", "status", "results", "comparisons", "differences_s", "error"}, "mobility_comparison")
    if raw["schema_version"] != W1_VERSION or raw["status"] != "ok" or type(raw["results"]) is not list or len(raw["results"]) != len(normalized) or type(raw["comparisons"]) is not list or type(raw["differences_s"]) is not list or raw["error"] is not None:
        raise tools.ContractViolation("mobility:comparison_result")
    for item, request in zip(raw["results"], normalized):
        _validate_result(item, request, snapshot)
    expected_pairs = {(left, right) for left in range(len(normalized)) for right in range(left + 1, len(normalized))}
    seen_pairs = set()
    comparable_pairs = set()
    for comparison in raw["comparisons"]:
        tools._keys(comparison, {"left_index", "right_index", "requested_changes", "held_constant", "comparability", "limitations"}, "mobility.comparison")
        left, right = comparison["left_index"], comparison["right_index"]
        if type(left) is not int or type(right) is not int or (left, right) not in expected_pairs or (left, right) in seen_pairs:
            raise tools.ContractViolation("mobility:comparison_index")
        seen_pairs.add((left, right))
        a, b = raw["results"][left], raw["results"][right]
        na, nb = a["normalized_request"], b["normalized_request"]
        changes, held = {}, {}
        if na is not None and nb is not None:
            for key in sorted(na.keys() | nb.keys()):
                if na.get(key) == nb.get(key):
                    held[key] = na.get(key)
                else:
                    changes[key] = {"left": na.get(key), "right": nb.get(key)}
        comparable = a["status"] == b["status"] == "ok" and all(na.get(key) == nb.get(key) for key in ("snapshot_id", "date", "timezone", "origin_id", "destination_id", "walking_profile_id"))
        if comparison["requested_changes"] != changes or comparison["held_constant"] != held or comparison["comparability"] != ("comparable" if comparable else "not_comparable"):
            raise tools.ContractViolation("mobility:comparison_semantics")
        if comparable:
            comparable_pairs.add((left, right))
    if seen_pairs != expected_pairs:
        raise tools.ContractViolation("mobility:missing_comparisons")
    seen_differences = set()
    for difference in raw["differences_s"]:
        tools._keys(difference, {"left_index", "right_index", "total_difference_s"}, "mobility.difference")
        pair = (difference["left_index"], difference["right_index"])
        if pair not in comparable_pairs or pair in seen_differences or type(difference["total_difference_s"]) is not int:
            raise tools.ContractViolation("mobility:invalid_difference")
        seen_differences.add(pair)
        left, right = pair
        if difference["total_difference_s"] != raw["results"][right]["itinerary"]["total_s"] - raw["results"][left]["itinerary"]["total_s"]:
            raise tools.ContractViolation("mobility:wrong_difference")
    if seen_differences != comparable_pairs:
        raise tools.ContractViolation("mobility:missing_difference")
    tools._finite(raw)
    claims: list[dict[str, Any]] = []
    catalog: dict[str, Any] = {}
    for index, item in enumerate(raw["results"]):
        date_text = normalized[index]["date"]
        catalog.update(_catalog(date_text))
        if item["status"] == "ok":
            _claim(raw, f"/results/{index}/itinerary/total_s", item["itinerary"]["total_s"], date_text, claims, "total_s")
    for index, difference in enumerate(raw["differences_s"]):
        date_text = normalized[difference["left_index"]]["date"]
        _claim(raw, f"/differences_s/{index}/total_difference_s", difference["total_difference_s"], date_text, claims, "total_difference_s")
    args = {"requests": normalized}
    outcomes = [_outcome(index, item) for index, item in enumerate(raw["results"])]
    return _envelope(raw, args, args, [], request_id, claims, outcomes, "valid", None, catalog)
