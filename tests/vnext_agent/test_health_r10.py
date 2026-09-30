"""Independent W2 boundary checks for the published W1 R6 package."""

from __future__ import annotations

import hashlib
import copy
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from agentes.gipuzkoa360_vnext import health_adapter, tools
from scripts.vnext_agent.build_r14_binding import MANIFEST, ROOT, ZIP, build as build_package
from scripts.vnext_agent.w1_r6_bundle import published_runtime


def _isolated(tmp_path: Path, operation: str, payload: dict) -> dict:
    with zipfile.ZipFile(ZIP) as archive:
        archive.extractall(tmp_path)
    script = """import json,socket,sys
socket.socket=lambda *a,**k: (_ for _ in ()).throw(RuntimeError('network forbidden'))
import main
data=json.loads(sys.stdin.read())
if data['operation']=='plan_visit':
    request=data['payload']['request']
    print(main._run('plan_visit', {'request':request}) if isinstance(request,list) else main.plan_visit(**request))
else:
    print(getattr(main,data['operation'])(**data['payload']))
"""
    environment = {**os.environ, "PYTHONPATH": "", "PYTHONNOUSERSITE": "1", "GIPUZKOA360_VNEXT_ROOT": str(tmp_path)}
    run = subprocess.run([sys.executable, "-c", script], input=json.dumps({"operation": operation, "payload": payload}), text=True, cwd=tmp_path, env=environment, capture_output=True, check=True)
    return json.loads(run.stdout)


def test_health_provider_and_model_view(tmp_path):
    build_package()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert hashlib.sha256(ZIP.read_bytes()).hexdigest() == manifest["sha256"]
    assert "mobility_adapter.py" not in manifest["members"]
    assert "prototypes/ir_y_volver/provider_r6.py" in {item["path"] for item in manifest["w1_source_files"]}
    directory = tmp_path / "isolated"
    directory.mkdir()
    catalog = _isolated(directory, "consultar_capacidades", {"pregunta_o_dimension": "plan_visit"})
    assert catalog["status"] == "valid", catalog
    assert catalog["mobility_catalog"]["destination"]["destination_id"] == "beasain_official_centre_anchor"
    assert catalog["mobility_catalog"]["comparison_size"]["maximum"] == 4
    request = {"origin_id": "zegama_center_stops", "destination_id": "beasain_official_centre_anchor", "date": "2026-09-29", "appointment_time": "09:45", "duration_minutes": 20}
    response = _isolated(directory, "plan_visit", {"request": request})
    assert response["status"] == "valid", response
    view = response["mobility"]["scenarios"][0]
    assert view["status"] == "ok"
    assert view["itinerary"]["total_s"] == 8591
    assert view["itinerary"]["outbound"]["trip_id"] == "1_101_LJ_31500"
    assert view["itinerary"]["return"]["trip_id"] == "1_106_LJ_37200"
    assert view["health_destination"]["entrance_verified"] is False
    assert view["health_destination"]["address_conflict"]
    assert any(item["field"] == "arrival_margin_minutes" and item["w2_attribution"] == "provider_default" for item in view["parameter_attribution"])
    assert "raw_result_json" not in response
    source = _isolated(directory, "consultar_fuente", {"source_id": "GTFS"})
    assert source["status"] == "valid" and source["source_metadata"][0]["url"].startswith("https://")


def test_published_w1_fourteen_cases_through_w2_boundary(tmp_path):
    build_package()
    directory = tmp_path / "conformance"
    directory.mkdir()
    with zipfile.ZipFile(ZIP) as archive:
        fixture = json.loads(archive.read("datos_preparados/vnext/w1_conformance_r7.json"))
    assert len(fixture["cases"]) == 14
    for case in fixture["cases"]:
        request = case.get("request", case.get("requests"))
        response = _isolated(directory, "plan_visit", {"request": request})
        expected = case["expected"]["expected_status"]
        if case["case_id"] == "invalid_structural":
            assert response["status"] == "error", (case["case_id"], response)
        elif isinstance(request, list):
            assert response["status"] == "valid", (case["case_id"], response)
            assert len(response["outcomes"]) == len(request)
        else:
            assert response["outcomes"][0]["status"] == expected, (case["case_id"], response)
            assert response["mobility"]["scenarios"][0]["status"] == expected


def test_health_rejects_tampered_identity_sources_times_and_entrance(tmp_path, monkeypatch):
    runtime, _ = published_runtime()
    with zipfile.ZipFile(__import__("io").BytesIO(runtime)) as archive:
        archive.extractall(tmp_path)
    for module_name in list(sys.modules):
        if module_name == "prototypes" or module_name.startswith("prototypes."):
            monkeypatch.delitem(sys.modules, module_name)
    monkeypatch.syspath_prepend(str(tmp_path))
    from prototypes.ir_y_volver import provider_r6

    request = {"origin_id": "zegama_center_stops", "destination_id": "beasain_official_centre_anchor", "date": "2026-09-29", "appointment_time": "09:45", "duration_minutes": 20}
    catalog, health, r4 = health_adapter._pinned(provider_r6)
    good = provider_r6.plan_visit(request)
    assert health_adapter._validate_health(good, request, catalog, health, r4, provider_r6, ROOT)["status"] == "ok"
    mutations = [
        ("trip", lambda raw: raw["itinerary"]["outbound"].update(trip_id="invented")),
        ("stop", lambda raw: raw["itinerary"]["return"].update(to_stop_id="invented")),
        ("time", lambda raw: raw["itinerary"]["outbound"].update(departure_time="08:47:38")),
        ("source", lambda raw: raw["sources"][0].update(url="https://invalid.example/")),
        ("default", lambda raw: raw["normalized_request"].update(arrival_margin_minutes=11)),
        ("entrance", lambda raw: raw["health_destination"].update(entrance_verified=True)),
    ]
    for name, mutate in mutations:
        changed = copy.deepcopy(good)
        mutate(changed)
        with pytest.raises(tools.ContractViolation, match="health:"):
            health_adapter._validate_health(changed, request, catalog, health, r4, provider_r6, ROOT)


def test_mobility_source_references_are_legible(tmp_path):
    build_package()
    directory = tmp_path / "sources"
    directory.mkdir()
    for source_id in ("GTFS", "HEALTH_REGISTRY", "HEALTH_PAGE", "PADI_2026", "OSM", "MODEL", "USER", "MODEL_DEFAULTS", "DERIVED"):
        result = _isolated(directory, "consultar_fuente", {"source_id": source_id})
        assert result["status"] == "valid", (source_id, result)
        metadata = result["source_metadata"][0]
        assert metadata["source_id"] == source_id and metadata["title"] and metadata["reference_period"]
        if source_id in {"USER", "MODEL_DEFAULTS", "DERIVED", "MODEL"}:
            assert not metadata["url"] or source_id == "MODEL"


def test_parameter_authorship_comparison_limit_and_unknown_date(tmp_path):
    build_package()
    directory = tmp_path / "provenance"
    directory.mkdir()
    base = {"origin_id": "zegama_center_stops", "destination_id": "beasain_official_centre_anchor", "date": "2026-09-29", "appointment_time": "09:45", "duration_minutes": 20}
    omitted = _isolated(directory, "plan_visit", {"request": base})
    explicit = _isolated(directory, "plan_visit", {"request": {**base, "arrival_margin_minutes": 10}})
    for result, expected in ((omitted, "provider_default"), (explicit, "tool_argument_origin_unverified")):
        attribution = {item["field"]: item for item in result["mobility"]["scenarios"][0]["parameter_attribution"]}
        assert attribution["arrival_margin_minutes"]["w2_attribution"] == expected
        assert result["mobility"]["scenarios"][0]["effective_parameters"]["arrival_margin_minutes"] == 10
    later = _isolated(directory, "plan_visit", {"request": {**base, "arrival_margin_minutes": 15}})
    assert later["mobility"]["scenarios"][0]["effective_parameters"]["arrival_margin_minutes"] == 15
    assert any(item["field"] == "arrival_margin_minutes" and item["w2_attribution"] == "tool_argument_origin_unverified" for item in later["mobility"]["scenarios"][0]["parameter_attribution"])
    unknown = _isolated(directory, "plan_visit", {"request": {**base, "date": "2026-09-30"}})
    assert unknown["status"] == "error" and unknown["outcomes"][0]["status"] == "unknown" and not unknown["claims"]
    four = _isolated(directory, "plan_visit", {"request": [{**base, "appointment_time": hour} for hour in ("09:15", "09:30", "09:45", "10:00")]})
    assert four["status"] == "valid" and len(four["mobility"]["scenarios"]) == 4
    five = _isolated(directory, "plan_visit", {"request": [base] * 5})
    assert five["status"] == "error" and not five["claims"]
