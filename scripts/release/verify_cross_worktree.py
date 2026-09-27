"""Build one commit in three independent clean worktrees, preserving each for inspection."""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--ref',default='HEAD')
    args=parser.parse_args()
    sha=subprocess.check_output(['git','rev-parse',args.ref],cwd=ROOT,text=True).strip()
    reports=[]
    for index,eol in enumerate(('false','true','input')):
        target=ROOT/'work'/f'cross-{sha[:12]}-{index}'
        if target.exists():
            raise SystemExit(f'Refuse to overwrite {target}; choose a new commit or inspect existing evidence.')
        subprocess.run(['git','-c',f'core.autocrlf={eol}','worktree','add','--detach',str(target),sha],cwd=ROOT,check=True,capture_output=True)
        clean=subprocess.check_output(['git','status','--porcelain'],cwd=target,text=True).strip()==''
        subprocess.run([sys.executable,'scripts/agent/build_portal_package.py'],cwd=target,check=True,capture_output=True)
        archive=target/'dist/gipuzkoa360-urban-challenge-rc2.zip'
        content=archive.read_bytes()
        with zipfile.ZipFile(archive) as package:
            members=[{'name':i.filename,'bytes':i.file_size,'sha256':hashlib.sha256(package.read(i)).hexdigest(),
                      'date_time':i.date_time,'create_system':i.create_system,'external_attr':i.external_attr,
                      'compress_type':i.compress_type,'flag_bits':i.flag_bits} for i in package.infolist()]
        reports.append({'checkout_autocrlf':eol,'clean_before_build':clean,'bytes':len(content),
                        'sha256':hashlib.sha256(content).hexdigest(),'members':members})
    success=all(x['clean_before_build'] for x in reports) and len({x['sha256'] for x in reports})==1
    report={'status':'PASS' if success else 'FAIL','candidate_sha':sha,'python':sys.version,
            'scope':'Three clean Windows worktrees, differing core.autocrlf; same Python/zlib toolchain. No claim of all zlib versions.',
            'attempted':3,'identical':sum(x['sha256']==reports[0]['sha256'] for x in reports),'builds':reports}
    output=ROOT/'analisis/cross_worktree_reproducibility.json'
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({k:v for k,v in report.items() if k!='builds'},indent=2))
    print(json.dumps({'bytes':reports[0]['bytes'],'sha256':reports[0]['sha256']}))
    raise SystemExit(0 if success else 1)


if __name__=='__main__':main()
