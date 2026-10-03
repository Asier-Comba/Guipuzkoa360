"""Generic endpoint binding, unchanged numbers and fail-closed public views."""
import copy
import importlib.util
import io
import json
import sys
import subprocess
import zipfile
import pytest
from scripts.vnext_agent import build_r24 as build
from tests.vnext_agent import test_r23_threshold as threshold_tests
from tests.vnext_agent import test_r22_attribution as attribution_tests

@pytest.fixture(scope='module')
def package(tmp_path_factory):
    build.build(); root = tmp_path_factory.mktemp('r24-health-scope')
    with zipfile.ZipFile(build.ZIP) as z: z.extractall(root)
    spec = importlib.util.spec_from_file_location('r24_health_scope_test_tools', root/'tools.py')
    module = importlib.util.module_from_spec(spec); sys.modules[spec.name] = module; spec.loader.exec_module(module)
    return root, module

@pytest.fixture(scope='module')
def health_observed(package):
    root,m=package
    completed=subprocess.run([sys.executable,'-X','utf8','-m','scripts.vnext_agent.worker_r24_scope',str(root)],cwd=build.ROOT,capture_output=True,text=True,encoding='utf-8',timeout=120)
    assert completed.returncode==0,completed.stderr
    return json.loads(completed.stdout)

def request(origin='zegama_center_stops', clock='09:30'):
    return {'request':dict(origin_id=origin, destination_id='beasain_official_centre_anchor', date='2026-09-29', appointment_time=clock, duration_minutes=20)}

@pytest.mark.parametrize('origin', ['zegama_center_stops','segura_herriko_plaza_stops','idiazabal_center_stops'])
@pytest.mark.parametrize('clock', ['09:30','09:45'])
def test_complete_scope_all_origins_and_times(package,health_observed,origin,clock):
    root,m=package; observed=health_observed['records'][origin+':'+clock]
    raw=observed['raw']; view=observed['view']
    assert view['status']=='valid',view
    s=view['mobility']['scenarios'][0]; scope=s['journey_scope']; summary=s['time_summary']
    assert scope['scope_kind']==raw['scope']=='origin_stop_presence_to_return_stop_arrival'
    assert scope['includes_return_trip'] is True
    assert scope['start']['kind']=='origin_stop_presence'
    assert scope['health_destination']['kind']=='intermediate_health_anchor'
    assert scope['end']['kind']=='return_stop_arrival'
    assert scope['end']!=scope['health_destination']
    assert scope['start']['origin_id']==scope['end']['origin_id']==origin
    assert scope['end']['clock']==raw['itinerary']['return']['arrival_time']==summary['scope_end_clock']
    assert scope['start']['clock']==summary['scope_start_clock']
    assert scope['end']['seconds']-scope['start']['seconds']==summary['total_s']
    assert s['health_destination']['wording']==m._R24_ANCHOR_MEANING
    assert s['health_destination']['kind']=='intermediate_health_anchor'
    assert scope['health_destination']['entrance_verified'] is False
    if origin=='zegama_center_stops':
        assert summary['total_s']==(10691 if clock=='09:30' else 8591)
        assert summary['total_hms']==('2 h 58 min 11 s' if clock=='09:30' else '2 h 23 min 11 s')
    prior=observed['prior']; projected=observed['projected']
    # Only scope/anchor wording fields change, no arithmetic or itinerary.
    p=projected['scenarios'][0]; old=prior['scenarios'][0]
    for k in ('itinerary','components_s','time_summary','sources','walking','effective_parameters','parameter_attribution'):
        assert p[k]==old[k]

@pytest.mark.parametrize('mutation',['scope','summary_end','summary_start','destination_id','entrance','origin_stop','return_stop','return_clock','departure_clock'])
def test_inconsistent_projection_fails_closed(health_observed,mutation):
    view=health_observed['faults'][mutation]
    assert view['status']=='error' and view['claims']==[] and 'mobility' not in view
    assert view['error']['retry_same_arguments'] is False

def test_catalog_wording_and_other_tools_unchanged(package):
    root,m=package
    old=m._r23_mobility_catalog_view(root); new=m._mobility_catalog_view(root)
    assert new['destination']['reference_point_meaning']==m._R24_ANCHOR_MEANING
    new['destination']['reference_point_meaning']=old['destination']['reference_point_meaning']
    assert new==old
    args={'categoria_servicio':'mental_health','umbral_km':1,'municipios':['Getaria']}
    actual=m.strict_loads(m.public_call('analizar_acceso_municipios',args,'TEST',root=root))
    prior=m.strict_loads(m._r22_public_call('analizar_acceso_municipios',args,'TEST',root=root))
    assert actual.pop('threshold_semantics')['operator']=='<='
    assert actual==prior

@pytest.mark.parametrize('count',[1,2,3])
def test_source_order_invariance_on_r24(package,count):
    attribution_tests.test_source_attribution_join_and_all_independent_permutations(package,count)

@pytest.mark.parametrize('tool,args',[('analizar_acceso_general',{}),('analizar_acceso_municipios',{'municipios':['Getaria']})])
def test_threshold_regression_on_r24(package,tool,args):
    threshold_tests.test_actual_outputs_metamorphic_and_source_preservation(package,tool,args)

@pytest.mark.parametrize('distance,expected',[(0,True),(1999.9,True),(2000,True),(2000.1,False),(None,False),(2000.04,False)])
def test_zero_and_boundaries_on_r24(package,monkeypatch,distance,expected):
    threshold_tests.test_boundary_and_display_rounding(package,monkeypatch,distance,expected)

def test_package_identity_and_two_builds():
    build.build(); before=build.ZIP.read_bytes(),build.MANIFEST.read_bytes()
    build.build(); assert before==(build.ZIP.read_bytes(),build.MANIFEST.read_bytes())
    with zipfile.ZipFile(io.BytesIO(build.blob(build.BASE_ZIP))) as old,zipfile.ZipFile(build.ZIP) as new:
        assert old.namelist()==new.namelist()
        assert [n for n in old.namelist() if old.read(n)!=new.read(n)]==['tools.py']
        assert old.read('main.py')==new.read('main.py')
        assert new.read('tools.py').startswith(old.read('tools.py'))
    meta=json.loads(build.MANIFEST.read_bytes())
    assert len(meta['public_tools'])==10 and len(meta['context_paths'])==15
    assert meta['context_assets_changed']==[] and meta['main_changed'] is False
