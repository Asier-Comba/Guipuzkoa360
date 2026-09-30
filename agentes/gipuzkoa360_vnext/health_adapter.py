"""W2 boundary for the pinned W1 0.3.1 health-visit provider.

The provider's ``human_explicit`` means present in its input dictionary. W2 does
not promote that to a claim that a person selected the parameter.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from . import tools
except ImportError:  # Generated standalone Studio bundle.
    import tools

try:
    from . import mobility_adapter
except ImportError:  # Generated standalone Studio bundle.
    import mobility_adapter


VERSION = "0.3.1"
SNAPSHOT_ID = "official-goierrialdea-go01-health-r5-20260929"
SNAPSHOT_SHA256 = "59fcded9e4236ee094eeb0881c4eb94f521b96fb6c8c89c881c3e9f6d5140901"
R4_SNAPSHOT_ID = "official-goierrialdea-go01-r4-20260929"
PROVIDER_SHA256 = "c9fe7e4c8078ba7f9bf2eb2a51e050b729d9f01e6021dbcc6909f951d2e936e8"
CATALOG_SHA256 = "c7bd3cc8ffe50956ce839bec0ef90a13578160a4d5b4053b09673d2dc4c4ec17"
RESULT_SCHEMA_SHA256 = "5408f0869cc243f901ce5d142865af968bac00b02113cfa0e793ed2b1a96226a"
SCOPE = "origin_stop_presence_to_return_stop_arrival"
COMPONENTS = (
    "initial_wait_s", "outbound_vehicle_s", "destination_walk_outbound_s",
    "pre_appointment_wait_s", "appointment_s", "destination_walk_return_s",
    "return_wait_s", "return_vehicle_s",
)
REQUEST_FIELDS = {
    "origin_id", "destination_id", "date", "appointment_time", "duration_minutes",
    "arrival_margin_minutes", "boarding_margin_minutes", "walking_profile_id",
    "snapshot_id", "return_deadline",
}
REQUIRED = {"origin_id", "destination_id", "date", "appointment_time", "duration_minutes"}
OFFICIAL_IDS = {"GTFS", "HEALTH_REGISTRY", "HEALTH_PAGE", "PADI_2026", "OSM"}


def _pinned(provider: Any) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    base = Path(provider.__file__).resolve().parent
    root = base.parents[1]
    expected = {
        base / "provider_r6.py": PROVIDER_SHA256,
        base / "contracts/v0.3.1/result.schema.json": RESULT_SCHEMA_SHA256,
        base / "snapshots" / f"{SNAPSHOT_ID}.json": SNAPSHOT_SHA256,
        root / "datos_preparados/movilidad/operational_catalog_r6.json": CATALOG_SHA256,
    }
    for path, digest in expected.items():
        if not path.is_file() or tools.digest(path.read_bytes()) != digest:
            raise tools.ContractViolation(f"health:unverified_pinned_blob:{path.name}")
    catalog = tools.strict_loads((root / "datos_preparados/movilidad/operational_catalog_r6.json").read_text(encoding="utf-8"))
    health = tools.strict_loads((base / "snapshots" / f"{SNAPSHOT_ID}.json").read_text(encoding="utf-8"))
    r4 = tools.strict_loads((base / "snapshots" / f"{R4_SNAPSHOT_ID}.json").read_text(encoding="utf-8"))
    if catalog["snapshot_id"] != SNAPSHOT_ID or catalog["snapshot_sha256"] != SNAPSHOT_SHA256 or catalog["contract_version"] != VERSION:
        raise tools.ContractViolation("health:catalog_contract")
    capability = provider.get_capabilities()
    snapshots = capability.get("snapshots", [])
    matched = [item for item in snapshots if item.get("snapshot_id") == SNAPSHOT_ID]
    if capability.get("schema_version") != VERSION or capability.get("provider_id") != "ir_y_volver_r6" or capability.get("error") is not None or len(matched) != 1 or matched[0].get("scenario_kind") != "health_visit" or matched[0].get("entrance_verified") is not False:
        raise tools.ContractViolation("health:capability_contract")
    return catalog, health, r4


def _request(value: Any, catalog: dict[str, Any]) -> dict[str, Any]:
    if type(value) is not dict or REQUIRED - set(value) or set(value) - REQUEST_FIELDS:
        raise tools.ContractViolation("health:invalid_request_fields")
    for field in ("origin_id", "destination_id", "date", "appointment_time"):
        tools._text(value[field], f"health.{field}")
    if type(value["duration_minutes"]) is not int:
        raise tools.ContractViolation("health:invalid_duration")
    for field in ("arrival_margin_minutes", "boarding_margin_minutes"):
        if field in value and type(value[field]) is not int:
            raise tools.ContractViolation(f"health:invalid_{field}")
    if value.get("snapshot_id", SNAPSHOT_ID) not in {SNAPSHOT_ID, R4_SNAPSHOT_ID}:
        raise tools.ContractViolation("health:unverified_requested_snapshot")
    for field in ("appointment_time", "return_deadline"):
        if value.get(field) is not None:
            mobility_adapter._clock(value[field])
    tools._finite(value)
    return dict(value)


def _expected(request: dict[str, Any], catalog: dict[str, Any]) -> dict[str, Any]:
    defaults = catalog["defaults"]
    return {
        "origin_id": request["origin_id"], "destination_id": request["destination_id"],
        "date": request["date"], "appointment_time": mobility_adapter._clock(request["appointment_time"]),
        "duration_minutes": request["duration_minutes"],
        "arrival_margin_minutes": request.get("arrival_margin_minutes", defaults["arrival_margin_minutes"]),
        "boarding_margin_minutes": request.get("boarding_margin_minutes", defaults["boarding_margin_minutes"]),
        "walking_profile_id": request.get("walking_profile_id", defaults["walking_profile_id"]),
        "snapshot_id": SNAPSHOT_ID, "timezone": defaults["timezone"],
        "return_deadline": mobility_adapter._clock(request["return_deadline"]) if request.get("return_deadline") else None,
    }


def _seconds(clock: str) -> int:
    hour, minute, second = map(int, clock.split(":"))
    return hour * 3600 + minute * 60 + second


def _leg_identity(leg: Any, snapshot: dict[str, Any]) -> None:
    if type(leg) is not dict:
        raise tools.ContractViolation("health:missing_leg")
    matches = [trip for trip in snapshot["trips"] if trip["trip_id"] == leg.get("trip_id")]
    if len(matches) != 1:
        raise tools.ContractViolation("health:trip_id_mismatch")
    trip = matches[0]
    stops = trip["stops"]
    starts = [stop for stop in stops if stop["sequence"] == leg.get("from_stop_sequence")]
    ends = [stop for stop in stops if stop["sequence"] == leg.get("to_stop_sequence")]
    if len(starts) != 1 or len(ends) != 1 or starts[0]["sequence"] >= ends[0]["sequence"]:
        raise tools.ContractViolation("health:stop_sequence_mismatch")
    start, end = starts[0], ends[0]
    expected = {
        "route_id": trip["route_id"], "service_id": trip["service_id"],
        "from_stop_id": start["stop_id"], "to_stop_id": end["stop_id"],
        "departure_time": start["departure"], "arrival_time": end["arrival"],
        "pickup_type": start["pickup_type"], "drop_off_type": end["drop_off_type"],
        "from_timepoint": start["timepoint"], "to_timepoint": end["timepoint"],
    }
    if any(leg.get(key) != value for key, value in expected.items()):
        raise tools.ContractViolation("health:leg_identity_mismatch")


def _validate_health(raw: Any, request: dict[str, Any], catalog: dict[str, Any], health: dict[str, Any], r4: dict[str, Any], provider: Any, root: Path) -> dict[str, Any]:
    schema_path = Path(provider.__file__).resolve().parent / "contracts/v0.3.1/result.schema.json"
    schema = tools.strict_loads(schema_path.read_text(encoding="utf-8"))
    try:
        provider.r5.schema_validate(raw, schema)
    except (ValueError, KeyError, TypeError) as exc:
        raise tools.ContractViolation("health:result_schema") from exc
    if raw["schema_version"] != VERSION or raw["scenario_kind"] != "health_visit" or raw["snapshot_id"] != SNAPSHOT_ID or raw["scope"] != SCOPE or raw["time_basis"] != "scheduled":
        raise tools.ContractViolation("health:identity_or_scope")
    normalized = raw["normalized_request"]
    if normalized is not None and normalized != _expected(request, catalog):
        raise tools.ContractViolation("health:request_mismatch")
    if raw["status"] == "ok" and normalized is None:
        raise tools.ContractViolation("health:missing_normalized_request")
    rows = raw["parameter_provenance"]
    if normalized is None:
        if rows:
            raise tools.ContractViolation("health:false_parameter_provenance")
    else:
        if type(rows) is not list or len(rows) != len(normalized) or {row.get("field") for row in rows} != set(normalized):
            raise tools.ContractViolation("health:parameter_provenance_shape")
        for row in rows:
            field = row["field"]
            explicit = field in request
            if row["value"] != normalized[field] or row["origin"] != ("human_explicit" if explicit else "model_default") or row["source_ref"] != ("USER" if explicit else "MODEL_DEFAULTS"):
                raise tools.ContractViolation("health:parameter_provenance_binding")
    metadata = tools._catalog(root)
    source_ids = set()
    for source in raw["sources"]:
        sid = source["source_id"]
        if sid in source_ids or sid not in metadata:
            raise tools.ContractViolation("health:source_identity")
        source_ids.add(sid)
        known = metadata[sid]
        producer_role = "user_input" if sid == "USER" else known["role"]
        expected_period = normalized["date"] if sid in {"USER", "MODEL_DEFAULTS", "DERIVED"} and normalized is not None else known["reference_period"]
        if source["source_role"] != producer_role or source["reference_period"] != expected_period:
            raise tools.ContractViolation("health:source_role_or_period")
        if sid in OFFICIAL_IDS and (source["source_sha256"] != known["source_sha256"] or source["url"] != known["url"]):
            raise tools.ContractViolation("health:external_source_mutation")
        if sid not in OFFICIAL_IDS and source["url"] is not None:
            raise tools.ContractViolation("health:internal_source_as_official")
    if raw["status"] == "ok":
        if raw["health_destination"] != health["health_destination"] or raw["health_destination"]["entrance_verified"] is not False or raw["health_destination"]["human_review_required"] is not True:
            raise tools.ContractViolation("health:destination_misrepresentation")
        itinerary = raw["itinerary"]
        _leg_identity(itinerary["outbound"], r4)
        _leg_identity(itinerary["return"], r4)
        if itinerary["origin_stop_id"] != itinerary["outbound"]["from_stop_id"] or itinerary["return_stop_id"] != itinerary["return"]["to_stop_id"]:
            raise tools.ContractViolation("health:stop_identity")
        walking = raw["walking"]
        if walking["outbound"] != health["walking_links"][itinerary["outbound"]["to_stop_id"]]["outbound"] or walking["return"] != health["walking_links"][itinerary["return"]["from_stop_id"]]["return"]:
            raise tools.ContractViolation("health:walking_identity")
        components = raw["components_s"]
        if type(components) is not dict or set(components) != set(COMPONENTS) or type(raw["components"]) is not list or len(raw["components"]) != 8:
            raise tools.ContractViolation("health:components_shape")
        if any(type(components[key]) is not int or components[key] < 0 for key in COMPONENTS) or sum(components.values()) != itinerary["total_s"] or itinerary["end_s"] - itinerary["start_s"] != itinerary["total_s"]:
            raise tools.ContractViolation("health:component_total")
        cursor = itinerary["start_s"]
        for field, item in zip(COMPONENTS, raw["components"]):
            if item["kind"] != field.removesuffix("_s") or item["start_s"] != cursor or item["end_s"] - item["start_s"] != item["seconds"] or item["seconds"] != components[field] or not set(item["source_refs"]) <= source_ids:
                raise tools.ContractViolation("health:component_interval_or_source")
            cursor = item["end_s"]
        if cursor != itinerary["end_s"] or components["initial_wait_s"] != normalized["boarding_margin_minutes"] * 60 or components["appointment_s"] != normalized["duration_minutes"] * 60 or components["destination_walk_outbound_s"] != walking["outbound"]["seconds"] or components["destination_walk_return_s"] != walking["return"]["seconds"]:
            raise tools.ContractViolation("health:parameter_or_walking_mismatch")
        if components["outbound_vehicle_s"] != _seconds(itinerary["outbound"]["arrival_time"]) - _seconds(itinerary["outbound"]["departure_time"]) or components["return_vehicle_s"] != _seconds(itinerary["return"]["arrival_time"]) - _seconds(itinerary["return"]["departure_time"]):
            raise tools.ContractViolation("health:schedule_component_mismatch")
        if itinerary["return_slack_s"] != _seconds(itinerary["return"]["departure_time"]) - _seconds(normalized["appointment_time"]) - normalized["duration_minutes"] * 60 - walking["return"]["seconds"] - normalized["boarding_margin_minutes"] * 60:
            raise tools.ContractViolation("health:return_slack_mismatch")
        if components["pre_appointment_wait_s"] != _seconds(normalized["appointment_time"]) - _seconds(itinerary["outbound"]["arrival_time"]) - walking["outbound"]["seconds"]:
            raise tools.ContractViolation("health:appointment_wait_mismatch")
    else:
        if raw["itinerary"] is not None or raw["components_s"] is not None or raw["walking"] is not None or type(raw["error"]) is not dict:
            raise tools.ContractViolation("health:error_shape")
    tools._finite(raw)
    return raw


def _claim(raw: dict[str, Any], pointer: str, unit: str, sources: list[str], catalog: dict[str, Any], claims: list[dict[str, Any]]) -> None:
    value = tools._pointer(raw, pointer)
    entity_type, entity_id, entity_label = tools._claim_entity(raw, pointer)
    metric = pointer.split("/")[-1]
    claims.append({
        "id": f"claim-{len(claims) + 1}", "label": metric, "value": value, "unit": unit,
        "period": ";".join(dict.fromkeys(catalog[source]["reference_period"] for source in sources)),
        "numerator": None, "denominator": None, "source_ids": sources,
        "evidence_path": pointer, "entity_type": entity_type, "entity_id": entity_id,
        "entity_label": entity_label, "metric_id": metric,
        "reference_periods": [{"source_id": source, "period": catalog[source]["reference_period"]} for source in sources],
        "source_refs": tools._source_roles(metric, sources), "derivation": "estimated_with_assumptions",
        "assumptions": ["Horario GTFS estático y paseo modelado; no duración real observada."],
    })


def _claims(raw: dict[str, Any], prefix: str, catalog: dict[str, Any], claims: list[dict[str, Any]]) -> None:
    sources = ["GTFS", "HEALTH_REGISTRY", "OSM", "MODEL", "USER", "MODEL_DEFAULTS", "DERIVED"]
    _claim(raw, prefix + "/itinerary/total_s", "s", sources, catalog, claims)
    for field in COMPONENTS:
        related = ["GTFS"] if field.endswith("vehicle_s") else ["USER", "MODEL_DEFAULTS"] if field in {"appointment_s", "initial_wait_s"} else sources
        _claim(raw, prefix + "/components_s/" + field, "s", related, catalog, claims)
    for direction in ("outbound", "return"):
        _claim(raw, prefix + f"/walking/{direction}/total_metres", "m", ["GTFS", "HEALTH_REGISTRY", "OSM", "MODEL"], catalog, claims)


def _error(raw: dict[str, Any]) -> dict[str, Any]:
    code = raw["error"]["code"]
    origin = "data" if code in {"invalid_health_snapshot", "date_not_validated"} else "domain"
    return {"origin": origin, "code": code, "message": raw["error"]["message"],
            "available_options": [], "safe_next_action": "Revise el catálogo, parámetros y fecha validada; este estado no prueba ausencia de transporte."}


def _envelope(raw: dict[str, Any], arguments: dict[str, Any], effective: dict[str, Any] | None, request_id: str, claims: list[dict[str, Any]], outcomes: list[dict[str, Any]], status: str, error: dict[str, Any] | None, root: Path) -> dict[str, Any]:
    raw_json = tools.canonical(raw)
    if len(raw_json.encode("utf-8")) > tools.MAX_EVIDENCE_BYTES:
        raise tools.ContractViolation("health:evidence_payload_too_large")
    snapshot = effective.get("snapshot_id") if effective else SNAPSHOT_ID
    result = {
        "schema_version": tools.VERSION, "request_id": request_id, "capability_id": "plan_visit",
        "normalized_input": {"tool": "plan_visit", "arguments": arguments},
        "effective_request": None if effective is None else {
            "operation": "plan_visit", "municipality_codes": [], "municipality_labels": [],
            "effective_period": effective.get("date"), "parameters": effective,
            "defaults_applied": sorted(set(effective) - set(arguments)), "snapshot_id": snapshot,
            "contracts": {"evidence": tools.VERSION, "capability": tools.CAPABILITY_VERSION, "mobility": VERSION},
        },
        "execution": {"request_id": request_id, "tool": "plan_visit", "arguments_sha256": tools.digest(tools.canonical(arguments)), "snapshot_id": snapshot, "state": "completed"},
        "status": status, "outcomes": outcomes, "claims": claims,
        "method": "W1 0.3.1: pares GO01 programados y paseo modelado hasta punto oficial del centro; validación W2 de identidad, parámetros y componentes.",
        "assumptions": ["Los argumentos del agente no acreditan autoría humana aunque W1 los marque human_explicit.", "Paseo de referencia 50 m/min + 120 s por enlace completo y sentido."],
        "limitations": ["Entrada física NOT_VERIFIED; conflicto Bernedo Enea 1 / Zaldizurreta 2 pendiente de revisión humana.", "GTFS estático y tiempos timepoint=0 aproximados; no realtime, domicilio, cita ni accesibilidad garantizada."],
        "error": error,
        "versions": {"data_sha256": SNAPSHOT_SHA256, "code_sha256": PROVIDER_SHA256,
                     "contract_sha256": tools.digest((root / "contracts/vnext/evidence-v1.1.schema.json").read_bytes())},
        "raw_result_json": raw_json, "raw_result_sha256": tools.digest(raw_json),
    }
    tools.validate_evidence(result, tools._catalog(root), root)
    return result


def consume_health(provider: Any, request: dict[str, Any], request_id: str, root: Path) -> dict[str, Any]:
    catalog, health, r4 = _pinned(provider)
    request = _request(request, catalog)
    if request.get("snapshot_id", SNAPSHOT_ID) != SNAPSHOT_ID:
        raise tools.ContractViolation("health:wrong_consumer_for_stop_only")
    raw = _validate_health(provider.plan_visit(request), request, catalog, health, r4, provider, root)
    normalized = raw["normalized_request"]
    status = {"ok": "valid", "no_feasible_journey": "no_data", "unknown": "error", "unsupported": "unsupported", "error": "error"}[raw["status"]]
    claims: list[dict[str, Any]] = []
    if status == "valid":
        _claims(raw, "", tools._catalog(root), claims)
    return _envelope(raw, request, normalized, request_id, claims, [{"index": 0, "status": raw["status"], "error": raw["error"]}], status, None if status == "valid" else _error(raw), root)


def consume_compare(provider: Any, requests: list[dict[str, Any]], request_id: str, root: Path) -> dict[str, Any]:
    if type(requests) is not list or not 2 <= len(requests) <= 4:
        raise tools.ContractViolation("health:comparison_requires_2_to_4")
    catalog, health, r4 = _pinned(provider)
    normalized = [_request(request, catalog) for request in requests]
    raw = provider.compare_visits(normalized)
    if raw.get("schema_version") != VERSION or raw.get("status") != "ok" or type(raw.get("results")) is not list or len(raw["results"]) != len(normalized) or type(raw.get("comparisons")) is not list or len(raw["comparisons"]) != len(normalized) * (len(normalized) - 1) // 2 or raw.get("error") is not None:
        raise tools.ContractViolation("health:comparison_shape")
    r4_snapshot = mobility_adapter._capabilities(provider.r4)
    for item, request in zip(raw["results"], normalized):
        if request.get("snapshot_id", SNAPSHOT_ID) == R4_SNAPSHOT_ID:
            mobility_adapter._validate_result(item, request, r4_snapshot)
        else:
            _validate_health(item, request, catalog, health, r4, provider, root)
    pairs = {(i, j) for i in range(len(normalized)) for j in range(i + 1, len(normalized))}
    seen = set()
    for comparison in raw["comparisons"]:
        left, right = comparison["left_index"], comparison["right_index"]
        if type(left) is not int or type(right) is not int or (left, right) not in pairs or (left, right) in seen:
            raise tools.ContractViolation("health:comparison_index")
        seen.add((left, right))
        a, b = raw["results"][left], raw["results"][right]
        na, nb = a["normalized_request"], b["normalized_request"]
        comparable = a["status"] == b["status"] == "ok" and all(na[key] == nb[key] for key in ("origin_id", "destination_id", "date", "snapshot_id", "walking_profile_id", "timezone"))
        if comparison["comparability"] != ("comparable" if comparable else "not_comparable") or comparison["total_difference_s"] != (b["itinerary"]["total_s"] - a["itinerary"]["total_s"] if comparable else None):
            raise tools.ContractViolation("health:comparison_delta")
        if na is not None and nb is not None:
            changes = [{"field": key, "left": na[key], "right": nb[key]} for key in sorted(na) if na[key] != nb[key]]
            held = [key for key in sorted(na) if na[key] == nb[key]]
            if comparison["requested_changes"] != changes or comparison["held_constant"] != held:
                raise tools.ContractViolation("health:comparison_parameters")
    if seen != pairs:
        raise tools.ContractViolation("health:missing_comparison")
    tools._finite(raw)
    claims: list[dict[str, Any]] = []
    source_catalog = tools._catalog(root)
    for index, item in enumerate(raw["results"]):
        if item["status"] == "ok" and item["schema_version"] == VERSION:
            _claims(raw, f"/results/{index}", source_catalog, claims)
        elif item["status"] == "ok":
            mobility_adapter._claim(raw, f"/results/{index}/itinerary/total_s", item["itinerary"]["total_s"], item["normalized_request"]["date"], claims, "total_s")
    for index, comparison in enumerate(raw["comparisons"]):
        if comparison["comparability"] == "comparable":
            _claim(raw, f"/comparisons/{index}/total_difference_s", "s", ["GTFS", "HEALTH_REGISTRY", "OSM", "MODEL", "USER", "MODEL_DEFAULTS", "DERIVED"], source_catalog, claims)
    args = {"requests": normalized}
    outcomes = [{"index": index, "status": item["status"], "error": item["error"]} for index, item in enumerate(raw["results"])]
    return _envelope(raw, args, args, request_id, claims, outcomes, "valid", None, root)
