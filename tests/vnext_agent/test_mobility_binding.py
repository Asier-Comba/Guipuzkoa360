"""Read-only binding tests against the published W1 commit, not a substitute provider."""

from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest

from agentes.gipuzkoa360_vnext import mobility_adapter, tools


ROOT = Path(__file__).resolve().parents[2]
W1_SHA = "c68eb5c55dec72a267b7435b4c364049f6eab408"
PROVIDER_PATH = "prototypes/ir_y_volver/provider.py"
SNAPSHOT_PATH = f"prototypes/ir_y_volver/snapshots/{mobility_adapter.SNAPSHOT_ID}.json"


def _git_blob(path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{W1_SHA}:{path}"], cwd=ROOT)


@pytest.fixture(scope="module")
def provider(tmp_path_factory):
    directory = tmp_path_factory.mktemp("published_w1")
    source = directory / "provider.py"
    source.write_bytes(_git_blob(PROVIDER_PATH))
    snapshots = directory / "snapshots"
    snapshots.mkdir()
    (snapshots / f"{mobility_adapter.SNAPSHOT_ID}.json").write_bytes(_git_blob(SNAPSHOT_PATH))
    spec = importlib.util.spec_from_file_location("published_w1_provider", source)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _request(**changes):
    result = {
        "origin_id": "zegama_center_stops", "destination_id": "beasain_center_stop_pair",
        "date": "2026-09-29", "appointment_time": "09:30", "duration_minutes": 30,
        "snapshot_id": mobility_adapter.SNAPSHOT_ID,
    }
    result.update(changes)
    return result


def test_published_w1_binding_preserves_provenance_and_sum(provider):
    item = mobility_adapter.consume_plan_visit(provider, _request(), "TEST_W1_BINDING")
    assert item["status"] == "valid"
    raw = tools.strict_loads(item["raw_result_json"])
    assert raw["status"] == "ok"
    assert raw["itinerary"]["total_s"] == sum(raw["components_s"].values())
    assert item["versions"]["data_sha256"] == mobility_adapter.SNAPSHOT_SHA256
    assert all(claim["source_ids"] == [mobility_adapter.SOURCE_ID] for claim in item["claims"])


def test_published_w1_unsupported_and_comparison_preserve_nonviable(provider):
    good = _request()
    bad = _request(origin_id="TEST_UNKNOWN_STOP")
    item = mobility_adapter.consume_plan_visit(provider, bad, "TEST_W1_UNSUPPORTED")
    assert item["status"] == "unsupported" and not item["claims"]
    compared = mobility_adapter.consume_compare_visits(provider, [good, bad])
    assert [part["status"] for part in compared["results"]] == ["ok", "unsupported"]


def test_changed_snapshot_is_rejected(provider, monkeypatch):
    monkeypatch.setattr(mobility_adapter, "SNAPSHOT_SHA256", "0" * 64)
    with pytest.raises(tools.ContractViolation, match="unverified_snapshot"):
        mobility_adapter.consume_plan_visit(provider, _request(), "TEST_W1_CHANGED")


def test_requested_unverified_snapshot_is_rejected(provider):
    with pytest.raises(tools.ContractViolation, match="unverified_requested_snapshot"):
        mobility_adapter.consume_plan_visit(provider, _request(snapshot_id="TEST_OTHER"), "TEST_W1_OTHER")
