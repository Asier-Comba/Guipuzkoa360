"""Real W1 0.2.0 blobs by published SHA, assembled outside every checkout."""

from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from agentes.gipuzkoa360_vnext import mobility_adapter as adapter, tools


ROOT = Path(__file__).resolve().parents[2]
PIN = adapter.W1_PIN
MANIFEST_PATH = "docs/vnext/w1/RUNTIME_MANIFEST_R4.json"


def _blob(path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{PIN}:{path}"], cwd=ROOT)


@pytest.fixture(scope="module")
def provider(tmp_path_factory):
    directory = tmp_path_factory.mktemp("w1_pinned_020")
    manifest = json.loads(_blob(MANIFEST_PATH))
    for item in manifest["files"]:
        destination = directory / item["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(_blob(item["path"]))
        assert tools.digest(destination.read_bytes()) == item["sha256"]
    prior_modules = {name: module for name, module in sys.modules.items() if name == "prototypes" or name.startswith("prototypes.")}
    for name in prior_modules:
        del sys.modules[name]
    sys.path.insert(0, str(directory))
    try:
        module = importlib.import_module("prototypes.ir_y_volver.provider")
        yield module
    finally:
        sys.path.remove(str(directory))
        for name in list(sys.modules):
            if name == "prototypes" or name.startswith("prototypes."):
                del sys.modules[name]
        sys.modules.update(prior_modules)


def request(**changes):
    value = {
        "origin_id": "zegama_center_stops", "destination_id": "beasain_center_stop_pair",
        "date": "2026-09-29", "appointment_time": "09:30", "duration_minutes": 30,
        "snapshot_id": adapter.SNAPSHOT_ID,
    }
    value.update(changes)
    return value


def test_published_w1_020_is_pinned_and_role_attributed(provider):
    item = adapter.consume_plan_visit(provider, request(), "TEST_W1_R4")
    assert item["status"] == "valid"
    raw = tools.strict_loads(item["raw_result_json"])
    assert raw["schema_version"] == "0.2.0"
    assert raw["scope"] == adapter.SCOPE
    independent = json.loads(_blob("docs/vnext/w1/REAL_CASES_R4.json"))["cases"][0]["independent_raw_expected"]
    assert raw["itinerary"]["total_s"] == independent["total_s"] == 8591
    assert raw["itinerary"]["total_s"] == sum(raw["components_s"].values())
    assert item["versions"]["data_sha256"] == adapter.SNAPSHOT_SHA256
    assert item["versions"]["code_sha256"] == adapter.PROVIDER_SHA256
    assert {ref["role"] for ref in next(claim for claim in item["claims"] if claim["metric_id"] == "appointment_s")["source_refs"]} == {"user_parameter"}
    assert {ref["role"] for ref in next(claim for claim in item["claims"] if claim["metric_id"] == "outbound_vehicle_s")["source_refs"]} == {"official_schedule"}
    assert {ref["role"] for ref in next(claim for claim in item["claims"] if claim["metric_id"] == "initial_wait_s")["source_refs"]} == {"modelling_assumption"}
    assert "appointment_time" in item["effective_request"]["parameters"]


def test_explicit_margin_is_user_parameter(provider):
    item = adapter.consume_plan_visit(provider, request(arrival_margin_minutes=15, boarding_margin_minutes=8), "TEST_W1_MARGINS")
    assert item["status"] == "valid"
    raw = tools.strict_loads(item["raw_result_json"])
    assert raw["components_s"]["initial_wait_s"] == 480
    assert {ref["role"] for ref in next(claim for claim in item["claims"] if claim["metric_id"] == "initial_wait_s")["source_refs"]} == {"user_parameter"}


def test_nonviable_and_unknown_remain_distinct(provider):
    unsupported = adapter.consume_plan_visit(provider, request(origin_id="TEST_UNKNOWN_STOP"), "TEST_W1_UNSUPPORTED")
    unknown = adapter.consume_plan_visit(provider, request(date="2026-09-30"), "TEST_W1_UNKNOWN")
    assert unsupported["outcomes"][0]["status"] == "unsupported"
    assert unknown["outcomes"][0]["status"] == "unknown"
    assert unsupported["claims"] == unknown["claims"] == []
    assert unknown["error"]["origin"] == "data"


def test_comparison_is_common_evidence_and_keeps_every_outcome(provider):
    item = adapter.consume_compare_visits(provider, [request(), request(appointment_time="10:30"), request(origin_id="TEST_UNKNOWN_STOP")], "TEST_W1_COMPARE")
    assert item["schema_version"] == tools.VERSION
    assert item["capability_id"] == "plan_visit"
    assert [part["status"] for part in item["outcomes"]] == ["ok", "ok", "unsupported"]
    raw = tools.strict_loads(item["raw_result_json"])
    assert len(raw["comparisons"]) == 3
    assert all(pair["comparability"] == "not_comparable" for pair in raw["comparisons"] if pair["right_index"] == 2)


@pytest.mark.parametrize("field,change", [
    ("appointment_time", "09:30:59"),
    ("arrival_margin_minutes", 1),
    ("boarding_margin_minutes", 1),
    ("walking_profile_id", "TEST_DECORATIVE"),
])
def test_effective_parameters_cannot_change_silently(provider, monkeypatch, field, change):
    original = provider.plan_visit

    def tampered(value):
        result = original(value)
        result["normalized_request"][field] = change
        return result

    monkeypatch.setattr(provider, "plan_visit", tampered)
    with pytest.raises(tools.ContractViolation, match="request_mismatch"):
        adapter.consume_plan_visit(provider, request(), "TEST_W1_TAMPER")


def test_requested_unverified_snapshot_and_changed_blob_are_rejected(provider, monkeypatch):
    with pytest.raises(tools.ContractViolation, match="unverified_requested_snapshot"):
        adapter.consume_plan_visit(provider, request(snapshot_id="TEST_OTHER"), "TEST_W1_OTHER")
    monkeypatch.setattr(adapter, "PROVIDER_SHA256", "0" * 64)
    with pytest.raises(tools.ContractViolation, match="unverified_pinned_blob"):
        adapter.consume_plan_visit(provider, request(), "TEST_W1_CHANGED")


def test_incompatible_provider_version_is_rejected(provider, monkeypatch):
    monkeypatch.setattr(adapter, "W1_VERSION", "0.3.0")
    with pytest.raises(tools.ContractViolation, match="provider_capability_not_verified"):
        adapter.consume_plan_visit(provider, request(), "TEST_W1_VERSION")


def test_false_comparable_difference_is_rejected(provider, monkeypatch):
    original = provider.compare_visits

    def tampered(requests):
        result = original(requests)
        result["differences_s"].append({"left_index": 0, "right_index": 1, "total_difference_s": 0})
        return result

    monkeypatch.setattr(provider, "compare_visits", tampered)
    with pytest.raises(tools.ContractViolation, match="invalid_difference"):
        adapter.consume_compare_visits(provider, [request(), request(origin_id="TEST_UNKNOWN_STOP")], "TEST_W1_FALSE_DELTA")
