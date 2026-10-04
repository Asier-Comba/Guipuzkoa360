"""Deterministic R28 build: append input normalization to frozen integrated R27."""
import ast
import io
import json
import zipfile
from scripts.vnext_agent import build_r27 as prior
from scripts.vnext_agent.build_r21 import ROOT, PUBLIC_TOOLS, sha

BASE = '33bb86de68fe6da68d68196b681e8bbf5f67902a'
OUT = ROOT / 'scripts/vnext_agent/dist/r28'
ZIP = OUT / 'gipuzkoa360-r28-final-agent.zip'
MANIFEST = OUT / 'gipuzkoa360-r28-final-agent-manifest.json'
PORTAL = ROOT / 'agentes/gipuzkoa360_vnext/portal_r28'


def build():
    baseline = prior.build()
    assert baseline['zip_sha256'] == '7c965ae39c2674f81fc137a1a8a47e384914141b2c104ac24dfc29b535dc79c6'
    assert baseline['manifest_sha256'] == '3f561005b81248f211670e817fcd3c413b92aa860ba46c5b7b4e8564b3619537'
    original = prior.ZIP.read_bytes()
    OUT.mkdir(parents=True, exist_ok=True)
    PORTAL.mkdir(parents=True, exist_ok=True)
    members, changed = {}, []
    with zipfile.ZipFile(io.BytesIO(original)) as old, zipfile.ZipFile(ZIP, 'w') as new:
        for info in old.infolist():
            before = old.read(info.filename)
            data = before
            if info.filename == 'tools.py':
                data += b'\n\n' + (ROOT / 'scripts/vnext_agent/r28_inputs.py').read_bytes().replace(b'\r\n', b'\n')
            new.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            members[info.filename] = {'bytes': len(data), 'sha256': sha(data)}
            if before != data:
                changed.append(info.filename)
            if info.filename in ('main.py', 'tools.py'):
                ast.parse(data)
                (PORTAL / info.filename).write_bytes(data)
    assert changed == ['tools.py']
    report = json.loads(prior.MANIFEST.read_bytes())
    report.update(package='GIPUZKOA360_R28_final_public_input_normalization',
                  base_r27_runtime=BASE, base_r27_zip_sha256=sha(original),
                  changed_members=changed, main_changed=False, members=members,
                  sha256=sha(ZIP.read_bytes()), bytes=ZIP.stat().st_size,
                  uncompressed_bytes=sum(v['bytes'] for v in members.values()),
                  runtime_delta='Deterministic pinned-catalog public visit labels and explicit date normalization only.')
    assert report['bytes'] < report['limit_bytes']
    MANIFEST.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2)+'\n', encoding='utf-8', newline='\n')
    return {'zip_sha256': report['sha256'], 'manifest_sha256': sha(MANIFEST.read_bytes()), 'bytes': report['bytes']}


if __name__ == '__main__':
    print(json.dumps(build(), sort_keys=True))
