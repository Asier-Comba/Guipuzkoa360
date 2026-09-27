"""Re-run release gates and retain command outcomes without modifying frozen inputs."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
from time import perf_counter
from verify_runtime_identity import ROOT, audit

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--output',type=Path,default=ROOT/'analisis/ops/release_regression.json'); args=parser.parse_args()
    before=audit(); rows=[]
    commands=[
      [sys.executable,'-m','pytest','-o','addopts=','-q'],
      ['node','--test','tests/e2e/contract_flow.test.mjs'],
      ['node','--check','scripts/jury_view.js'],
      ['node','--check','scripts/build_jury.mjs'],
      ['node','--check','scripts/build_results.mjs'],
      [sys.executable,'scripts/benchmark/verify_jury_results.py','--output','work/jury-gate.json'],
      [sys.executable,'scripts/release/verify_final_artifacts.py'],
      [sys.executable,'scripts/ops/verify_package.py'],
      [sys.executable,'scripts/ops/compute_source_health.py','--output','work/source-health.json'],
      [sys.executable,'scripts/evaluation/evaluate_next.py','--output-dir','work/next'],
    ]
    for command in commands:
        start=perf_counter(); result=subprocess.run(command,cwd=ROOT,capture_output=True,encoding='utf-8',errors='replace')
        rows.append({'command':['python' if v==sys.executable else v for v in command], 'exit_code':result.returncode,
                     'duration_seconds':round(perf_counter()-start,3),'stdout_tail':result.stdout[-6000:],
                     'stderr_tail':result.stderr[-1500:]})
        print(json.dumps({'command':rows[-1]['command'],'exit_code':result.returncode}),flush=True)
    after=audit()
    report={'scope':'local release regression; not portal or remote Actions',
            'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            'python':platform.python_version(),'commands':rows,'runtime_before':before,'runtime_after':after,
            'package':json.loads((ROOT/'work/package-gate.json').read_text(encoding='utf-8')),
            'status':'PASS' if before['status']==after['status']=='PASS' and all(r['exit_code']==0 for r in rows) else 'FAIL'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
    raise SystemExit(report['status']!='PASS')

if __name__=='__main__': main()
