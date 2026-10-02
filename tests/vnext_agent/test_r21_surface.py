"""Ten-tool build gate, real composition evidence and source coverage."""
import ast
import io
import json
import zipfile
import pytest
from scripts.vnext_agent.build_r21 import ZIP, MANIFEST, PORTAL, PROMPT, BASE_ZIP, BASE_HASH, PUBLIC_TOOLS, blob, build, sha
from scripts.vnext_agent.verify_r21 import run_worker, focal_cases, composition_check
from scripts.vnext_agent import verify_r20
from scripts.vnext_agent.eval_r21 import generate, expand, FAMILIES, build as build_corpus

@pytest.fixture(scope='module')
def observed(tmp_path_factory):
    build(); root = tmp_path_factory.mktemp('r21-observer')
    with zipfile.ZipFile(ZIP) as z: z.extractall(root)
    cases = focal_cases(); comparison = [r for r in verify_r20.focal_cases() if r['tool']=='comparar_municipios']
    refs = [{**verify_r20.mapped_case(r),'id':'internal:'+r['id']} for r in comparison]
    negative,_ = verify_r20.negative_cases(); negative = [r for r in negative if r['tool'] in PUBLIC_TOOLS]
    return {'data':run_worker(root,cases+refs+negative),'comparisons':comparison,'negative':negative}

def test_exact_ten_unique_build_gate(observed):
    data = observed['data']; assert set(data['signatures'])==set(PUBLIC_TOOLS) and len(set(PUBLIC_TOOLS))==10
    caps = data['records']['caps']['view']; assert caps['public_tool_count']==10
    assert [c['id'] for c in caps['capabilities']]==PUBLIC_TOOLS
    for c in caps['capabilities']:
        sig=data['signatures'][c['id']]
        assert [f['name'] for f in c['input_fields']]==sig['fields']
        assert {f['name'] for f in c['input_fields'] if f['required']}==set(sig['required'])
    assert all(not c['callable_tool'] for c in caps['composed_capabilities'])
    tree=ast.parse((PORTAL/'main.py').read_text(encoding='utf-8'))
    assert not any(isinstance(n,ast.FunctionDef) and n.name in {'comparar_municipios','consultar_fuente'} for n in tree.body)
    registered=next(n.value for n in tree.body if isinstance(n,ast.Assign) and getattr(n.targets[0],'id',None)=='TOOLS')
    assert [n.id for n in registered.elts]==PUBLIC_TOOLS

@pytest.mark.parametrize('tool,fields',[
    ('analizar_acceso_general',['categoria_servicio','umbral_km']),
    ('analizar_acceso_municipios',['categoria_servicio','umbral_km','municipios']),
    ('simular_anadir_servicio',['categoria_servicio','latitud','longitud','umbral_km']),
    ('simular_retirar_servicio',['categoria_servicio','service_id','umbral_km']),
    ('simular_cambiar_umbral',['categoria_servicio','umbral_actual_km','nuevo_umbral_km'])])
def test_r20_required_actions_retained(observed,tool,fields):
    sig=observed['data']['signatures'][tool]; assert sig['fields']==sig['required']==fields and sig['defaults']=={}

def test_88_municipality_names_and_codes_same_raw(observed):
    records=observed['data']['records']; codes={k.split(':')[1] for k in records if k.startswith('summary:')}; assert len(codes)==88
    for code in codes:
        a,b=(records['summary:'+code+':'+f] for f in ('municipality_name','municipality_code'))
        assert a['status']==b['status']=='valid' and a['raw_sha256']==b['raw_sha256']

def test_composed_comparison_matches_unchanged_internal_engine(observed):
    result=composition_check(observed['data']['records'],observed['comparisons']); assert result['cases']==4 and not result['findings']

def test_sources_full_existing_cards_and_both_age_methods(observed):
    caps=observed['data']['records']['caps']['view']; sources={s['source_id']:s for s in caps['sources_catalog']}
    source=sources['EUSTAT_EMH_2025']; assert source['reference_period']=='2025-01-01' and source['institution'].startswith('Eustat')
    assert 'pivote de total/65+' in source['method'] and source['limitations']
    assert '1949' not in json.dumps(caps['age_group_derivations']['65'])
    assert '<= 1949' in caps['age_group_derivations']['75']['condition']
    non_web_roles={'user_parameter','modelling_assumption','derived_network','model_parameter','agent_or_user_parameter','derived_metric'}
    for s in sources.values():
        assert s.get('title') and s.get('institution') and s.get('reference_period')
        assert s.get('url') or s.get('role') in non_web_roles
    assert sources['ODE_HEALTH_CENTRES_2026']['limitations']

@pytest.mark.parametrize('age',['65','75'])
def test_analytical_age_metadata_isolated(observed,age):
    view=observed['data']['records']['rank'+age]['view']; assert set(view['age_group_derivations'])=={age}
    if age=='65': assert '1949' not in json.dumps(view)

@pytest.mark.parametrize('clock,expected',[('09:30',10691),('09:45',8591)])
def test_public_health_golden_values(observed,clock,expected):
    r=observed['data']['records']['health:'+clock]; assert r['status']=='valid'
    assert expected in [c['value'] for c in r['claims'] if c['unit']=='s'],r['view']

def test_invalid_no_claims_no_retry(observed):
    for c in observed['negative']:
        r=observed['data']['records'][c['id']]; assert r['status'] in {'error','binding_rejected'} and not r.get('claims')
        if r['status']=='error': assert r['view']['error']['retry_same_arguments'] is False

def test_immutable_r20_prefix_assets_provider_double_build():
    base=blob(BASE_ZIP); assert sha(base)==BASE_HASH
    with zipfile.ZipFile(io.BytesIO(base)) as a, zipfile.ZipFile(ZIP) as b:
        assert a.namelist()==b.namelist() and b.read('tools.py').startswith(a.read('tools.py'))
        assert [n for n in a.namelist() if a.read(n)!=b.read(n)]==['main.py','tools.py']
    before=ZIP.read_bytes(),MANIFEST.read_bytes(); build(); assert before==(ZIP.read_bytes(),MANIFEST.read_bytes())
    manifest=json.loads(MANIFEST.read_bytes()); assert len(manifest['context_paths'])==15 and not manifest['w1_runtime_changed'] and not manifest['v4_changed']

def test_general_prompt_no_test_entities_values_or_internal_generation():
    text=PROMPT.read_text(encoding='utf-8'); assert len(text)<6000
    assert all(s in text for s in ('ROLE','REASONING LOOP','EVIDENCE','TOOL SELECTION','FOLLOW-UP','ERROR RECOVERY','SEMANTIC LIMITS','COMMUNICATION'))
    assert all(t not in text.casefold() for t in ('getaria','zegama','legorreta','alegia','aduna','r21','10691','8591'))

def test_preselected_stratified_protocol_outside_package():
    rows,sample=generate(); assert generate()==(rows,sample) and len(rows)==264 and len(FAMILIES)==24 and len(sample)==22
    assert not any(r['tool'] in {'comparar_municipios','consultar_fuente'} for r in rows)
    assert all(s['tool'] in PUBLIC_TOOLS for r in rows for s in r.get('composition',[]))
    assert len(expand(rows))==297
    a=build_corpus(); assert build_corpus()==a
    with zipfile.ZipFile(ZIP) as z: assert not any('corpus' in n or 'protocol' in n for n in z.namelist())
