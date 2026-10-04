"""Full inherited raw parity, adapting only the intentionally changed public input."""
import argparse
import copy
import json
from pathlib import Path
from scripts.vnext_agent import verify_r22 as verification, build_r26 as build

def run(output):
    verification.build=build
    original=verification.prior.run_worker
    def worker(root,cases):
        cases=copy.deepcopy(cases)
        if Path(root).name=='r21':
            for row in cases:
                args=row['arguments']
                if row['tool']=='plan_visit' and row.get('route')!='internal' and 'appointment_time' in args:
                    args['appointment_times']=[args.pop('appointment_time')]
        return original(root,cases)
    verification.prior.run_worker=worker
    result=verification.run(output)
    report=json.loads(output.read_bytes())
    report.update(generation='R26',base_r25_runtime=build.BASE,
        comparison_boundary='New time pairs tested separately; existing single requests mapped only appointment_time -> appointment_times singleton. Raw results/effective requests/claims must remain equal.')
    output.write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    return {k:v for k,v in report.items() if k!='records'}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=build.ROOT/'outputs/r26/offline-audit.json')
    report=run(parser.parse_args().output);print(json.dumps(report,sort_keys=True));raise SystemExit(report['status']!='PASS')
