"""Frozen-byte raw parity plus R19 structural corpus; zero model calls."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import io
import json
from pathlib import Path
import tempfile
import zipfile
from scripts.vnext_agent import verify_r15 as previous
from scripts.vnext_agent.build_r19 import BASE,BASE_ZIP,BASE_HASH,ROOT,ZIP,MANIFEST,blob,sha
from scripts.vnext_agent.eval_r19 import generate
from scripts.vnext_agent.verify_r18 import issues_for

def run(output):
    baseline,candidate=blob(BASE_ZIP),ZIP.read_bytes();assert sha(baseline)==BASE_HASH
    manifest=MANIFEST.read_bytes();assert json.loads(manifest)['sha256']==sha(candidate)
    oracle=previous.ORACLE.read_bytes();assert sha(oracle)==previous.ORACLE_HASH
    legacy=previous.make_cases(baseline,json.loads(oracle))
    # Old public capabilities are tested unchanged by their historical suites.
    # Here we compare the same raw engine calls independently of the new API.
    for case in legacy:
        if case['tool']=='plan_visit' and 'request' not in case['arguments']:
            case['arguments']={'request':case['arguments']}
        case['route']='internal';case['keep_view']=True
    generated,_=generate();cases=legacy+generated
    with tempfile.TemporaryDirectory(prefix='r19-parity-') as directory:
        roots=[Path(directory)/x for x in ('r18','r19')]
        for root,data in zip(roots,(baseline,candidate),strict=True):
            with zipfile.ZipFile(io.BytesIO(data)) as z:z.extractall(root)
        with ThreadPoolExecutor(max_workers=2) as pool:
            old,new=list(pool.map(lambda root:previous.run_worker(root,cases),roots))
    findings=[];records=[];parity=0;oracle_pass=0
    for case in cases:
        a,b=old['records'][case['id']],new['records'][case['id']];issues=[]
        for key in ('status','raw_sha256','raw_status','outcomes','execute_calls','totals_s','provenance_sha256'):
            if a.get(key)!=b.get(key):issues.append('changed_raw_or_provenance:'+key)
        if a.get('raw_sha256')==b.get('raw_sha256'):parity+=1
        if b['status']=='escaped_exception':issues.append('escaped_exception')
        if 'oracle' in case:
            if b.get('oracle',{}).get('pass'):oracle_pass+=1
            else:issues.append('oracle')
        view=b.get('view',{});issues+=issues_for(view)
        strip={'age_group','age_derivation_ref','forbidden_inferences'}
        oldclaims=[{k:v for k,v in c.items() if k not in strip} for c in a.get('view',{}).get('claims',[])]
        newclaims=[{k:v for k,v in c.items() if k not in strip} for c in view.get('claims',[])]
        if oldclaims!=newclaims:issues.append('analytical_claim_changed')
        if view.get('status')=='valid':
            for claim in view.get('claims',[]):
                if claim.get('age_group'):
                    age=claim['age_group']
                    if view.get('age_group_derivations',{}).get(age,{}).get('output_field')!='population_'+age+'_plus':issues.append('age_semantic_mismatch')
        elif view and b['status']!='binding_rejected':
            if view.get('claims') or view.get('error',{}).get('retry_same_call') is not False:issues.append('unsafe_error')
        record={'id':case['id'],'group':case['group'],'status':b['status'],'raw_sha256':b.get('raw_sha256'),'issues':issues};records.append(record)
        if issues:findings.append(record)
    result={'classification':'AUTHOR_OFFLINE_STRUCTURAL_NOT_LLM_OR_PORTAL','status':'FAIL' if findings else 'PASS','base_r18':BASE,'zip_sha256':sha(candidate),'manifest_sha256':sha(manifest),'generated_corpus_sha256':sha((ROOT/'outputs/r19/generated-corpus.json').read_bytes()),'cases':len(cases),'legacy_raw_cases':len(legacy),'generated_cases':len(generated),'raw_parity':parity,'oracle':oracle_pass,'findings':findings,'records':records,'model_calls':0,'offline_critical':0 if not findings else None,'offline_high':0 if not findings else None,'offline_medium':0 if not findings else None,'limitations':'Offline paraphrases do not prove LLM routing; no global retry suppression or portal success claimed.'}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    return {k:v for k,v in result.items() if k!='records'}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'outputs/r19/offline-audit.json')
    args=parser.parse_args();report=run(args.output);print(json.dumps(report,sort_keys=True));raise SystemExit(report['status']!='PASS')
