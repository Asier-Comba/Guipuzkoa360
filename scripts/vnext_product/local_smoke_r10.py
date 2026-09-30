"""Single-turn real-agent capture, gated on a reviewed assembly and human authorization.

Default preflight is read-only and never loads a model. Captures are raw evidence;
reviewed W3_TRACE_2.1.0 files are scored with the existing scorer, not auto-graded here.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import uuid
import zipfile

from scripts.vnext_product.package_review import review_assembly, rooted
from scripts.vnext_product.score_runs import strict_json, canonical, sha
ROOT=Path(__file__).resolve().parents[2]
PLAN=ROOT/'docs/vnext/w3/SMOKE_PLAN_R10.json'


def now():return datetime.now(timezone.utc).isoformat()

def preflight():
    # Names/booleans only: never read or serialize credential values.
    modules={name:importlib.util.find_spec(name) is not None for name in ['langchain','langchain_core']}
    return {'classification':'PREFLIGHT_NO_MODEL','status':'BLOCKED','llm_executed':0,'portal_executed':0,
            'dependencies_present':modules,'credential_present':{k:bool(os.environ.get(k)) for k in ['OPENAI_API_KEY','AZURE_OPENAI_API_KEY','ANTHROPIC_API_KEY']},
            'blockers':['No reviewed W2 health 0.3.1 combined package published at R10 acceptance pin.',
                        'No supplied model/configuration or resource/budget authorization for local invocation.',
                        'Current QA interpreter lacks langchain/langchain_core; no new global dependency installed.'],
            'smoke_plan_sha256':sha(PLAN.read_bytes()),'trace_contract':'W3_TRACE_2.1.0','scorer':'2.1.0',
            'counter_semantics':'Counts actual on_chat_model_start callbacks, not tools, attempts or successful answers.'}


def check_config(config, evidence_root):
    if config.get('existing_resources_authorized') is not True or not config.get('human_authorization_reference'):
        raise ValueError('Explicit human resource/budget authorization is required')
    limit=config.get('max_model_calls_per_turn')
    if type(limit) is not int or not 1<=limit<=8:raise ValueError('A bounded authorized model-call budget is required')
    total=config.get('max_model_calls_total')
    if type(total) is not int or not 1<=total<=288:raise ValueError('A bounded authorized total budget is required')
    path=rooted(evidence_root,config['assembly_manifest_file'])
    if sha(path.read_bytes())!=config['assembly_manifest_sha256']:raise ValueError('Assembly identity changed')
    manifest=strict_json(path.read_text(encoding='utf-8'))
    review_assembly(evidence_root,manifest)
    health=rooted(evidence_root,config['health_review_file'])
    if sha(health.read_bytes())!=config['health_review_sha256']:raise ValueError('Health acceptance identity changed')
    review=strict_json(health.read_text(encoding='utf-8'))
    if review.get('package_sha256')!=manifest['package_sha256'] or review.get('combined_health_acceptance')!='PASS':
        raise ValueError('Combined health acceptance must apply to the same W2 package')
    factory=rooted(evidence_root,config['model_factory_file'])
    if sha(factory.read_bytes())!=config['model_factory_sha256']:raise ValueError('Model factory identity changed')
    return manifest,factory


def capture_turn(agent, observer, prompt, before):
    """Retain an attempt even if construction/call fails before any final message."""
    record={'started_at':now(),'prompt':prompt,'history_before':before,'events':observer.events,
            'final_response':None,'observed_messages':[],'error_observation':None}
    try:
        reply=agent.invoke({'messages':before+[{'role':'user','content':prompt}]},
                           config={'callbacks':[observer],'recursion_limit':24})
        messages=reply.get('messages',[])
        record['observed_messages']=[m.model_dump(mode='json') if hasattr(m,'model_dump') else m for m in messages]
        last=messages[-1] if messages else None
        kind=getattr(last,'type',None) or (last.get('role') if isinstance(last,dict) else None)
        content=getattr(last,'content',None) if not isinstance(last,dict) else last.get('content')
        tool_calls=getattr(last,'tool_calls',None) if not isinstance(last,dict) else last.get('tool_calls')
        if kind in {'ai','assistant'} and not tool_calls and isinstance(content,str) and content.strip():
            record['final_response']=content
            record['invocation_state']='completed' if observer.model_calls else 'capture_incomplete'
        else:
            record['invocation_state']='capture_incomplete' if observer.model_calls else 'not_started'
            record['error_observation']='No observed text assistant final; raw messages preserved.'
    except BaseException as exc:
        record['invocation_state']=('interrupted' if isinstance(exc,KeyboardInterrupt) else 'failed') if observer.model_calls else 'not_started'
        record['error_observation']=type(exc).__name__+': '+str(exc)
    record.update(ended_at=now(),model_invocations_started=observer.model_calls,llm_executed=bool(observer.model_calls))
    if record['invocation_state']!='completed':record['final_response']=None
    return record


def execute(config,root,scenario_id,turn_index,out):
    manifest,factory_path=check_config(config,root)
    if (out/'STOP_CRITICAL_HIGH.json').exists():raise ValueError('Affected batch stopped: new candidate and reproduction required')
    plan=strict_json(PLAN.read_text(encoding='utf-8'))
    scenario=next((s for s in plan['cases'] if s['conversation_id']==scenario_id),None)
    if not scenario or not 1<=turn_index<=len(scenario['turns']):raise ValueError('Unknown frozen smoke turn')
    out.mkdir(parents=True,exist_ok=True)
    identity={k:manifest[k] for k in ['runtime_commit','package_sha256','model_id','model_config','context_mode','data_manifest_sha256']}
    existing=sorted(out.glob(f'{scenario_id}-*.json'))
    before=[]
    if turn_index>1:
        prior=[strict_json(p.read_text(encoding='utf-8')) for p in existing]
        valid=[r for r in prior if r['turn_index']==turn_index-1 and r['invocation_state']=='completed' and r['identity']==identity]
        if not valid:raise ValueError('Observed previous successful turn in same candidate/session is required')
        # Use the last captured full history, including observed tool calls/messages.
        before=max(valid,key=lambda r:r['ended_at'])['observed_messages']
    used_calls=sum(strict_json(p.read_text(encoding='utf-8')).get('model_invocations_started',0) for p in out.glob('VN-CONV-*.json'))
    if used_calls>=config['max_model_calls_total']:raise ValueError('Authorized batch model-call cap reached')
    from langchain_core.callbacks import BaseCallbackHandler
    class Observer(BaseCallbackHandler):
        raise_error=True
        def __init__(self):self.events=[];self.model_calls=0
        def on_chat_model_start(self,serialized,messages,**kw):
            if self.model_calls>=config['max_model_calls_per_turn'] or used_calls+self.model_calls>=config['max_model_calls_total']:raise RuntimeError('Authorized per-turn model-call cap reached')
            self.model_calls+=1;self.events.append({'event':'model_start','at':now(),'run_id':str(kw.get('run_id'))})
        def on_llm_end(self,response,**kw):self.events.append({'event':'model_end','at':now(),'run_id':str(kw.get('run_id'))})
        def on_llm_error(self,error,**kw):self.events.append({'event':'model_error','at':now(),'message':type(error).__name__+': '+str(error)})
        def on_tool_start(self,serialized,input_str,**kw):self.events.append({'event':'tool_start','at':now(),'run_id':str(kw.get('run_id')),'name':serialized.get('name'),'input':input_str,'arguments':kw.get('inputs')})
        def on_tool_end(self,output,**kw):self.events.append({'event':'tool_end','at':now(),'run_id':str(kw.get('run_id')),'output':output.model_dump(mode='json') if hasattr(output,'model_dump') else output})
        def on_tool_error(self,error,**kw):self.events.append({'event':'tool_error','at':now(),'run_id':str(kw.get('run_id')),'message':type(error).__name__+': '+str(error)})
    observer=Observer()
    with tempfile.TemporaryDirectory(prefix='g360-real-agent-') as directory:
        with zipfile.ZipFile(rooted(root,manifest['package_file'])) as z:z.extractall(directory)
        old_cwd=Path.cwd();old_path=list(sys.path)
        try:
            os.chdir(directory);sys.path.insert(0,directory)
            for name,path in [('authorized_model_factory',factory_path),('candidate_main',Path(directory)/'main.py')]:
                spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
                if name=='authorized_model_factory':factory=module
                else:main=module
            # The human-supplied factory uses already authorized resources; the runner selects no provider.
            agent=main.build_agent(factory.build_model(manifest['model_id'],manifest['model_config']))
            r=capture_turn(agent,observer,scenario['turns'][turn_index-1]['prompt'],before)
        except BaseException as exc:
            r={'started_at':now(),'ended_at':now(),'prompt':scenario['turns'][turn_index-1]['prompt'],
               'history_before':before,'events':observer.events,'observed_messages':[],'final_response':None,
               'invocation_state':'failed' if observer.model_calls else 'not_started',
               'model_invocations_started':observer.model_calls,'llm_executed':bool(observer.model_calls),
               'error_observation':type(exc).__name__+': '+str(exc)}
        finally:os.chdir(old_cwd);sys.path[:]=old_path
    attempt=1+sum(p.name.startswith(f'{scenario_id}-{turn_index}-') for p in existing)
    r.update(classification='LOCAL_LLM_RAW_CAPTURE_NOT_YET_SCORED',identity=identity,
             conversation_id=scenario_id,turn_index=turn_index,attempt=attempt,session_id=scenario_id+'-'+manifest['package_sha256'],
             smoke_plan_sha256=sha(PLAN.read_bytes()),assembly_manifest_sha256=config['assembly_manifest_sha256'],
             trace_target='W3_TRACE_2.1.0',verdict='not_scored',review_required=True)
    path=out/f'{scenario_id}-{turn_index}-{attempt}-{uuid.uuid4().hex}.json'
    path.write_bytes(canonical(r)+b'\n')
    return {'capture':str(path),'invocation_state':r['invocation_state'],'model_invocations_started':observer.model_calls,'verdict':'not_scored'}


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',action='store_true');p.add_argument('--config',type=Path);p.add_argument('--evidence-root',type=Path);p.add_argument('--scenario');p.add_argument('--turn',type=int,default=1);p.add_argument('--output-dir',type=Path,default=ROOT/'resultados/vnext/r10/local_capture');p.add_argument('--preflight-output',type=Path)
    a=p.parse_args()
    if not a.run:
        r=preflight()
        if a.preflight_output:a.preflight_output.write_bytes(canonical(r)+b'\n')
    else:
        if not a.config or not a.evidence_root or not a.scenario:p.error('--run needs authorized config, evidence-root and frozen scenario')
        r=execute(strict_json(a.config.read_text(encoding='utf-8')),a.evidence_root,a.scenario,a.turn,a.output_dir)
    print(json.dumps(r,ensure_ascii=False))
if __name__=='__main__':main()
