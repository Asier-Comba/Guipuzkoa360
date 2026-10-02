"""Structural attribution tests. Model wording is tested only in real Studio."""
import ast
import copy
import importlib.util
import io
import itertools
import json
import sys
import zipfile
import pytest
from scripts.vnext_agent import build_r22 as build
from scripts.vnext_agent.verify_r21 import run_worker

@pytest.fixture(scope="module")
def package(tmp_path_factory):
    build.build()
    root = tmp_path_factory.mktemp("r22-attribution")
    with zipfile.ZipFile(build.ZIP) as z:
        z.extractall(root)
    spec = importlib.util.spec_from_file_location("r22_attribution_test_tools", root / "tools.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return root, module

def make_claim(module, catalog, count):
    ids = ["ODE_HEALTH_CENTRES_2026", "GEOEUSKADI_MUNICIPIOS_2025", "EUSTAT_EMH_2025"][:count]
    return {"source_ids": ids, "metric_id": "nearest_distance_m",
            "source_refs": module._source_roles("nearest_distance_m", ids),
            "reference_periods": [{"source_id": sid, "period": catalog[sid]["reference_period"]} for sid in ids],
            "period": "DELIBERATELY_NONATTRIBUTABLE"}

@pytest.mark.parametrize("count", [1, 2, 3])
def test_source_attribution_join_and_all_independent_permutations(package, count):
    root, module = package
    catalog = module._catalog(root); claim = make_claim(module, catalog, count)
    expected = module.source_attributions(claim, catalog)
    assert [r["source_id"] for r in expected] == sorted(claim["source_ids"])
    for ids in itertools.permutations(claim["source_ids"]):
        for refs in itertools.permutations(claim["source_refs"]):
            for periods in itertools.permutations(claim["reference_periods"]):
                shuffled = {**claim, "source_ids": list(ids), "source_refs": list(refs), "reference_periods": list(periods)}
                assert module.source_attributions(shuffled, catalog) == expected
    by_id = {r["source_id"]: r for r in expected}
    assert by_id["ODE_HEALTH_CENTRES_2026"]["public_role"] == "registro sanitario"
    assert by_id["ODE_HEALTH_CENTRES_2026"]["period"] == "2026-09-20"
    if count >= 2:
        assert by_id["GEOEUSKADI_MUNICIPIOS_2025"]["public_role"] == "punto municipal/cartografía"
        assert by_id["GEOEUSKADI_MUNICIPIOS_2025"]["period"] == "2025-05-07"

@pytest.mark.parametrize("field", ["source_ids", "source_refs", "reference_periods"])
@pytest.mark.parametrize("mutation", ["duplicate", "missing", "extra", "not_list"])
def test_partial_or_duplicate_join_fails_closed(package, field, mutation):
    root, module = package
    catalog = module._catalog(root); claim = make_claim(module, catalog, 2)
    if mutation == "duplicate": claim[field].append(copy.deepcopy(claim[field][0]))
    if mutation == "missing": claim[field].pop()
    if mutation == "extra": claim[field].append("NOT_REAL" if field == "source_ids" else {"source_id": "NOT_REAL"})
    if mutation == "not_list": claim[field] = None
    with pytest.raises(module.ContractViolation):
        module.source_attributions(claim, catalog)

@pytest.mark.parametrize("mutation", ["swapped_dates", "swapped_roles", "unknown_role", "missing_catalog", "catalog_wrong_id", "invalid_institution"])
def test_unverified_pair_rejected(package, mutation):
    root, module = package
    catalog = copy.deepcopy(module._catalog(root)); claim = make_claim(module, catalog, 2)
    if mutation == "swapped_dates":
        a, b = claim["reference_periods"]; a["period"], b["period"] = b["period"], a["period"]
    if mutation == "swapped_roles":
        a, b = claim["source_refs"]; a["role"], b["role"] = b["role"], a["role"]
    if mutation == "unknown_role": claim["source_refs"][0]["role"] = "made_up"
    if mutation == "missing_catalog": catalog.pop(claim["source_ids"][0])
    if mutation == "catalog_wrong_id": catalog[claim["source_ids"][0]]["source_id"] = "NOT_REAL"
    if mutation == "invalid_institution": catalog[claim["source_ids"][0]]["institution"] = {}
    with pytest.raises(module.ContractViolation):
        module.source_attributions(claim, catalog)

@pytest.fixture(scope="module")
def observed(package):
    root, _ = package
    rows = [{"id": category + ":" + town, "tool": "analizar_acceso_municipios",
             "arguments": dict(categoria_servicio=category, umbral_km=1, municipios=[town])}
            for category in ("primary_care", "hospital", "mental_health", "other_health")
            for town in ("Getaria", "Aduna", "Eibar", "Tolosa")]
    rows += [{"id": "health", "tool": "plan_visit", "arguments": dict(origin_id="zegama_center_stops", destination_id="beasain_official_centre_anchor", date="2026-09-29", appointment_time="09:30", duration_minutes=20)}]
    return run_worker(root, rows)

@pytest.mark.parametrize("category", ["primary_care", "hospital", "mental_health", "other_health"])
@pytest.mark.parametrize("town", ["Getaria", "Aduna", "Eibar", "Tolosa"])
def test_explicit_source_question_data_generalizes(observed, category, town):
    record = observed["records"][category + ":" + town]
    assert record["status"] == "valid"
    claim = next(c for c in record["claims"] if c["metric_id"] == "nearest_distance_m")
    pairs = {r["public_role"]: r for r in claim["source_attributions"]}
    assert pairs["registro sanitario"]["period"] == "2026-09-20"
    assert pairs["punto municipal/cartografía"]["period"] == "2025-05-07"
    assert pairs["registro sanitario"]["institution"] == "Gobierno Vasco - Departamento de Salud"
    assert pairs["punto municipal/cartografía"]["institution"] == "Gobierno Vasco - geoEuskadi"
    if town == "Getaria" and category == "mental_health": assert claim["value"] == 2913.3

def test_health_all_roles_are_closed_and_dates_not_model_versions(observed):
    record = observed["records"]["health"]
    assert record["status"] == "valid", record
    roles = {r["role"] for c in record["claims"] for r in c["source_attributions"]}
    assert {"official_schedule", "official_health_registry", "open_network", "model_parameter", "agent_or_user_parameter", "derived_metric"} <= roles
    assert all(r["period"] != "R5.1" for c in record["claims"] for r in c["source_attributions"])

def test_closed_role_map_covers_entire_existing_catalog(package):
    root, module = package
    catalog = module._catalog(root)
    for metric in ("population_total", "primary_care_per_10000_65_plus"):
        for row in module._source_roles(metric, list(catalog)):
            assert row["role"] in module._PUBLIC_SOURCE_ROLES
    assert module._PUBLIC_SOURCE_ROLES["denominator"] == "demografía usada como denominador"
    assert module._PUBLIC_SOURCE_ROLES["numerator"] == "registro sanitario usado como numerador"

def test_no_unasked_source_dates_contract_and_no_prompt_conflict():
    node = next(n for n in ast.parse((build.PORTAL / "main.py").read_text(encoding="utf-8")).body if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", None) == "SYSTEM_PROMPT")
    prompt = ast.literal_eval(node.value)
    assert build.ATTRIBUTION_PRINCIPLE in prompt and build.COMMUNICATION in prompt
    assert build.OLD_COMMUNICATION not in prompt
    assert "Getaria" not in prompt and "2026-09-20" not in prompt and "2025-05-07" not in prompt
    assert len(prompt) < 6000

def test_only_two_members_change_double_build():
    build.build(); before = build.ZIP.read_bytes(), build.MANIFEST.read_bytes()
    build.build(); assert before == (build.ZIP.read_bytes(), build.MANIFEST.read_bytes())
    with zipfile.ZipFile(io.BytesIO(build.blob(build.BASE_ZIP))) as old, zipfile.ZipFile(build.ZIP) as new:
        assert old.namelist() == new.namelist()
        assert [n for n in old.namelist() if old.read(n) != new.read(n)] == ["main.py", "tools.py"]
        assert new.read("tools.py").startswith(old.read("tools.py"))
        old_tree, new_tree = (ast.parse(z.read("main.py")) for z in (old, new))
        for tree in (old_tree, new_tree):
            tree.body = [n for n in tree.body if not (isinstance(n, ast.Assign) and getattr(n.targets[0], "id", None) == "SYSTEM_PROMPT")]
        assert ast.dump(old_tree) == ast.dump(new_tree)
    meta = json.loads(build.MANIFEST.read_bytes())
    assert len(meta["context_paths"]) == 15 and not meta["context_assets_changed"]

def test_no_partial_public_claims_on_attribution_failure(package, monkeypatch):
    root, module = package
    monkeypatch.setattr(module, "source_attributions", lambda *args: (_ for _ in ()).throw(module.ContractViolation("TEST_ONLY")))
    view = module.strict_loads(module.public_call("analizar_acceso_municipios", dict(categoria_servicio="mental_health", umbral_km=1, municipios=["Getaria"]), "TEST_ONLY", root=root))
    assert view["status"] == "error" and view["claims"] == []
    assert view["request_id"] == "TEST_ONLY" and view["capability_id"] == "analizar_acceso_municipios"
    assert view["error"]["code"] == "source_attribution_failure"
    assert view["error"]["error_class"] == "contract_or_data_failure" and view["error"]["retry_same_arguments"] is False
