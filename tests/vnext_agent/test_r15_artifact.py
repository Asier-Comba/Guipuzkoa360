"""Permanent exact-artifact regressions for the public/engine contract split."""
import io
import json
import os
import subprocess
import sys
import zipfile

from scripts.vnext_agent.build_r15 import BASE_ZIP, MANIFEST, ROOT, ZIP, blob, build, sha


def test_r15_reproducible_members_and_frozen_engine_assets():
    build()
    first, manifest = ZIP.read_bytes(), MANIFEST.read_bytes()
    build()
    assert (first, manifest) == (ZIP.read_bytes(), MANIFEST.read_bytes())
    report = json.loads(manifest)
    with zipfile.ZipFile(io.BytesIO(blob(BASE_ZIP))) as old, zipfile.ZipFile(ZIP) as new:
        assert old.namelist() == new.namelist()
        assert len(new.namelist()) == len(set(new.namelist())) == 25
        assert [n for n in old.namelist() if old.read(n) != new.read(n)] == ['main.py', 'tools.py']
        for name in new.namelist():
            assert report['members'][name] == {'bytes': len(new.read(name)), 'sha256': sha(new.read(name))}
        for name in report['context_paths']:
            assert new.read(name) == old.read(name)
        for name in ('main.py', 'tools.py'):
            assert new.read(name) == (ROOT / 'agentes/gipuzkoa360_vnext/portal' / name).read_bytes()
    assert report['sha256'] == sha(first)


def test_generated_public_contract_matches_callable_and_preserves_internal_engine(tmp_path):
    build()
    with zipfile.ZipFile(ZIP) as archive:
        archive.extractall(tmp_path)
    code = r'''
import inspect,json,main,tools
catalog=json.loads(main.consultar_capacidades('plan_visit'))
assert catalog['status']=='valid',catalog
fields=list(inspect.signature(main.plan_visit).parameters)
assert fields==['origin_id','destination_id','date','appointment_time','duration_minutes']
assert catalog['mobility_catalog']['request_fields']==fields
assert catalog['mobility_catalog']['required_fields']==fields
assert [x['name'] for x in catalog['capabilities'][0]['input_fields']]==fields
assert all(x['required'] for x in catalog['capabilities'][0]['input_fields'])
assert 'comparison_size' not in catalog['mobility_catalog']
assert catalog['mobility_catalog']['comparison']['batch_supported'] is False
assert catalog['mobility_catalog']['comparison']['mode']=='individual_calls'
assert 'side_by_side_only' in catalog['mobility_catalog']['comparison']['cross_origin_comparison']
assert 'stop_only explicit' not in catalog['capabilities'][0]['coverage']['scope']
fixture=json.load(open('datos_preparados/vnext/w1_conformance_r7.json'))
request=next(c['request'] for c in fixture['cases'] if c['case_id']=='health_defaults_omitted')
request={**request,'appointment_time':'09:30'}
left=json.loads(main.plan_visit(**request))
right=json.loads(main.plan_visit(**{**request,'appointment_time':'09:45'}))
assert left['status']==right['status']=='valid'
assert left['mobility']['scenarios'][0]['itinerary']['total_s']==10691
assert right['mobility']['scenarios'][0]['itinerary']['total_s']==8591
assert right['mobility']['scenarios'][0]['itinerary']['total_s']-left['mobility']['scenarios'][0]['itinerary']['total_s']==-2100
for field in ('return_deadline','snapshot_id','walking_profile_id','arrival_margin_minutes','boarding_margin_minutes'):
    try: main.plan_visit(**request,**{field:''})
    except TypeError: pass
    else: raise AssertionError('Unexpected public optional '+field)
    assert field not in left['normalized_input']['arguments']
legacy=next(c['request'] for c in fixture['cases'] if c['case_id']=='legacy_r4_explicit')
assert json.loads(main._run('plan_visit',{'request':legacy}))['status']=='valid'
internal=json.loads(main._run('plan_visit',{'request':[request,{**request,'duration_minutes':27}]}))
assert internal['status']=='valid' and len(internal['mobility']['scenarios'])==2
bad=tools.execute('plan_visit',{'request':{**request,'return_deadline':''}},'M05_REPLAY')
assert bad['status']=='error' and bad['error']['message']=='mobility:invalid_clock'
assert not bad['claims'] and not bad['outcomes'] and bad['raw_result_json'] is None
assert json.loads(main.plan_visit(**request))['mobility']==left['mobility']
'''
    env = {**os.environ, 'PYTHONPATH': '', 'PYTHONNOUSERSITE': '1', 'PYTHONUTF8': '1', 'GIPUZKOA360_VNEXT_ROOT': str(tmp_path)}
    run = subprocess.run([sys.executable, '-c', code], cwd=tmp_path, env=env, text=True, encoding='utf-8', capture_output=True, timeout=120)
    assert run.returncode == 0, run.stdout + run.stderr
