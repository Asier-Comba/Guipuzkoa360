"""Full inherited parity/oracle gates on the exact R23 package."""
import argparse
import json
from pathlib import Path
from scripts.vnext_agent import verify_r22 as prior, build_r23 as build

def run(output):
    prior.build = build
    result = prior.run(output)
    report = json.loads(output.read_bytes())
    report.update(generation='R23', base_r22=build.BASE)
    output.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2)+'\n', encoding='utf-8', newline='\n')
    return {k:v for k,v in report.items() if k != 'records'}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path, default=build.ROOT/'outputs/r23/offline-audit.json')
    result = run(parser.parse_args().output); print(json.dumps(result, sort_keys=True)); raise SystemExit(result['status'] != 'PASS')
