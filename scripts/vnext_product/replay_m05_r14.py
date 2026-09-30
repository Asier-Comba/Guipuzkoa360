"""Replay observed flat arguments, plus explicitly offline omission control."""
import argparse
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'resultados/vnext/r14'
CHILD=r'''
import json,sys,socket
from pathlib import Path
p=json.load(sys.stdin);root=Path(p['root']);sys.path.insert(0,str(root))
socket.socket=lambda *a,**k: (_ for _ in ()).throw(RuntimeError('offline network forbidden'))
import main
results=[]
for args in p['arguments']:
 results.append({'arguments':args,'output':json.loads(main.plan_visit(**args))})
control=dict(p['arguments'][0]);del control['return_deadline']
good=json.loads(main.plan_visit(**control))
assert all(r['output']['error']['message']=='mobility:invalid_clock' and not r['output']['claims'] and r['output']['raw_result_sha256'] is None for r in results)
assert good['status']=='valid' and good['mobility']['scenarios'][0]['itinerary']['total_s']==10691
json.dump({'classification':'OFFLINE_REPLAY_AND_OMISSION_CONTROL_NOT_AGENT','model_calls':0,'observed_argument_replays':results,'control':{'change':'Only remove return_deadline empty string; no candidate byte change','arguments':control,'output':good},'conclusion':'Empty return_deadline is preserved by flat wrapper and rejected; omitted optional succeeds offline. Full served schema and reason for model empty value NOT_OBSERVED.'},sys.stdout)
'''

def run(python,candidate):
    nodes=json.loads((OUT/'M05_normalized.json').read_bytes())
    args=[json.loads(n['arguments']) for n in nodes if n.get('tool')=='plan_visit']
    assert len(args)==3 and all(q['return_deadline']=='' for q in args)
    p={'root':str(candidate.resolve()),'arguments':args[:2]}
    r=subprocess.run([str(python),'-I','-X','utf8','-c',CHILD],input=json.dumps(p),encoding='utf-8',capture_output=True,cwd=candidate,check=True)
    report=json.loads(r.stdout)
    (OUT/'M05_offline_reproduction.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--python',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True)
    a=p.parse_args();run(a.python,a.candidate);print('Two actual error arguments reproduced; omitted-deadline control10691s offline, no LLM')
