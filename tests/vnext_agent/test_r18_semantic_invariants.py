"""Properties of evidence/projection, not simulated LLM routing or holdout."""
import ast
import copy
import io
import json
import zipfile
from pathlib import Path
import pytest
from scripts.vnext_agent import r18_semantics as semantics,verify_r15 as verifier
from scripts.vnext_agent.build_r18 import BASE_HASH,BASE_ZIP,MANIFEST,PORTAL,PROMPT,ZIP,blob,build,sha
from scripts.vnext_agent.eval_r18 import build as corpus_build,generate

@pytest.fixture(scope='module')
def observed(tmp_path_factory):
    build(); root=tmp_path_factory.mktemp('r18-semantic')
    with zipfile.ZipFile(ZIP) as z:z.extractall(root)
    cases=[
        {'id':'summary','tool':'obtener_resumen_territorial','arguments':{'municipio':'Tolosa'}},
        {'id':'entity','tool':'obtener_resumen_territorial','arguments':{'municipio':'Eibar'}},
        {'id':'comparison','tool':'comparar_municipios','arguments':{'municipios':['Eibar','Tolosa'],'grupo_edad':'75'}},
        {'id':'access','tool':'analizar_acceso_servicios','arguments':{'categoria_servicio':'primary_care','municipios':['Aduna','Tolosa'],'umbral_km':2}},
        {'id':'coincidence','tool':'analizar_coincidencia','arguments':{'categoria_servicio':'primary_care','grupo_edad':'65','umbral_km':2}},
        {'id':'age_mutation','tool':'analizar_coincidencia','arguments':{'categoria_servicio':'primary_care','grupo_edad':'75','umbral_km':3,'cuantil':0.8}},
        {'id':'scenario','tool':'simular_escenario','arguments':{'accion':'change_threshold','categoria_servicio':'primary_care','nuevo_umbral_km':3}},
        {'id':'capabilities','tool':'consultar_capacidades','arguments':{}},
        {'id':'source','tool':'consultar_fuente','arguments':{'source_id':'EUSTAT_EMH_2025'}},
        {'id':'invalid','tool':'consultar_capacidades','arguments':{'pregunta_o_dimension':''}},
        {'id':'invalid_age','tool':'analizar_envejecimiento','arguments':{'grupo_edad':'66'}},
        {'id':'threshold','tool':'analizar_acceso_servicios','arguments':{'categoria_servicio':'primary_care','municipios':['Aduna','Tolosa'],'umbral_km':3}},
        {'id':'paraphrase','tool':'obtener_resumen_territorial','arguments':{'municipio':'Tolosa'},'prompt':'Quiero saberlo con otras palabras, por favor.'},
    ]
    visit={'origin_id':'zegama_center_stops','destination_id':'beasain_official_centre_anchor','date':'2026-09-29','appointment_time':'09:30','duration_minutes':20}
    for name,delta in [('main',{}),('time',{'appointment_time':'09:45'}),('duration',{'duration_minutes':35}),('unsupported',{'date':'2030-01-01'})]:
        cases.append({'id':name,'tool':'plan_visit','arguments':{**visit,**delta}})
    for c in cases:c['keep_view']=True
    return verifier.run_worker(root,cases)

def views(observed):
    return [r['view'] for r in observed['records'].values()]

def test_p01_subject_preserved_and_radius_never_population(observed):
    for v in views(observed):
        for c in v.get('claims',[]):
            assert c['subject'] and c['numeric_role']=='analytical'
            if c['metric_id'] in semantics._DISTANCE_FIELDS:
                assert c['subject']=='punto representativo municipal y registro sanitario'
                assert 'distribución espacial' in c['forbidden_inferences'][0]
    for c in observed['records']['access']['view']['municipal_classifications']:
        assert c['subject']=='punto representativo municipal' and type(c['value']) is bool

@pytest.mark.parametrize('field',['within_threshold_count','outside_threshold_count','highlighted_count','affected_rows','improved_distance_rows','worsened_distance_rows','threshold_status_changes'])
def test_p02_municipal_units_not_registry_counts(field):
    assert semantics._semantic_kind(field)[2]=='municipios'
    assert semantics._semantic_kind('registered_service_count')[2]=='registros'

def test_p02_relative_distance_unit_is_percentage(observed):
    assert semantics._semantic_kind('difference_relative_pct')[2]=='%'
    assert all(c['unit']=='%' for c in observed['records']['scenario']['view']['claims'] if c['metric_id']=='difference_relative_pct')

def test_p03_sources_preserved_by_real_projection(observed):
    for v in views(observed):
        for c in v.get('claims',[]):
            assert c['source_ids'] and {r['source_id'] for r in c['reference_periods']}==set(c['source_ids'])
            assert {r['source_id'] for r in c['source_refs']}==set(c['source_ids'])

def test_p04_period_preserved_no_homogeneous_snapshot(observed):
    v=observed['records']['access']['view']
    for c in v['claims']:
        assert c['period']=='2026-09-20;2025-05-07'
    for c in observed['records']['summary']['view']['claims']:
        if c['metric_id'].startswith(('pct_','population')):assert c['period']=='2025-01-01'

def test_p05_entity_substitution_really_executes_other_municipality(observed):
    a,b=(observed['records'][k] for k in ('summary','entity'))
    assert a['execute_calls']==b['execute_calls']==1 and a['raw_sha256']!=b['raw_sha256']
    assert {c['entity_id'] for c in a['view']['claims']}=={'20071'}
    assert {c['entity_id'] for c in b['view']['claims']}=={'20030'}

def test_p06_derivation_preserves_numerator_denominator(observed):
    for v in views(observed):
        for c in v.get('claims',[]):
            if c['metric_id'].startswith('pct_'):
                n,d=c['numerator'],c['denominator']
                assert n['unit']==d['unit']=='personas'
                assert n['period']==d['period']=='2025-01-01'
                assert n['source_id']==d['source_id']=='EUSTAT_EMH_2025'
                assert c['value']==round(n['value']/d['value']*100,3)

def test_p07_every_public_capability_has_subject_and_limits(observed):
    caps=observed['records']['capabilities']['view']['capabilities']
    enabled=[c for c in caps if c['enabled']]
    assert len(enabled)==9
    for cap in enabled:assert cap['semantic_contract']['subject'] and cap['semantic_contract']['limits']
    access=next(c for c in enabled if c['id']=='analizar_acceso_servicios')
    assert 'distribución espacial' in access['semantic_contract']['forbidden_inferences'][0]

@pytest.mark.parametrize('name',['invalid','invalid_age','unsupported'])
def test_p08_error_has_zero_analytical_evidence(observed,name):
    v=observed['records'][name]['view']
    assert v['status']!='valid' and not v['claims'] and 'mobility' not in v

@pytest.mark.parametrize('before,after',[('access','threshold'),('coincidence','age_mutation'),('main','time'),('main','duration')])
def test_p09_changed_parameters_produce_new_bound_execution(observed,before,after):
    a,b=(observed['records'][k] for k in (before,after))
    assert a['execute_calls']==b['execute_calls']==1
    assert a['raw_sha256']!=b['raw_sha256']
    assert a['view']['normalized_input']!=b['view']['normalized_input']

def test_p10_metadata_projection_hides_raw_and_keeps_history(observed):
    for v in views(observed):assert 'raw_result_json' not in v and 'versions' not in v
    with zipfile.ZipFile(ZIP) as z,zipfile.ZipFile(io.BytesIO(blob(BASE_ZIP))) as old:
        for n in z.namelist():
            if n not in {'main.py','tools.py'}:assert z.read(n)==old.read(n)

def test_p11_time_numbers_components_and_scope_consistent(observed):
    for name in ('main','time','duration'):
        scenario=observed['records'][name]['view']['mobility']['scenarios'][0]
        t=scenario['time_summary']
        assert t['total_s']==sum(scenario['components_s'].values())==t['scope_end_s']-t['scope_start_s']
        seconds=t['total_s']
        assert t['total_hms']==f'{seconds//3600} h {seconds%3600//60} min {seconds%60} s'
    assert observed['records']['main']['view']['mobility']['scenarios'][0]['time_summary']['total_s']==10691
    assert observed['records']['time']['view']['mobility']['scenarios'][0]['time_summary']['total_s']==8591

def test_p12_operational_metadata_not_analytical(observed):
    for v in views(observed):
        assert all(c['metric_id'] not in semantics._OPERATIONAL_FIELDS for c in v['claims'])
        if v['status']=='valid':assert v['operational_metadata']['not_analytical_evidence'] is True

def test_unregistered_future_numeric_metric_fails_closed(monkeypatch):
    monkeypatch.setattr(semantics,'ContractViolation',ValueError,raising=False)
    with pytest.raises(ValueError,match='unclassified_metric'):semantics._semantic_kind('invented_population_in_radius')

def test_metamorphic_irrelevant_wording_not_read_by_tool(observed):
    a,b=(observed['records'][k] for k in ('summary','paraphrase'))
    assert a['raw_sha256']==b['raw_sha256'] and a['view']==b['view']
    # This proves deterministic tool invariance, NOT that the LLM maps prose.

def test_general_prompt_not_router_or_gold_cases():
    prompt=PROMPT.read_text(encoding='utf-8')
    for value in ('Zegama','Segura','Aduna','Tolosa','Eibar','Ordizia','10691','8591','507','09:30','09:45'):
        assert value not in prompt
    assert all(section in prompt for section in ('ROLE','EVIDENCE','REASONING LOOP','TOOL USE','CONTEXT','NUMBERS','SOURCES','LIMITS','RECOVERY','STYLE'))
    assert 'time_summary' in prompt and 'age_group_derivation' in prompt
    tree=ast.parse((PORTAL/'main.py').read_text(encoding='utf-8'))
    assert not any(isinstance(n,ast.Import) and any(x.name=='re' for x in n.names) for n in ast.walk(tree))

def test_reproducible_two_member_delta_and_corpus():
    build(); before,meta=ZIP.read_bytes(),MANIFEST.read_bytes();build()
    assert before==ZIP.read_bytes() and meta==MANIFEST.read_bytes()
    with zipfile.ZipFile(io.BytesIO(before)) as z,zipfile.ZipFile(io.BytesIO(blob(BASE_ZIP))) as old:
        assert z.namelist()==old.namelist()
        assert [n for n in z.namelist() if z.read(n)!=old.read(n)]==['main.py','tools.py']
    a=corpus_build();b=corpus_build();assert a==b and a['size']==156
    corpus,sample=generate();assert len(sample)==13 and len({x['family'] for x in sample})==13
    assert all(x not in json.loads(meta)['members'] for x in ['generated-corpus.json','real-protocol.json'])
