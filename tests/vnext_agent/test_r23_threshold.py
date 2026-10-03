"""Inclusive boundary, exact argument binding and fail-closed projection."""
import ast
import copy
import importlib.util
import io
import json
import sys
import zipfile
import pytest
from scripts.vnext_agent import build_r23 as build

@pytest.fixture(scope='module')
def package(tmp_path_factory):
    build.build(); root = tmp_path_factory.mktemp('r23-threshold')
    with zipfile.ZipFile(build.ZIP) as z: z.extractall(root)
    spec = importlib.util.spec_from_file_location('r23_threshold_test_tools', root/'tools.py')
    module = importlib.util.module_from_spec(spec); sys.modules[spec.name] = module; spec.loader.exec_module(module)
    return root, module

@pytest.mark.parametrize('distance,expected', [(0,True),(1999.9,True),(2000,True),(2000.1,False),(None,False),(2000.04,False)])
def test_boundary_and_display_rounding(package, monkeypatch, distance, expected):
    root, m = package; repo = m.territorial.DataRepository(root/'datos_preparados'); town = repo.municipalities()[0]
    service = next(s for s in repo.services() if s['service_category']=='primary_care') if distance is not None else None
    monkeypatch.setattr(m, 'nearest_service_projected', lambda *args: (distance,service))
    raw = {'filters':{'threshold_km':2,'service_category':'primary_care'}, 'data':[{'municipality_code':town['municipality_code'], 'nearest_distance_m':round(distance,1) if distance is not None else None, 'nearest_service_id':service['service_id'] if service else None, 'within_threshold':expected}]}
    view = {'municipal_classifications':[{'entity_id':town['municipality_code'],'metric_id':'within_threshold','value':expected}]}
    result = m._r23_threshold_semantics(view,raw,{'umbral_km':2,'categoria_servicio':'primary_care'},root)
    assert result['threshold_semantics']['operator']=='<=' and result['threshold_semantics']['zero_distance_included'] is True
    assert result['municipal_classifications'][0]['value'] is expected

@pytest.mark.parametrize('tool,args', [('analizar_acceso_general',{}),('analizar_acceso_municipios',{'municipios':['Getaria']})])
def test_actual_outputs_metamorphic_and_source_preservation(package,tool,args):
    root,m = package; results=[]
    for threshold in (1,2,6):
        values={'categoria_servicio':'mental_health','umbral_km':threshold,**args}
        prior=m.strict_loads(m._r22_public_call(tool,values,'TEST',root=root))
        actual=m.strict_loads(m.public_call(tool,values,'TEST',root=root))
        assert actual['status']=='valid',actual
        assert {k:v for k,v in actual.items() if k!='threshold_semantics'}==prior
        semantics=actual['threshold_semantics']; assert semantics['threshold_km']==threshold and semantics['threshold_m']==threshold*1000
        assert semantics['operator']=='<=' and semantics['zero_distance_included'] is True and semantics['missing_distance_within_threshold'] is False
        results.append(actual)
    assert results[0]['claims']==results[1]['claims']==results[2]['claims']
    for before,after in zip(results,results[1:]):
        left={c['entity_id']:c['value'] for c in before['municipal_classifications']}
        right={c['entity_id']:c['value'] for c in after['municipal_classifications']}
        assert all(not v or right[k] for k,v in left.items())

@pytest.mark.parametrize('mutation',['raw_threshold','raw_bool','public_bool','digest','nan'])
def test_inconsistent_projection_fails_closed(package,monkeypatch,mutation):
    root,m=package; args={'categoria_servicio':'primary_care','umbral_km':2,'municipios':['Aduna']}
    original=m.execute
    def execute(*a,**kw):
        result=original(*a,**kw)
        if mutation=='digest': result['raw_result_sha256']='0'*64
        if mutation in {'raw_threshold','raw_bool'}:
            raw=m.strict_loads(result['raw_result_json'])
            if mutation=='raw_threshold': raw['filters']['threshold_km']=6
            else: raw['data'][0]['within_threshold']=not raw['data'][0]['within_threshold']
            result['raw_result_json']=m.canonical(raw)
        return result
    # Only mutate the reobservation, keeping the prior validated response intact.
    prior=m._r22_public_call
    rendered=prior('analizar_acceso_municipios',args,'TEST',root=root)
    if mutation=='public_bool':
        view=m.strict_loads(rendered); view['municipal_classifications'][0]['value']=not view['municipal_classifications'][0]['value']; rendered=m.canonical(view)
    monkeypatch.setattr(m,'_r22_public_call',lambda *a,**kw:rendered)
    monkeypatch.setattr(m,'execute',execute)
    if mutation=='nan': args['umbral_km']=float('nan')
    result=m.strict_loads(m.public_call('analizar_acceso_municipios',args,'TEST',root=root))
    assert result['status']=='error' and result['claims']==[] and 'threshold_semantics' not in result
    assert result['error']['code']=='threshold_semantics_failure' and result['error']['retry_same_arguments'] is False

def test_package_delta_and_double_build():
    build.build(); before=build.ZIP.read_bytes(),build.MANIFEST.read_bytes(); build.build(); assert before==(build.ZIP.read_bytes(),build.MANIFEST.read_bytes())
    with zipfile.ZipFile(io.BytesIO(build.blob(build.BASE_ZIP))) as old,zipfile.ZipFile(build.ZIP) as new:
        assert [n for n in old.namelist() if old.read(n)!=new.read(n)]==['main.py','tools.py']
        assert new.read('tools.py').startswith(old.read('tools.py'))
        a,b=(ast.parse(z.read('main.py')) for z in (old,new))
        for tree in (a,b):
            for node in tree.body:
                if isinstance(node,ast.FunctionDef) and node.name in {'analizar_acceso_general','analizar_acceso_municipios'}: node.body.pop(0)
        assert ast.dump(a)==ast.dump(b)
    meta=json.loads(build.MANIFEST.read_bytes()); assert len(meta['public_tools'])==10 and len(meta['context_paths'])==15 and meta['context_assets_changed']==[]
