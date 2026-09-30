"""R12 independent intake of an exact W2 ZIP in clean supported processes.

W1 fixtures supply public requests; W3 checks model projection and frozen independently
contrasted R10 data itself, without using W1's intake/parity verdict helpers.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile
from scripts.vnext_product.package_review import review_zip

PACKAGE_SHA='b4feb978b625b34f9d7331ce8d376a34a29e84e4783868f83ce48a0c0d1011be'
W1_SHA='c66d44af702eb3410fcea05ae8711f537214f675e83a7fda38c39c3b39a1b910'
W1_RUNTIME='cb061a9e00a6496c40488a596bd94834bc2c49b2'
ROOT=Path(__file__).resolve().parents[2]
CHILD=r'''
import json,os,sys,socket,inspect,traceback
from pathlib import Path
package_root=Path.cwd()
sys.path.insert(0,str(package_root))
def no_network(*a,**k):raise RuntimeError('Network denied in independent offline intake')
socket.create_connection=no_network;socket.socket=no_network
import tools,main
payload=json.load(sys.stdin)
if payload.get('foreign_cwd'):os.chdir(payload['foreign_cwd'])
results=[]
for item in payload['calls']:
    record=dict(item)
    try:
        envelope=tools.execute(item['tool'],item['arguments'],item['id'],root=package_root)
        record['envelope']=envelope
        try:record['public_result']=json.loads(tools.public_result(envelope))
        except Exception as exc:record['public_exception']={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}
        if item['tool']=='plan_visit':
            from prototypes.ir_y_volver import provider_r6 as provider
            q=item['arguments']['request']
            record['producer']=provider.compare_visits(q) if isinstance(q,list) else provider.plan_visit(q)
    except Exception as exc:record['exception']={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}
    results.append(record)
# Exact generated @tool function with fallback decorator: NOT a model routing claim.
direct={}
if not payload.get('foreign_cwd'):
    for key,q in payload['direct_requests'].items():
        try:direct[key]=json.loads(main.plan_visit(q))
        except Exception as exc:direct[key]={'exception':repr(exc)}
    def substituted(handler,args):return handler(**{**args,'municipio':'Tolosa'})
    s=tools.execute('obtener_resumen_territorial',{'municipio':'Aduna','periodo':None},'R12-substitution',root=package_root,transport=substituted)
    direct['municipal_substitution']={'envelope':s,'public_result':json.loads(tools.public_result(s))}
json.dump({'results':results,'direct_tool_outputs':direct,'tool_names':[t.__name__ for t in main.TOOLS],
    'source_signature':str(inspect.signature(main.plan_visit)),'isolated':sys.flags.isolated,'cwd_is_package':Path.cwd()==package_root,
    'model_executed':0,'network_disabled':True},sys.stdout,ensure_ascii=True)
'''


def sha(data):return hashlib.sha256(data).hexdigest()
def emit(path,data):path.write_bytes((json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode())


def projection_findings(record,labels):
    issues=[];env=record.get('envelope',{});raw_text=env.get('raw_result_json')
    if not raw_text:return [{'severity':'HIGH','id':'NO_RAW_RESULT','detail':env.get('error')}]
    raw=json.loads(raw_text);view=record.get('public_result')
    if not view:return [{'severity':'HIGH','id':'NO_PUBLIC_RESULT','detail':record.get('public_exception',record.get('exception'))}]
    if raw!=record.get('producer'):issues.append({'severity':'HIGH','id':'PRODUCER_RAW_MISMATCH'})
    raw_results=raw.get('results',[raw]);scenarios=view.get('mobility',{}).get('scenarios',[])
    if len(scenarios)!=len(raw_results):return issues+[{'severity':'HIGH','id':'SCENARIO_COUNT'}]
    stop_names={s['stop_id']:s['name'] for s in labels['stops']}
    for index,(r,v) in enumerate(zip(raw_results,scenarios)):
        for key in ['status','scenario_kind','scope','time_basis','snapshot_id','error']:
            if v.get(key)!=r.get(key):issues.append({'severity':'HIGH','id':'PUBLIC_SEMANTIC_MISMATCH','field':key,'index':index})
        if v.get('effective_parameters')!=(r.get('normalized_request') or {}):issues.append({'severity':'HIGH','id':'EFFECTIVE_PARAMETERS','index':index})
        sources={s['source_id']:s for s in v.get('sources',[])}
        for source in r['sources']:
            for key in ['source_role','publisher','url','reference_period','transformation']:
                if sources.get(source['source_id'],{}).get(key)!=source.get(key):issues.append({'severity':'HIGH','id':'PUBLIC_SOURCE','field':key,'source':source['source_id'],'index':index})
        if r['status']!='ok':
            if v.get('itinerary') is not None:issues.append({'severity':'HIGH','id':'FAILED_STATE_ITINERARY','index':index})
            continue
        if v.get('components_s')!=r['components_s']:issues.append({'severity':'HIGH','id':'COMPONENTS','index':index})
        for key in ['total_s','return_slack_s','origin_stop_id','return_stop_id']:
            if v.get('itinerary',{}).get(key)!=r['itinerary'][key]:issues.append({'severity':'HIGH','id':'ITINERARY','field':key,'index':index})
        for direction in ['outbound','return']:
            leg=r['itinerary'][direction];public_leg=v.get('itinerary',{}).get(direction,{})
            for key,value in leg.items():
                if public_leg.get(key)!=value:issues.append({'severity':'HIGH','id':'BUS_FACT','field':key,'direction':direction,'index':index})
            for end in ['from','to']:
                expected=stop_names.get(leg[end+'_stop_id'])
                if expected is None:
                    issues.append({'severity':'MEDIUM' if r['scenario_kind']=='stop_only' else 'HIGH','id':'LABEL_NOT_IN_CONSUMER_CATALOG','stop_id':leg[end+'_stop_id'],'index':index})
                    continue
                if public_leg.get(end+'_stop_label')!=expected:issues.append({'severity':'HIGH','id':'STOP_LABEL','expected':expected,'observed':public_leg.get(end+'_stop_label'),'index':index})
        if r['scenario_kind']=='health_visit':
            if v.get('health_destination',{}).get('entrance_verified') is not False:issues.append({'severity':'HIGH','id':'ENTRANCE_PROMOTED','index':index})
            for direction in ['outbound','return']:
                for field in ['total_metres','seconds','modelled_access','entrance_verified','source_refs']:
                    if v.get('walking',{}).get(direction,{}).get(field)!=r['walking'][direction][field]:issues.append({'severity':'HIGH','id':'WALKING','field':field,'index':index})
        supplied={p['field']:p for p in r.get('parameter_provenance',[])}
        for p in v.get('parameter_attribution',[]):
            expected='provider_default' if supplied.get(p['field'],{}).get('origin')=='model_default' else 'tool_argument_origin_unverified'
            if p.get('w2_attribution')!=expected:issues.append({'severity':'HIGH','id':'USER_DEFAULT_ATTRIBUTION','index':index})
    if raw.get('comparisons',[])!=view.get('mobility',{}).get('comparisons',[]):issues.append({'severity':'HIGH','id':'COMPARISON_PROJECTION'})
    return issues


def run(package,manifest_file,w1_root,python,out):
    manifest=json.loads(manifest_file.read_bytes())
    if sha(package.read_bytes())!=PACKAGE_SHA or manifest['sha256']!=PACKAGE_SHA or manifest['bytes']!=package.stat().st_size:raise ValueError('Exact W2 baseline identity mismatch')
    static=review_zip(package,{n:v['sha256'] for n,v in manifest['members'].items()},['studio','langchain','pytest','agentes','scripts','prototypes','health_adapter','mobility_adapter'])
    with zipfile.ZipFile(package) as z:
        for name in z.namelist():
            if len(z.read(name))!=manifest['members'][name]['bytes']:raise ValueError('Member length mismatch')
        nested=z.read('datos_preparados/vnext/w1_r6_runtime.zip')
        if sha(nested)!=W1_SHA:raise ValueError('Nested W1 runtime changed')
        labels=json.loads(z.read('datos_preparados/vnext/consumer_labels_r7.json'))
        catalog=json.loads(z.read('datos_preparados/vnext/operational_catalog_r6.json'))
        if sha(z.read('datos_preparados/vnext/operational_catalog_r6.json'))!='c7bd3cc8ffe50956ce839bec0ef90a13578160a4d5b4053b09673d2dc4c4ec17':raise ValueError('Operational catalog pin differs')
        if sha(z.read('datos_preparados/vnext/consumer_labels_r7.json'))!='f0804b646d0473531e4f9ad12e31dc1ee7ee50cab69576bc95a0485b8da62799':raise ValueError('Stop-label pin differs')
        source_names=z.namelist()
        generated=ast.parse(z.read('tools.py').decode())
        main_tree=ast.parse(z.read('main.py').decode())
        context_files=next(ast.literal_eval(n.value) for n in main_tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='STUDIO_CONTEXT_FILES' for t in n.targets))
        helpers=next(ast.literal_eval(n.value) for n in generated.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='_W1_HELPERS' for t in n.targets))
        if set(helpers)!={'health_adapter','mobility_adapter'}:raise ValueError('Generated embedded helper set changed')
        if sha(helpers['health_adapter'].encode())!='b9099cadb8d63e8a42824e8db8541b9c8f733ae0a211df3a2da3dbfc3a467a67':raise ValueError('Health adapter source identity differs')
        for name in ['main.py','tools.py']:
            tree=ast.parse(z.read(name).decode())
            if any(isinstance(n,ast.ImportFrom) and n.module and n.module.split('.')[0] in {'scripts','agentes','pytest'} for n in ast.walk(tree)):raise ValueError('Test-only dependency in runtime')
        static['bundled_imports_verified']=['prototypes (nested hashed W1 ZIP)','health_adapter/mobility_adapter (embedded helper source)']
        static['repository_test_only_imports']=['scripts','agentes','pytest']
    with zipfile.ZipFile(io.BytesIO(nested)) as z:
        nested_names=z.namelist()
        if any(n.lower().endswith(('.html','.htm','.pdf')) for n in source_names+nested_names):raise ValueError('Raw full page/PDF in package')
        nested_manifest=json.loads((w1_root/'docs/vnext/w1/RUNTIME_MANIFEST_R6.json').read_bytes())
        nested_members={x['path']:x['sha256'] for x in nested_manifest['files']}
        for n in z.namelist():
            if sha(z.read(n))!=nested_members[n]:raise ValueError('Nested W1 member differs')
    conformance=json.loads((w1_root/'docs/vnext/w1/CONSUMER_CONFORMANCE_R7.json').read_bytes())
    old=json.loads((ROOT/'resultados/vnext/r10/health_evidence.json').read_bytes())
    calls=[{'id':row['case_id'],'tool':'plan_visit','arguments':{'request':row.get('request',row.get('requests'))}} for row in conformance['cases']]
    calls += [{'id':'W3-'+key,'tool':'plan_visit','arguments':{'request':item['request']}} for key,item in old['outputs'].items()]
    main=old['outputs']['main']['request'];legacy=next(c['arguments']['request'] for c in calls if c['id']=='legacy_r4_explicit')
    calls += [{'id':'origin-'+o['origin_id'],'tool':'plan_visit','arguments':{'request':dict(main,origin_id=o['origin_id'])}} for o in catalog['origins']]
    calls += [{'id':key,'tool':'plan_visit','arguments':{'request':q}} for key,q in [('sequence-health-1',main),('sequence-legacy',legacy),('sequence-health-2',main)]]
    calls += [{'id':'main-time-comparison','tool':'plan_visit','arguments':{'request':[main,old['outputs']['time']['request']]}}]
    calls += [{'id':name,'tool':'obtener_resumen_territorial','arguments':{'municipio':name,'periodo':None}} for name in ['Aduna','Tolosa']]
    calls += [{'id':'coincidence','tool':'analizar_coincidencia','arguments':{'categoria_servicio':'primary_care','grupo_edad':'65','umbral_km':2.0,'periodo':None,'cuantil':0.75}},
              {'id':'capabilities','tool':'consultar_capacidades','arguments':{'pregunta_o_dimension':'plan_visit'}},
              {'id':'source-GTFS','tool':'consultar_fuente','arguments':{'source_id':'GTFS'}}]
    def execute(payload,selected_files=None):
        with tempfile.TemporaryDirectory(prefix='g360-r12-intake-') as d:
            with zipfile.ZipFile(package) as z:
                for name in selected_files or z.namelist():z.extract(name,d)
            result=subprocess.run([str(python),'-I','-X','utf8','-c',CHILD],cwd=d,input=json.dumps(payload),encoding='utf-8',text=True,capture_output=True,check=False)
            if result.returncode:raise RuntimeError('Independent child failed: '+result.stderr)
            return json.loads(result.stdout)
    supported=execute({'calls':calls,'direct_requests':{'health':main,'legacy':legacy,'mixed':[main,legacy]}})
    # Separate process reproduces only the evaluator's foreign-root assumption.
    foreign=execute({'calls':[c for c in calls if c['id'] in ['health_defaults_omitted','legacy_r4_explicit']],'foreign_cwd':str(w1_root.resolve()),'direct_requests':{}})
    declared=execute({'calls':[c for c in calls if c['id'] in ['health_defaults_omitted','legacy_r4_explicit']],'direct_requests':{'health':main}},['main.py','tools.py']+context_files)
    findings=[];summary=[]
    for record in supported['results']:
        issues=[]
        if record['tool']=='plan_visit':
            if record['id']=='invalid_structural':
                if record.get('envelope',{}).get('status')!='error' or record.get('envelope',{}).get('claims'):issues=[{'severity':'HIGH','id':'INVALID_TYPE_ACCEPTED'}]
            else:issues=projection_findings(record,labels)
            if record['id'].startswith('W3-'):
                expected=old['outputs'][record['id'][3:]]['result']
                observed=json.loads(record['envelope']['raw_result_json']) if record.get('envelope',{}).get('raw_result_json') else None
                if observed!=expected:issues.append({'severity':'HIGH','id':'INDEPENDENT_R10_DATA_MISMATCH'})
        elif record.get('envelope',{}).get('status')!='valid':issues=[{'severity':'HIGH','id':'LEGITIMATE_RESULT_REJECTED'}]
        findings.extend(dict(issue,case_id=record['id']) for issue in issues)
        summary.append({'id':record['id'],'status':'FAIL' if any(i['severity'] in {'HIGH','CRITICAL'} for i in issues) else 'WARN' if issues else 'PASS','envelope_status':record.get('envelope',{}).get('status'),'public_exception':record.get('public_exception')})
    rates=lambda name:[c for c in next(r for r in supported['results'] if r['id']==name)['public_result']['claims'] if 'per_10000' in c['label']]
    sub=supported['direct_tool_outputs']['municipal_substitution']
    territorial={'binding_rejects_substitution':sub['envelope']['status']=='error' and not sub['public_result']['claims'],'aduna_unattributed_rates_absent':not rates('Aduna'),'tolosa_positive_rates_retained':len(rates('Tolosa'))==8,'highlighted_unit_municipios':any(c['label']=='highlighted_count' and c['value']==7 and c['unit']=='municipios' for c in next(r for r in supported['results'] if r['id']=='coincidence')['public_result']['claims'])}
    if not all(territorial.values()):findings.append({'severity':'HIGH','id':'TERRITORIAL_REGRESSION'})
    for name,view in supported['direct_tool_outputs'].items():
        if name!='municipal_substitution' and ('exception' in view or 'mobility' not in view):findings.append({'severity':'HIGH','id':'GENERATED_TOOL_PROJECTION','case_id':name})
    out.mkdir(parents=True,exist_ok=True);emit(out/'candidate_evidence.json',supported);emit(out/'foreign_cwd_diagnostic.json',foreign)
    emit(out/'declared_files_diagnostic.json',declared)
    emit(out/'deployment_review.json',{'classification':'OFFLINE_REPRODUCTION_OF_OBSERVED_STUDIO_DECLARED_FILES_NOT_PORTAL_LLM','status':'FAIL','severity':'HIGH','id':'STUDIO_FREEZE_OMITS_RUNTIME_ASSETS','owner':'W2','declared_context_files':context_files,'required_but_omitted':['datos_preparados/vnext/w1_r6_runtime.zip','datos_preparados/vnext/mobility_sources.json','scripts/vnext_agent/w1_pin.json'],'model_calls':0,'portal_version_created':False,'basis':'Studio UI says only declared data plus agent Python modules are frozen. Package-cwd process with exactly those files cannot bootstrap the mobility producer. Full ZIP acceptance remains separate.'})
    health=next(r for r in supported['results'] if r['id']=='W3-main');time=next(r for r in supported['results'] if r['id']=='W3-time')
    report={'classification':'OFFLINE_TOOL_INDEPENDENT_EXACT_PACKAGE_NOT_LLM','package_sha256':PACKAGE_SHA,'w2_pin':'2321e03e3d994b488db9723560383d9defedcac7','w1_runtime_git_real':W1_RUNTIME,'w1_nested_package_sha256':W1_SHA,'integrity':'PASS','static':static,'nested_members':len(nested_names),'source_policy':'PASS_NO_COMPLETE_HTML_PDF_HOLDOUT_OR_SECRET_PATTERN','catalog_labels':'PASS_EXACT_PINS','calls':summary,'territorial_retest':territorial,'findings':findings,'acceptance':'FAIL' if any(i['severity'] in {'HIGH','CRITICAL'} for i in findings) else 'PASS_WITH_MEDIUM_LIMIT' if findings else 'PASS','generated_tools_tested':True,'model_routing':'NOT_RUN','studio_served_schema':'NOT_OBSERVED','parity_basis':'Actual bundled producer plus independently contrasted frozen W3 R10 outputs/GTFS arithmetic; no W1 verdict helper used.','verified_conditional_delta_s':json.loads(time['envelope']['raw_result_json'])['itinerary']['total_s']-json.loads(health['envelope']['raw_result_json'])['itinerary']['total_s'],'foreign_root_diagnostic':'Evaluator changes cwd while execute root points to ZIP; diagnostic is outside supported package-cwd mode, not a Studio test.','llm_executed':0,'evidence_sha256':sha((out/'candidate_evidence.json').read_bytes()),'foreign_diagnostic_sha256':sha((out/'foreign_cwd_diagnostic.json').read_bytes())}
    emit(out/'candidate_review.json',report);return report


def main():
    p=argparse.ArgumentParser();p.add_argument('--package',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--w1-root',type=Path,required=True);p.add_argument('--python',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args();r=run(a.package,a.manifest,a.w1_root,a.python,a.output_dir);print(json.dumps({'acceptance':r['acceptance'],'calls':len(r['calls']),'findings':r['findings'],'delta_s':r['verified_conditional_delta_s']},ensure_ascii=True))
if __name__=='__main__':main()
