"""Exact-package structural acceptance; no model, internet or holdout."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import io
import json
from pathlib import Path
import tempfile
import zipfile
from scripts.vnext_agent import verify_r15 as previous
from scripts.vnext_agent.build_r18 import BASE,BASE_ZIP,BASE_HASH,ROOT,ZIP,MANIFEST,blob,sha
from scripts.vnext_agent.eval_r18 import generate

def issues_for(view):
    issues=[]
    if view.get('status')!='valid':
        if view.get('claims') or view.get('mobility'):issues.append('error_with_analytical_evidence')
        return issues
    for c in view.get('claims',[]):
        if c.get('numeric_role')!='analytical' or not c.get('subject'):issues.append('untyped_claim')
        if c['metric_id'] in {'total_result_rows','returned_rows','joined_rows'}:issues.append('operational_claim')
        if c['metric_id'] in {'within_threshold_count','outside_threshold_count','highlighted_count'} and c['unit']!='municipios':issues.append('wrong_municipality_unit')
    for s in view.get('mobility',{}).get('scenarios',[]):
        if s['status']=='ok':
            t=s['time_summary']
            if t['total_s']!=sum(s['components_s'].values()) or t['total_s']!=t['scope_end_s']-t['scope_start_s']:issues.append('time_invariant')
    return issues

def run(output,generated_only=False):
    baseline,candidate=blob(BASE_ZIP),ZIP.read_bytes()
    assert sha(baseline)==BASE_HASH
    oracle=previous.ORACLE.read_bytes(); assert sha(oracle)==previous.ORACLE_HASH
    cases=[] if generated_only else previous.make_cases(baseline,json.loads(oracle))
    for c in cases:
        if c['tool']=='obtener_resumen_territorial' and 'periodo' in c['arguments']:c['route']='internal'
        c['keep_view']=True
    generated,_=generate(); cases+=generated
    corpus_sha256=sha((ROOT/'outputs/r18/generated-corpus.json').read_bytes())
    with tempfile.TemporaryDirectory(prefix='r18-parity-') as d:
        roots=[Path(d)/x for x in ('r17','r18')]
        for root,data in zip(roots,(baseline,candidate),strict=True):
            with zipfile.ZipFile(io.BytesIO(data)) as z:z.extractall(root)
        with ThreadPoolExecutor(max_workers=2) as pool:
            old,new=list(pool.map(lambda root:previous.run_worker(root,cases),roots))
    records=[];findings=[];oracle_pass=0;parity=0;time_summaries=0
    for case in cases:
        a,b=old['records'][case['id']],new['records'][case['id']];issues=[]
        for key in ('status','error','raw_sha256','raw_status','outcomes','execute_calls'):
            if a.get(key)!=b.get(key):issues.append('raw_execution:'+key)
        if b.get('status')=='valid':
            for key in ('totals_s','provenance_sha256'):
                if a.get(key)!=b.get(key):issues.append('valid_projection:'+key)
        elif b.get('view',{}).get('mobility'):
            issues.append('invalid_partial_projection')
        if a.get('raw_sha256')==b.get('raw_sha256'):parity+=1
        if 'oracle' in case:
            if b.get('oracle',{}).get('pass'):oracle_pass+=1
            else:issues.append('oracle')
        if b.get('status')=='escaped_exception':issues.append('escaped_exception')
        issues+=issues_for(b.get('view',{}))
        # Only these deliberate model-facing unit/operational changes are legal.
        expected=[]
        for c in a.get('view',{}).get('claims',[]):
            if c['metric_id'] in {'total_result_rows','returned_rows','joined_rows'}:continue
            c=dict(c)
            if c['metric_id']=='difference_relative_pct':c['unit']='%'
            if c['metric_id'] in {'within_threshold_count','outside_threshold_count'}:c['unit']='municipios'
            expected.append(c)
        actual=[{k:v for k,v in c.items() if k not in {'subject','numeric_role','allowed_transformations','forbidden_inferences'}} for c in b.get('view',{}).get('claims',[])]
        if expected!=actual:issues.append('unexpected_analytical_claim_change')
        time_summaries+=sum(s['status']=='ok' for s in b.get('view',{}).get('mobility',{}).get('scenarios',[]))
        rec={'id':case['id'],'group':case['group'],'status':b['status'],'raw_sha256':b.get('raw_sha256'),'issues':issues}
        records.append(rec)
        if issues:findings.append(rec)
    if {k:{x:v for x,v in s.items() if x!='docstring'} for k,s in old['signatures'].items()}!={k:{x:v for x,v in s.items() if x!='docstring'} for k,s in new['signatures'].items()}:findings.append({'id':'signatures','issues':['changed']})
    result={'classification':'AUTHOR_OFFLINE_STRUCTURAL_NOT_REAL_AGENT','status':'FAIL' if findings else 'PASS','base_r17':BASE,'zip_sha256':sha(candidate),'manifest_sha256':sha(MANIFEST.read_bytes()),'generated_corpus_sha256':corpus_sha256,'generated_only':generated_only,'cases':len(cases),'raw_parity':parity,'oracle':oracle_pass,'time_summaries':time_summaries,'findings':findings,'records':records,'model_calls':0,'holdout':'SEALED_NOT_EXECUTED'}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    return {k:v for k,v in result.items() if k!='records'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'work/r18-audit.json');p.add_argument('--generated-only',action='store_true')
    args=p.parse_args();r=run(args.output,args.generated_only);print(json.dumps(r,sort_keys=True));raise SystemExit(r['status']!='PASS')
