"""Surgical threshold-only build from immutable R22 bytes."""
import ast
import io
import json
import subprocess
import zipfile
from scripts.vnext_agent.build_r21 import ROOT, PUBLIC_TOOLS, sha

BASE = '202352adc10e90a4b98125387af8e0ff7a438073'
BASE_ZIP = 'scripts/vnext_agent/dist/r22/gipuzkoa360-r22-final-agent.zip'
BASE_MANIFEST = 'scripts/vnext_agent/dist/r22/gipuzkoa360-r22-final-agent-manifest.json'
BASE_HASH = '6f7912c17f06c81f637dea26ea8bb49287f56c7c41099c20cb11b4ef98373c47'
BASE_MANIFEST_HASH = '29a4d17b0e39962210b7847e83595485ac14f4878dd97717345a66e8c66adc8a'
OUT = ROOT / 'scripts/vnext_agent/dist/r23'
ZIP = OUT / 'gipuzkoa360-r23-final-agent.zip'
MANIFEST = OUT / 'gipuzkoa360-r23-final-agent-manifest.json'
PORTAL = ROOT / 'agentes/gipuzkoa360_vnext/portal_r23'
DELTA = ROOT / 'scripts/vnext_agent/r23_threshold.py'
DESCRIPTION = ' umbral_km debe ser >0 y <=100. La clasificación de salida es distancia_m <= umbral_km*1000; una distancia observada de 0 está incluida.'

def blob(path):
    return subprocess.check_output(['git', 'show', f'{BASE}:{path}'], cwd=ROOT)

def generated_main(data):
    text = data.decode('utf-8'); lines = text.splitlines(keepends=True)
    nodes = [n for n in ast.parse(text).body if isinstance(n, ast.FunctionDef) and n.name in {'analizar_acceso_general', 'analizar_acceso_municipios'}]
    assert len(nodes) == 2
    for node in reversed(nodes):
        doc = node.body[0]; value = ast.literal_eval(doc.value)
        value = value.replace(' y clasificación con umbral >0 y <=100 km', '').replace('; umbral >0 y <=100 km', '')
        lines[doc.lineno-1:doc.end_lineno] = ['    ' + repr(value + DESCRIPTION) + '\n']
    return ''.join(lines).encode('utf-8')

def build():
    baseline, metadata = blob(BASE_ZIP), blob(BASE_MANIFEST)
    assert sha(baseline) == BASE_HASH and sha(metadata) == BASE_MANIFEST_HASH
    prior = json.loads(metadata); OUT.mkdir(parents=True, exist_ok=True); PORTAL.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(baseline)) as old, zipfile.ZipFile(ZIP, 'w') as new:
        text = old.read('tools.py').decode('utf-8')
        overrides = {'main.py': generated_main(old.read('main.py')), 'tools.py': text.encode('utf-8') + b'\n\n' + DELTA.read_bytes().replace(b'\r\n', b'\n')}
        members, changed = {}, []
        for info in old.infolist():
            original = old.read(info.filename); data = overrides.get(info.filename, original)
            new.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            members[info.filename] = {'bytes': len(data), 'sha256': sha(data)}
            if data != original: changed.append(info.filename)
    assert changed == ['main.py', 'tools.py'] and len(members) == 25
    for name, data in overrides.items(): ast.parse(data); (PORTAL / name).write_bytes(data)
    report = {'package': 'GIPUZKOA360_R23_final_agent', 'base_r22_tested_runtime': BASE,
              'base_r22_zip_sha256': BASE_HASH, 'base_r22_manifest_sha256': BASE_MANIFEST_HASH,
              'sha256': sha(ZIP.read_bytes()), 'bytes': ZIP.stat().st_size, 'members': members,
              'members_count': len(members), 'changed_members': changed, 'context_paths': prior['context_paths'],
              'context_assets_changed': [], 'uncompressed_bytes': sum(x['bytes'] for x in members.values()),
              'limit_bytes': prior['limit_bytes'], 'public_tools': PUBLIC_TOOLS, 'w1_runtime_changed': False,
              'v4_changed': False, 'runtime_delta': 'Verified inclusive threshold projection and two access descriptions only',
              'portal_real_agent': 'NOT_RUN'}
    assert report['bytes'] < report['limit_bytes']
    MANIFEST.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2)+'\n', encoding='utf-8', newline='\n')
    return {'zip_sha256': report['sha256'], 'manifest_sha256': sha(MANIFEST.read_bytes()), 'bytes': report['bytes']}

if __name__ == '__main__': print(json.dumps(build(), sort_keys=True))
