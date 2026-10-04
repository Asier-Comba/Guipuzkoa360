"""R27 integrated: W1 threshold ledger + W3 bounded presentation guards."""
import ast
import io
import json
import subprocess
import zipfile
from scripts.vnext_agent.build_r21 import ROOT, PUBLIC_TOOLS, sha

BASE = 'd5c02a2f9a1d8b67b5a74c3569c7e98094b0eacd'
BASE_ZIP = 'scripts/vnext_agent/dist/r26/gipuzkoa360-r26-final-agent.zip'
BASE_MANIFEST = 'scripts/vnext_agent/dist/r26/gipuzkoa360-r26-final-agent-manifest.json'
BASE_HASH = '9716389b7094096195062e8bda9b9ddd4c0f21cedce09cee8496b6ae45f570c7'
BASE_MANIFEST_HASH = 'dae1dfee59ebbd8839b3ab7468be9c04b4e0d9abd621e933a751824575b40a3e'
OUT = ROOT / 'scripts/vnext_agent/dist/r27'
ZIP = OUT / 'gipuzkoa360-r27-integrated-agent.zip'
MANIFEST = OUT / 'gipuzkoa360-r27-integrated-agent-manifest.json'
PORTAL = ROOT / 'agentes/gipuzkoa360_vnext/portal_r27'


def blob(path):
    return subprocess.check_output(['git', 'show', f'{BASE}:{path}'], cwd=ROOT)


def build():
    baseline, metadata = blob(BASE_ZIP), blob(BASE_MANIFEST)
    assert sha(baseline) == BASE_HASH and sha(metadata) == BASE_MANIFEST_HASH
    prior = json.loads(metadata)
    OUT.mkdir(parents=True, exist_ok=True)
    PORTAL.mkdir(parents=True, exist_ok=True)
    candidate_main = (PORTAL / 'main.py').read_bytes().replace(b'\r\n', b'\n')
    ast.parse(candidate_main)
    members = {}
    changed = []
    with zipfile.ZipFile(io.BytesIO(baseline)) as old, zipfile.ZipFile(ZIP, 'w') as new:
        for info in old.infolist():
            original = old.read(info.filename)
            data = original
            if info.filename == 'main.py':
                data = candidate_main
            elif info.filename == 'tools.py':
                data += b'\n\n' + (ROOT / 'scripts/vnext_agent/r27_threshold.py').read_bytes().replace(b'\r\n', b'\n')
            new.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            members[info.filename] = dict(bytes=len(data), sha256=sha(data))
            if data != original:
                changed.append(info.filename)
            if info.filename in ('main.py', 'tools.py'):
                ast.parse(data)
                (PORTAL / info.filename).write_bytes(data)
    assert changed == ['main.py', 'tools.py'] and len(members) == len(prior['members'])
    report = {**prior, 'package': 'GIPUZKOA360_R27_integrated_release_candidate', 'base_r26_runtime': BASE,
        'base_r26_zip_sha256': BASE_HASH, 'base_r26_manifest_sha256': BASE_MANIFEST_HASH,
        'sha256': sha(ZIP.read_bytes()), 'bytes': ZIP.stat().st_size, 'members': members,
        'changed_members': changed, 'context_assets_changed': [],
        'uncompressed_bytes': sum(x['bytes'] for x in members.values()),
        'runtime_delta': 'W1 verified threshold_transition_ledger v1 plus three bounded W3 presentation guards; no data/provider/core arithmetic changes.',
        'portal_real_agent': 'NOT_RUN'}
    assert report['bytes'] < report['limit_bytes']
    MANIFEST.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8', newline='\n')
    return dict(zip_sha256=report['sha256'], manifest_sha256=sha(MANIFEST.read_bytes()), bytes=report['bytes'])


if __name__ == '__main__':
    print(json.dumps(build(), sort_keys=True))
