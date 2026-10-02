"""Independent structured properties; no simulated natural-language routing."""
import ast
import io
import json
import random
import subprocess
import sys
import zipfile
import pytest
from scripts.vnext_agent import verify_r15 as verifier
from scripts.vnext_agent.build_r19 import BASE_HASH,BASE_ZIP,ZIP,MANIFEST,PORTAL,PROMPT,blob,build,sha
from scripts.vnext_agent.eval_r19 import generate,build as build_corpus,FAMILIES

REMOVED={'consultar_capacidades':['pregunta_o_dimension'],'comparar_municipios':['periodo','categoria_servicio','umbral_km'],'analizar_envejecimiento':['periodo'],'analizar_acceso_servicios':['periodo'],'analizar_coincidencia':['periodo'],'simular_escenario':['periodo'],'obtener_resumen_territorial':['periodo']}

def focal_cases():
    cases=[]
    def add(id,tool,args,**extra):cases.append(dict(id=id,tool=tool,arguments=args,keep_view=True,**extra))
    bases={'consultar_capacidades':{},'comparar_municipios':{'municipios':['Eibar','Tolosa']},'analizar_envejecimiento':{},'analizar_acceso_servicios':{'categoria_servicio':'mental_health','municipios':['Getaria']},'analizar_coincidencia':{'categoria_servicio':'primary_care'},'simular_escenario':{'accion':'change_threshold','categoria_servicio':'primary_care','nuevo_umbral_km':3},'obtener_resumen_territorial':{'municipio':'Orio'}}
    for tool,fields in REMOVED.items():
        for field in fields:
            for i,value in enumerate(('', '.', None, '2025-01-01')):add(f'removed:{tool}:{field}:{i}',tool,{**bases[tool],field:value})
    for age in ('65','75'):
        for measure in ('percentage','count'):add('rank'+age+measure,'analizar_envejecimiento',{'grupo_edad':age,'medida':measure,'top_n':5})
        add('compare'+age,'comparar_municipios',{'municipios':['Eibar','Tolosa'],'grupo_edad':age})
        add('coincidence'+age,'analizar_coincidencia',{'categoria_servicio':'primary_care','grupo_edad':age,'umbral_km':2})
    for town in ('Getaria','Eibar','Tolosa','Aduna'):
        for category in ('mental_health','primary_care','hospital'):
            for state,extra in [('omitted',{}),('none',{'umbral_km':1.0}),('explicit',{'umbral_km':1.0})]:
                add(f'access:{town}:{category}:{state}','analizar_acceso_servicios',{'categoria_servicio':category,'municipios':[town],**extra})
    add('all_omitted','analizar_acceso_servicios',{'categoria_servicio':'primary_care'})
    add('all_none','analizar_acceso_servicios',{'categoria_servicio':'primary_care','municipios':None})
    add('capabilities','consultar_capacidades',{})
    add('summary','obtener_resumen_territorial',{'municipio':'Orio'})
    add('source','consultar_fuente',{'source_id':'EUSTAT_EMH_2025'})
    add('source_missing','consultar_fuente',{})
    for i,text in enumerate(('',' ','.','UNKNOWN')):
        add(f'badsource:{i}','consultar_fuente',{'source_id':text})
        add(f'badage:{i}','analizar_envejecimiento',{'grupo_edad':text})
    for value in (0,101):
        add('badthreshold:'+str(value),'analizar_acceso_servicios',{'categoria_servicio':'primary_care','umbral_km':value})
    for phrase in ('Muéstrame la población mayor','Quiero el resumen','Dilo con otras palabras'):
        add('phrase:'+phrase,'obtener_resumen_territorial',{'municipio':'Orio'},prompt=phrase)
    return cases

@pytest.fixture(scope='module')
def observed(tmp_path_factory):
    build();root=tmp_path_factory.mktemp('r19-interface')
    with zipfile.ZipFile(ZIP) as z:z.extractall(root)
    return verifier.run_worker(root,focal_cases())

@pytest.mark.parametrize('tool,fields',REMOVED.items())
def test_removed_fields_cannot_bind(observed,tool,fields):
    for field in fields:
        assert field not in observed['signatures'][tool]['fields']
        for i in range(4):
            row=observed['records'][f'removed:{tool}:{field}:{i}']
            assert row['status']=='binding_rejected' and row['execute_calls']==0 and row['claims']==0

@pytest.mark.parametrize('age,measure',[('65','percentage'),('65','count'),('75','percentage'),('75','count')])
def test_age_group_isolation(observed,age,measure):
    view=observed['records']['rank'+age+measure]['view']
    assert view['status']=='valid' and set(view['age_group_derivations'])=={age}
    assert 'age_group_derivation' not in view
    for claim in view['claims']:
        assert claim['age_group']==age and claim['age_derivation_ref']=='/age_group_derivations/'+age
    if age=='65':
        assert '1949' not in json.dumps(view) and 'population_75_plus' not in json.dumps(view)
        assert view['claims'][0]['value']==(27.931 if measure=='percentage' else 48832)
    else:assert '<= 1949' in view['age_group_derivations']['75']['condition']

def test_both_groups_separate_claim_semantics(observed):
    view=observed['records']['summary']['view'];assert set(view['age_group_derivations'])=={'65','75'}
    for claim in view['claims']:
        if claim.get('age_group'):
            assert claim['age_derivation_ref']=='/age_group_derivations/'+claim['age_group']
            assert view['age_group_derivations'][claim['age_group']]['output_field']=='population_'+claim['age_group']+'_plus'

def test_capabilities_zero_arg_and_public_catalog(observed):
    view=observed['records']['capabilities']['view'];assert view['status']=='valid'
    assert observed['signatures']['consultar_capacidades']['fields']==[]
    assert len(view['capabilities'])==9 and view['sources_catalog']
    for cap in view['capabilities']:
        assert set(f['name'] for f in cap['input_fields'])==set(observed['signatures'][cap['id']]['fields'])
        assert not any(f['name'] in REMOVED.get(cap['id'],[]) for f in cap['input_fields'])
    assert observed['signatures']['consultar_fuente']['required']==['source_id']
    assert observed['records']['source_missing']['status']=='binding_rejected'

def test_getaria_first_structured_call(observed):
    r=observed['records']['access:Getaria:mental_health:omitted'];v=r['view']
    assert r['status']=='valid' and r['execute_calls']==1
    assert [c['value'] for c in v['claims'] if c['metric_id']=='nearest_distance_m']==[2913.3]
    assert v['municipal_classifications'][0]['value'] is False
    assert v['municipal_classifications'][0]['subject']=='punto representativo municipal'
    assert all(c['period']=='2026-09-20;2025-05-07' for c in v['claims'])

@pytest.mark.parametrize('town',['Getaria','Eibar','Tolosa','Aduna'])
def test_entity_category_substitution_and_defaults(observed,town):
    for category in ('mental_health','primary_care','hospital'):
        records=[observed['records'][f'access:{town}:{category}:{state}'] for state in ('omitted','none','explicit')]
        assert all(r['status']=='valid' for r in records)
        assert len({r['raw_sha256'] for r in records})==1
        assert all(all(c['entity_label']==town for c in r['view']['claims'] if c['entity_type']=='municipality') for r in records)

def test_optional_list_none_is_all_not_empty_text(observed):
    a,b=(observed['records'][key] for key in ('all_omitted','all_none'))
    assert a['status']==b['status']=='valid' and a['raw_sha256']==b['raw_sha256']

def test_errors_have_no_claims_or_retry_permission(observed):
    for key,record in observed['records'].items():
        assert record['status']!='escaped_exception',key
        if record['status']=='error':
            view=record['view'];assert view['claims']==[]
            assert view['error']['retry_same_call'] is False
            assert type(view['error']['invalid_fields']) is list
            assert view['error']['recommended_next_step']
            assert not any(k in view for k in ('mobility','municipal_classifications','age_group_derivations'))
    assert observed['records']['badage:0']['view']['error']['invalid_fields']==['grupo_edad']
    assert observed['records']['badage:0']['view']['error']['allowed_values']['grupo_edad']==['65','75']

def test_every_claim_has_typed_grounding(observed):
    for record in observed['records'].values():
        for c in record.get('view',{}).get('claims',[]):
            for key in ('metric_id','subject','unit','entity_id','source_ids','reference_periods','derivation','evidence_path','forbidden_inferences'):assert c.get(key), (key,c)

def test_phrase_properties_are_only_structured_request_stability(observed):
    rows=[r for k,r in observed['records'].items() if k.startswith('phrase:')]
    assert len({r['raw_sha256'] for r in rows})==1

def test_enum_annotations_no_unnecessary_optional_free_text():
    tree=ast.parse((PORTAL/'main.py').read_text(encoding='utf-8'))
    functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.decorator_list]
    assert len(functions)==9
    optional_strings=[]
    for f in functions:
        optional=f.args.args[len(f.args.args)-len(f.args.defaults):] if f.args.defaults else []
        for arg in optional:
            annotation=ast.unparse(arg.annotation)
            if annotation in ('str','str | None'):optional_strings.append((f.name,arg.arg))
    assert optional_strings==[('simular_escenario','service_id')]
    for f in functions:
        for arg in f.args.args:
            if arg.arg in {'grupo_edad','categoria_servicio','medida','accion'}:assert ast.unparse(arg.annotation).startswith('Literal[')

def test_package_changed_members_only_and_double_build():
    before=(ZIP.read_bytes(),MANIFEST.read_bytes());build();assert before==(ZIP.read_bytes(),MANIFEST.read_bytes())
    original=blob(BASE_ZIP);assert sha(original)==BASE_HASH
    with zipfile.ZipFile(io.BytesIO(original)) as old,zipfile.ZipFile(ZIP) as new:
        assert old.namelist()==new.namelist()
        assert [name for name in old.namelist() if old.read(name)!=new.read(name)]==['main.py','tools.py']
    meta=json.loads(MANIFEST.read_bytes());assert len(meta['context_paths'])==15 and meta['w1_runtime_changed'] is False

def test_nonfinite_values_at_python_boundary(tmp_path):
    # Nonfinite values cannot travel through the strict JSON worker protocol;
    # inject Python values directly in a separate process instead.
    with zipfile.ZipFile(ZIP) as z:z.extractall(tmp_path)
    program="""import sys,json
sys.path.insert(0,sys.argv[1])
import main,tools
for value in (float('nan'),float('inf'),float('-inf')):
 for fn,args in [(main.analizar_acceso_servicios,dict(categoria_servicio='primary_care',umbral_km=value)),(main.simular_escenario,dict(accion='add_service',categoria_servicio='primary_care',latitud=value,longitud=-2))]:
  view=json.loads(fn(**args))
  assert view['status']=='error' and view['claims']==[] and view['error']['retry_same_call'] is False
print('PASS: six nonfinite calls, zero claims')
"""
    result=subprocess.run([sys.executable,'-c',program,str(tmp_path)],cwd=tmp_path,text=True,capture_output=True)
    assert result.returncode==0,result.stderr

def test_prompt_is_general_not_benchmark_conditioning():
    text=PROMPT.read_text(encoding='utf-8').casefold()
    assert len(text)<5000
    assert all(word not in text for word in ('getaria','legazpi','legorreta','alegia','orio','aduna','zegama','1949','2913','27.931'))

def test_seeded_corpus_frozen_properties():
    first=generate();assert first==generate()
    rows,sample=first;assert len(rows)==216 and len(sample)==18
    assert {r['family'] for r in rows}==set(FAMILIES)
    for row in rows:assert not set(row['arguments'])&set(REMOVED.get(row['tool'],[]))
    build_corpus()
    protocol=json.loads((PORTAL.parents[2]/'outputs/r19/real-protocol.json').read_bytes())
    assert protocol['selected_before_any_response'] and protocol['offline_llm_calls']==0
