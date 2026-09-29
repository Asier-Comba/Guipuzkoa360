"""Planificador determinista, directo y acotado para un snapshot GTFS normalizado."""

from __future__ import annotations

import json
import math
import re
import hashlib
from datetime import date
from pathlib import Path
from typing import Any


from prototypes.ir_y_volver.snapshot_validation import SnapshotError, strict_loads, validate, enum

SCHEMA_VERSION = "0.2.0"
TIME_BASIS = "scheduled"
SCOPE = "origin_stop_presence_to_return_stop_arrival"
DEFAULT_SNAPSHOT_ID = "official-goierrialdea-go01-r4-20260929"
STATUSES = ["ok", "no_feasible_journey", "unsupported", "unknown", "error"]
ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = Path(__file__).with_name("snapshots") / "allowlist.json"
ALLOWED_FIELDS = {
    "origin_id",
    "destination_id",
    "date",
    "appointment_time",
    "duration_minutes",
    "arrival_margin_minutes",
    "boarding_margin_minutes",
    "walking_profile_id",
    "snapshot_id",
    "return_deadline",
}


def _load_snapshot(snapshot_id: str) -> dict[str, Any]:
    if snapshot_id.startswith("TEST_") or snapshot_id.startswith("synthetic"):
        raise FileNotFoundError(snapshot_id)
    try:
        manifest = strict_loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        if type(manifest) is not dict or manifest.get("schema_version") != SCHEMA_VERSION:
            raise SnapshotError("invalid allowlist")
        records = manifest["snapshots"]
        if type(records) is not dict:
            raise SnapshotError("invalid allowlist entries")
        if snapshot_id not in records:
            raise FileNotFoundError(snapshot_id)
        entry = records[snapshot_id]
        if entry["validation_status"] != "VALIDATED_STOP_ONLY" or entry["schema_version"] != SCHEMA_VERSION:
            raise SnapshotError("snapshot not validated")
        filename = entry["file"]
        if type(filename) is not str or not re.fullmatch(r"[a-zA-Z0-9_-]+\.json", filename):
            raise SnapshotError("invalid allowlist path")
        raw = (MANIFEST_PATH.parent / filename).read_bytes()
        if hashlib.sha256(raw).hexdigest() != entry["sha256"]:
            raise SnapshotError("snapshot hash mismatch")
        payload = strict_loads(raw)
        _validate_snapshot(payload)
        if payload["snapshot_id"] != snapshot_id or payload.get("fixture_kind") != "OFFICIAL_DERIVED":
            raise SnapshotError("snapshot identity/classification mismatch")
        for key in ("coverage", "sources", "walking_profiles"):
            if payload[key] != entry[key]:
                raise SnapshotError("manifest metadata mismatch: " + key)
        return payload
    except FileNotFoundError as exc:
        if exc.filename is None:
            raise
        raise SnapshotError("missing allowlisted file") from exc
    except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError) as exc:
        raise SnapshotError(str(exc)) from exc


def _validate_snapshot(snapshot: dict[str, Any]) -> None:
    try:
        validate(snapshot)
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError, RecursionError) as exc:
        raise SnapshotError(str(exc)) from exc


def _seconds(value: str) -> int:
    match = re.fullmatch(r"(\d{1,2}):([0-5]\d):([0-5]\d)", str(value))
    if not match:
        raise SnapshotError(f"Hora GTFS inválida: {value!r}")
    hour, minute, second = map(int, match.groups())
    return hour * 3600 + minute * 60 + second


def _clock_seconds(value: str) -> int:
    match = re.fullmatch(r"([01]\d|2[0-3]):([0-5]\d)(?::([0-5]\d))?", value)
    if not match:
        raise ValueError("appointment_time debe ser HH:MM o HH:MM:SS")
    hour, minute, second = match.groups()
    return int(hour) * 3600 + int(minute) * 60 + int(second or 0)


def _integer(value: Any, field: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field} debe ser entero")
    if not minimum <= value <= maximum:
        raise ValueError(f"{field} fuera de rango [{minimum}, {maximum}]")
    return value


def _stop_component(record: dict[str, Any], field: str, stop_id: str) -> int:
    mapping = record.get(field)
    if not isinstance(mapping, dict) or stop_id not in mapping:
        raise SnapshotError(f"Falta {field} explícito para stop_id={stop_id}")
    value = mapping[stop_id]
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value < 0
        or int(value) != value
    ):
        raise SnapshotError(f"{field}[{stop_id}] debe ser un número entero finito no negativo")
    return int(value)


def _base(status: str, snapshot_id: str | None, normalized: dict[str, Any] | None, snapshot: dict[str, Any] | None, *, error: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "normalized_request": normalized,
        "status": status,
        "scenario_kind": (snapshot or {}).get("scenario_kind"),
        "time_basis": TIME_BASIS,
        "scope": SCOPE,
        "snapshot_id": snapshot_id,
        "itinerary": None,
        "components_s": None,
        "components": None,
        "sources": list((snapshot or {}).get("sources", [])),
        "assumptions": [
            "Horarios programados; no incorpora incidencias ni retrasos en tiempo real.",
            "La búsqueda solo contempla viajes directos y paradas declaradas en el catálogo.",
            "Solo embarque y desembarque ordinarios; no se presume reserva ni acuerdo con conductor.",
            "Inicio en parada con margen de embarque; no incluye acceso desde domicilio.",
        ],
        "limitations": list((snapshot or {}).get("limitations", [])),
        "error": error,
    }


def _normalize(request: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise ValueError("request debe ser un objeto")
    unknown = sorted(set(request) - ALLOWED_FIELDS)
    if unknown:
        raise ValueError(f"Campos desconocidos: {unknown}")
    required = {"origin_id", "destination_id", "date", "appointment_time", "duration_minutes"}
    missing = sorted(required - request.keys())
    if missing:
        raise ValueError(f"Faltan campos: {missing}")
    for field in ("origin_id", "destination_id", "date", "appointment_time"):
        if not isinstance(request[field], str) or not request[field]:
            raise ValueError(f"{field} debe ser texto no vacío")
    parsed_date = date.fromisoformat(request["date"])
    appointment_s = _clock_seconds(request["appointment_time"])
    defaults = snapshot["defaults"]
    normalized = {
        "origin_id": request["origin_id"],
        "destination_id": request["destination_id"],
        "date": parsed_date.isoformat(),
        "appointment_time": f"{appointment_s // 3600:02d}:{appointment_s % 3600 // 60:02d}:{appointment_s % 60:02d}",
        "duration_minutes": _integer(request["duration_minutes"], "duration_minutes", 1, 720),
        "arrival_margin_minutes": _integer(request.get("arrival_margin_minutes", defaults["arrival_margin_minutes"]), "arrival_margin_minutes", 0, 240),
        "boarding_margin_minutes": _integer(request.get("boarding_margin_minutes", defaults["boarding_margin_minutes"]), "boarding_margin_minutes", 0, 120),
        "walking_profile_id": request.get("walking_profile_id", defaults["walking_profile_id"]),
        "snapshot_id": snapshot["snapshot_id"],
        "timezone": "Europe/Madrid",
        "return_deadline": request.get("return_deadline"),
    }
    if normalized["return_deadline"] is not None:
        if not isinstance(normalized["return_deadline"], str):
            raise ValueError("return_deadline debe ser hora o null")
        value = _clock_seconds(normalized["return_deadline"])
        normalized["return_deadline"] = f"{value // 3600:02d}:{value % 3600 // 60:02d}:{value % 60:02d}"
    if not isinstance(normalized["walking_profile_id"], str) or normalized["walking_profile_id"] not in snapshot.get("walking_profiles", {}):
        raise ValueError("walking_profile_id no soportado")
    return normalized


def _active_services(snapshot: dict[str, Any], target: date) -> set[str]:
    weekday = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")[target.weekday()]
    active = {
        str(row["service_id"])
        for row in snapshot["calendar"]
        if date.fromisoformat(_iso_date(row["start_date"])) <= target <= date.fromisoformat(_iso_date(row["end_date"]))
        and int(row[weekday]) == 1
    }
    for row in snapshot.get("calendar_dates", []):
        if _iso_date(row["date"]) != target.isoformat():
            continue
        if int(row["exception_type"]) == 1:
            active.add(str(row["service_id"]))
        elif int(row["exception_type"]) == 2:
            active.discard(str(row["service_id"]))
    return active


def _iso_date(value: str) -> str:
    value = str(value)
    if re.fullmatch(r"\d{8}", value):
        return f"{value[:4]}-{value[4:6]}-{value[6:]}"
    return date.fromisoformat(value).isoformat()


def _legs(snapshot: dict[str, Any], active: set[str], from_stops: set[str], to_stops: set[str]) -> list[dict[str, Any]]:
    legs: list[dict[str, Any]] = []
    for trip in snapshot["trips"]:
        if str(trip["service_id"]) not in active:
            continue
        items = trip["stops"]
        for start_index, start in enumerate(items):
            if str(start["stop_id"]) not in from_stops or enum(start.get("pickup_type", 0), (0,1,2,3), 0) != 0:
                continue
            for end in items[start_index + 1 :]:
                if str(end["stop_id"]) not in to_stops or enum(end.get("drop_off_type", 0), (0,1,2,3), 0) != 0:
                    continue
                departure = _seconds(start["departure"])
                arrival = _seconds(end["arrival"])
                if arrival < departure:
                    raise SnapshotError(f"Tiempo invertido en {trip['trip_id']}")
                legs.append({
                    "trip_id": str(trip["trip_id"]),
                    "route_id": str(trip["route_id"]),
                    "service_id": str(trip["service_id"]),
                    "from_stop_id": str(start["stop_id"]),
                    "to_stop_id": str(end["stop_id"]),
                    "from_stop_sequence": int(start["sequence"]),
                    "to_stop_sequence": int(end["sequence"]),
                    "departure_time": start["departure"],
                    "arrival_time": end["arrival"],
                    "departure_s": departure,
                    "arrival_s": arrival,
                    "pickup_type": enum(start.get("pickup_type", 0), (0,1,2,3), 0),
                    "drop_off_type": enum(end.get("drop_off_type", 0), (0,1,2,3), 0),
                    "from_timepoint": enum(start.get("timepoint", 1), (0,1), 1),
                    "to_timepoint": enum(end.get("timepoint", 1), (0,1), 1),
                })
    return legs


def plan_visit(request: dict[str, Any]) -> dict[str, Any]:
    requested_snapshot = request.get("snapshot_id", DEFAULT_SNAPSHOT_ID) if isinstance(request, dict) else None
    if not isinstance(requested_snapshot, str) or not requested_snapshot:
        return _base("error", None, None, None, error={"code": "invalid_request", "message": "snapshot_id debe ser texto no vacío cuando se proporciona"})
    try:
        snapshot = _load_snapshot(requested_snapshot)
        _validate_snapshot(snapshot)
    except FileNotFoundError:
        return _base("unknown", requested_snapshot, None, None, error={"code": "snapshot_not_found", "message": "El snapshot solicitado no está disponible"})
    except SnapshotError as exc:
        return _base("unknown", requested_snapshot, None, None, error={"code": "invalid_snapshot", "message": str(exc)})
    try:
        normalized = _normalize(request, snapshot)
    except (ValueError, TypeError) as exc:
        return _base("error", requested_snapshot, None, snapshot, error={"code": "invalid_request", "message": str(exc)})
    if normalized["origin_id"] not in snapshot["origins"] or normalized["destination_id"] not in snapshot["destinations"]:
        return _base("unsupported", requested_snapshot, normalized, snapshot, error={"code": "catalog_scope", "message": "Origen o destino fuera del catálogo del snapshot"})
    coverage = snapshot["coverage"]
    target = date.fromisoformat(normalized["date"])
    if not date.fromisoformat(_iso_date(coverage["start_date"])) <= target <= date.fromisoformat(_iso_date(coverage["end_date"])):
        return _base("unknown", requested_snapshot, normalized, snapshot, error={"code": "date_outside_feed_coverage", "message": "Fecha fuera de la vigencia declarada del feed"})
    validated = {_iso_date(item) for item in coverage.get("validated_dates", [])}
    if normalized["date"] not in validated:
        return _base("unknown", requested_snapshot, normalized, snapshot, error={"code": "date_not_validated", "message": "La fecha está cubierta nominalmente pero no validada para este snapshot"})
    try:
        active = _active_services(snapshot, target)
        origin = snapshot["origins"][normalized["origin_id"]]
        destination = snapshot["destinations"][normalized["destination_id"]]
        origin_stops = {str(value) for value in origin["stop_ids"]}
        destination_stops = {str(value) for value in destination["stop_ids"]}
        origin_access_by_stop = {
            stop_id: _stop_component(origin, "access_s_by_stop", stop_id)
            for stop_id in origin_stops
        }
        destination_walk_by_stop = {
            stop_id: _stop_component(destination, "walk_s_by_stop", stop_id)
            for stop_id in destination_stops
        }
        outbound = _legs(snapshot, active, origin_stops, destination_stops)
        inbound = _legs(snapshot, active, destination_stops, origin_stops)
    except (KeyError, TypeError, ValueError, SnapshotError) as exc:
        return _base("unknown", requested_snapshot, normalized, snapshot, error={"code": "data_integrity", "message": str(exc)})
    appointment_s = _clock_seconds(normalized["appointment_time"])
    duration_s = normalized["duration_minutes"] * 60
    arrival_margin_s = normalized["arrival_margin_minutes"] * 60
    boarding_margin_s = normalized["boarding_margin_minutes"] * 60
    deadline = _clock_seconds(normalized["return_deadline"]) if normalized["return_deadline"] else 86399
    if appointment_s + duration_s >= 86400:
        return _base("unsupported", requested_snapshot, normalized, snapshot, error={"code":"cross_day_appointment", "message":"Consulta fuera del mismo día civil"})
    # No timezone database dependency: transition Sundays in Europe/Madrid are excluded.
    if target.month in (3, 10) and target.weekday() == 6 and target.day >= 25:
        return _base("unsupported", requested_snapshot, normalized, snapshot, error={"code":"dst_transition", "message":"Día de transición horaria no soportado"})
    if any(leg["arrival_s"] >= 86400 or leg["departure_s"] >= 86400 for leg in outbound + inbound):
        return _base("unsupported", requested_snapshot, normalized, snapshot, error={"code":"multiday_service", "message":"El corredor contiene viajes que cruzan el día civil"})
    pairs: list[tuple[int, str, str, dict[str, Any], dict[str, Any], dict[str, int]]] = []
    for out in outbound:
        out_walk = destination_walk_by_stop[out["to_stop_id"]]
        if out["departure_s"] - boarding_margin_s < 0:
            continue
        if out["arrival_s"] + out_walk > appointment_s - arrival_margin_s:
            continue
        ready_return_s = appointment_s + duration_s
        for back in inbound:
            back_walk = destination_walk_by_stop[back["from_stop_id"]]
            if back["arrival_s"] > deadline:
                continue
            if back["departure_s"] < ready_return_s + back_walk + boarding_margin_s:
                continue
            components = {
                "initial_wait_s": boarding_margin_s,
                "outbound_vehicle_s": out["arrival_s"] - out["departure_s"],
                "destination_walk_outbound_s": out_walk,
                "pre_appointment_wait_s": appointment_s - out["arrival_s"] - out_walk,
                "appointment_s": duration_s,
                "destination_walk_return_s": back_walk,
                "return_wait_s": back["departure_s"] - ready_return_s - back_walk,
                "return_vehicle_s": back["arrival_s"] - back["departure_s"],
            }
            if any(value < 0 or not math.isfinite(value) for value in components.values()):
                continue
            total = sum(components.values())
            pairs.append((total, out["trip_id"], back["trip_id"], out, back, components))
    result = _base("no_feasible_journey", requested_snapshot, normalized, snapshot)
    if not pairs:
        result["error"] = {"code": "no_pair_in_complete_direct_search", "message": "No hay pareja directa viable en el alcance completo del snapshot"}
        return result
    total, _, _, out, back, components = min(pairs, key=lambda item: (item[0], item[1], item[2]))
    cursor = out["departure_s"] - boarding_margin_s
    timeline = []
    for kind, duration in components.items():
        basis = ("parameter:boarding_margin_minutes" if kind == "initial_wait_s" else
                 "parameter:duration_minutes" if kind == "appointment_s" else
                 "assumption:stop_only_explicit_zero" if "walk" in kind else
                 "source:GTFS stop_times + effective appointment parameters")
        timeline.append({"kind":kind[:-2], "start_s":cursor, "end_s":cursor+duration,
                         "seconds":duration, "basis":basis, "derivation":"end_s - start_s"})
        cursor += duration
    assert cursor == back["arrival_s"]
    result.update({
        "status": "ok",
        "itinerary": {
            "outbound": {key: value for key, value in out.items() if not key.endswith("_s")},
            "return": {key: value for key, value in back.items() if not key.endswith("_s")},
            "total_s": total,
            "start_s": out["departure_s"] - boarding_margin_s,
            "end_s": back["arrival_s"],
            "vehicle_span_s": back["arrival_s"] - out["departure_s"],
            "origin_stop_id": out["from_stop_id"],
            "return_stop_id": back["to_stop_id"],
            "return_slack_s": back["departure_s"] - appointment_s - duration_s - destination_walk_by_stop[back["from_stop_id"]] - boarding_margin_s,
            "alternatives_evaluated": len(pairs),
        },
        "components_s": components,
        "components": timeline,
        "error": None,
    })
    return result


def compare_visits(requests: list[dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(requests, list) or not 2 <= len(requests) <= 32:
        return {"schema_version": SCHEMA_VERSION, "status": "error", "results": [], "comparisons": [], "differences_s": [], "error": {"code": "invalid_request_count", "message": "Se requieren entre 2 y 32 peticiones"}}
    results = [plan_visit(request) for request in requests]
    differences = []
    comparisons = []
    for left_index, left in enumerate(results):
        for right_index in range(left_index + 1, len(results)):
            right = results[right_index]
            a, b = left["normalized_request"], right["normalized_request"]
            changes, held = {}, {}
            if a is not None and b is not None:
                for key in sorted(a.keys() | b.keys()):
                    if a.get(key) == b.get(key):
                        held[key] = a.get(key)
                    else:
                        changes[key] = {"left":a.get(key), "right":b.get(key)}
            compatible = left["status"] == right["status"] == "ok" and all(
                a.get(key) == b.get(key) for key in ("snapshot_id","date","timezone","origin_id","destination_id","walking_profile_id"))
            comparisons.append({"left_index":left_index,"right_index":right_index,
                "requested_changes":changes, "held_constant":held,
                "comparability":"comparable" if compatible else "not_comparable",
                "limitations":["Delta de escenarios programados; no atribución causal ni ahorro real."]})
            if compatible:
                differences.append({"left_index":left_index,"right_index":right_index,
                    "total_difference_s":right["itinerary"]["total_s"]-left["itinerary"]["total_s"]})
    return {"schema_version": SCHEMA_VERSION, "status": "ok", "results": results, "comparisons":comparisons, "differences_s": differences, "error": None}


def get_capabilities() -> dict[str, Any]:
    snapshots = []
    try:
        entries = strict_loads(MANIFEST_PATH.read_text(encoding="utf-8"))["snapshots"]
        if type(entries) is not dict:
            raise SnapshotError("invalid manifest")
    except (OSError, ValueError, KeyError, TypeError, RecursionError):
        entries = {}
    for snapshot_id in entries:
        try:
            payload = _load_snapshot(snapshot_id)
        except (OSError, ValueError, TypeError):
            continue
        if payload.get("fixture_kind") == "SYNTHETIC_TEST_ONLY":
            continue
        snapshots.append({
            "snapshot_id": payload["snapshot_id"],
            "fixture_kind": payload.get("fixture_kind", "OFFICIAL_DERIVED"),
            "coverage": payload["coverage"],
            "origins": sorted(payload["origins"]),
            "destinations": sorted(payload["destinations"]),
            "defaults":payload["defaults"],
            "walking_profiles":payload["walking_profiles"],
            "scenario_kind":payload["scenario_kind"],
        })
    return {"schema_version": SCHEMA_VERSION, "provider_id": "ir_y_volver", "time_basis": TIME_BASIS, "scope": SCOPE, "statuses": STATUSES, "snapshots": snapshots}
