"""Planificador determinista, directo y acotado para un snapshot GTFS normalizado."""

from __future__ import annotations

import json
import math
import re
from datetime import date
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "0.1.0"
TIME_BASIS = "scheduled"
SCOPE = "stop_to_stop_with_destination_walk"
DEFAULT_SNAPSHOT_ID = "official-goierrialdea-go01-20260928"
STATUSES = ["ok", "no_feasible_journey", "unsupported", "unknown", "error"]
ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_DIRS = [Path(__file__).with_name("snapshots"), ROOT / "tests" / "mobility" / "fixtures"]
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
}


class SnapshotError(ValueError):
    """Snapshot ausente o internamente incoherente."""


def _snapshot_paths() -> list[Path]:
    return sorted(path for directory in SNAPSHOT_DIRS if directory.exists() for path in directory.glob("*.json"))


def _load_snapshot(snapshot_id: str) -> dict[str, Any]:
    for path in _snapshot_paths():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SnapshotError(f"No se pudo leer {path.name}: {exc}") from exc
        if payload.get("snapshot_id") == snapshot_id:
            _validate_snapshot(payload)
            return payload
    raise FileNotFoundError(snapshot_id)


def _validate_snapshot(snapshot: dict[str, Any]) -> None:
    required = {"snapshot_id", "timezone", "coverage", "defaults", "origins", "destinations", "calendar", "trips"}
    missing = sorted(required - snapshot.keys())
    if missing:
        raise SnapshotError(f"Faltan claves del snapshot: {missing}")
    if snapshot["timezone"] != "Europe/Madrid":
        raise SnapshotError("La zona horaria debe ser Europe/Madrid")
    seen: set[str] = set()
    for trip in snapshot["trips"]:
        trip_id = str(trip.get("trip_id", ""))
        if not trip_id or trip_id in seen:
            raise SnapshotError("trip_id ausente o duplicado")
        seen.add(trip_id)
        sequences = [int(item["sequence"]) for item in trip.get("stops", [])]
        if len(sequences) != len(set(sequences)) or sequences != sorted(sequences):
            raise SnapshotError(f"Secuencia inválida en {trip_id}")
        for item in trip.get("stops", []):
            _seconds(item["arrival"])
            _seconds(item["departure"])


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
        "time_basis": TIME_BASIS,
        "scope": SCOPE,
        "snapshot_id": snapshot_id,
        "itinerary": None,
        "components_s": None,
        "sources": list((snapshot or {}).get("sources", [])),
        "assumptions": [
            "Horarios programados; no incorpora incidencias ni retrasos en tiempo real.",
            "La búsqueda solo contempla viajes directos y paradas declaradas en el catálogo.",
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
    }
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
            if str(start["stop_id"]) not in from_stops or int(start.get("pickup_type", 0)) == 1:
                continue
            for end in items[start_index + 1 :]:
                if str(end["stop_id"]) not in to_stops or int(end.get("drop_off_type", 0)) == 1:
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
                    "pickup_type": int(start.get("pickup_type", 0)),
                    "drop_off_type": int(end.get("drop_off_type", 0)),
                    "from_timepoint": int(start.get("timepoint", 0)),
                    "to_timepoint": int(end.get("timepoint", 0)),
                })
    return legs


def plan_visit(request: dict[str, Any]) -> dict[str, Any]:
    requested_snapshot = request.get("snapshot_id", DEFAULT_SNAPSHOT_ID) if isinstance(request, dict) else None
    if not isinstance(requested_snapshot, str) or not requested_snapshot:
        return _base("error", None, None, None, error={"code": "invalid_request", "message": "snapshot_id debe ser texto no vacío cuando se proporciona"})
    try:
        snapshot = _load_snapshot(requested_snapshot)
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
    pairs: list[tuple[int, str, str, dict[str, Any], dict[str, Any], dict[str, int]]] = []
    for out in outbound:
        out_walk = destination_walk_by_stop[out["to_stop_id"]]
        origin_access = origin_access_by_stop[out["from_stop_id"]]
        if out["arrival_s"] + out_walk > appointment_s - arrival_margin_s:
            continue
        ready_return_s = appointment_s + duration_s
        for back in inbound:
            back_walk = destination_walk_by_stop[back["from_stop_id"]]
            return_access = origin_access_by_stop[back["to_stop_id"]]
            if back["departure_s"] < ready_return_s + back_walk + boarding_margin_s:
                continue
            components = {
                "origin_access_outbound_s": origin_access,
                "outbound_vehicle_s": out["arrival_s"] - out["departure_s"],
                "destination_walk_outbound_s": out_walk,
                "pre_appointment_wait_s": appointment_s - out["arrival_s"] - out_walk,
                "appointment_s": duration_s,
                "destination_walk_return_s": back_walk,
                "return_wait_s": back["departure_s"] - ready_return_s - back_walk,
                "return_vehicle_s": back["arrival_s"] - back["departure_s"],
                "origin_access_return_s": return_access,
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
    result.update({
        "status": "ok",
        "itinerary": {
            "outbound": {key: value for key, value in out.items() if not key.endswith("_s")},
            "return": {key: value for key, value in back.items() if not key.endswith("_s")},
            "total_s": total,
            "alternatives_evaluated": len(pairs),
        },
        "components_s": components,
        "error": None,
    })
    return result


def compare_visits(requests: list[dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(requests, list) or not 2 <= len(requests) <= 32:
        return {"schema_version": SCHEMA_VERSION, "status": "error", "results": [], "differences_s": [], "error": {"code": "invalid_request_count", "message": "Se requieren entre 2 y 32 peticiones"}}
    results = [plan_visit(request) for request in requests]
    differences = []
    ok = [(index, item) for index, item in enumerate(results) if item["status"] == "ok"]
    for left_pos, (left_index, left) in enumerate(ok):
        for right_index, right in ok[left_pos + 1 :]:
            if left["snapshot_id"] == right["snapshot_id"] and left["normalized_request"]["date"] == right["normalized_request"]["date"]:
                differences.append({"left_index": left_index, "right_index": right_index, "total_difference_s": right["itinerary"]["total_s"] - left["itinerary"]["total_s"]})
    return {"schema_version": SCHEMA_VERSION, "status": "ok", "results": results, "differences_s": differences, "error": None}


def get_capabilities() -> dict[str, Any]:
    snapshots = []
    for path in _snapshot_paths():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            _validate_snapshot(payload)
        except (OSError, json.JSONDecodeError, SnapshotError):
            continue
        if payload.get("fixture_kind") == "SYNTHETIC_TEST_ONLY":
            continue
        snapshots.append({
            "snapshot_id": payload["snapshot_id"],
            "fixture_kind": payload.get("fixture_kind", "OFFICIAL_DERIVED"),
            "coverage": payload["coverage"],
            "origins": sorted(payload["origins"]),
            "destinations": sorted(payload["destinations"]),
        })
    return {"schema_version": SCHEMA_VERSION, "provider_id": "ir_y_volver", "time_basis": TIME_BASIS, "scope": SCOPE, "statuses": STATUSES, "snapshots": snapshots}
