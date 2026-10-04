"""Cold-process, network-denied observer, not a model or Studio simulator."""
import inspect
import json
import os
from pathlib import Path
import socket
import sys
import types
from scripts.vnext_agent.verify_r15 import oracle_check, canonical, sha

def worker(root):
    def denied(*args,**kwargs):raise RuntimeError('R20 observer network denied')
    socket.socket=denied;socket.create_connection=denied
    root=Path(root).resolve();os.environ['GIPUZKOA360_VNEXT_ROOT']=str(root);sys.path.insert(0,str(root))
    import main, tools
    main.uuid4=lambda:types.SimpleNamespace(hex='R20_FIXED_OBSERVER')
    signatures={f.__name__:{'fields':list(inspect.signature(f).parameters),'required':[k for k,v in inspect.signature(f).parameters.items() if v.default is inspect.Parameter.empty],'defaults':{k:v.default for k,v in inspect.signature(f).parameters.items() if v.default is not inspect.Parameter.empty}} for f in main.TOOLS}
    original=tools.execute;captured=[]
    def capture(*args,**kwargs):
        if current_fault[0]=='synthetic_observed_transport':
            result=tools._error(args[2],args[0],args[1],'transport','observed_transport_failure','SYNTHETIC TEST ONLY: observed transport failure')
        elif current_fault[0]=='synthetic_contract_failure':
            result=tools._error(args[2],args[0],args[1],'execution','contract_violation','SYNTHETIC TEST ONLY: contract violation')
        else:result=original(*args,**kwargs)
        captured.append(result);return result
    tools.execute=capture
    current_fault=[None]
    records={}
    for case in json.loads(sys.stdin.read())['cases']:
        captured.clear();args=dict(case['arguments'])
        current_fault[0]=case.get('fault')
        for k,token in case.get('nonfinite',{}).items():args[k]=float(token)
        try:
            if case.get('route')=='internal':
                result=tools.execute(case['tool'],args,'R20_FIXED_OBSERVER',root=root);rendered=tools.public_result(result,root=root)
            else:
                function=getattr(main,case['tool']);inspect.signature(function).bind(**args);rendered=function(**args)
            view=tools.strict_loads(rendered);raw=captured[-1].get('raw_result_json') if captured else None
            record={'status':view['status'],'execute_calls':len(captured),'raw_sha256':sha(raw) if raw else None,'claims':view.get('claims',[]),'view':view,'engine_input':captured[-1]['normalized_input'] if captured else None,'effective_request':captured[-1].get('effective_request') if captured else None}
            if case.get('oracle'):record['oracle']=oracle_check(case['oracle'],view,tools.strict_loads(raw) if raw else None)
            if case.get('keep_raw') and raw:record['raw']=tools.strict_loads(raw)
            records[case['id']]=record
        except TypeError as exc:
            try:inspect.signature(getattr(main,case['tool'])).bind(**args)
            except TypeError:records[case['id']]={'status':'binding_rejected','claims':[],'execute_calls':0,'error':str(exc)}
            else:records[case['id']]={'status':'escaped_exception','error':repr(exc)}
        except Exception as exc:records[case['id']]={'status':'escaped_exception','error':repr(exc)}
    return {'records':records,'signatures':signatures,'model_calls':0,'network':'denied','classification':'OFFLINE_PUBLIC_BINDING_NOT_SERVED_STUDIO_SCHEMA'}

if __name__=='__main__':print(canonical(worker(sys.argv[1])))
