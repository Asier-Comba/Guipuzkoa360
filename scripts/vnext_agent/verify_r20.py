"""Frozen R19/R20 raw parity, public mappings, boundaries and metamorphics."""
import argparse
import ast
from concurrent.futures import ThreadPoolExecutor
import io
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import zipfile
from scripts.vnext_agent.build_r20 import ROOT,ZIP,MANIFEST,BASE,BASE_ZIP,BASE_HASH,PUBLIC_TOOLS,blob,sha
from scripts.vnext_agent import verify_r15 as legacy

def run_worker(root,cases):
    output=subprocess.run([sys.executable,'-X','utf8','-m','scripts.vnext_agent.worker_r20',str(root)],cwd=ROOT,input=json.dumps({'cases':cases},allow_nan=False),capture_output=True,text=True,encoding='utf-8',timeout=600)
    if output.returncode:raise RuntimeError(output.stderr)
    return json.loads(output.stdout)

def focal_cases():
    rows=[]
    def add(id,tool,args,**kw):rows.append(dict(id=id,tool=tool,arguments=args,**kw))
    for category in ('primary_care','mental_health','hospital','other_health'):
        add('general:'+category,'analizar_acceso_general',dict(categoria_servicio=category,umbral_km=1),keep_raw=True)
        for town in ('Getaria','Aduna','Eibar','Tolosa'):
            add('selected:'+category+':'+town,'analizar_acceso_municipios',dict(categoria_servicio=category,umbral_km=1,municipios=[town]),keep_raw=True)
        for old,new in ((1,6),(2,3),(100,1),(1,1)):
            add(f'change:{category}:{old}:{new}','simular_cambiar_umbral',dict(categoria_servicio=category,umbral_actual_km=old,nuevo_umbral_km=new),keep_raw=True)
        add('add:'+category,'simular_anadir_servicio',dict(categoria_servicio=category,latitud=43,longitud=-2,umbral_km=1),keep_raw=True)
    add('caps','consultar_capacidades',{})
    add('summary','obtener_resumen_territorial',{'municipio':'Aduna'})
    add('source','consultar_fuente',{'source_id':'EUSTAT_EMH_2025'})
    for age in ('65','75'):
        add('rank'+age,'analizar_envejecimiento',{'grupo_edad':age,'medida':'percentage','top_n':5})
        add('compare'+age,'comparar_municipios',{'municipios':['Eibar','Tolosa'],'grupo_edad':age})
        add('compare_reverse'+age,'comparar_municipios',{'municipios':['Tolosa','Eibar'],'grupo_edad':age})
        add('coincidence'+age,'analizar_coincidencia',{'categoria_servicio':'primary_care','grupo_edad':age,'umbral_km':2,'cuantil':.75},keep_raw=True)
    for selector in (['Getaria','Eibar'],['Eibar','Getaria'],['20039'],['Getaria']):
        add('selector:'+repr(selector),'analizar_acceso_municipios',dict(categoria_servicio='mental_health',umbral_km=1,municipios=selector),keep_raw=True)
    for age in ('omitted','explicit'):
        add('defaults:'+age,'analizar_envejecimiento',{} if age=='omitted' else dict(grupo_edad='65',medida='percentage',top_n=10))
    for source in ('EUSTAT_EMH_2025','EUSTAT_EMH_2025'):
        add('repeat_source:'+str(len(rows)),'consultar_fuente',{'source_id':source})
    return rows

def negative_cases():
    rows=[]
    bases={'analizar_acceso_general':dict(categoria_servicio='primary_care',umbral_km=1),'analizar_acceso_municipios':dict(categoria_servicio='primary_care',umbral_km=1,municipios=['Aduna']),'simular_anadir_servicio':dict(categoria_servicio='primary_care',latitud=43,longitud=-2,umbral_km=1),'simular_retirar_servicio':dict(categoria_servicio='primary_care',service_id='UNKNOWN',umbral_km=1),'simular_cambiar_umbral':dict(categoria_servicio='mental_health',umbral_actual_km=1,nuevo_umbral_km=6)}
    def add(tool,args,**kw):rows.append(dict(id='invalid:'+str(len(rows)),tool=tool,arguments=args,expected='safe_error',**kw))
    for tool,args in bases.items():
        for key in args:
            add(tool,{k:v for k,v in args.items() if k!=key})
            for value in (None,'',' ','.',[],{},True):add(tool,{**args,key:value})
        forbidden={'analizar_acceso_general':['municipios','periodo'],'analizar_acceso_municipios':['periodo'],'simular_anadir_servicio':['service_id','nuevo_umbral_km','accion','periodo'],'simular_retirar_servicio':['latitud','longitud','nuevo_umbral_km','accion','periodo'],'simular_cambiar_umbral':['latitud','longitud','service_id','accion','umbral_km','periodo']}[tool]
        for key in forbidden:add(tool,{**args,key:None})
        for field in args:
            if 'umbral' in field:
                for value in (-1,0,100.001):add(tool,{**args,field:value})
                for token in ('nan','inf','-inf'):add(tool,args,nonfinite={field:token})
    for value in ([],None,[''],[' '],['Aduna','Aduna'],['Aduna','20002'],['UNKNOWN'],['*'],['ALL'],['Aduna']*89):
        add('analizar_acceso_municipios',{**bases['analizar_acceso_municipios'],'municipios':value})
    for value in ([],['Aduna'],['Eibar','Eibar'],['Eibar','20030'],['UNKNOWN','Tolosa']):add('comparar_municipios',{'municipios':value})
    for field,limit in (('latitud',90),('longitud',180)):
        for value in (limit+1,-limit-1):add('simular_anadir_servicio',{**bases['simular_anadir_servicio'],field:value})
        for token in ('nan','inf','-inf'):add('simular_anadir_servicio',bases['simular_anadir_servicio'],nonfinite={field:token})
    add('simular_retirar_servicio',bases['simular_retirar_servicio'])
    rng=random.Random(2002026)
    # Five thousand input-boundary attacks, not five thousand happy-path outputs.
    fuzz=[]
    for i in range(5000):
        tool=rng.choice(list(bases));args=dict(bases[tool]);key=rng.choice([k for k in args if k!='service_id'])
        values=(None,'',' ','.',[],{},True)
        args[key]=rng.choice(values)
        fuzz.append(dict(id=f'fuzz:{i:04d}',tool=tool,arguments=args,expected='safe_error'))
    return rows,fuzz

def mapped_case(case):
    tool=case['tool'];args=dict(case['arguments'])
    # A public Python call materializes its signature defaults in locals().
    # Mirror THAT boundary in the independent engine call, rather than falsely
    # comparing it with a caller that omitted engine arguments/provenance.
    if case.get('route','public')!='internal':
        defaults={'analizar_envejecimiento':dict(grupo_edad='65',medida='percentage',top_n=10),'comparar_municipios':dict(grupo_edad='65'),'analizar_coincidencia':dict(grupo_edad='65',umbral_km=1.0,cuantil=.75)}
        args={**defaults.get(tool,{}),**args}
    if tool.startswith('analizar_acceso_'):tool='analizar_acceso_servicios'
    if tool=='simular_cambiar_umbral':tool='simular_escenario';args['accion']='change_threshold';args['umbral_km']=args.pop('umbral_actual_km')
    elif tool=='simular_anadir_servicio':tool='simular_escenario';args.update(accion='add_service',service_id=None)
    elif tool=='simular_retirar_servicio':tool='simular_escenario';args['accion']='remove_service'
    if tool=='plan_visit' and 'request' not in args:args={'request':args}
    return {**case,'tool':tool,'arguments':args,'route':'internal'}

def run(output):
    candidate=ZIP.read_bytes();baseline=blob(BASE_ZIP);assert sha(baseline)==BASE_HASH
    meta=json.loads(MANIFEST.read_bytes());assert meta['sha256']==sha(candidate)
    with zipfile.ZipFile(io.BytesIO(baseline)) as a,zipfile.ZipFile(io.BytesIO(candidate)) as b:
        assert a.namelist()==b.namelist()
        changed=[name for name in a.namelist() if a.read(name)!=b.read(name)];assert changed==['main.py','tools.py']
        assert b.read('tools.py').startswith(a.read('tools.py'))
        # Prefix preservation proves every old engine/helper/validation statement
        # remains byte-identical, including embedded W1 helpers and formulae.
    with tempfile.TemporaryDirectory(prefix='r20-acceptance-') as temp:
        old,new=(Path(temp)/x for x in ('r19','r20'))
        for root,data in ((old,baseline),(new,candidate)):
            with zipfile.ZipFile(io.BytesIO(data)) as z:z.extractall(root)
        focal=focal_cases();initial=run_worker(new,focal)
        for category in ('primary_care','mental_health','hospital','other_health'):
            services=initial['records']['general:'+category]['view'].get('observed_services',[])
            assert services,(category,initial['records']['general:'+category])
            focal.append(dict(id='remove:'+category,tool='simular_retirar_servicio',arguments=dict(categoria_servicio=category,service_id=services[0]['service_id'],umbral_km=1),keep_raw=True))
        from scripts.vnext_agent.eval_r20 import generate
        corpus,_=generate();negative,fuzz=negative_cases()
        legacy_cases=legacy.make_cases(baseline,json.loads(legacy.ORACLE.read_bytes()))
        # Historical audits stay internal and unchanged, not misrouted through
        # the deliberately removed public generic operations.
        historical=[mapped_case(c) for c in legacy_cases]
        old_cases=[mapped_case(c) for c in focal+corpus]+historical
        new_cases=focal+corpus+historical+negative+fuzz
        with ThreadPoolExecutor(max_workers=2) as pool:
            af=pool.submit(run_worker,old,old_cases);bf=pool.submit(run_worker,new,new_cases);a,b=af.result(),bf.result()
    findings=[];parity=0;oracle=0;records=[]
    for c in focal+corpus+historical:
        ident=c['id'];left,right=a['records'][ident],b['records'][ident];issues=[]
        if left['status']!=right['status'] or left.get('raw_sha256')!=right.get('raw_sha256'):issues.append('raw_or_status_drift')
        else:parity+=1
        if left.get('effective_request')!=right.get('effective_request'):issues.append('effective_request_drift')
        if left.get('claims')!=right.get('claims'):issues.append('analytical_claim_drift')
        if right['status']=='escaped_exception':issues.append('escaped_exception')
        if c.get('oracle'):
            if right.get('oracle',{}).get('pass'):oracle+=1
            else:issues.append('oracle')
        if issues:findings.append({'id':ident,'issues':issues})
        records.append({'id':ident,'status':right['status'],'raw_sha256':right.get('raw_sha256'),'issues':issues})
    for c in negative+fuzz:
        r=b['records'][c['id']]
        if r['status'] not in {'error','binding_rejected'} or r.get('claims') or (r.get('view',{}).get('error',{}).get('retry_same_arguments') not in (None,False)):
            findings.append({'id':c['id'],'issues':['unsafe_invalid'],'record':r})
    caps=b['records']['caps']['view']['capabilities'];sigs=b['signatures']
    assert set(sigs)==set(PUBLIC_TOOLS)=={c['id'] for c in caps}
    for cap in caps:
        assert set(f['name'] for f in cap['input_fields'])==set(sigs[cap['id']]['fields'])
        assert set(f['name'] for f in cap['input_fields'] if f['required'])==set(sigs[cap['id']]['required'])
    # Distinct metamorphic checks, each uses independent rows/outputs.
    props={}
    props['entity_substitution']=all(all(v['entity_label']==town for v in b['records']['selected:mental_health:'+town]['claims'] if v['entity_type']=='municipality') for town in ('Getaria','Aduna','Eibar','Tolosa'))
    props['age_isolation']=all(set(b['records']['rank'+age]['view']['age_group_derivations'])=={age} for age in ('65','75'))
    props['category_substitution']=all(r['engine_input']['arguments']['categoria_servicio']==category for category in ('primary_care','mental_health','hospital','other_health') for r in [b['records']['general:'+category]])
    threshold_rows=b['records']['change:mental_health:1:6']['raw']['data']
    props['threshold_only']=all(r['baseline_distance_m']==r['scenario_distance_m'] for r in threshold_rows)
    props['defaults_equivalence']=b['records']['defaults:omitted']['raw_sha256']==b['records']['defaults:explicit']['raw_sha256']
    props['source_stability']=len({r['raw_sha256'] for k,r in b['records'].items() if k.startswith('repeat_source:')})==1
    props['comparison_order']=sorted((c['metric_id'],c['entity_id'],c['value']) for c in b['records']['compare65']['claims'])==sorted((c['metric_id'],c['entity_id'],c['value']) for c in b['records']['compare_reverse65']['claims'])
    props['code_name_equivalence']=b['records']["selector:['20039']"]['raw_sha256']==b['records']["selector:['Getaria']"]['raw_sha256']
    props['selector_order']=b['records']["selector:['Getaria', 'Eibar']"]['raw_sha256']==b['records']["selector:['Eibar', 'Getaria']"]['raw_sha256']
    props['boundary_rejection']=not any(f['issues']==['unsafe_invalid'] for f in findings)
    props['claim_grounding']=all(all(c.get(k) for k in ('metric_id','subject','unit','entity_id','source_ids','reference_periods','derivation','evidence_path','forbidden_inferences')) for r in b['records'].values() for c in r.get('claims',[]))
    for key,value in props.items():
        if not value:findings.append({'id':'metamorphic:'+key,'issues':['property_failed']})
    result={'status':'FAIL' if findings else 'PASS','classification':'AUTHOR_OFFLINE_NOT_PORTAL_OR_LLM','base':BASE,'zip_sha256':sha(candidate),'manifest_sha256':sha(MANIFEST.read_bytes()),'raw_cases':len(old_cases),'raw_parity':parity,'oracle':oracle,'focal':len(focal),'corpus':len(corpus),'negative':len(negative),'fuzz':len(fuzz),'metamorphic':props,'findings':findings,'records':records,'public_tools':len(sigs),'changed_members':changed,'model_calls':0}
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    return {k:v for k,v in result.items() if k!='records'}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'outputs/r20/offline-audit.json');args=parser.parse_args();report=run(args.output);print(json.dumps(report,sort_keys=True));raise SystemExit(report['status']!='PASS')
