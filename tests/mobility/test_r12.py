import copy
import io
import json
import zipfile

import pytest

from prototypes.ir_y_volver import provider_r6
from scripts.mobility import intake_candidate_r12 as gate


def fixtures(requests=None):
    cases = gate.acceptance_cases()
    request = cases[0]["request"]
    raw = provider_r6.plan_visit(request) if requests is None else provider_r6.compare_visits(requests)
    snapshot = json.loads((gate.ROOT / "prototypes/ir_y_volver/snapshots/official-goierrialdea-go01-r4-20260929.json").read_text(encoding="utf-8"))
    labels = {"stops": {key: value["name"] for key, value in snapshot["stops"].items()}, "routes": {"1": "GO01"}}
    requirements = json.loads((gate.DOC / "MODEL_VIEW_REQUIREMENTS_R11.json").read_text(encoding="utf-8"))["requirements"]
    raws = raw.get("results", [raw])
    scenarios = []
    for index, item in enumerate(raws):
        scenario = {**copy.deepcopy(item), "index": index, "effective_parameters": copy.deepcopy(item["normalized_request"] or {})}
        scenario["sources"] = [{key: source.get(key) for key in ("source_id", "source_role", "publisher", "url", "reference_period", "transformation")} for source in item["sources"]]
        scenario["parameter_attribution"] = [{"field": row["field"], "value": row["value"], "provider_origin": row["origin"],
                                               "w2_attribution": "provider_default" if row["origin"] == "model_default" else "tool_argument_origin_unverified"} for row in item.get("parameter_provenance", [])]
        if item["status"] == "ok":
            for direction in ("outbound", "return"):
                leg = scenario["itinerary"][direction]
                leg.update(route_label=labels["routes"][leg["route_id"]],
                           from_stop_label=labels["stops"][leg["from_stop_id"]], to_stop_label=labels["stops"][leg["to_stop_id"]])
        scenarios.append(scenario)
    view = {"mobility": {"scenarios": scenarios, "comparisons": copy.deepcopy(raw.get("comparisons", []))},
            "outcomes": [{"index": i, "status": item["status"], "error": item["error"]} for i, item in enumerate(raws)], "claims": []}
    case = dict(operation="plan" if requests is None else "compare")
    return raw, view, labels, requirements, case


def test_real_pin_and_strict_exit_statuses():
    assert gate.REAL_PIN != gate.HISTORICAL_ERRATA
    for status in ("FAIL", "NOT_RUN", "VERIFIER_ERROR"):
        assert gate.exit_code({"FINAL_STATUS": status}) == 1
    assert gate.exit_code({"FINAL_STATUS": "PASS"}) == 0
    assert gate.exit_code({"FINAL_STATUS": "NOT_RUN"}, False) == 0


def test_other_origins_and_legacy_applicability():
    originals = gate.acceptance_cases()
    for name in ("origin_idiazabal_center_stops", "origin_segura_herriko_plaza_stops", "legacy_r4_explicit"):
        request = next(row["request"] for row in originals if row["case_id"] == name)
        raw, view, labels, requirements, case = fixtures([request, request])
        findings, decisions, count = gate.validate_view(view, raw, labels, requirements, case)
        assert findings == [], (name, findings)
        assert count > 0
        if name == "legacy_r4_explicit":
            assert any("0.2.0" in row["reason"] for row in decisions)


@pytest.mark.parametrize("mutation", ["swap", "status", "params", "delta", "empty", "duplicate_truth", "contradictory_claim", "drop_failed"])
def test_comparison_mutations_are_scoped(mutation):
    base = gate.acceptance_cases()[0]["request"]
    raw, view, labels, requirements, case = fixtures([base, {**base, "duration_minutes": 30}])
    scenarios = view["mobility"]["scenarios"]
    if mutation == "swap":
        scenarios.reverse()
    elif mutation == "status":
        scenarios[1]["status"] = "no_feasible_journey"
    elif mutation == "params":
        scenarios[1]["effective_parameters"]["duration_minutes"] = 99
    elif mutation == "delta":
        view["mobility"]["comparisons"][0]["total_difference_s"] = 99
    elif mutation == "empty":
        view["mobility"]["scenarios"] = []
    elif mutation == "duplicate_truth":
        view["truth_elsewhere"] = copy.deepcopy(scenarios[1])
        scenarios[1]["itinerary"]["outbound"]["trip_id"] = "wrong"
    elif mutation == "contradictory_claim":
        view["claims"] = [{"evidence_path": "/results/1/itinerary/total_s", "value": -1}]
    else:
        view["mobility"]["scenarios"].pop()
    assert gate.validate_view(view, raw, labels, requirements, case)[0], mutation


def test_failures_and_empty_comparisons_not_vacuously_accepted():
    base = gate.acceptance_cases()[0]["request"]
    failed = next(row["request"] for row in gate.acceptance_cases() if row["case_id"] == "health_no_feasible")
    raw, view, labels, requirements, case = fixtures([base, failed])
    assert gate.validate_view(view, raw, labels, requirements, case)[0] == []
    view["mobility"]["scenarios"].pop()
    assert gate.validate_view(view, raw, labels, requirements, case)[0]
    assert gate.validate_view({"mobility": {"scenarios": []}}, {"results": [], "comparisons": []}, labels, requirements, case)[0]


def test_missing_oracle_pointer_is_verifier_error_not_w2_defect():
    raw, view, labels, requirements, case = fixtures()
    requirements.append({"requirement_id": "broken", "source_path": "/does_not_exist", "applicability": "ok"})
    records, errors = gate.evaluate({"records": [{"case_id": "x", "raw": raw}], "labels": labels},
                                   {"records": [{"case_id": "x", "envelope": {"raw_result_json": json.dumps(raw)}, "view": view}]},
                                   [{"case_id": "x", "operation": "plan"}], requirements)
    assert errors and errors[0]["owner"] == "W1"
    assert errors[0]["stage"] == "assertions"
    assert "KeyError" in errors[0]["detail"]


def test_cold_worker_has_no_parent_modules_environment_or_network(tmp_path, monkeypatch):
    (tmp_path / "tools.py").write_text("import os,sys,socket\nfrom pathlib import Path\ndef execute(*a,**k):\n assert 'prototypes.ir_y_volver.provider_r6' not in sys.modules\n assert 'PRIVATE_SENTINEL' not in os.environ\n try: socket.getaddrinfo('example.org',443)\n except RuntimeError: pass\n else: raise AssertionError('network available')\n return {'raw_result_json':None}\ndef public_result(e): return '{}'\n", encoding="utf-8")
    monkeypatch.setenv("PRIVATE_SENTINEL", "must not enter worker")
    result = gate.run_worker("candidate", tmp_path, [{"case_id": "x", "request": {}}])
    assert result["isolated"] and result["records"][0]["view"] == {}
    assert result["imports"]["tools"] == str(tmp_path / "tools.py")


def package_fixture(tmp_path, monkeypatch):
    nested = io.BytesIO()
    with zipfile.ZipFile(nested, "w") as archive:
        archive.writestr("prototypes/__init__.py", "")
    monkeypatch.setattr(gate, "R6_SHA", gate.digest(nested.getvalue()))
    contents = {"tools.py": b"pass\n", "datos_preparados/vnext/w1_r6_runtime.zip": nested.getvalue()}
    package = tmp_path / "test.zip"
    with zipfile.ZipFile(package, "w") as archive:
        for name, data in contents.items():
            archive.writestr(name, data)
    manifest = dict(sha256=gate.digest(package.read_bytes()), bytes=package.stat().st_size,
                    w1_runtime_commit_observed=gate.REAL_PIN, w1_contract="0.3.1", w1_package_sha256=gate.R6_SHA,
                    w1_source_files=[dict(path="prototypes/__init__.py", bytes=0, sha256=gate.digest(b""))],
                    members={name: dict(bytes=len(data), sha256=gate.digest(data)) for name, data in contents.items()})
    return package, manifest


def test_manifest_closure_and_actual_nested_bytes(tmp_path, monkeypatch):
    package, manifest = package_fixture(tmp_path, monkeypatch)
    assert gate.inspect(package, manifest)["compatible"]
    missing = copy.deepcopy(manifest)
    del missing["members"]["tools.py"]
    with pytest.raises(ValueError, match="close"):
        gate.inspect(package, missing)
    monkeypatch.setattr(gate, "R6_SHA", "0" * 64)
    with pytest.raises(ValueError, match="actual nested"):
        gate.inspect(package, manifest)


def test_historical_text_pin_does_not_authorize_candidate(tmp_path, monkeypatch):
    package, manifest = package_fixture(tmp_path, monkeypatch)
    manifest["w1_runtime_commit_observed"] = gate.HISTORICAL_ERRATA
    assert gate.inspect(package, manifest)["compatible"] is False


def test_nested_manifest_cannot_omit_a_runtime_member(tmp_path, monkeypatch):
    package, manifest = package_fixture(tmp_path, monkeypatch)
    manifest["w1_source_files"] = []
    with pytest.raises(ValueError, match="not closed"):
        gate.inspect(package, manifest)


def test_label_severity_is_preserved_from_existing_requirements():
    raw, view, labels, requirements, case = fixtures()
    view["mobility"]["scenarios"][0]["itinerary"]["outbound"]["to_stop_label"] = "wrong"
    findings = gate.validate_view(view, raw, labels, requirements, case)[0]
    assert len(findings) == 1
    assert findings[0]["requirement_id"] == "MV-OUT-TO-LABEL"
    assert findings[0]["severity"] == "high"


def test_invalid_candidate_raw_json_is_not_a_verifier_exception():
    raw, view, labels, requirements, case = fixtures()
    records, errors = gate.evaluate({"records": [{"case_id": "x", "raw": raw}], "labels": labels},
                                   {"records": [{"case_id": "x", "envelope": {"raw_result_json": "NaN"}, "view": view}]},
                                   [{"case_id": "x", "operation": "plan"}], requirements)
    assert not errors
    assert records[0]["raw_status"] == "FAIL"
    assert records[0]["raw_binding"] == "invalid_candidate_raw_json"


def test_source_enrichment_is_allowed_but_required_facts_stay_exact():
    raw, view, labels, requirements, case = fixtures()
    sources = view["mobility"]["scenarios"][0]["sources"]
    sources[0]["title"] = "Readable catalog metadata"
    assert not gate.validate_view(view, raw, labels, requirements, case)[0]
    sources[0]["publisher"] = "Fabricated publisher"
    assert gate.validate_view(view, raw, labels, requirements, case)[0]
    sources[0]["publisher"] = raw["sources"][0]["publisher"]
    del sources[0]["url"]
    assert gate.validate_view(view, raw, labels, requirements, case)[0]


def test_rejected_root_is_not_profiled_as_a_none_fallback(tmp_path):
    (tmp_path / "tools.py").write_text("import os\nfrom pathlib import Path\ndef _workspace_root():\n candidate=Path(os.environ['GIPUZKOA360_VNEXT_ROOT'])\n raise ValueError('invalid root')\ndef execute(*a,**k):\n try: _workspace_root()\n except ValueError: return {'status':'error','claims':[]}\ndef public_result(e): return '{}'\n", encoding="utf-8")
    invalid = tmp_path / "absent"
    result = gate.run_worker("candidate", tmp_path, [{"case_id": "x", "request": {}}], configured=invalid)
    roots = result["records"][0]["roots_observed"]
    assert roots and roots[0]["root"] == str(invalid)
    assert roots[0]["resolution"] == "rejected"


def test_freeze_inventory_comes_from_literal_editor_declaration():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("main.py", "STUDIO_CONTEXT_FILES=['asset.json']\n")
        archive.writestr("tools.py", "pass\n")
        archive.writestr("asset.json", "{}")
        archive.writestr("tests/gold.json", "{}")
    with zipfile.ZipFile(buffer) as archive:
        assert gate.declared_freeze(archive) == ["main.py", "tools.py", "asset.json"]
    broken = io.BytesIO()
    with zipfile.ZipFile(broken, "w") as archive:
        archive.writestr("main.py", "STUDIO_CONTEXT_FILES=['absent.json']\n")
        archive.writestr("tools.py", "pass\n")
    with zipfile.ZipFile(broken) as archive:
        with pytest.raises(ValueError, match="missing"):
            gate.declared_freeze(archive)


def test_unknown_normalization_is_not_a_phantom_effective_request():
    request = next(row["request"] for row in gate.acceptance_cases() if row["case_id"] == "health_profile_unsupported")
    raw, view, labels, requirements, case = fixtures([request, request])
    findings, decisions, count = gate.validate_view(view, raw, labels, requirements, case)
    assert not findings
    assert any(row.get("requirement_id") == "MV-EFFECTIVE" and row["status"] == "NOT_APPLICABLE" for row in decisions)


def test_controlled_snapshot_rejection_preserves_reason_without_claims():
    expected = {"status": "unknown", "error": {"code": "snapshot_not_found"}}
    view = {"status": "error", "claims": [], "error": {"code": "contract_violation", "message": "health:unverified_requested_snapshot", "safe_next_action": "Review snapshot"}}
    assert gate.controlled_rejection(view, expected)
    view["claims"] = [{"value": 42}]
    assert not gate.controlled_rejection(view, expected)
    view["claims"] = []
    view["error"]["message"] = "data_unavailable"
    assert not gate.controlled_rejection(view, expected)
