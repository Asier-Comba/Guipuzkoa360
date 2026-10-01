"""Permanent tests of the exact public package, no model/holdout calls."""
import ast
import csv
import inspect
import io
import json
import os
import subprocess
import sys
import zipfile

import pytest

from scripts.vnext_agent.build_r17 import BASE_ZIP, MANIFEST, PORTAL, ZIP, blob, build
from scripts.vnext_agent import verify_r15
from scripts.vnext_agent.verify_r17 import public_language


@pytest.fixture(scope="module")
def generated(tmp_path_factory):
    build()
    directory = tmp_path_factory.mktemp("r17")
    with zipfile.ZipFile(ZIP) as archive:
        archive.extractall(directory)
    return directory


@pytest.fixture(scope="module")
def observed(generated):
    cases = [
        {"id": "summary", "tool": "obtener_resumen_territorial", "arguments": {"municipio": "Aduna"}, "keep_view": True},
        {"id": "engine", "tool": "obtener_resumen_territorial", "arguments": {"municipio": "Aduna", "periodo": "2025-01-01"}, "route": "internal", "keep_view": True},
        {"id": "cap", "tool": "consultar_capacidades", "arguments": {}, "keep_view": True},
        {"id": "source", "tool": "consultar_fuente", "arguments": {"source_id": "EUSTAT_EMH_2025"}, "keep_view": True},
        *[{"id": "extra:" + str(i), "tool": "obtener_resumen_territorial", "arguments": {"municipio": "Aduna", "periodo": p}} for i, p in enumerate(("", None, "2025-01-01"))],
    ]
    return verify_r15.run_worker(generated, cases)


def test_summary_signature_exactly_one_required_string(observed):
    sig = observed["signatures"]["obtener_resumen_territorial"]
    assert sig["fields"] == sig["required"] == ["municipio"]
    assert sig["types"] == {"municipio": "<class 'str'>"} and sig["defaults"] == {}


@pytest.mark.parametrize("index", range(3))
def test_public_extra_period_rejected_before_execution(observed, index):
    record = observed["records"]["extra:" + str(index)]
    assert record["status"] == "binding_rejected" and record["execute_calls"] == 0 and record["claims"] == 0


def test_engine_explicit_period_raw_and_claim_parity(observed):
    a, b = (observed["records"][key] for key in ("summary", "engine"))
    assert a["status"] == b["status"] == "valid"
    assert a["raw_sha256"] == b["raw_sha256"] and a["view"]["claims"] == b["view"]["claims"]
    assert "periodo" not in a["view"]["normalized_input"]["arguments"]


def test_capabilities_match_every_enabled_public_signature(observed):
    for cap in observed["records"]["cap"]["view"]["capabilities"]:
        if cap["enabled"] and cap["id"] in observed["signatures"]:
            assert [f["name"] for f in cap["input_fields"]] == observed["signatures"][cap["id"]]["fields"]
        if cap["id"] == "obtener_resumen_territorial":
            assert cap["periodo_demografico_actual"] == "2025-01-01"
            assert "period_policy" not in cap
            assert all("nullable" not in f for f in cap["input_fields"])


def test_aduna_oracle_and_verified_birth_year_derivation(observed):
    view = observed["records"]["summary"]["view"]
    claims = {c["metric_id"]: c for c in view["claims"]}
    assert claims["population_75_plus"]["value"] == 36
    assert claims["population_total"]["value"] == 507
    assert claims["pct_75_plus"]["value"] == 7.101
    for key in ("population_75_plus", "population_total", "pct_75_plus"):
        assert claims[key]["source_ids"] == ["EUSTAT_EMH_2025"]
    derivation = view["age_group_derivation"]
    assert derivation["source_field"] == "año de nacimiento" and "<= 1949" in derivation["condition"]
    assert derivation["reference_period"] == "2025-01-01" and "agregados" in derivation["limitation"]
    assert derivation == observed["records"]["source"]["view"]["age_group_derivation"]


def test_single_demographic_period_verified_from_all_frozen_rows():
    with zipfile.ZipFile(io.BytesIO(blob(BASE_ZIP))) as archive:
        rows = list(csv.DictReader(io.StringIO(archive.read("datos_preparados/demografia.csv").decode("utf-8"))))
    assert len(rows) == 88 and {r["reference_period"] for r in rows} == {"2025-01-01"}


def test_no_internal_language_in_public_model_metadata(observed):
    for record in observed["records"].values():
        assert not public_language(record.get("view", {}))


def test_double_build_and_exactly_two_changed_members():
    build()
    before, manifest = ZIP.read_bytes(), MANIFEST.read_bytes()
    build()
    assert before == ZIP.read_bytes() and manifest == MANIFEST.read_bytes()
    with zipfile.ZipFile(io.BytesIO(blob(BASE_ZIP))) as old, zipfile.ZipFile(ZIP) as new:
        assert old.namelist() == new.namelist() and len(new.namelist()) == 25
        assert [n for n in old.namelist() if old.read(n) != new.read(n)] == ["main.py", "tools.py"]
        for n in json.loads(manifest)["context_paths"]:
            assert old.read(n) == new.read(n)


def test_prompt_general_without_demo_gold():
    tree = ast.parse((PORTAL / "main.py").read_text(encoding="utf-8"))
    prompt = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign) and n.targets[0].id == "SYSTEM_PROMPT")
    for value in ("Aduna", "1949", "507", "10691", "8591", "Zegama", "09:30", "09:45"):
        assert value not in prompt
    assert "age_group_derivation" in prompt and "time_summary" in prompt
    assert "ENGINE_CONTRACT" not in prompt and "PUBLIC_AGENT_CONTRACT" not in prompt


def test_r16_time_and_r15_flat_binding_regression(generated):
    cases = []
    base = dict(origin_id="zegama_center_stops", destination_id="beasain_official_centre_anchor", date="2026-09-29", appointment_time="09:30", duration_minutes=20)
    for time in ("09:30", "09:45"):
        cases.append({"id": time, "tool": "plan_visit", "arguments": {**base, "appointment_time": time}, "keep_view": True})
    cases.append({"id": "nested", "tool": "plan_visit", "arguments": {"request": base}})
    for field in ("return_deadline", "snapshot_id", "walking_profile_id", "arrival_margin_minutes", "boarding_margin_minutes"):
        cases.append({"id": field, "tool": "plan_visit", "arguments": {**base, field: None}})
    result = verify_r15.run_worker(generated, cases)
    assert result["signatures"]["plan_visit"]["fields"] == list(base)
    assert all(result["records"][key]["status"] == "binding_rejected" for key in ("nested", "return_deadline", "snapshot_id", "walking_profile_id", "arrival_margin_minutes", "boarding_margin_minutes"))
    a, b = [result["records"][key]["view"]["mobility"]["scenarios"][0] for key in ("09:30", "09:45")]
    assert a["time_summary"]["total_s"] == 10691 and a["time_summary"]["total_hms"] == "2 h 58 min 11 s"
    assert a["time_summary"]["scope_start_clock"] == "08:09:37" and a["time_summary"]["scope_end_clock"] == "11:07:48"
    assert a["itinerary"]["outbound"]["departure_time"] == "08:12:37"
    assert b["time_summary"]["total_s"] == 8591 and b["time_summary"]["total_hms"] == "2 h 23 min 11 s"
    assert b["time_summary"]["total_s"] - a["time_summary"]["total_s"] == -2100


def test_birth_derivation_metadata_mutation_fails_closed(generated):
    code = '''import json, main
p='datos_preparados/metadata_sources.json'
rows=json.load(open(p,encoding='utf-8'))
next(r for r in rows if r['source_id']=='EUSTAT_EMH_2025')['method']='unsupported transformation'
open(p,'w',encoding='utf-8').write(json.dumps(rows))
r=json.loads(main.obtener_resumen_territorial('Aduna'))
assert r['status']=='error' and not r['claims']
'''
    # Use a separate root; never mutate the module fixture shared by other tests.
    import tempfile
    with tempfile.TemporaryDirectory(prefix="r17-mutated-") as temporary:
        with zipfile.ZipFile(ZIP) as archive:
            archive.extractall(temporary)
        env = {**os.environ, "PYTHONPATH": "", "GIPUZKOA360_VNEXT_ROOT": temporary, "PYTHONUTF8": "1"}
        p = subprocess.run([sys.executable, "-c", code], cwd=temporary, env=env, capture_output=True, text=True, timeout=90)
        assert p.returncode == 0, p.stdout + p.stderr
