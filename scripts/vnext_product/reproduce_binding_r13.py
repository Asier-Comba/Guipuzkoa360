"""Replay observed argument objects offline; this never calls a language model."""
import argparse
import json
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[2]
CHILD=r'''
import sys,json,socket
from pathlib import Path
p=json.load(sys.stdin);root=Path(p['root']);sys.path.insert(0,str(root))
def deny(*a,**k):raise RuntimeError('Network denied')
socket.socket=deny;socket.create_connection=deny
import tools
out=[]
for i,c in enumerate(p['calls']):
 e=tools.execute('plan_visit',c['arguments'],'R13-M04-offline-'+str(i),root=root)
 out.append({'arguments':c['arguments'],'output':json.loads(tools.public_result(e)),'raw_result':e.get('raw_result_json')})
json.dump({'classification':'OFFLINE_REPLAY_OF_ACTUAL_AGENT_ARGS_NOT_LLM','model_calls':0,'results':out},sys.stdout)
'''
def run(python,candidate):
    smoke=json.loads((ROOT/'resultados/vnext/r13/PORTAL_SMOKE_R13.json').read_bytes())
    payload={'root':str(candidate.resolve()),'calls':smoke['turns'][3]['tool_calls']}
    r=subprocess.run([str(python),'-I','-X','utf8','-c',CHILD],input=json.dumps(payload),encoding='utf-8',capture_output=True,cwd=candidate,check=True)
    report=json.loads(r.stdout)
    assert len(report['results'])==2
    assert all(x['output']['error']['message']=='arguments:request:invalid_value' and x['raw_result'] is None for x in report['results'])
    (ROOT/'resultados/vnext/r13/request_binding_reproduction.json').write_bytes((json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode())
    return report
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--python',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True)
    a=p.parse_args();r=run(a.python,a.candidate);print('Two observed string requests rejected offline; no provider raw and no LLM.')
