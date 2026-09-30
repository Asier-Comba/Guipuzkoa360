"""Contrast saved parity with final oracle and replay exact historical M04 args."""
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import zipfile
from scripts.vnext_agent.build_r14_binding import ROOT, ZIP
from scripts.vnext_agent.verify_r14_binding import emit

def run():
    output=ROOT/'resultados/vnext/r14'
    oracle=json.loads((ROOT/'docs/vnext/w3/r14/FINAL_ORACLE_R13.json').read_bytes())
    parity=json.loads((output/'parity.json').read_bytes())
    records={r['case']:r['public_result'] for r in parity['records']}
    checked=[]
    for case in oracle['cases']:
        v=records[case['case_id']]
        assert v['status']==case['expected_consumer_envelope_status']
        scenarios=v.get('mobility',{}).get('scenarios',[])
        if scenarios:
            s=scenarios[0]
            assert s['status']==case['expected_status']
            for metric in case['numeric_claims']:
                actual=s['itinerary']['total_s'] if metric['metric']=='total_s' else s['components_s'][metric['metric']]
                assert actual==metric['value'],(case['case_id'],metric)
            sources={x['source_id']:x for x in s['sources']}
            for fact in case['source_facts']:
                assert sources[fact['source_id']]['reference_period']==fact['reference_period']
            for field in ['scenario_kind','snapshot_id','time_basis']:
                assert s[field]==case['critical_semantic_facts'][field]
            if s.get('health_destination'):
                assert s['health_destination']['entrance_verified'] is False
                assert s['health_destination']['modelled_access'] is True
                assert s['health_destination']['human_review_required'] is True
        else:
            assert not v['claims'] and v['raw_result_sha256'] is None
        checked.append({'case':case['case_id'],'status':'PASS','numeric_components_checked':len(case['numeric_claims']),'source_periods_checked':len(case['source_facts']) if scenarios else 0})
    for row in parity['records']:
        for s in row['public_result'].get('mobility',{}).get('scenarios',[]):
            for p in s['parameter_attribution']:
                assert p['w2_attribution']!='human_explicit'
                if p['provider_origin']=='model_default':assert p['w2_attribution']=='provider_default'
    emit(output/'truth_pack_contrast.json',{'status':'PASS','cases':checked,'parameter_attribution':'PASS; caller does not prove human choice','oracle_sha256':hashlib.sha256((ROOT/'docs/vnext/w3/r14/FINAL_ORACLE_R13.json').read_bytes()).hexdigest(),'llm_calls':0})
    old_bytes=subprocess.check_output(['git','show','46657c9fc966052dce8b5de75959f8c68282cfb4:resultados/vnext/r13/request_binding_reproduction.json'],cwd=ROOT)
    historical=json.loads(old_bytes)
    with tempfile.TemporaryDirectory(prefix='g360-r14-replay-') as d, zipfile.ZipFile(ZIP) as z:
        z.extractall(d)
        sys.path.insert(0,d)
        import tools
        results=[]
        for c in historical['results']:
            envelope=tools.execute('plan_visit',c['arguments'],c['output']['request_id'],root=Path(d))
            value=json.loads(tools.public_result(envelope,root=Path(d)))
            assert value==c['output'], 'historical output changed'
            assert envelope['raw_result_json'] is None
            results.append({'arguments':c['arguments'],'output':value,'raw_result':None})
    emit(output/'historical_m04_replay.json',{'classification':'EXACT_HISTORICAL_ARGUMENT_REPLAY_NOT_LLM','status':'BOTH_CONTROLLED_REJECTIONS_UNCHANGED','original_reproduction_sha256':hashlib.sha256(old_bytes).hexdigest(),'original_commit':'46657c9fc966052dce8b5de75959f8c68282cfb4','results':results})

if __name__=='__main__':run();print('Final truth pack and exact historical M04 replay PASS')
