"""Assemble R13 observed smoke and separately labelled deterministic product evidence."""
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile
import csv
import io

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'resultados/vnext/r13'
ZIP_SHA='3951b290b6ca59c336886a3f0acee77a68036d4fbcbc06c2cedfe22400c08616'
W2='8c94f8c3cf9d732c4ce94af7b4bef8f6e154c243'
VERSION='agentv_c51dbaf6651f484bbbc435d4f8e27b4a'

def read(path):return json.loads(path.read_bytes())
def emit(path,data):path.write_bytes((json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))

def assemble(package):
    assert hashlib.sha256(package.read_bytes()).hexdigest()==ZIP_SHA
    reports=read(BASE/'flat_declared.json');rows={r['id']:r for r in reports['records']}
    prior=read(ROOT/'resultados/vnext/r12/health_evidence.json')
    evidence=dict(prior,classification='OFFLINE_W2_EXACT_PACKAGE_R13_NOT_AGENT',w2_pin=W2,package_sha256=ZIP_SHA,
        support_pin='7f434a469d7f94fdff8ae7d2665644426a217250',
        portal_health_status='BLOCKED_REQUEST_BINDING_R13_M04',portal_user_messages=4,
        portal_version_id=VERSION,producer_package_sha256=read(BASE/'offline_review.json')['nested_w1_sha256'])
    for key in prior['outputs']:
        row=rows['W3-'+key]
        evidence['outputs'][key]={'request':row['arguments']['request'],'result':json.loads(row['envelope']['raw_result_json'])}
    evidence['comparison']=json.loads(rows['main-time-comparison']['envelope']['raw_result_json'])
    emit(BASE/'health_evidence.json',evidence)
    plan=read(ROOT/'docs/vnext/w3/SMOKE_PLAN_R13.json');smoke=read(BASE/'PORTAL_SMOKE_R13.json')
    dimensions='INTENT_UNDERSTANDING CAPABILITY_DISCOVERY TOOL_SELECTION ARGUMENT_BINDING TOOL_RESULT_USE GROUNDING NUMERIC_CORRECTNESS IDENTITY_CORRECTNESS SOURCE_GROUNDING LIMIT_HANDLING FOLLOWUP_CONTEXT RECALCULATION ERROR_RECOVERY HALLUCINATION CLARITY'.split()
    score=[]
    for i in range(12):
        row={'slot':plan['messages'][i]['id'],'session':plan['messages'][i]['session']}
        if i>=4:
            row.update(state='NOT_RUN_STOPPED_HIGH',dimensions={d:'NOT_OBSERVED' for d in dimensions},findings=[])
            score.append(row);continue
        original=read(BASE/('M'+str(i+1).zfill(2)+'.json'))
        calls=[];results=[];final=None
        for node in original:
            calls.extend(node.get('toolcalls',[]))
            if node.get('tool'):calls.append({'name':node['tool'],'args':node['args']})
            if node.get('result'):results.append(json.loads(node['result']))
            if 'is-assistant' in node['class'] and not node.get('toolcalls') and not node.get('tool'):final=node['text'].split('\n',1)[1].strip()
        calls=[{'name':c['name'].removeprefix('Tool · '),'arguments':json.loads(c['args'])} for c in calls]
        turn=smoke['turns'][i]
        turn.update(tool_calls=calls,tool_outputs=results,assistant_final=final,errors=[r['error'] for r in results if r.get('error')],
            portal_version_id=VERSION,model_visible_configuration='openai:gpt-5.6-luna',model_request_identity='NOT_OBSERVED',
            model_history='NOT_OBSERVED',model_call_count='NOT_OBSERVED',latency_visible='NOT_OBSERVED',
            capture_scope='Current conversation DOM: actual args, tool output JSON and final; not model input history')
        ds={d:'PASS' for d in dimensions}
        ds.update(RECALCULATION='NOT_APPLICABLE',ERROR_RECOVERY='NOT_APPLICABLE')
        if i==0:ds['FOLLOWUP_CONTEXT']='NOT_APPLICABLE'
        if i in [0,1]:ds['SOURCE_GROUNDING']='WARN'
        if i==1:ds['RECALCULATION']='PASS'
        if i==2:ds.update(NUMERIC_CORRECTNESS='NOT_APPLICABLE',IDENTITY_CORRECTNESS='PASS',SOURCE_GROUNDING='NOT_APPLICABLE',ERROR_RECOVERY='PASS')
        if i==3:ds.update(ARGUMENT_BINDING='FAIL',NUMERIC_CORRECTNESS='NOT_APPLICABLE',SOURCE_GROUNDING='NOT_APPLICABLE',ERROR_RECOVERY='WARN',CLARITY='WARN')
        notes=[
            'Five demographic claims match final; source ID/75+ derivation exist in tool output, absent in final copy. No health counts promoted.',
            'Fresh Aduna and Tolosa tool results; 2432-36=2396 and 12.131-7.101=5.030 percentage points. Periods and service denominator preserved.',
            'Catalog consulted; decisive origin/time/duration requested; no substitution of Aduna; defaults and modelled scope stated.',
            'Correct tool, wrong argument type twice: request is text, expected object/list. Both return invalid_arguments; final honestly abstains. No provider health execution observed.'
        ]
        row.update(state='COMPLETED',dimensions=ds,notes=notes[i],evidence=turn['evidence_file'],findings=['R13-REQUEST-BINDING'] if i==3 else ['R13-SOURCE-COPY'] if i<2 else [])
        score.append(row)
    smoke.update(status='STOPPED_HIGH',sessions_used=1,clean_session='NOT_RUN_STOPPED_HIGH',actual_tool_call_count_observed=7,
        official_delivery={'MAIN':'FAIL','VARIATION':'NOT_RUN','LIMIT':'PASS_SCOPE_CLARIFICATION_ONLY','DIRECTLY_CONTRASTED_FIGURE':'Aduna 36/507*100=7.101%; health total NOT_OBSERVED'},
        critical=0,high=1,medium=1,full_export='NOT_OBSERVED_DOWNLOAD_TIMEOUT',served_full_schema='NOT_OBSERVED',
        remaining_slots='M05-M12 not submitted, including session B, because stop-on-High takes precedence')
    emit(BASE/'PORTAL_SMOKE_R13.json',smoke)
    emit(BASE/'TURN_SCORECARD_R13.json',{'classification':'MANUAL_INDEPENDENT_VISIBLE_TURN_REVIEW_NOT_FULL_BENCHMARK','dimensions':dimensions,'turns':score,
        'critical':0,'high':1,'medium':1,'severity_count_scope':'Unique candidate findings, not repeated tool attempts; platform summary warning separate.',
        'findings':[{'id':'R13-REQUEST-BINDING','severity':'HIGH','owner':'W2','scope':'agent/tool interface integration; platform schema cause NOT_OBSERVED',
        'evidence':'M04.json','reproduction':'Frozen M04 natural question: two plan_visit calls with string request; error arguments:request:invalid_value; no raw result.',
        'next_action':'W2 reproduce served/decorator request schema and structured argument generation; new package requires W1 acceptance before W3 resumes.'},
        {'id':'R13-SOURCE-COPY','severity':'MEDIUM','owner':'W2','scope':'M01/M02 final response omits explicit source identity and derived 75+ methodology present in output.'}],
        'platform_observation':{'severity':'WARN','owner':'platform UI','detail':'Review summary says no tool errors although both outputs have status:error. Do not use execution completion as semantic PASS.'}})
    with zipfile.ZipFile(package) as z:
        data=z.read('datos_preparados/demografia.csv')
        rows_csv=list(csv.DictReader(io.StringIO(data.decode('utf-8-sig'))))
        aduna=next(r for r in rows_csv if r.get('municipality_code')=='20002')
    assert int(aduna['population_total'])==507 and int(aduna['population_75_plus'])==36
    emit(BASE/'agent_figure_contrast.json',{'classification':'ACTUAL_AGENT_M01_FIGURE_VS_EXACT_SOURCE_FILE','source_id':'EUSTAT_EMH_2025',
        'period':'2025-01-01','source_path':'datos_preparados/demografia.csv','source_sha256':hashlib.sha256(data).hexdigest(),
        'row':aduna,'unit':'%','formula':'round(36 / 507 * 100, 3)','result':round(36/507*100,3),'actual_agent_evidence':'M01.json',
        'method_limit':'75+ derived from birth year, not a separately sourced direct 75+ series; not a portal health result.'})
    support='f7a376b3cee79078cbc8b3f878f6eea3a53fcebb'
    blob=subprocess.check_output(['git','show',support+':docs/vnext/w2/RAG_AB_R13.json'],cwd=ROOT)
    rag=json.loads(blob)
    emit(BASE/'rag_review.json',{'w2_support_sha':support,'source_path':'docs/vnext/w2/RAG_AB_R13.json','source_sha256':hashlib.sha256(blob).hexdigest(),
        'decision':rag['decision'],'questions':rag['question_count'],'supported':15,'unsupported':3,'llm_calls':0,
        'arms':{k:{n:v for n,v in val.items() if n!='rows'} for k,val in rag['arms'].items()},
        'review':'Same four pinned documents; retrieval hit improves 14/15 to 15/15, but support completeness falls 14/15 to 11/15. Lower context does not offset lost support. NO_GO upheld.',
        'limits':rag['limits'],'candidate_changed':False})
    return smoke

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--package',type=Path,required=True)
    r=assemble(p.parse_args().package);print(json.dumps({'used':r['user_messages_used_of_12'],'status':r['status']}))
