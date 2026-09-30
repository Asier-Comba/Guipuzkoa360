"""Repackage frozen patch3, replacing ONLY main.py; no producer regeneration."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
BASE = '8c94f8c3cf9d732c4ce94af7b4bef8f6e154c243'
OUT = ROOT / 'scripts/vnext_agent/dist/r14'
ZIP = OUT / 'gipuzkoa360-r14-binding.zip'
MANIFEST = OUT / 'gipuzkoa360-r14-binding-manifest.json'

def sha(b):
    return hashlib.sha256(b).hexdigest()

def blob(path):
    return subprocess.check_output(['git', 'show', f'{BASE}:{path}'], cwd=ROOT)

def build():
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError('Build the reviewed ZIP with CPython 3.12; other compression runtimes require a new candidate identity')
    import io
    baseline = blob('scripts/vnext_agent/dist/gipuzkoa360-vnext-w2.zip')
    assert sha(baseline) == '3951b290b6ca59c336886a3f0acee77a68036d4fbcbc06c2cedfe22400c08616'
    report = json.loads(blob('scripts/vnext_agent/dist/gipuzkoa360-vnext-w2-manifest.json'))
    source = (ROOT / 'agentes/gipuzkoa360_vnext/main.py').read_text(encoding='utf-8')
    boundary = 'try:\n    from . import tools as evidence\nexcept ImportError:\n    import tools as evidence'
    assert source.count(boundary) == 1
    main = source.replace(boundary, 'import tools as evidence').encode('utf-8')
    generated = ROOT / 'agentes/gipuzkoa360_vnext/portal/main.py'
    generated.write_bytes(main)
    OUT.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(baseline)) as old, zipfile.ZipFile(ZIP, 'w') as new:
        members = {}
        for info in old.infolist():
            data = main if info.filename == 'main.py' else old.read(info.filename)
            new.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            members[info.filename] = {'bytes': len(data), 'sha256': sha(data)}
    constants = {n.targets[0].id: ast.literal_eval(n.value) for n in ast.parse(main).body
                 if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)
                 and n.targets[0].id in {'SYSTEM_PROMPT', 'STUDIO_CONTEXT_FILES'}}
    assert len(constants['SYSTEM_PROMPT']) <= 8000
    report.update(package='GIPUZKOA360_R14_portal_binding', sha256=sha(ZIP.read_bytes()),
                  bytes=ZIP.stat().st_size, members=members,
                  instruction_chars=len(constants['SYSTEM_PROMPT']),
                  uncompressed_bytes=sum(v['bytes'] for v in members.values()),
                  r14_base_runtime=BASE, r14_base_zip_sha256=sha(baseline),
                  r14_changed_members=['main.py'],
                  r14_interface='flat single visit; internal structured request unchanged',
                  r14_historical_audit_tests='Patch3 test members retained byte-identical; flat-interface tests are off-package')
    MANIFEST.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2)+'\n', encoding='utf-8', newline='\n')
    return {'zip_sha256': report['sha256'], 'manifest_sha256': sha(MANIFEST.read_bytes()),
            'main_sha256': sha(main), 'tools_sha256': members['tools.py']['sha256']}

if __name__ == '__main__':
    print(json.dumps(build()))
