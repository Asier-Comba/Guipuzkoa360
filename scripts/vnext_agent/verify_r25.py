"""Inherited full raw/oracle/source/threshold gates on the exact R25 package."""
import argparse
import json
from pathlib import Path
from scripts.vnext_agent import verify_r22 as prior, build_r25 as build

def run(output):
    prior.build = build
    prior.run(output)
    report = json.loads(output.read_bytes())
    report.update(generation='R25', base_r24=build.BASE,
                  parity_baseline_runtime=report['base'],
                  parity_baseline_changed_members=report['changed_members'],
                  changed_members=['main.py','tools.py'])
    output.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2)+'\n', encoding='utf-8', newline='\n')
    return {k:v for k,v in report.items() if k != 'records'}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path, default=build.ROOT/'outputs/r25/offline-audit.json')
    result = run(parser.parse_args().output); print(json.dumps(result, sort_keys=True)); raise SystemExit(result['status'] != 'PASS')
