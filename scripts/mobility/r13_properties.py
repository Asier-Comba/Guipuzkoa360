"""Support-only R13 generated inputs and independently checked invariants.

No caching, replacement or patching of the producer's execution path.
"""
from __future__ import annotations

import copy
import csv
import hashlib
import json
import io
import random
import zipfile
from collections import Counter
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEED = 360013
HEALTH_ID = "official-goierrialdea-go01-health-r5-20260929"
LEGACY_ID = "official-goierrialdea-go01-r4-20260929"
ORIGINS = ("zegama_center_stops", "idiazabal_center_stops", "segura_herriko_plaza_stops")
BASE = dict(origin_id=ORIGINS[0], destination_id="beasain_official_centre_anchor",
            date="2026-09-29", appointment_time="09:45", duration_minutes=20)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def clock(text):
    parts = list(map(int, text.split(":")))
    return parts[0] * 3600 + parts[1] * 60 + (parts[2] if len(parts) == 3 else 0)


def generated_requests(count, seed=SEED):
    """Every complete 40-input block includes each explicit boundary family."""
    rng = random.Random(seed)
    durations = (1, 720, 20, 26, 30, 60, 0, 721)
    arrival = (0, 10, 1, 45, 240, -1, 241)
    boarding = (0, 3, 1, 15, 120, -1, 121)
    for index in range(count):
        mode = index % 40
        q = {**BASE, "origin_id": ORIGINS[(index // 40) % 3],
             "appointment_time": f"{rng.randrange(24):02d}:{rng.randrange(60):02d}:{rng.randrange(60):02d}",
             "duration_minutes": rng.choice((1, 20, 26, 30, 60, 120, 720))}
        family = "health_day_distribution"
        if mode < 8:
            q["duration_minutes"] = durations[mode]; family = "duration_boundary"
        elif mode < 15:
            q["arrival_margin_minutes"] = arrival[mode - 8]; family = "arrival_boundary"
        elif mode < 22:
            q["boarding_margin_minutes"] = boarding[mode - 15]; family = "boarding_boundary"
        elif mode < 26:
            # Public 09:45 base returns 11:07:49; exercise exact +/-1 explicitly.
            q.update(appointment_time="09:45", duration_minutes=20,
                     return_deadline=(None, "11:07:48", "11:07:49", "11:07:50")[mode - 22])
            family = "return_deadline_boundary"
        elif mode == 26:
            q.update(snapshot_id=HEALTH_ID); family = "explicit_health_snapshot"
        elif mode == 27:
            q.update(snapshot_id=LEGACY_ID, destination_id="beasain_center_stop_pair", walking_profile_id="stop_only")
            family = "legacy_explicit"
        elif mode == 28:
            q["snapshot_id"] = "missing_snapshot"; family = "unknown_snapshot"
        elif mode == 29:
            q["snapshot_id"] = rng.choice(("", "../unsafe", "TEST_synthetic", "bad snapshot")); family = "malformed_snapshot"
        elif mode == 30:
            q["duration_minutes"] = rng.choice((True, None, "20", [], {}, 1.5)); family = "wrong_numeric_type"
        elif mode == 31:
            q[rng.choice(("origin_id", "destination_id", "date", "appointment_time"))] = ""; family = "empty_text"
        elif mode == 32:
            q["unexpected"] = index; family = "extra_field"
        elif mode == 33:
            del q[rng.choice(tuple(BASE))]; family = "missing_field"
        elif mode == 34:
            q = rng.choice(([], {}, [BASE], None, "request")); family = "wrong_top_level"
        elif mode == 35:
            q["snapshot_id"] = rng.choice(([], {}, None, True, 42)); family = "wrong_snapshot_type"
        elif mode == 36:
            q["return_deadline"] = rng.choice(([], {}, "24:00", "", 0)); family = "wrong_deadline"
        elif mode == 37:
            q["date"] = "2026-09-30"; family = "unvalidated_date"
        elif mode == 38:
            q["date"] = rng.choice(("2026-02-30", "not-a-date", [], {})); family = "invalid_date"
        else:
            q[rng.choice(("origin_id", "destination_id", "appointment_time"))] = rng.choice(([], {}, True, 42))
            family = "unexpected_nested_type"
        yield index, family, q


@lru_cache(maxsize=2)
def result_schema(version):
    return json.loads((ROOT / f"prototypes/ir_y_volver/contracts/v{version}/result.schema.json").read_bytes())


@lru_cache(maxsize=1)
def raw_route_ids():
    path = ROOT / "datos_originales/movilidad/goierrialdea-3276fcae.zip"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == "3276fcae7bfa5002a39a2a094fef6637603de2e50648a46a436b314db27832a4"
    with zipfile.ZipFile(path) as archive:
        return {row["trip_id"]: row["route_id"] for row in csv.DictReader(io.StringIO(archive.read("trips.txt").decode("utf-8-sig")))}


def check_result(result, request):
    from prototypes.ir_y_volver.schema_r5 import validate
    from scripts.mobility.audit_r7 import HEALTH, validate_health_result, _ROWS
    assert result["status"] in {"ok", "no_feasible_journey", "unknown", "unsupported", "error"}, "status"
    assert result["time_basis"] == "scheduled", "observed schedule"
    schema = result_schema(result["schema_version"])
    validate(result, schema, schema)  # Closed schema and finiteness, including error outputs.
    canonical(result)
    if result["schema_version"] == "0.3.1":
        validate_health_result(result, request if type(request) is dict else {})
        assert result["scenario_kind"] == "health_visit"
        assert result["limitations"] == HEALTH["limitations"] or not result["limitations"]
    else:
        assert "health_destination" not in result and "walking" not in result, "fabricated legacy health"
    q = result["normalized_request"]
    if type(request) is dict:
        if request.get("date") == "2026-09-30" and q:
            assert q["date"] == "2026-09-30" and result["status"] != "ok", "silent date replacement"
        sid = request.get("snapshot_id")
        if type(sid) is str and sid not in (HEALTH_ID, LEGACY_ID):
            assert result["status"] != "ok" and result["snapshot_id"] == (sid or None), "snapshot fallback"
    if result["status"] != "ok":
        assert result["itinerary"] is None and result["components_s"] is None and result["components"] is None
        return
    it, components = result["itinerary"], result["components"]
    assert it["end_s"] - it["start_s"] == it["total_s"] == sum(row["seconds"] for row in components)
    assert all(row["seconds"] >= 0 and row["end_s"] - row["start_s"] == row["seconds"] for row in components)
    assert all(a["end_s"] == b["start_s"] for a, b in zip(components, components[1:]))
    assert result["components_s"]["appointment_s"] == q["duration_minutes"] * 60
    assert result["components_s"]["initial_wait_s"] == q["boarding_margin_minutes"] * 60
    assert components[0]["start_s"] == it["start_s"] and components[-1]["end_s"] == it["end_s"]
    for direction in ("outbound", "return"):
        leg = it[direction]
        assert leg["route_id"] == raw_route_ids()[leg["trip_id"]], "GTFS route binding"
        for end, field in (("from", "departure_time"), ("to", "arrival_time")):
            raw_row = _ROWS[(leg["trip_id"], leg[end + "_stop_id"], str(leg[end + "_stop_sequence"]))]
            assert raw_row[field] == leg[field], "scheduled row mismatch"
            if raw_row.get("timepoint") in ("", "0"):
                assert any(word in " ".join(result["limitations"]).lower() for word in ("aproxim", "interpol"))
    if q.get("return_deadline"):
        assert clock(it["return"]["arrival_time"]) <= clock(q["return_deadline"])
    if result["schema_version"] == "0.3.1":
        hd = result["health_destination"]
        assert hd["modelled_access"] is True and hd["entrance_verified"] is False and hd["entrance_verification"] == "NOT_VERIFIED"
        for direction in ("outbound", "return"):
            w = result["walking"][direction]
            assert w["modelled_access"] is True and w["entrance_verified"] is False


def metamorphic_cases():
    cases = []
    for origin in ORIGINS:
        base = {**BASE, "origin_id": origin}
        for field, value in (("appointment_time", "09:30"), ("duration_minutes", 26),
                             ("arrival_margin_minutes", 1), ("boarding_margin_minutes", 1),
                             ("origin_id", ORIGINS[(ORIGINS.index(origin) + 1) % 3]),
                             ("return_deadline", "11:07:48")):
            cases.append(dict(case_id=f"{origin}_{field}", operation="compare", changed_field=field,
                              requests=[base, {**base, field: value}, base]))
        cases.append(dict(case_id=origin + "_defaults", operation="compare", default_pair=True,
                          requests=[base, {**base, "arrival_margin_minutes": 10, "boarding_margin_minutes": 3,
                                           "walking_profile_id": "poc_reference_50m_min_plus_120s",
                                           "snapshot_id": HEALTH_ID, "return_deadline": None}]))
    cases.append(dict(case_id="invalid_change_no_delta", operation="compare", changed_field="duration_minutes",
                      requests=[BASE, {**BASE, "duration_minutes": "20"}]))
    cases.append(dict(case_id="mixed_snapshot_no_delta", operation="compare",
                      requests=[BASE, {**BASE, "snapshot_id": LEGACY_ID, "destination_id": "beasain_center_stop_pair"}]))
    return cases


def check_metamorphic(raw, case):
    results = raw["results"]
    assert len(results) == len(case["requests"]) and len(raw["comparisons"]) == len(results) * (len(results) - 1) // 2
    if len(results) == 3:
        assert canonical(results[0]) == canonical(results[2]), "A-B-A contamination"
    for row in raw["comparisons"]:
        left, right = results[row["left_index"]], results[row["right_index"]]
        a, b = left["normalized_request"], right["normalized_request"]
        if a and b:
            changed = [{"field": key, "left": a.get(key), "right": b.get(key)} for key in sorted(a.keys() | b.keys()) if a.get(key) != b.get(key)]
            held = [key for key in sorted(a.keys() | b.keys()) if a.get(key) == b.get(key)]
            assert row["requested_changes"] == changed and row["held_constant"] == held
        comparable = left["status"] == right["status"] == "ok" and all(a.get(k) == b.get(k) for k in ("snapshot_id", "date", "timezone", "origin_id", "destination_id", "walking_profile_id"))
        assert row["comparability"] == ("comparable" if comparable else "not_comparable")
        assert row["total_difference_s"] == (right["itinerary"]["total_s"] - left["itinerary"]["total_s"] if comparable else None)
    if case.get("default_pair"):
        assert results[0]["normalized_request"] == results[1]["normalized_request"]
        assert results[0]["itinerary"] == results[1]["itinerary"]
        assert results[0]["parameter_provenance"] != results[1]["parameter_provenance"]


def raw_spot_check(request, result, raw, health):
    """Expected trip selection derives from CSV, not from provider output."""
    from scripts.mobility.verify_health_r5 import oracle
    from scripts.mobility.build_r8 import walk_oracle
    measured = copy.deepcopy(health)
    walks = {}
    for sid, links in measured["walking_links"].items():
        walks[sid] = {}
        for direction, link in links.items():
            independent = walk_oracle(link)
            link["seconds"] = independent["seconds"]
            walks[sid][direction] = independent
    expected = oracle(raw, request, measured)
    assert expected["status"] == result["status"] == "ok"
    a, b, c, d = expected["rows"]
    out_walk = measured["walking_links"][b["stop_id"]]["outbound"]["seconds"]
    back_walk = measured["walking_links"][c["stop_id"]]["return"]["seconds"]
    ap, boarding = clock(request["appointment_time"]), request.get("boarding_margin_minutes", 3) * 60
    durations = dict(initial_wait_s=boarding, outbound_vehicle_s=clock(b["arrival_time"]) - clock(a["departure_time"]),
                     destination_walk_outbound_s=out_walk, pre_appointment_wait_s=ap - clock(b["arrival_time"]) - out_walk,
                     appointment_s=request["duration_minutes"] * 60, destination_walk_return_s=back_walk,
                     return_wait_s=clock(c["departure_time"]) - ap - request["duration_minutes"] * 60 - back_walk,
                     return_vehicle_s=clock(d["arrival_time"]) - clock(c["departure_time"]))
    assert result["components_s"] == durations and sum(durations.values()) == expected["total_s"] == result["itinerary"]["total_s"]
    routes = {trip["trip_id"]: trip["route_id"] for trip in raw["trips.txt"]}
    for direction, rows in (("outbound", (a, b)), ("return", (c, d))):
        leg = result["itinerary"][direction]
        assert leg["trip_id"] == rows[0]["trip_id"] and leg["route_id"] == routes[rows[0]["trip_id"]]
        for end, row in zip(("from", "to"), rows):
            assert leg[end + "_stop_id"] == row["stop_id"] and leg[end + "_stop_sequence"] == int(row["stop_sequence"])
        assert leg["departure_time"] == rows[0]["departure_time"] and leg["arrival_time"] == rows[1]["arrival_time"]
    assert result["itinerary"]["return_slack_s"] == expected["return_slack_s"]
    return dict(request=request, expected=expected, reconstructed_components_s=durations,
                walking={"outbound": walks[b["stop_id"]]["outbound"], "return": walks[c["stop_id"]]["return"]}, status="PASS")
