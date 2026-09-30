from __future__ import annotations

import copy
import json
from datetime import date
from pathlib import Path

import pytest

from prototypes.ir_y_volver import provider


FIXTURE = Path(__file__).with_name("fixtures") / "synthetic_snapshot.json"
OFFICIAL = Path(__file__).parents[2] / "prototypes" / "ir_y_volver" / "snapshots" / "official-goierrialdea-go01-20260928.json"


def request(**updates):
    value = {
        "origin_id": "origin_a",
        "destination_id": "destination_b",
        "date": "2026-09-29",
        "appointment_time": "10:00",
        "duration_minutes": 30,
        "snapshot_id": "synthetic-contract-v1",
    }
    value.update(updates)
    return value


def load_fixture():
    s = json.loads(FIXTURE.read_text(encoding="utf-8"))
    s['schema_version']='0.2.0'
    s['scenario_kind']='stop_only'
    s['coverage']['direct_search_complete']=True
    s['stops']={key:{'name':key,'lat':43.0,'lon':-2.0} for key in ('A','B')}
    s['sources']=[{'source_id':'TEST_SOURCE','publisher':'SYNTHETIC','url':'https://example.invalid/test',
                   'source_sha256':'0'*64,'retrieved_date':'2026-09-29'}]
    return s


@pytest.fixture(autouse=True)
def explicit_test_injection(monkeypatch):
    original = provider._load_snapshot
    def loader(snapshot_id):
        if snapshot_id == 'synthetic-contract-v1':
            return load_fixture()
        return original(snapshot_id)
    monkeypatch.setattr(provider, '_load_snapshot', loader)


def install_snapshot(monkeypatch, tmp_path, payload):
    monkeypatch.setattr(provider, "_load_snapshot", lambda _: payload)


def test_valid_weekday_uses_defaults_and_disjoint_components():
    result = provider.plan_visit(request())
    assert result["status"] == "ok"
    assert result["normalized_request"]["arrival_margin_minutes"] == 10
    assert result["normalized_request"]["boarding_margin_minutes"] == 3
    assert result["itinerary"]["total_s"] == sum(result["components_s"].values()) == 8580


@pytest.mark.parametrize("day", ["2026-10-03", "2026-10-04"])
def test_weekend_calendar(day):
    result = provider.plan_visit(request(date=day))
    assert result["status"] == "ok"
    assert result["itinerary"]["outbound"]["service_id"] == "WE"


@pytest.mark.parametrize(
    ("updates", "code"),
    [
        ({"extra": 1}, "invalid_request"),
        ({"duration_minutes": True}, "invalid_request"),
        ({"duration_minutes": 0}, "invalid_request"),
        ({"duration_minutes": 721}, "invalid_request"),
        ({"duration_minutes": float("nan")}, "invalid_request"),
        ({"appointment_time": "25:00"}, "invalid_request"),
        ({"date": "29/09/2026"}, "invalid_request"),
        ({"walking_profile_id": "wheelchair"}, "invalid_request"),
        ({"origin_id": ""}, "invalid_request"),
    ],
)
def test_invalid_requests_are_not_defaulted(updates, code):
    result = provider.plan_visit(request(**updates))
    assert result["status"] == "error"
    assert result["error"]["code"] == code


def test_missing_snapshot_is_unknown():
    result = provider.plan_visit(request(snapshot_id="missing"))
    assert result["status"] == "unknown"
    assert result["error"]["code"] == "snapshot_not_found"


def test_omitted_snapshot_uses_catalog_default():
    item = {
        "origin_id": "zegama_center_stops",
        "destination_id": "beasain_center_stop_pair",
        "date": "2026-09-29",
        "appointment_time": "10:00",
        "duration_minutes": 30,
    }
    result = provider.plan_visit(item)
    assert result["status"] == "ok"
    assert result["snapshot_id"] == provider.DEFAULT_SNAPSHOT_ID
    assert result["normalized_request"]["snapshot_id"] == provider.DEFAULT_SNAPSHOT_ID


@pytest.mark.parametrize("field", ["origin_id", "destination_id"])
def test_catalog_miss_is_unsupported(field):
    result = provider.plan_visit(request(**{field: "outside"}))
    assert result["status"] == "unsupported"


def test_date_outside_feed_is_unknown():
    result = provider.plan_visit(request(date="2026-10-05"))
    assert result["status"] == "unknown"
    assert result["error"]["code"] == "date_outside_feed_coverage"


def test_covered_but_unvalidated_date_is_unknown(monkeypatch, tmp_path):
    snapshot = load_fixture()
    snapshot["coverage"]["validated_dates"].remove("2026-10-03")
    install_snapshot(monkeypatch, tmp_path, snapshot)
    result = provider.plan_visit(request(date="2026-10-03"))
    assert result["status"] == "unknown"
    assert result["error"]["code"] == "date_not_validated"


def test_calendar_exception_adds_service(monkeypatch, tmp_path):
    snapshot = load_fixture()
    snapshot["calendar_dates"] = [{"service_id": "WE", "date": "20260929", "exception_type": 1}]
    install_snapshot(monkeypatch, tmp_path, snapshot)
    result = provider.plan_visit(request())
    assert result["status"] == "ok"


def test_calendar_exception_removes_only_service(monkeypatch, tmp_path):
    snapshot = load_fixture()
    snapshot["calendar_dates"] = [{"service_id": "WD", "date": "20260929", "exception_type": 2}]
    install_snapshot(monkeypatch, tmp_path, snapshot)
    result = provider.plan_visit(request())
    assert result["status"] == "no_feasible_journey"


@pytest.mark.parametrize("trip_id", ["OUT_WD_1", "BACK_WD_1"])
def test_missing_direction_is_no_feasible_after_complete_search(monkeypatch, tmp_path, trip_id):
    snapshot = load_fixture()
    snapshot["trips"] = [trip for trip in snapshot["trips"] if trip["trip_id"] != trip_id]
    install_snapshot(monkeypatch, tmp_path, snapshot)
    assert provider.plan_visit(request())["status"] == "no_feasible_journey"


def test_pickup_forbidden_blocks_outbound(monkeypatch, tmp_path):
    snapshot = load_fixture()
    snapshot["trips"][0]["stops"][0]["pickup_type"] = 1
    install_snapshot(monkeypatch, tmp_path, snapshot)
    assert provider.plan_visit(request())["status"] == "no_feasible_journey"


def test_dropoff_forbidden_blocks_outbound(monkeypatch, tmp_path):
    snapshot = load_fixture()
    snapshot["trips"][0]["stops"][1]["drop_off_type"] = 1
    install_snapshot(monkeypatch, tmp_path, snapshot)
    assert provider.plan_visit(request())["status"] == "no_feasible_journey"


def test_repeated_sequence_is_data_failure(monkeypatch, tmp_path):
    snapshot = load_fixture()
    snapshot["trips"][0]["stops"][1]["sequence"] = 1
    install_snapshot(monkeypatch, tmp_path, snapshot)
    result = provider.plan_visit(request())
    assert result["status"] == "unknown"
    assert result["error"]["code"] == "invalid_snapshot"


def test_empty_data_is_data_failure(monkeypatch, tmp_path):
    snapshot = load_fixture()
    snapshot.pop("trips")
    install_snapshot(monkeypatch, tmp_path, snapshot)
    assert provider.plan_visit(request())["status"] == "unknown"


def test_exact_arrival_margin_is_feasible():
    result = provider.plan_visit(request(appointment_time="09:50", arrival_margin_minutes=10, duration_minutes=40))
    assert result["status"] == "ok"


def test_exact_boarding_margin_is_feasible():
    result = provider.plan_visit(request(duration_minutes=37, boarding_margin_minutes=3))
    assert result["status"] == "ok"
    assert result["components_s"]["return_wait_s"] == 180


def test_insufficient_arrival_margin_is_not_feasible():
    result = provider.plan_visit(request(appointment_time="09:49", arrival_margin_minutes=10))
    assert result["status"] == "no_feasible_journey"


def test_duration_change_can_remove_return():
    result = provider.plan_visit(request(duration_minutes=500))
    assert result["status"] == "no_feasible_journey"


def test_gtfs_time_over_24_hours(monkeypatch, tmp_path):
    snapshot = load_fixture()
    snapshot["trips"][1]["stops"][0]["departure"] = "25:00:00"
    snapshot["trips"][1]["stops"][0]["arrival"] = "25:00:00"
    snapshot["trips"][1]["stops"][1]["arrival"] = "25:40:00"
    snapshot["trips"][1]["stops"][1]["departure"] = "25:40:00"
    install_snapshot(monkeypatch, tmp_path, snapshot)
    result = provider.plan_visit(request(duration_minutes=500))
    assert result["status"] == "unsupported"
    assert result["error"]["code"] == "multiday_service"


def test_disconnected_walk_is_not_hidden(monkeypatch, tmp_path):
    snapshot = load_fixture()
    snapshot["destinations"]["destination_b"]["walk_s_by_stop"].pop("B")
    snapshot["destinations"]["destination_b"].pop("walk_s", None)
    install_snapshot(monkeypatch, tmp_path, snapshot)
    result = provider.plan_visit(request())
    assert result["status"] == "unknown"
    assert result["error"]["code"] == "invalid_snapshot"
    assert "walk_s_by_stop" in result["error"]["message"]


def test_missing_origin_access_is_not_hidden(monkeypatch, tmp_path):
    snapshot = load_fixture()
    snapshot["origins"]["origin_a"]["access_s_by_stop"].pop("A")
    install_snapshot(monkeypatch, tmp_path, snapshot)
    result = provider.plan_visit(request())
    assert result["status"] == "unknown"
    assert result["error"]["code"] == "invalid_snapshot"
    assert "access_s_by_stop" in result["error"]["message"]


@pytest.mark.parametrize("count", [0, 1, 33])
def test_compare_count_limits(count):
    result = provider.compare_visits([request()] * count)
    assert result["status"] == "error"


def test_compare_preserves_non_viable_and_only_compares_compatible():
    result = provider.compare_visits([request(), request(duration_minutes=500), request(date="2026-10-03")])
    assert [item["status"] for item in result["results"]] == ["ok", "no_feasible_journey", "ok"]
    assert result["differences_s"] == []


def _to_seconds(value):
    hour, minute, second = map(int, value.split(":"))
    return hour * 3600 + minute * 60 + second


def _independent_oracle(snapshot, origin_id, appointment):
    """Oráculo pequeño: enumera filas directamente, sin llamar a choose_pair/_legs."""
    origin_stops = set(snapshot["origins"][origin_id]["stop_ids"])
    destination_stops = set(snapshot["destinations"]["beasain_center_stop_pair"]["stop_ids"])
    appointment_s = _to_seconds(appointment + ":00")
    candidates = []
    outbound = []
    inbound = []
    for trip in snapshot["trips"]:
        if trip["service_id"] != "LJ":
            continue
        for i, start in enumerate(trip["stops"]):
            for end in trip["stops"][i + 1 :]:
                if start["pickup_type"] != 0 or end["drop_off_type"] != 0:
                    continue
                leg = (trip, start, end)
                if start["stop_id"] in origin_stops and end["stop_id"] in destination_stops:
                    outbound.append(leg)
                if start["stop_id"] in destination_stops and end["stop_id"] in origin_stops:
                    inbound.append(leg)
    for out_trip, out_start, out_end in outbound:
        out_departure = _to_seconds(out_start["departure"])
        out_arrival = _to_seconds(out_end["arrival"])
        if out_arrival > appointment_s - 600:
            continue
        for back_trip, back_start, back_end in inbound:
            back_departure = _to_seconds(back_start["departure"])
            back_arrival = _to_seconds(back_end["arrival"])
            if back_departure < appointment_s + 1800 + 180:
                continue
            candidates.append((back_arrival - out_departure + 180, out_trip["trip_id"], back_trip["trip_id"]))
    return min(candidates) if candidates else None


@pytest.mark.parametrize(
    ("origin_id", "appointment"),
    [
        ("zegama_center_stops", "09:30"),
        ("zegama_center_stops", "10:00"),
        ("zegama_center_stops", "15:00"),
        ("zegama_center_stops", "17:00"),
        ("segura_herriko_plaza_stops", "09:30"),
        ("segura_herriko_plaza_stops", "13:00"),
        ("segura_herriko_plaza_stops", "19:00"),
        ("idiazabal_center_stops", "10:00"),
        ("idiazabal_center_stops", "12:00"),
        ("idiazabal_center_stops", "17:00"),
    ],
)
def test_ten_official_rows_against_independent_oracle(origin_id, appointment):
    snapshot = json.loads(OFFICIAL.read_text(encoding="utf-8"))
    expected = _independent_oracle(snapshot, origin_id, appointment)
    result = provider.plan_visit({
        "origin_id": origin_id,
        "destination_id": "beasain_center_stop_pair",
        "date": "2026-09-29",
        "appointment_time": appointment,
        "duration_minutes": 30,
        "snapshot_id": provider.DEFAULT_SNAPSHOT_ID,
    })
    assert expected is not None
    assert result["status"] == "ok"
    assert (result["itinerary"]["total_s"], result["itinerary"]["outbound"]["trip_id"], result["itinerary"]["return"]["trip_id"]) == expected


def test_capabilities_only_advertise_runtime_snapshots():
    capabilities = provider.get_capabilities()
    kinds = {item["snapshot_id"]: item["fixture_kind"] for item in capabilities["snapshots"]}
    assert kinds[provider.DEFAULT_SNAPSHOT_ID] == "OFFICIAL_DERIVED"
    assert "synthetic-contract-v1" not in kinds
