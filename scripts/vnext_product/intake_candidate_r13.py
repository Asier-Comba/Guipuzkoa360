"""Independent exact patch3 intake. Reuses W3 assertions, never a W1/W2 verdict."""
import argparse,ast,csv,hashlib,io,json,os,subprocess,tempfile,zipfile
from pathlib import Path
from scripts.vnext_product.package_review import review_zip
from scripts.vnext_product.intake_candidate_r12 import projection_findings
from scripts.vnext_product.review_health_r10 import contrast,GTFS_SHA
ROOT=Path(__file__).resolve().parents[2]
ZIP_SHA='3951b290b6ca59c336886a3f0acee77a68036d4fbcbc06c2cedfe22400c08616'
MANIFEST_SHA='a672bf9a2afece58c468a1f762c860f0217536a2a4fa18737ba768cab755c70a'
W1_ZIP='c66d44af702eb3410fcea05ae8711f537214f675e83a7fda38c39c3b39a1b910'
CHILD=r'''
import sys,os,json,socket,traceback
from pathlib import Path
p=json.load(sys.stdin)
for k in list(os.environ):
 if k.startswith('GIPUZKOA360') or k=='PYTHONPATH':os.environ.pop(k)
sys.path.insert(0,p['module_dir']);os.chdir(p['cwd'])
def deny(*a,**k):raise RuntimeError('Offline network denied')
socket.socket=deny;socket.create_connection=deny
import tools,main
out={'mode':p['mode'],'root':str(tools._workspace_root()),'root_matches':tools._workspace_root()==Path(p['root']),'network_disabled':True,'isolated':sys.flags.isolated,'model_calls':0,'records':[]}
for q in p['calls']:
 r=dict(q)
 try:
  e=tools.execute(q['tool'],q['arguments'],q['id']);r['envelope']=e;r['public_result']=json.loads(tools.public_result(e))
  if q['tool']=='plan_visit':
   from prototypes.ir_y_volver import provider_r6 as provider
   v=q['arguments']['request'];r['producer']=provider.compare_visits(v) if type(v) is list else provider.plan_visit(v)
 except Exception as exc:r['exception']={'type':type(exc).__name__,'message':str(exc)}
 out['records'].append(r)
out['direct_generated_views']={k:json.loads(main.plan_visit(v)) for k,v in p['direct'].items()}
os.environ['GIPUZKOA360_VNEXT_ROOT']=str(Path(p['root'])/'absent')
out['invalid_root']=json.loads(main.plan_visit(p['direct']['health']))
json.dump(out,sys.stdout,ensure_ascii=True)
'''
def sha(b):return hashlib.sha256(b).hexdigest()
def emit(p,x):p.write_text(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')
def project(record,labels):
    issues=[i for i in projection_findings(record,labels) if i['id']!='USER_DEFAULT_ATTRIBUTION']
    raw=json.loads(record['envelope']['raw_result_json']);items=raw.get('results',[raw]);original=record['arguments']['request'];original=original if type(original) is list else [original]
    for r,v,q in zip(items,record['public_result']['mobility']['scenarios'],original):
        provenance={p['field']:p for p in r.get('parameter_provenance',[])}
        effective=r.get('normalized_request') or {}
        if len(v['parameter_attribution'])!=len(effective):issues.append({'severity':'HIGH','id':'ATTRIBUTION_COVERAGE'})
        for p in v['parameter_attribution']:
            default=provenance.get(p['field'],{}).get('origin')=='model_default'
            expected='provider_default' if default else 'tool_argument_origin_unverified' if p['field'] in q else 'legacy_provider_default'
            if p['w2_attribution']!=expected or p['value']!=effective[p['field']]:issues.append({'severity':'HIGH','id':'ATTRIBUTION_BINDING'})
    return issues
def run(a):
    assert sha(a.package.read_bytes())==ZIP_SHA and sha(a.manifest.read_bytes())==MANIFEST_SHA
    manifest=json.loads(a.manifest.read_bytes());assert manifest['sha256']==ZIP_SHA
    static=review_zip(a.package,{n:v['sha256'] for n,v in manifest['members'].items()},['studio','langchain','pytest','agentes','scripts','prototypes','health_adapter','mobility_adapter'])
    with zipfile.ZipFile(a.package) as z:
        tree=ast.parse(z.read('main.py'));ctx=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='STUDIO_CONTEXT_FILES' for t in n.targets))
        assert len(ctx)==15 and len(set(ctx))==15
        assert all(len(z.read(n))==v['bytes'] for n,v in manifest['members'].items())
        nested=z.read('datos_preparados/vnext/w1_r6_runtime.zip');assert sha(nested)==W1_ZIP
        labels=json.loads(z.read('datos_preparados/vnext/consumer_labels_r7.json'))
        with zipfile.ZipFile(io.BytesIO(nested)) as w:
            wmanifest=json.loads((a.w1_root/'docs/vnext/w1/RUNTIME_MANIFEST_R6.json').read_bytes());expected={r['path']:r['sha256'] for r in wmanifest['files']}
            assert set(w.namelist())==set(expected) and all(sha(w.read(n))==expected[n] for n in w.namelist())
            snapshot=json.loads(w.read('prototypes/ir_y_volver/snapshots/official-goierrialdea-go01-r4-20260929.json'))
        names={r['stop_id'] for r in labels['stops']}
        labels['stops'] += [{'stop_id':sid,'name':r['name']} for sid,r in snapshot['stops'].items() if sid not in names]
        old=json.loads((ROOT/'resultados/vnext/r12/candidate_evidence.json').read_bytes())
        calls=[{k:r[k] for k in ['id','tool','arguments']} for r in old['results']]
        main=next(r for r in calls if r['id']=='W3-main')['arguments']['request'];legacy=next(r for r in calls if r['id']=='legacy_r4_explicit')['arguments']['request']
        calls += [{'id':'source-health','tool':'consultar_fuente','arguments':{'source_id':'HEALTH_REGISTRY'}},{'id':'source-unknown','tool':'consultar_fuente','arguments':{'source_id':'FAKE'}}]
        a.output.mkdir(parents=True,exist_ok=True);reports=[]
        for mode in ['flat_full','flat_declared','flat_foreign_cwd','nested_declared_foreign_cwd']:
            with tempfile.TemporaryDirectory(prefix='g360-w3-r13-') as d:
                root=Path(d);module=root/'agentes/patch3' if mode.startswith('nested') else root;module.mkdir(parents=True,exist_ok=True)
                for n in z.namelist() if mode=='flat_full' else ctx:
                    z.extract(n,root)
                for n in ['main.py','tools.py']:(module/n).write_bytes(z.read(n))
                p={'mode':mode,'root':str(root),'module_dir':str(module),'cwd':str(a.w1_root.resolve()) if 'foreign' in mode else str(root),'calls':calls,'direct':{'health':main,'legacy':legacy,'mixed':[main,legacy]}}
                result=subprocess.run([str(a.python),'-I','-X','utf8','-c',CHILD],input=json.dumps(p),text=True,encoding='utf-8',capture_output=True,cwd=d)
                if result.returncode:raise RuntimeError(result.stderr)
                observed=json.loads(result.stdout);findings=[]
                for r in observed['records']:
                    e=r.get('envelope',{})
                    if r['id']=='invalid_structural':
                        if e.get('status')!='error' or e.get('claims'):findings.append({'id':r['id'],'severity':'HIGH','detail':'invalid input accepted'})
                    elif r['tool']=='plan_visit':findings.extend(dict(f,case_id=r['id']) for f in project(r,labels))
                    elif r['id']=='source-unknown':
                        if e.get('status')=='valid' or e.get('claims'):findings.append({'id':r['id'],'severity':'HIGH','detail':'false source accepted'})
                    elif e.get('status')!='valid':findings.append({'id':r['id'],'severity':'HIGH','detail':r})
                    if len(json.dumps(r.get('public_result')).encode())>120000:findings.append({'id':r['id'],'severity':'HIGH','detail':'payload limit'})
                for k,v in observed['direct_generated_views'].items():
                    if v['status']!='valid' or 'mobility' not in v:findings.append({'id':k,'severity':'HIGH','detail':'generated view'})
                by={r['id']:r for r in observed['records']}
                rates=lambda key:[c for c in by[key]['public_result']['claims'] if 'per_10000' in c['label']]
                if rates('Aduna') or len(rates('Tolosa'))!=8:findings.append({'id':'territorial_rates','severity':'HIGH'})
                if not any(c['label']=='highlighted_count' and c['value']==7 and c['unit']=='municipios' for c in by['coincidence']['public_result']['claims']):findings.append({'id':'territorial_count','severity':'HIGH'})
                if observed['invalid_root']['status']!='error' or observed['invalid_root']['claims'] or not observed['root_matches']:findings.append({'id':'root','severity':'HIGH'})
                emit(a.output/(mode+'.json'),observed);reports.append({'mode':mode,'cases':len(calls),'findings':findings,'root_matches':observed['root_matches'],'status':'FAIL' if findings else 'PASS'})
    assert sha(a.gtfs.read_bytes())==GTFS_SHA
    with zipfile.ZipFile(a.gtfs) as g:
        rows={(r['trip_id'],r['stop_id'],r['stop_sequence']):dict(r,csv_line=line) for line,r in enumerate(csv.DictReader(io.StringIO(g.read('stop_times.txt').decode('utf-8-sig'))),2)}
    records={r['id']:r for r in json.loads((a.output/'flat_declared.json').read_bytes())['records']}
    independent={key:contrast(json.loads(records['W3-'+key]['envelope']['raw_result_json']),rows) for key in ['main','time']}
    report={'package_sha256':ZIP_SHA,'manifest_sha256':MANIFEST_SHA,'classification':'INDEPENDENT_OFFLINE_TOOL_NOT_LLM','static':static,'declared_paths':ctx,'nested_w1_sha256':W1_ZIP,'modes':reports,'independent_source':{'gtfs_sha256':GTFS_SHA,'contrast':independent,'delta_s':independent['time']['total_s_reconstructed']-independent['main']['total_s_reconstructed']},'acceptance':'FAIL' if any(m['findings'] for m in reports) else 'PASS','model_calls':0}
    emit(a.output/'offline_review.json',report);return report
def main():
    p=argparse.ArgumentParser()
    for k in ['package','manifest','w1-root','python','gtfs','output']:p.add_argument('--'+k,type=Path,required=True)
    r=run(p.parse_args());print(json.dumps({'acceptance':r['acceptance'],'modes':r['modes'],'delta':r['independent_source']['delta_s']}))
if __name__=='__main__':main()
