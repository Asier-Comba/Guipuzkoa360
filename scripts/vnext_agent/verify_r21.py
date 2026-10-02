"""Independent raw comparison with R20, composed summaries, sources and bounds.

Reuses the network-denied observation harness, never simulates a model reply.
Historical direct comparison/source tools are exercised only as internal oracles.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import io
import json
from pathlib import Path
import tempfile
import zipfile
from scripts.vnext_agent import verify_r20 as old, verify_r15 as legacy
from scripts.vnext_agent.build_r21 import ROOT, ZIP, MANIFEST, BASE, BASE_ZIP, BASE_HASH, PUBLIC_TOOLS, blob, sha
from scripts.vnext_agent.eval_r21 import generate, expand

run_worker = old.run_worker

def focal_cases():
    rows = []
    for row in old.focal_cases():
        if row['tool'] == 'comparar_municipios':
            for index, town in enumerate(row['arguments']['municipios']): rows.append({'id':row['id'] + ':' + str(index),'tool':'obtener_resumen_territorial','arguments':{'municipio':town}})
        elif row['tool'] == 'consultar_fuente': rows.append({**row,'tool':'consultar_capacidades','arguments':{}})
        else: rows.append(row)
    with zipfile.ZipFile(ZIP) as z:
        import csv
        towns = list(csv.DictReader(io.StringIO(z.read('datos_preparados/demografia.csv').decode('utf-8'))))
    for town in towns:
        for field in ('municipality_name','municipality_code'):
            rows.append({'id':'summary:' + town['municipality_code'] + ':' + field,'tool':'obtener_resumen_territorial','arguments':{'municipio':town[field]}})
    for clock in ('09:30','09:45'):
        rows.append({'id':'health:' + clock,'tool':'plan_visit','arguments':dict(origin_id='zegama_center_stops',destination_id='beasain_official_centre_anchor',date='2026-09-29',appointment_time=clock,duration_minutes=20)})
    return rows

def composition_check(records, comparisons):
    findings = []; count = 0
    for row in comparisons:
        age = row['arguments']['grupo_edad']; selected = []
        for index in range(len(row['arguments']['municipios'])):
            selected += records[row['id'] + ':' + str(index)]['claims']
        expected = records['internal:' + row['id']]['claims']
        for claim in expected:
            match = [c for c in selected if c['metric_id']==claim['metric_id'] and c['entity_id']==claim['entity_id'] and c['unit']==claim['unit']]
            if len(match)!=1 or any(match[0].get(k)!=claim.get(k) for k in ('value','period','source_ids')):
                findings.append({'id':row['id'],'issues':['composed_claim_mismatch'],'metric':claim['metric_id'],'age':age})
        count += 1
    return {'cases':count,'findings':findings}

def run(output):
    candidate = ZIP.read_bytes(); baseline = blob(BASE_ZIP); assert sha(baseline)==BASE_HASH
    meta = json.loads(MANIFEST.read_bytes()); assert meta['sha256']==sha(candidate)
    with zipfile.ZipFile(io.BytesIO(baseline)) as a, zipfile.ZipFile(io.BytesIO(candidate)) as b:
        assert a.namelist()==b.namelist()
        changed = [n for n in a.namelist() if a.read(n)!=b.read(n)]; assert changed==['main.py','tools.py']
        assert b.read('tools.py').startswith(a.read('tools.py'))
    with tempfile.TemporaryDirectory(prefix='r21-acceptance-') as temp:
        before, after = (Path(temp)/x for x in ('r20','r21'))
        for root, data in ((before,baseline),(after,candidate)):
            with zipfile.ZipFile(io.BytesIO(data)) as z: z.extractall(root)
        focal = focal_cases(); initial = run_worker(after,focal)
        for category in ('primary_care','hospital','mental_health','other_health'):
            identity = initial['records']['general:'+category]['view']['observed_services'][0]['service_id']
            focal.append({'id':'remove:'+category,'tool':'simular_retirar_servicio','arguments':dict(categoria_servicio=category,service_id=identity,umbral_km=1),'keep_raw':True})
        corpus, _ = generate(); expanded = expand(corpus)
        # Explicit comparisons remain internal references, never public calls.
        comparisons = [r for r in old.focal_cases() if r['tool']=='comparar_municipios']
        for r in corpus:
            if 'comparison_age' in r: comparisons.append({'id':r['id'],'tool':'comparar_municipios','arguments':{'municipios':[s['arguments']['municipio'] for s in r['composition']],'grupo_edad':r['comparison_age']}})
        refs = [{**old.mapped_case(r),'id':'internal:'+r['id']} for r in comparisons]
        historical = [old.mapped_case(r) for r in legacy.make_cases(baseline,json.loads(legacy.ORACLE.read_bytes()))]
        positive = focal + expanded + refs + historical
        negative, fuzz = old.negative_cases(); negative = [r for r in negative if r['tool'] in PUBLIC_TOOLS]
        with ThreadPoolExecutor(max_workers=2) as pool:
            fa = pool.submit(run_worker,before,[old.mapped_case(r) for r in positive]); fb = pool.submit(run_worker,after,positive+negative+fuzz)
            a,b = fa.result(),fb.result()
    findings = []; parity = 0; oracle = 0; records = []
    for row in positive:
        key = row['id']; left,right = a['records'][key], b['records'][key]; issues=[]
        if left['status']!=right['status'] or left.get('raw_sha256')!=right.get('raw_sha256'): issues.append('raw_or_status_drift')
        else: parity += 1
        for field in ('effective_request','claims'):
            if left.get(field)!=right.get(field): issues.append(field+'_drift')
        if right['status']=='escaped_exception': issues.append('escaped_exception')
        if row.get('oracle'):
            if right.get('oracle',{}).get('pass'): oracle += 1
            else: issues.append('oracle')
        if issues: findings.append({'id':key,'issues':issues})
        records.append({'id':key,'status':right['status'],'raw_sha256':right.get('raw_sha256'),'issues':issues})
    for row in negative+fuzz:
        result = b['records'][row['id']]
        if result['status'] not in {'error','binding_rejected'} or result.get('claims') or result.get('view',{}).get('error',{}).get('retry_same_arguments') not in (None,False): findings.append({'id':row['id'],'issues':['unsafe_invalid']})
    caps = b['records']['caps']['view']; sigs = b['signatures']
    # The observer emits canonical sorted JSON: mapping key order is not the
    # TOOLS registration order. Check order in the catalog and generated AST.
    assert set(sigs)==set(PUBLIC_TOOLS) and len(sigs)==10
    assert [c['id'] for c in caps['capabilities']]==PUBLIC_TOOLS and caps['public_tool_count']==10
    for cap in caps['capabilities']:
        sig = sigs[cap['id']]
        assert [f['name'] for f in cap['input_fields']]==sig['fields']
        assert {f['name'] for f in cap['input_fields'] if f['required']}==set(sig['required'])
    composed = composition_check(b['records'],comparisons); findings += composed['findings']
    props = {}
    props['age_isolation'] = all(set(b['records']['rank'+age]['view']['age_group_derivations'])=={age} for age in ('65','75'))
    props['threshold_only'] = all(r['baseline_distance_m']==r['scenario_distance_m'] for r in b['records']['change:mental_health:1:6']['raw']['data'])
    props['defaults_equivalence'] = b['records']['defaults:omitted']['raw_sha256']==b['records']['defaults:explicit']['raw_sha256']
    props['entity_substitution'] = all(all(c['entity_label']==town for c in b['records']['selected:mental_health:'+town]['claims'] if c['entity_type']=='municipality') for town in ('Getaria','Aduna','Eibar','Tolosa'))
    props['selector_order'] = b['records']["selector:['Getaria', 'Eibar']"]['raw_sha256']==b['records']["selector:['Eibar', 'Getaria']"]['raw_sha256']
    props['code_name_equivalence'] = b['records']["selector:['20039']"]['raw_sha256']==b['records']["selector:['Getaria']"]['raw_sha256']
    props['all_88_names_codes'] = all(b['records']['summary:'+code+':municipality_name']['raw_sha256']==b['records']['summary:'+code+':municipality_code']['raw_sha256'] for code in {k.split(':')[1] for k in b['records'] if k.startswith('summary:')})
    props['composed_comparison'] = not composed['findings']
    non_web_roles = {'user_parameter','modelling_assumption','derived_network','model_parameter','agent_or_user_parameter','derived_metric'}
    props['source_cards_complete'] = all(all(s.get(k) for k in ('source_id','title','institution','reference_period')) and (s.get('url') or s.get('role') in non_web_roles) for s in caps['sources_catalog']) and any(s.get('method') and s.get('limitations') for s in caps['sources_catalog'])
    props['public_health_totals'] = all(b['records']['health:'+clock]['status']=='valid' and expected in [c['value'] for c in b['records']['health:'+clock]['claims'] if c['unit']=='s'] for clock,expected in [('09:30',10691),('09:45',8591)])
    props['both_age_methods_catalog'] = set(caps['age_group_derivations'])=={'65','75'}
    props['source_stability'] = len({r['raw_sha256'] for k,r in b['records'].items() if k.startswith('repeat_source:')})==1
    props['boundary_rejection'] = not any('unsafe_invalid' in f['issues'] for f in findings)
    props['claim_grounding'] = all(all(c.get(k) for k in ('metric_id','subject','unit','entity_id','source_ids','reference_periods','derivation','evidence_path','forbidden_inferences')) for r in b['records'].values() for c in r.get('claims',[]))
    # Store catalog and composition evidence, not just a boolean count.
    output.parent.mkdir(parents=True,exist_ok=True)
    (output.parent/'catalog-observed.json').write_text(json.dumps(caps,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    for key,value in props.items():
        if not value: findings.append({'id':'metamorphic:'+key,'issues':['property_failed']})
    report = {'status':'FAIL' if findings else 'PASS','classification':'AUTHOR_OFFLINE_NOT_PORTAL_OR_LLM','base':BASE,'zip_sha256':sha(candidate),'manifest_sha256':sha(MANIFEST.read_bytes()),'raw_cases':len(positive),'raw_parity':parity,'oracle':oracle,'focal':len(focal),'corpus':len(corpus),'expanded_corpus_calls':len(expanded),'composed_comparisons':composed['cases'],'negative':len(negative),'fuzz':len(fuzz),'metamorphic':props,'findings':findings,'records':records,'public_tools':len(sigs),'changed_members':changed,'model_calls':0}
    output.write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    return {k:v for k,v in report.items() if k!='records'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--output',type=Path,default=ROOT/'outputs/r21/offline-audit.json'); args=parser.parse_args(); result=run(args.output); print(json.dumps(result,sort_keys=True)); raise SystemExit(result['status']!='PASS')
