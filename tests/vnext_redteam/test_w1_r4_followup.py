"""Ensure the newer W1 pin stays distinct from the historical W2 run."""

import json
from copy import deepcopy
from pathlib import Path

import pytest

from scripts.vnext_product.w1_r4_viewmodel import viewmodel


ROOT = Path(__file__).resolve().parents[2]


def test_w1_r4_followup_is_pinned_and_limited():
    report = json.loads((ROOT / "resultados/vnext/r4_independent/w1_r4_followup.json").read_text(encoding="utf-8"))
    assert report["w1_head"] == "725a7b73ae0381092cd80edc41b8a25432d75fcd"
    assert report["provider_sha256"] == "c97842617f3077c2eec1892653361b4471a18e1c64f8127b808b9968401cb834"
    assert report["checks"] == {f"C-R3-{n:02}": "PASS" for n in range(5, 9)}
    assert report["w2_adapter"] == "NOT_RUN_INCOMPATIBLE_0.1.0"
    assert report["llm_executed"] == report["portal_executed"] == 0
    assert report["observed"]["base_total_s"] == 8591
    assert report["observed"]["return_slack_s"] == 1610


def test_w1_r4_components_reconcile_without_new_route_calculation():
    report = json.loads((ROOT / "resultados/vnext/r4_independent/w1_r4_followup.json").read_text(encoding="utf-8"))
    model = viewmodel(report["results"]["base"])
    assert model["total_s"] == 8591
    assert model["return_slack_s"] == 1610
    assert model["timeline"][0]["kind"] == "initial_wait"
    assert model["sources"][0]["source_id"] == "MOVEUSKADI_GOIERRIALDEA_3276fcae7bfa"
    bad = deepcopy(report["results"]["base"])
    bad["components"][1]["seconds"] += 1
    with pytest.raises(ValueError, match="Intervals"):
        viewmodel(bad)


def test_w1_r4_non_viable_does_not_acquire_a_fake_total():
    report = json.loads((ROOT / "resultados/vnext/r4_independent/w1_r4_followup.json").read_text(encoding="utf-8"))
    bad = deepcopy(report["results"]["base"])
    bad["status"] = "no_feasible_journey"
    with pytest.raises(ValueError, match="invented itinerary"):
        viewmodel(bad)
    bad["itinerary"] = None
    bad["components"] = None
    bad["components_s"] = None
    projected = viewmodel(bad)
    assert projected["total_s"] is None
    assert projected["return_slack_s"] is None
