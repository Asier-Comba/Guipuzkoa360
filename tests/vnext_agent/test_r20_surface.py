"""Structural contracts and real raw outputs; no canned LLM routing."""
import ast
import io
import json
import zipfile
import pytest
from scripts.vnext_agent.build_r20 import ZIP,MANIFEST,PORTAL,PROMPT,PUBLIC_TOOLS,BASE_ZIP,BASE_HASH,blob,build,sha
from scripts.vnext_agent.verify_r20 import run_worker,focal_cases,negative_cases,mapped_case
from scripts.vnext_agent.eval_r20 import generate,FAMILIES,build as build_corpus

@pytest.fixture(scope='module')
def observed(tmp_path_factory):
    build();root=tmp_path_factory.mktemp('r20-surface')
    with zipfile.ZipFile(ZIP) as z:z.extractall(root)
    focal=focal_cases();negative,_=negative_cases()
    obs=run_worker(root,focal+negative)
    removals=[]
    for category in ('primary_care','hospital','mental_health','other_health'):
        identity=obs['records']['general:'+category]['view']['observed_services'][0]['service_id']
        removals.append(dict(id='remove:'+category,tool='simular_retirar_servicio',arguments=dict(categoria_servicio=category,service_id=identity,umbral_km=1),keep_raw=True))
    faults=[dict(id=f,tool='simular_cambiar_umbral',arguments=dict(categoria_servicio='primary_care',umbral_actual_km=1,nuevo_umbral_km=2),fault=f) for f in ('synthetic_observed_transport','synthetic_contract_failure')]
    return {'public':obs,'removed':run_worker(root,removals),'engine':run_worker(root,[mapped_case(c) for c in focal+removals]),'negative':negative,'faults':run_worker(root,faults)}

@pytest.mark.parametrize('tool,fields',[
    ('analizar_acceso_general',['categoria_servicio','umbral_km']),
    ('analizar_acceso_municipios',['categoria_servicio','umbral_km','municipios']),
    ('simular_anadir_servicio',['categoria_servicio','latitud','longitud','umbral_km']),
    ('simular_retirar_servicio',['categoria_servicio','service_id','umbral_km']),
    ('simular_cambiar_umbral',['categoria_servicio','umbral_actual_km','nuevo_umbral_km'])])
def test_exact_required_fields_no_irrelevant_slots(observed,tool,fields):
    sig=observed['public']['signatures'][tool]
    assert sig['fields']==sig['required']==fields and sig['defaults']=={}

def test_only_twelve_tools_and_exact_capability_contract(observed):
    obs=observed['public'];caps=obs['records']['caps']['view']['capabilities']
    assert set(obs['signatures'])==set(PUBLIC_TOOLS)=={c['id'] for c in caps}
    assert 'simular_escenario' not in obs['signatures'] and 'analizar_acceso_servicios' not in obs['signatures']
    for cap in caps:
        sig=obs['signatures'][cap['id']]
        assert [f['name'] for f in cap['input_fields']]==sig['fields']
        assert set(f['name'] for f in cap['input_fields'] if f['required'])==set(sig['required'])

@pytest.mark.parametrize('category',['primary_care','hospital','mental_health','other_health'])
def test_three_action_parity_and_effective_engine_mapping(observed,category):
    for id,source in [('change:'+category+':1:6',observed['public']),('add:'+category,observed['public']),('remove:'+category,observed['removed'])]:
        a,b=source['records'][id],observed['engine']['records'][id]
        assert a['status']==b['status']=='valid'
        assert a['raw_sha256']==b['raw_sha256'] and a['claims']==b['claims'] and a['effective_request']==b['effective_request']
    args=observed['public']['records']['change:'+category+':1:6']['engine_input']['arguments']
    assert args==dict(accion='change_threshold',categoria_servicio=category,umbral_km=1,nuevo_umbral_km=6)
    assert observed['public']['records']['add:'+category]['engine_input']['arguments']['service_id'] is None

def test_getaria_and_period_subject_preserved(observed):
    r=observed['public']['records']['selected:mental_health:Getaria'];view=r['view']
    assert r['status']=='valid' and r['execute_calls']==1
    assert [c['value'] for c in r['claims'] if c['metric_id']=='nearest_distance_m']==[2913.3]
    assert view['municipal_classifications'][0]['value'] is False
    assert view['municipal_classifications'][0]['subject']=='punto representativo municipal'
    assert all(c['period']=='2026-09-20;2025-05-07' for c in r['claims'])

def test_general_never_receives_empty_selector(observed):
    r=observed['public']['records']['general:primary_care']
    assert r['status']=='valid' and 'municipios' not in r['engine_input']['arguments']
    assert len(r['raw']['data'])==88

def test_observed_identity_matches_same_validated_raw_row(observed):
    for r in observed['public']['records'].values():
        view=r.get('view',{})
        for item in view.get('observed_services',[]):
            row=r['raw']['data'][int(item['evidence_path'].split('/')[2])]
            assert item['service_id']==row['nearest_service_id']
            assert item['municipality_code']==row['municipality_code'] and item['raw_result_sha256']==r['raw_sha256']

@pytest.mark.parametrize('family',['analizar_acceso_general','analizar_acceso_municipios','simular_anadir_servicio','simular_retirar_servicio','simular_cambiar_umbral','comparar_municipios'])
def test_invalid_types_bounds_empty_duplicate_unknown_no_partial_claims(observed,family):
    cases=[c for c in observed['negative'] if c['tool']==family];assert cases
    for case in cases:
        r=observed['public']['records'][case['id']]
        assert r['status'] in {'error','binding_rejected'} and not r.get('claims'),(case,r)
        if r['status']=='error':
            e=r['view']['error']
            for key in ('error_class','invalid_fields','retry_same_arguments','allowed_values','required_next_information','corrected_call_possible'):assert key in e
            assert e['retry_same_arguments'] is False

@pytest.mark.parametrize('age',['65','75'])
def test_age_metadata_retained_not_cross_group(observed,age):
    view=observed['public']['records']['rank'+age]['view']
    assert set(view['age_group_derivations'])=={age}
    if age=='65':assert '1949' not in json.dumps(view) and 'population_75_plus' not in json.dumps(view)
    else:assert '<= 1949' in view['age_group_derivations']['75']['condition']

def test_claims_preserve_metric_entity_units_period_sources_limits(observed):
    for r in observed['public']['records'].values():
        for c in r.get('claims',[]):
            assert all(c.get(k) for k in ('metric_id','subject','entity_id','unit','reference_periods','source_ids','evidence_path','derivation','forbidden_inferences'))

def test_no_global_dedup_or_regex_routing():
    text=(PORTAL/'tools.py').read_text(encoding='utf-8')
    delta=text[text.index('"""Public adapter appended'):]
    assert not any(k in delta for k in ('seen_calls','seen_requests','conversation_id','session_id'))
    main=ast.parse((PORTAL/'main.py').read_text(encoding='utf-8'))
    assert not any(isinstance(n,ast.Import) and any(x.name=='re' for x in n.names) for n in ast.walk(main))

def test_observed_transport_and_contract_recovery_are_distinct(observed):
    transport=observed['faults']['records']['synthetic_observed_transport']['view']
    contract=observed['faults']['records']['synthetic_contract_failure']['view']
    assert not transport['claims'] and not contract['claims']
    assert transport['error']['error_class']=='observed_transport_failure'
    assert transport['error']['retry_same_arguments'] is True and transport['error']['maximum_identical_retries']==1
    assert contract['error']['retry_same_arguments'] is False and contract['error']['maximum_identical_retries']==0

def test_unchanged_engine_assets_provider_and_two_independent_builds():
    baseline=blob(BASE_ZIP);assert sha(baseline)==BASE_HASH
    with zipfile.ZipFile(io.BytesIO(baseline)) as a,zipfile.ZipFile(ZIP) as b:
        assert a.namelist()==b.namelist() and b.read('tools.py').startswith(a.read('tools.py'))
        assert [n for n in a.namelist() if a.read(n)!=b.read(n)]==['main.py','tools.py']
    before=ZIP.read_bytes(),MANIFEST.read_bytes();build();assert before==(ZIP.read_bytes(),MANIFEST.read_bytes())
    metadata=json.loads(MANIFEST.read_bytes());assert len(metadata['context_paths'])==15 and not metadata['w1_runtime_changed'] and not metadata['v4_changed']

def test_short_general_prompt_not_specific_failure_conditioning():
    text=PROMPT.read_text(encoding='utf-8');assert len(text)<6000
    assert all(section in text for section in ('ROLE','REASONING LOOP','EVIDENCE','TOOL SELECTION','FOLLOW-UP','ERROR RECOVERY','SEMANTIC LIMITS','COMMUNICATION'))
    assert all(x not in text.casefold() for x in ('getaria','scenario-04','r19','r20','10691','8591','zegama','1km','6km'))

def test_frozen_corpus_and_protocol_outside_runtime():
    rows,sample=generate();assert generate()==(rows,sample)
    assert len(rows)==264 and len(FAMILIES)==24 and {r['family'] for r in rows}==set(FAMILIES)
    assert len(sample)==22 and not any(r['tool'] in {'simular_escenario','analizar_acceso_servicios'} for r in rows)
    first=build_corpus();assert build_corpus()==first
    with zipfile.ZipFile(ZIP) as z:assert not any('corpus' in n or 'protocol' in n for n in z.namelist())
