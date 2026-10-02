"""Ten-tool interface built only from the exact tested R20 package."""
import ast
import io
import json
import subprocess
import zipfile
from scripts.vnext_agent.build_r16 import ROOT, sha

BASE = '81c42da2e8ab7074074d9f114d4ac7990e715da4'
BASE_ZIP = 'scripts/vnext_agent/dist/r20/gipuzkoa360-r20-final-agent.zip'
BASE_MANIFEST = 'scripts/vnext_agent/dist/r20/gipuzkoa360-r20-final-agent-manifest.json'
BASE_HASH = '9a271888b414168d06d92dad1b9a9ee594ee0209f78f0abee8d85925cdb6e33e'
BASE_MANIFEST_HASH = '0362aa249756275f6377cf9b3d3e4859f1f01ad856e0e5663e5cc12150030081'
OUT = ROOT / 'scripts/vnext_agent/dist/r21'
ZIP = OUT / 'gipuzkoa360-r21-final-agent.zip'
MANIFEST = OUT / 'gipuzkoa360-r21-final-agent-manifest.json'
PORTAL = ROOT / 'agentes/gipuzkoa360_vnext/portal_r21'
PROMPT = ROOT / 'scripts/vnext_agent/r21_prompt.txt'
DELTA = ROOT / 'scripts/vnext_agent/r21_surface.py'
PUBLIC_TOOLS = ['obtener_resumen_territorial', 'analizar_envejecimiento', 'analizar_acceso_general', 'analizar_acceso_municipios', 'analizar_coincidencia', 'simular_anadir_servicio', 'simular_retirar_servicio', 'simular_cambiar_umbral', 'consultar_capacidades', 'plan_visit']

def blob(path):
    return subprocess.check_output(['git', 'show', f'{BASE}:{path}'], cwd=ROOT)

def generated_main(data):
    text = data.decode('utf-8'); lines = text.splitlines(keepends=True); changes = []
    for node in ast.parse(text).body:
        if isinstance(node, ast.FunctionDef) and node.name in {'comparar_municipios', 'consultar_fuente'}:
            start = min([node.lineno] + [d.lineno for d in node.decorator_list])
            changes.append((start - 1, node.end_lineno, ''))
        elif isinstance(node, ast.Assign) and getattr(node.targets[0], 'id', None) in {'SYSTEM_PROMPT', 'TOOLS'}:
            replacement = ('SYSTEM_PROMPT = ' + repr(PROMPT.read_text(encoding='utf-8').strip()) if node.targets[0].id == 'SYSTEM_PROMPT' else 'TOOLS = [' + ', '.join(PUBLIC_TOOLS) + ']') + '\n'
            changes.append((node.lineno - 1, node.end_lineno, replacement))
    for start, end, replacement in sorted(changes, reverse=True): lines[start:end] = [replacement]
    text = ''.join(lines).replace('Catálogo completo de las doce operaciones públicas, decisiones necesarias, cobertura, fuentes, fechas y límites, incluidas opciones de visita sanitaria.', 'Catálogo de las diez herramientas públicas, decisiones, cobertura y fichas de fuentes con institución, fecha, método y límites; incluye opciones de visita sanitaria y capacidades compuestas. Para explicar procedencia sin pedir códigos técnicos.')
    ast.parse(text)
    return text.encode('utf-8')

def build():
    assert len(PUBLIC_TOOLS) == len(set(PUBLIC_TOOLS)) == 10
    baseline, metadata = blob(BASE_ZIP), blob(BASE_MANIFEST)
    assert sha(baseline) == BASE_HASH and sha(metadata) == BASE_MANIFEST_HASH
    prior = json.loads(metadata); OUT.mkdir(parents=True, exist_ok=True); PORTAL.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(baseline)) as old, zipfile.ZipFile(ZIP, 'w') as new:
        overrides = {'main.py': generated_main(old.read('main.py')), 'tools.py': old.read('tools.py') + b'\n\n' + DELTA.read_bytes().replace(b'\r\n', b'\n')}
        members = {}; changed = []
        for info in old.infolist():
            original = old.read(info.filename); data = overrides.get(info.filename, original)
            new.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            members[info.filename] = {'bytes': len(data), 'sha256': sha(data)}
            if data != original: changed.append(info.filename)
    assert changed == ['main.py', 'tools.py'] and len(members) == 25
    for name, data in overrides.items(): ast.parse(data); (PORTAL / name).write_bytes(data)
    report = {'package': 'GIPUZKOA360_R21_final_agent', 'base_r20_tested_runtime': BASE, 'base_r20_zip_sha256': BASE_HASH, 'base_r20_manifest_sha256': BASE_MANIFEST_HASH, 'sha256': sha(ZIP.read_bytes()), 'bytes': ZIP.stat().st_size, 'members': members, 'members_count': len(members), 'changed_members': changed, 'context_paths': prior['context_paths'], 'context_assets_changed': [], 'uncompressed_bytes': sum(x['bytes'] for x in members.values()), 'limit_bytes': prior['limit_bytes'], 'public_tools': PUBLIC_TOOLS, 'w1_runtime_changed': False, 'v4_changed': False, 'source_delta_sha256': sha(DELTA.read_bytes().replace(b'\r\n', b'\n')), 'system_prompt_sha256': sha(PROMPT.read_bytes().replace(b'\r\n', b'\n')), 'runtime_delta': 'Ten-tool surface and source catalog projection only; complete R20 tools prefix and 23 other members unchanged', 'portal_real_agent': 'NOT_RUN'}
    assert report['bytes'] < report['limit_bytes']
    MANIFEST.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8', newline='\n')
    return {'zip_sha256': report['sha256'], 'manifest_sha256': sha(MANIFEST.read_bytes()), 'bytes': report['bytes']}

if __name__ == '__main__': print(json.dumps(build(), sort_keys=True))
