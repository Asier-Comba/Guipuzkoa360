"""R16 deterministic presentation regressions, not claims about a real LLM."""
import copy
import inspect
import io
import json
import os
import subprocess
import sys
import zipfile

import pytest

from agentes.gipuzkoa360_vnext.tools import ContractViolation
from scripts.vnext_agent import r16_presentation as presentation
from scripts.vnext_agent.build_r16 import BASE_ZIP, MANIFEST, PORTAL, ROOT, ZIP, blob, build, sha


@pytest.fixture(autouse=True)
def exception_type(monkeypatch):
    monkeypatch.setattr(presentation, "ContractViolation", ContractViolation, raising=False)


@pytest.mark.parametrize("seconds", [0, 1, 59, 60, 61, 3599, 3600, 3601, 86399, *range(0, 86400, 997)])
def test_duration_and_clock_integer_round_trip(seconds):
    duration = presentation._duration_hms(seconds).split()
    h, m, s = map(int, duration[::2])
    assert 0 <= m < 60 and 0 <= s < 60 and h * 3600 + m * 60 + s == seconds
    clock = presentation._civil_clock(seconds)
    assert len(clock) == 8
    h, m, s = map(int, clock.split(":"))
    assert h * 3600 + m * 60 + s == seconds


@pytest.mark.parametrize("value", [-1, 86400, True, None, 1.0, "61", float("nan"), float("inf")])
def test_formatter_fails_closed_for_invalid_types_or_civil_day(value):
    for function in (presentation._duration_hms, presentation._civil_clock):
        with pytest.raises(ContractViolation):
            function(value)


def fixture_result():
    return {"scope": "origin_stop_presence_to_return_stop_arrival",
            "itinerary": {"start_s": 61, "end_s": 3661, "total_s": 3600,
                          "outbound": {"departure_time": "00:02:01"}},
            "components_s": {"initial_wait_s": 60, "vehicle_s": 3540}}


def test_scope_and_initial_wait_are_not_vehicle_departure():
    summary = presentation._time_summary(fixture_result())
    assert summary["scope_start_clock"] == "00:01:01"
    assert summary["scope_end_clock"] == "01:01:01"
    assert summary["total_s"] == 3600 and summary["total_hms"] == "1 h 0 min 0 s"
    assert summary["scope_start_s"] != 121


@pytest.mark.parametrize("path,value", [
    (("itinerary", "start_s"), True), (("itinerary", "end_s"), 3660),
    (("itinerary", "total_s"), 3599), (("itinerary", "start_s"), 61.0),
    (("components_s", "initial_wait_s"), -1), (("components_s", "vehicle_s"), 3541),
    (("components_s", "vehicle_s"), True), (("components_s", "initial_wait_s"), 0),
])
def test_scope_or_component_mutations_are_rejected(path, value):
    result = fixture_result()
    result[path[0]][path[1]] = value
    with pytest.raises(ContractViolation):
        presentation._time_summary(result)


def test_reproducible_exact_package_and_only_two_changed_members():
    build()
    first, manifest = ZIP.read_bytes(), MANIFEST.read_bytes()
    build()
    assert first == ZIP.read_bytes() and manifest == MANIFEST.read_bytes()
    report = json.loads(manifest)
    with zipfile.ZipFile(io.BytesIO(blob(BASE_ZIP))) as old, zipfile.ZipFile(ZIP) as new:
        assert old.namelist() == new.namelist() and len(new.namelist()) == 25
        assert [n for n in old.namelist() if old.read(n) != new.read(n)] == ["main.py", "tools.py"]
        for path in report["context_paths"]:
            assert new.read(path) == old.read(path)
        for path in ("main.py", "tools.py"):
            assert new.read(path) == (PORTAL / path).read_bytes()


def test_exact_generated_projection_and_fail_closed(tmp_path):
    build()
    with zipfile.ZipFile(ZIP) as archive:
        archive.extractall(tmp_path)
    code = r'''
import copy, inspect, json, socket, main, tools
socket.socket=lambda *a,**k: (_ for _ in ()).throw(AssertionError('network forbidden'))
fields=['origin_id','destination_id','date','appointment_time','duration_minutes']
assert list(inspect.signature(main.plan_visit).parameters)==fields
assert len(main.TOOLS)==9
cap=json.loads(main.consultar_capacidades('plan_visit'))
catalog=cap['mobility_catalog']
assert {x['municipality_name'] for x in catalog['origin_options']}=={'Zegama','Segura','Idiazabal'}
assert catalog['request_fields']==catalog['required_fields']==fields
assert catalog['comparison']['mode']=='individual_calls' and not catalog['comparison']['batch_supported']
assert 'engine_contract' not in catalog and 'provider_defaults' not in catalog
assert catalog['modelling_assumptions']['arrival_margin_minutes']==10
assert catalog['modelling_assumptions']['boarding_margin_minutes']==3
q=dict(origin_id='zegama_center_stops',destination_id='beasain_official_centre_anchor',date='2026-09-29',appointment_time='09:30',duration_minutes=20)
raw=tools.execute('plan_visit',{'request':q},'TEST_SCOPE')
assert raw['status']=='valid'
result=json.loads(raw['raw_result_json'])
view=json.loads(tools.public_result(raw))
summary=view['mobility']['scenarios'][0]['time_summary']
assert summary['total_s']==10691 and summary['total_hms']=='2 h 58 min 11 s'
assert summary['scope_start_clock']=='08:09:37' and summary['scope_end_clock']=='11:07:48'
assert summary['scope_end_s']-summary['scope_start_s']==sum(result['components_s'].values())==10691
assert result['itinerary']['outbound']['departure_time']=='08:12:37' and summary['initial_wait_s']==180
right=json.loads(main.plan_visit(**{**q,'appointment_time':'09:45'}))
rs=right['mobility']['scenarios'][0]['time_summary']
assert rs['total_s']==8591 and rs['total_hms']=='2 h 23 min 11 s'
assert rs['total_s']-summary['total_s']==-2100
for field in ('return_deadline','snapshot_id','walking_profile_id','arrival_margin_minutes','boarding_margin_minutes'):
    try: main.plan_visit(**q,**{field:''})
    except TypeError: pass
    else: raise AssertionError('public optional '+field)
try: main.plan_visit(request=q)
except TypeError: pass
else: raise AssertionError('nested public request')
legacy=json.load(open('datos_preparados/vnext/w1_conformance_r7.json'))
legacy=next(c['request'] for c in legacy['cases'] if c['case_id']=='legacy_r4_explicit')
assert json.loads(main._run('plan_visit',{'request':legacy}))['status']=='valid'
assert json.loads(main._run('plan_visit',{'request':{**q,'return_deadline':''}}))['status']=='error'
assert json.loads(main.obtener_resumen_territorial('Aduna',periodo=''))['status']=='error'
assert json.loads(main.obtener_resumen_territorial('Aduna'))['status']=='valid'
# Force corruption after the original view projection. The public boundary
# must discard the entire mobility result, not publish a partly correct total.
original=tools._time_summary
def corrupt(result):
    altered=copy.deepcopy(result); altered['itinerary']['start_s']+=1
    return original(altered)
tools._time_summary=corrupt
failure=json.loads(tools.public_result(raw))
assert failure['status']=='error' and not failure['claims'] and 'mobility' not in failure
assert failure['error']['code']=='public_projection_unverified'
print(json.dumps({'status':'PASS','main':summary,'variation':rs,'network':'denied'}))
'''
    env = {**os.environ, "PYTHONPATH": "", "PYTHONNOUSERSITE": "1", "PYTHONUTF8": "1", "GIPUZKOA360_VNEXT_ROOT": str(tmp_path)}
    process = subprocess.run([sys.executable, "-c", code], cwd=tmp_path, env=env, text=True, encoding="utf-8", capture_output=True, timeout=120)
    assert process.returncode == 0, process.stdout + process.stderr


def test_prompt_has_general_rules_not_demo_gold():
    import ast
    build()
    constants = {n.targets[0].id: ast.literal_eval(n.value) for n in ast.parse((PORTAL / "main.py").read_text(encoding="utf-8")).body
                 if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id == "SYSTEM_PROMPT"}
    prompt = constants["SYSTEM_PROMPT"]
    for gold in ("10691", "8591", "Zegama", "09:30", "09:45", "08:09:37", "2 h 58"):
        assert gold not in prompt
    for rule in ("time_summary", "total_hms", "scope_start_clock", "scope_end_clock", "outbound.departure", "origin_options", "invalid_arguments", "máximo una", "omite periodo"):
        assert rule in prompt
