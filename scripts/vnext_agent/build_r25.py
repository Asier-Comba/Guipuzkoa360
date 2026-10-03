"""Reconciled presentation over immutable R24; engine and data unchanged."""
import ast
import io
import json
import subprocess
import zipfile
from scripts.vnext_agent.build_r21 import ROOT, PUBLIC_TOOLS, sha

BASE = 'e4f16aed15cf2b0ba60836926aaabf511a1cdbc3'
BASE_ZIP = 'scripts/vnext_agent/dist/r24/gipuzkoa360-r24-final-agent.zip'
BASE_MANIFEST = 'scripts/vnext_agent/dist/r24/gipuzkoa360-r24-final-agent-manifest.json'
BASE_HASH = 'bfba5c253ced6edff365f42d72c1f53aebbf7e82c7a5a8de90e51611fbfe824e'
BASE_MANIFEST_HASH = 'ddb3f4bd53be3c595a669832abc3bad179e4449564503fd8c2fd33cc45891b47'
OUT = ROOT / 'scripts/vnext_agent/dist/r25'
ZIP = OUT / 'gipuzkoa360-r25-final-agent.zip'
MANIFEST = OUT / 'gipuzkoa360-r25-final-agent-manifest.json'
PORTAL = ROOT / 'agentes/gipuzkoa360_vnext/portal_r25'
DELTA = ROOT / 'scripts/vnext_agent/r25_reconciled_visit.py'

def blob(path):
    return subprocess.check_output(['git', 'show', f'{BASE}:{path}'], cwd=ROOT)

def build():
    baseline, metadata = blob(BASE_ZIP), blob(BASE_MANIFEST)
    assert sha(baseline) == BASE_HASH and sha(metadata) == BASE_MANIFEST_HASH
    prior = json.loads(metadata)
    OUT.mkdir(parents=True, exist_ok=True); PORTAL.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(baseline)) as old, zipfile.ZipFile(ZIP, 'w') as new:
        tools = old.read('tools.py') + b'\n\n' + DELTA.read_bytes().replace(b'\r\n', b'\n')
        prompt_extension = (
            'SYSTEM_PROMPT += ' + repr('\n\nVISIT DURATION PRESENTATION\nEn visitas sanitarias válidas usa duration_ledger como única presentación de duraciones: copia total_human, start_clock, end_clock y la tabla answer_table_markdown completa. No agrupes ni omitas componentes, no conviertas unidades ni calcules subtotales nuevos. Los márgenes ya están incluidos en las esperas y no se vuelven a sumar. Conserva journey_scope, fuentes, supuestos y límites. Una comparación requiere nuevas ejecuciones válidas; su diferencia es condicional, no ahorro observado.') + '\n'
        ).encode('utf-8')
        # A literal assignment remains visible to Studio's static inspection.
        main_text = old.read('main.py').decode('utf-8')
        prompt_node = next(n for n in ast.parse(main_text).body if isinstance(n, ast.Assign)
                          and any(isinstance(t, ast.Name) and t.id == 'SYSTEM_PROMPT' for t in n.targets))
        extension_node = ast.parse(prompt_extension).body[0]
        old_line = main_text.splitlines()[prompt_node.lineno - 1]
        main = main_text.replace(old_line, 'SYSTEM_PROMPT = ' + repr(
            ast.literal_eval(prompt_node.value) + ast.literal_eval(extension_node.value)), 1).encode('utf-8')
        members, changed = {}, []
        for info in old.infolist():
            original = old.read(info.filename)
            data = tools if info.filename == 'tools.py' else main if info.filename == 'main.py' else original
            new.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            members[info.filename] = {'bytes': len(data), 'sha256': sha(data)}
            if data != original: changed.append(info.filename)
        for name in ('main.py', 'tools.py'):
            data = tools if name == 'tools.py' else main
            ast.parse(data); (PORTAL / name).write_bytes(data)
    assert changed == ['main.py', 'tools.py'] and len(members) == 25
    report = {
        'package': 'GIPUZKOA360_R25_final_agent', 'base_r24_evidence_head': BASE,
        'base_r24_tested_runtime': '7d1d2da3a88c5f8880bf228dd4ae70855bff3866',
        'base_r24_zip_sha256': BASE_HASH, 'base_r24_manifest_sha256': BASE_MANIFEST_HASH,
        'sha256': sha(ZIP.read_bytes()), 'bytes': ZIP.stat().st_size, 'members': members,
        'members_count': len(members), 'changed_members': changed,
        'context_paths': prior['context_paths'], 'context_assets_changed': [],
        'uncompressed_bytes': sum(x['bytes'] for x in members.values()),
        'limit_bytes': prior['limit_bytes'], 'public_tools': PUBLIC_TOOLS,
        'w1_runtime_changed': False, 'v4_changed': False, 'main_changed': True,
        'runtime_delta': 'Verified eight-component duration partition and deterministic table; prompt selects that projection',
        'portal_real_agent': 'NOT_RUN',
    }
    assert report['bytes'] < report['limit_bytes']
    MANIFEST.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2)+'\n', encoding='utf-8', newline='\n')
    return {'zip_sha256': report['sha256'], 'manifest_sha256': sha(MANIFEST.read_bytes()), 'bytes': report['bytes']}

if __name__ == '__main__': print(json.dumps(build(), sort_keys=True))
