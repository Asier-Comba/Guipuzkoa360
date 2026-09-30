import copy
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

from prototypes.ir_y_volver import provider_r6
from scripts.mobility import build_r11
from scripts.mobility import intake_candidate_r11 as intake


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/vnext/w1"


def load(name):
    return json.loads((DOC / name).read_text(encoding="utf-8"))


def canonical_raw(request=None):
    return provider_r6.plan_visit(request or build_r11.BASE)


def complete_view(raw, request=None):
    request = request or build_r11.BASE
    base = json.loads((ROOT / "prototypes/ir_y_volver/snapshots/official-goierrialdea-go01-r4-20260929.json").read_text(encoding="utf-8"))
    labels = {key: base["stops"][key]["name"] for key in ("8305", "7219", "7218", "8309")}
    defaults = [row["field"] for row in raw["parameter_provenance"] if row["origin"] == "model_default"]
    return {
        "status": raw["status"], "projection": copy.deepcopy(raw), "route_label": "GO01",
        "stop_labels": {"outbound": {"from_stop_label": labels["8305"], "to_stop_label": labels["7219"]},
                        "return": {"from_stop_label": labels["7218"], "to_stop_label": labels["8309"]}},
        "timepoint_note": "Los timepoint=0 son horarios programados aproximados/interpolados.",
        "normalized_input": {"arguments": copy.deepcopy(request)},
        "effective_request": {"parameters": copy.deepcopy(raw["normalized_request"]), "defaults_applied": defaults},
    }


def requirements():
    return load("MODEL_VIEW_REQUIREMENTS_R11.json")["requirements"]


def remove_timepoint_wording(value):
    if type(value) is dict:
        for key, child in list(value.items()):
            value[key] = remove_timepoint_wording(child)
    elif type(value) is list:
        for index, child in enumerate(value):
            value[index] = remove_timepoint_wording(child)
    elif type(value) is str:
        return value.replace("aproximados", "programados").replace("approximate", "scheduled").replace("interpolados", "programados")
    return value


def test_r11_generator_is_reproducible_and_runtime_frozen(tmp_path):
    before = hashlib.sha256((ROOT / "prototypes/ir_y_volver/provider_r6.py").read_bytes()).hexdigest()
    first = build_r11.build()
    one = (DOC / "integration_r11/W1_HANDSHAKE_R11.json").read_bytes()
    second = build_r11.build()
    assert one == (DOC / "integration_r11/W1_HANDSHAKE_R11.json").read_bytes()
    assert first == second
    assert before == "c9fe7e4c8078ba7f9bf2eb2a51e050b729d9f01e6021dbcc6909f951d2e936e8"


def test_unknown_summary_is_generic_and_detailed_mapping_remains_bound():
    handshake = load("integration_r11/W1_HANDSHAKE_R11.json")
    unknown = next(row for row in handshake["status_semantics"] if row["status"] == "unknown")
    text = unknown["meaning"].casefold()
    assert "error.code" in text
    assert "fecha no está validada" not in text
    assert handshake["status_error_semantics_ref"]["path"].endswith("STATUS_ERROR_SEMANTICS_R10.json")


def test_oracle_contract_and_public_gold_are_non_holdout():
    oracle = load("MODEL_VIEW_REQUIREMENTS_R11.json")
    assert len(oracle["requirements"]) >= 35
    required = {"requirement_id", "applicability", "source_path", "semantic_fact", "allowed_projection", "forbidden_omission", "severity"}
    assert all(required <= set(row) for row in oracle["requirements"])
    gold = load("DETERMINISTIC_GOLD_R11.json")
    assert gold["classification"] == "DETERMINISTIC_PUBLIC_GOLD_NOT_HOLDOUT"
    assert gold["contains_final_answer_wording"] is False
    assert len(gold["cases"]) == 6


def test_complete_model_view_contains_required_semantic_facts():
    raw = canonical_raw()
    assert intake.validate_model_view(complete_view(raw), raw, requirements()) == []


def test_identity_and_semantic_mutations_fail_even_when_total_is_correct():
    raw = canonical_raw()
    mutations = [
        ("trip_id", lambda view: view["projection"]["itinerary"]["outbound"].__setitem__("trip_id", "MUTATED")),
        ("route_label", lambda view: (view.__setitem__("route_label", "MUTATED"),
                                      view["projection"]["sources"][0].__setitem__("transformation", "route MUTATED"))),
        ("stop_id", lambda view: view["projection"]["itinerary"]["outbound"].__setitem__("from_stop_id", "MUTATED")),
        ("stop_label", lambda view: view["stop_labels"]["outbound"].__setitem__("from_stop_label", "MUTATED")),
        ("departure", lambda view: view["projection"]["itinerary"]["outbound"].__setitem__("departure_time", "00:00:00")),
        ("arrival", lambda view: view["projection"]["itinerary"]["return"].__setitem__("arrival_time", "00:00:00")),
        ("centre_id", lambda view: view["projection"]["health_destination"].__setitem__("centre_id", "MUTATED")),
        ("centre_label", lambda view: view["projection"]["health_destination"].__setitem__("name", "MUTATED")),
        ("entrance", lambda view: view["projection"]["health_destination"].__setitem__("entrance_verified", True)),
        ("modelled", lambda view: view["projection"]["health_destination"].__setitem__("modelled_access", False)),
        ("source", lambda view: view["projection"]["sources"][0].__setitem__("source_id", "MUTATED")),
        ("timepoint", remove_timepoint_wording),
    ]
    for name, mutate in mutations:
        view = complete_view(raw)
        expected_total = view["projection"]["itinerary"]["total_s"]
        mutate(view)
        assert view["projection"]["itinerary"]["total_s"] == expected_total
        gaps = intake.classify_mutated_view(view, raw, requirements())
        assert gaps, name


def test_caller_provenance_defaults_explicit_and_changed_followup():
    requests = [build_r11.BASE, {**build_r11.BASE, "boarding_margin_minutes": 3},
                {**build_r11.BASE, "boarding_margin_minutes": 8},
                {**build_r11.BASE, "boarding_margin_minutes": 8, "appointment_time": "10:15"}]
    for request in requests:
        raw = canonical_raw(request)
        assert intake.validate_caller_provenance(complete_view(raw, request), raw) == []
    bad = complete_view(canonical_raw())
    bad["effective_request"]["defaults_applied"].remove("boarding_margin_minutes")
    assert intake.validate_caller_provenance(bad, canonical_raw())


def make_old_candidate(tmp_path):
    package = tmp_path / "candidate.zip"
    members = {"tools.py": "def public_result(x): return '{}'\n", "mobility_adapter.py": "pass\n"}
    with zipfile.ZipFile(package, "w") as archive:
        for name, value in members.items():
            archive.writestr(name, value)
    raw = package.read_bytes()
    manifest = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "w1_pin": "old", "w1_contract": "0.2.0",
                "members": {name: {"bytes": len(value.encode()), "sha256": hashlib.sha256(value.encode()).hexdigest()} for name, value in members.items()}}
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return package, path


def test_diagnostic_and_strict_not_run_exit_codes(tmp_path):
    package, manifest = make_old_candidate(tmp_path)
    report = intake.intake(package, manifest, intake.RUNTIME_PIN, strict=False)
    assert report["FINAL_STATUS"] == "NOT_RUN"
    assert intake.exit_code(report, False) == 0
    assert intake.exit_code(report, True) != 0


def test_package_failure_categories_and_distribution_policy(tmp_path):
    package, manifest_path = make_old_candidate(tmp_path)
    manifest = json.loads(manifest_path.read_text())
    manifest["sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    report = intake.intake(package, manifest_path, intake.RUNTIME_PIN, strict=False)
    assert report["findings"][0]["category"] == "PACKAGE_INTEGRITY_FAILURE"
    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr("tools.py", "def public_result(x): return '{}'\n")
        archive.writestr("mobility_adapter.py", "pass\n")
        archive.writestr("raw/osakidetza.html", "private raw")
    raw = package.read_bytes()
    manifest = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "w1_pin": "old", "w1_contract": "0.2.0", "members": {}}
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    report = intake.intake(package, manifest_path, intake.RUNTIME_PIN, strict=False)
    assert any(row["category"] == "DISTRIBUTION_POLICY_FAILURE" for row in report["findings"])


def test_failure_catalog_is_complete_and_structured():
    required = {"PACKAGE_INTEGRITY_FAILURE", "MANIFEST_FAILURE", "INCOMPATIBLE_W1_PIN", "ADAPTER_IMPORT_FAILURE",
                "PRODUCER_ADAPTER_PARITY_FAILURE", "MODEL_VIEW_MISSING", "MODEL_VIEW_WRONG_VALUE",
                "MODEL_VIEW_WRONG_SEMANTICS", "DISTRIBUTION_POLICY_FAILURE", "NOT_RUN"}
    assert required == set(intake.FAILURE_CATALOG)
    assert all(len(value) == 4 for value in intake.FAILURE_CATALOG.values())


def test_validated_invalid_request_reason_is_an_allowed_failure_projection():
    raw = provider_r6.plan_visit({**build_r11.BASE, "duration_minutes": "20"})
    view = {"status": "error", "error": {"code": "contract_violation", "message": "health:invalid_duration",
                                                   "safe_next_action": "Revise el valor."}}
    assert intake.safe_failure_projection(view, raw) is True
