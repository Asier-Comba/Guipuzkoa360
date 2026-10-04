"""Tools-only health-scope projection over the immutable exact R23 package."""
import ast
import io
import json
import subprocess
import zipfile
from scripts.vnext_agent.build_r21 import ROOT, PUBLIC_TOOLS, sha

BASE = '6e960e873972b06fbd9e5125e7a498eef61c6d3a'
BASE_ZIP = 'scripts/vnext_agent/dist/r23/gipuzkoa360-r23-final-agent.zip'
BASE_MANIFEST = 'scripts/vnext_agent/dist/r23/gipuzkoa360-r23-final-agent-manifest.json'
BASE_HASH = 'b88f44aaabeac6cf50ee7a0e3aaea7295737f0b00bfb47cc2e34c1240e63b2e0'
BASE_MANIFEST_HASH = 'ceaed687082f4ab165e79ae828cd8f0b17ca51cd888669f9c21f0e3ab6ef9f62'
OUT = ROOT / 'scripts/vnext_agent/dist/r24'
ZIP = OUT / 'gipuzkoa360-r24-final-agent.zip'
MANIFEST = OUT / 'gipuzkoa360-r24-final-agent-manifest.json'
PORTAL = ROOT / 'agentes/gipuzkoa360_vnext/portal_r24'
DELTA = ROOT / 'scripts/vnext_agent/r24_health_scope.py'

def blob(path):
    return subprocess.check_output(['git', 'show', f'{BASE}:{path}'], cwd=ROOT)

def build():
    baseline, metadata = blob(BASE_ZIP), blob(BASE_MANIFEST)
    assert sha(baseline) == BASE_HASH and sha(metadata) == BASE_MANIFEST_HASH
    prior = json.loads(metadata)
    OUT.mkdir(parents=True, exist_ok=True); PORTAL.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(baseline)) as old, zipfile.ZipFile(ZIP, 'w') as new:
        tools = old.read('tools.py') + b'\n\n' + DELTA.read_bytes().replace(b'\r\n', b'\n')
        members, changed = {}, []
        for info in old.infolist():
            original = old.read(info.filename)
            data = tools if info.filename == 'tools.py' else original
            new.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            members[info.filename] = {'bytes': len(data), 'sha256': sha(data)}
            if data != original: changed.append(info.filename)
        for name in ('main.py', 'tools.py'):
            data = tools if name == 'tools.py' else old.read(name)
            ast.parse(data); (PORTAL / name).write_bytes(data)
    assert changed == ['tools.py'] and len(members) == 25
    report = {
        'package': 'GIPUZKOA360_R24_final_agent', 'base_r23_tested_runtime': BASE,
        'base_r23_zip_sha256': BASE_HASH, 'base_r23_manifest_sha256': BASE_MANIFEST_HASH,
        'sha256': sha(ZIP.read_bytes()), 'bytes': ZIP.stat().st_size, 'members': members,
        'members_count': len(members), 'changed_members': changed,
        'context_paths': prior['context_paths'], 'context_assets_changed': [],
        'uncompressed_bytes': sum(x['bytes'] for x in members.values()),
        'limit_bytes': prior['limit_bytes'], 'public_tools': PUBLIC_TOOLS,
        'w1_runtime_changed': False, 'v4_changed': False, 'main_changed': False,
        'runtime_delta': 'Verified complete journey start/intermediate/end projection; main and prompt unchanged',
        'portal_real_agent': 'NOT_RUN',
    }
    assert report['bytes'] < report['limit_bytes']
    MANIFEST.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2)+'\n', encoding='utf-8', newline='\n')
    return {'zip_sha256': report['sha256'], 'manifest_sha256': sha(MANIFEST.read_bytes()), 'bytes': report['bytes']}

if __name__ == '__main__': print(json.dumps(build(), sort_keys=True))
