"""Presentation/reasoning boundary over immutable R17; no engine regeneration."""
import ast
import io
import json
import subprocess
import sys
import zipfile
from pathlib import Path
from scripts.vnext_agent.build_r16 import ROOT, sha

BASE = '8f3ee977cea3295f8f5a92b776e44a598d897016'
BASE_ZIP = 'scripts/vnext_agent/dist/r17/gipuzkoa360-r17-final-agent.zip'
BASE_MANIFEST = 'scripts/vnext_agent/dist/r17/gipuzkoa360-r17-final-agent-manifest.json'
BASE_HASH = '1b263724110c68efab69c14e479f50ed2d101f935c6c83102bb0e5d4c699dc79'
BASE_MANIFEST_HASH = '246f703e1e1881fe984598fe7b428b1b18380c43e7555c03fca2b53dd1982fee'
OUT = ROOT / 'scripts/vnext_agent/dist/r18'
ZIP = OUT / 'gipuzkoa360-r18-final-agent.zip'
MANIFEST = OUT / 'gipuzkoa360-r18-final-agent-manifest.json'
PORTAL = ROOT / 'agentes/gipuzkoa360_vnext/portal_r18'
DELTA = ROOT / 'scripts/vnext_agent/r18_semantics.py'
PROMPT = ROOT / 'scripts/vnext_agent/r18_prompt.txt'

def blob(path):
    return subprocess.check_output(['git','show',f'{BASE}:{path}'],cwd=ROOT)

def generated_main(data):
    text = data.decode('utf-8')
    tree = ast.parse(text)
    node = next(n for n in tree.body if isinstance(n, ast.Assign) and n.targets[0].id == 'SYSTEM_PROMPT')
    lines = text.splitlines(keepends=True)
    prompt = PROMPT.read_text(encoding='utf-8').replace('\r\n','\n').strip()
    lines[node.lineno-1:node.end_lineno] = ['SYSTEM_PROMPT = '+repr(prompt)+'\n']
    text = ''.join(lines)
    changes = {
        'Distancia geométrica a registros, no viaje ni accesibilidad.': 'Distancia euclídea en metros desde un punto representativo municipal no ponderado por población al registro más cercano. El umbral clasifica municipios, NO personas ni hogares: no hay distribución espacial de residentes. No mide viaje ni accesibilidad individual.',
        'Cruce descriptivo, no causalidad.': 'Cruce de proporción municipal de edad y distancia desde punto municipal al registro. No cuantifica residentes próximos, cobertura individual ni causalidad.',
        'Consulta operaciones públicas, cobertura, periodos, enums y límites. pregunta_o_dimension es texto de búsqueda o nombre de tool; omitido/null lista el catálogo. No ejecuta ni añade capacidades.': 'Descubre qué puede responderse, sobre qué sujeto y con qué cobertura, fuentes y límites. Para ayuda general OMITE el argumento o usa null; nunca cadena vacía. Para filtrar usa la pregunta real o nombre de operación. El catálogo no ejecuta un análisis ni autoriza inferencias adicionales.',
    }
    for old,new in changes.items():
        assert text.count(old)==1,old
        text=text.replace(old,new)
    ast.parse(text)
    return text.encode('utf-8')

def generated_tools(data):
    text=data.decode('utf-8')
    assert text.count('def _public_result(')==1
    text=text.replace('def _public_result(', 'def _r17_public_result(')
    text+='\n\n'+DELTA.read_text(encoding='utf-8').replace('\r\n','\n')
    ast.parse(text)
    return text.encode('utf-8')

def build():
    if sys.version_info[:2]!=(3,12):
        raise RuntimeError('Canonical bundle requires CPython 3.12')
    baseline,meta=blob(BASE_ZIP),blob(BASE_MANIFEST)
    assert sha(baseline)==BASE_HASH and sha(meta)==BASE_MANIFEST_HASH
    report=json.loads(meta)
    OUT.mkdir(parents=True,exist_ok=True); PORTAL.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(baseline)) as old,zipfile.ZipFile(ZIP,'w') as new:
        overrides={'main.py':generated_main(old.read('main.py')),'tools.py':generated_tools(old.read('tools.py'))}
        members,changed={},[]
        for info in old.infolist():
            original=old.read(info.filename); data=overrides.get(info.filename,original)
            new.writestr(info,data,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
            members[info.filename]={'bytes':len(data),'sha256':sha(data)}
            if data!=original: changed.append(info.filename)
    assert changed==['main.py','tools.py'] and len(members)==25
    for name,data in overrides.items(): (PORTAL/name).write_bytes(data)
    report={
        'package':'GIPUZKOA360_R18_general_agent','base_r17_head':BASE,
        'base_r17_zip_sha256':BASE_HASH,'base_r17_manifest_sha256':BASE_MANIFEST_HASH,
        'sha256':sha(ZIP.read_bytes()),'bytes':ZIP.stat().st_size,'members':members,
        'members_count':len(members),'changed_members':changed,'context_paths':report['context_paths'],
        'context_assets_changed':[],'uncompressed_bytes':sum(x['bytes'] for x in members.values()),
        'limit_bytes':report['limit_bytes'],'public_tools':9,'w1_runtime_changed':False,'v4_changed':False,
        'source_delta_sha256':sha(DELTA.read_bytes().replace(b'\r\n',b'\n')),
        'system_prompt_sha256':sha(PROMPT.read_bytes().replace(b'\r\n',b'\n')),
        'runtime_delta':'General instructions and model-facing semantic projection only; raw engine and historical packages unchanged',
        'portal_real_agent':'NOT_RUN','holdout':'SEALED_NOT_EXECUTED',
    }
    assert report['bytes']<report['limit_bytes']
    MANIFEST.write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    return {'zip_sha256':report['sha256'],'manifest_sha256':sha(MANIFEST.read_bytes()),'bytes':report['bytes']}

if __name__=='__main__': print(json.dumps(build(),sort_keys=True))
