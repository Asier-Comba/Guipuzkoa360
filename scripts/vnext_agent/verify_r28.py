"""Run inherited raw/oracle/fuzz gates on the exact R28 package."""
import argparse
import json
from pathlib import Path
from scripts.vnext_agent import verify_r26 as prior, build_r28 as build


def run(output):
    prior.build = build
    prior.run(output)
    report = json.loads(output.read_bytes())
    report.update(generation='R28', base_r27_runtime=build.BASE,
                  changed_members_vs_r27=['tools.py'],
                  scope='Public input normalization; canonical raw mathematics unchanged.')
    output.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2)+'\n', encoding='utf-8', newline='\n')
    return {k:v for k,v in report.items() if k != 'records'}


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=build.ROOT/'work/r28-audit.json')
    result=run(parser.parse_args().output)
    print(json.dumps(result,sort_keys=True))
    raise SystemExit(result['status'] != 'PASS')
