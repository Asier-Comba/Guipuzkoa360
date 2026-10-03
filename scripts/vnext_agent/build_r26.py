"""R26 bounded public comparison; immutable R25 provider and context assets."""
import ast
import io
import json
import subprocess
import zipfile
from scripts.vnext_agent.build_r21 import ROOT, PUBLIC_TOOLS, sha

BASE='f955669adb2920718b5b888b916681fc00dc3593'
BASE_ZIP='scripts/vnext_agent/dist/r25/gipuzkoa360-r25-final-agent.zip'
BASE_MANIFEST='scripts/vnext_agent/dist/r25/gipuzkoa360-r25-final-agent-manifest.json'
BASE_HASH='86d16dc187197f9b40f1839989b98ea0af2dc2c37496f4920eaa87d2befb3850'
BASE_MANIFEST_HASH='cbefb81e27797138b525ba457edf2c84f29a646b0540b9df374b0171320d1a48'
OUT=ROOT/'scripts/vnext_agent/dist/r26'
ZIP=OUT/'gipuzkoa360-r26-final-agent.zip'
MANIFEST=OUT/'gipuzkoa360-r26-final-agent-manifest.json'
PORTAL=ROOT/'agentes/gipuzkoa360_vnext/portal_r26'

def blob(path):return subprocess.check_output(['git','show',f'{BASE}:{path}'],cwd=ROOT)

def build():
    baseline, metadata=blob(BASE_ZIP),blob(BASE_MANIFEST)
    assert sha(baseline)==BASE_HASH and sha(metadata)==BASE_MANIFEST_HASH
    prior=json.loads(metadata);OUT.mkdir(parents=True,exist_ok=True);PORTAL.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(baseline)) as old,zipfile.ZipFile(ZIP,'w') as new:
        tools=old.read('tools.py')+b'\n\n'+(ROOT/'scripts/vnext_agent/r26_comparison.py').read_bytes().replace(b'\r\n',b'\n')
        main=old.read('main.py').decode('utf-8'); tree=ast.parse(main)
        prompt=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SYSTEM_PROMPT' for t in n.targets))
        old_prompt=ast.literal_eval(prompt.value)
        old_prompt=old_prompt.replace('Para comparar visitas calcula cada una; mismo origen y supuestos permiten delta condicional, distintos orígenes solo lado a lado.','Para comparar horas de la misma visita usa una sola llamada con las dos horas. No calcules diferencias entre salidas individuales. Distintos orígenes solo lado a lado, sin delta numérico.')
        extension='\n\nVISIT COMPARISON\nplan_visit recibe cinco campos obligatorios, incluido appointment_times: lista de una hora para una visita o dos horas distintas [base confirmada, nueva hora] para comparar la misma visita. Máximo dos horas HH:MM. En seguimiento conserva origen, destino, fecha y duración confirmados. Si pide cambiar la hora y comparar, incluye ambas horas en UNA llamada. Si la base es ambigua, pregunta. Una hora no añade escenarios. Para una visita copia duration_ledger. Para dos horas copia comparison_ledger.comparison_table_markdown y comparison_sentence como autoridad. NO sumes, restes, conviertas segundos, derives diferencias, signos, desplazamientos ni subtotales por tu cuenta. No presentes cálculos parciales ante error. La comparación es condicionada a horarios programados y paseo modelado, no ahorro observado ni recomendación de hora. La lista de horas no compara orígenes distintos.'
        lines=main.splitlines(keepends=True)
        lines[prompt.lineno-1:prompt.end_lineno]=['SYSTEM_PROMPT = '+repr(old_prompt+extension)+'\n']
        main=''.join(lines); tree=ast.parse(main); fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='plan_visit')
        replacement='''def plan_visit(origin_id: str, destination_id: str, date: str, appointment_times: list[str], duration_minutes: int) -> str:
    """One scheduled/modelled visit with one HH:MM time, or a verified comparison with two distinct HH:MM times [baseline,new]. Exactly five required fields. Keep origin/destination/date/duration identical in comparison. List length 1–2 only. Copy duration_ledger for one scenario, comparison_ledger table and sentence for two. No model arithmetic, realtime, home or appointments availability. Consultar_capacidades supplies supported inputs."""
    return _run('plan_visit', locals())
'''
        lines=main.splitlines(keepends=True);lines[fn.lineno-1:fn.end_lineno]=[replacement];main=''.join(lines).encode('utf-8')
        members={};changed=[]
        for info in old.infolist():
            original=old.read(info.filename);data=tools if info.filename=='tools.py' else main if info.filename=='main.py' else original
            new.writestr(info,data,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
            members[info.filename]={'bytes':len(data),'sha256':sha(data)}
            if data!=original:changed.append(info.filename)
        for name,data in [('main.py',main),('tools.py',tools)]:ast.parse(data);(PORTAL/name).write_bytes(data)
    assert changed==['main.py','tools.py'] and len(members)==25
    report={**prior,'package':'GIPUZKOA360_R26_final_agent','base_r25_runtime':BASE,'base_r25_zip_sha256':BASE_HASH,'base_r25_manifest_sha256':BASE_MANIFEST_HASH,'sha256':sha(ZIP.read_bytes()),'bytes':ZIP.stat().st_size,'members':members,'changed_members':changed,'context_assets_changed':[],'uncompressed_bytes':sum(x['bytes'] for x in members.values()),'runtime_delta':'Public bounded time list, existing provider comparison, fail-closed deterministic comparison ledger and authoritative text','portal_real_agent':'NOT_RUN'}
    assert report['bytes']<report['limit_bytes']
    MANIFEST.write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    return {'zip_sha256':report['sha256'],'manifest_sha256':sha(MANIFEST.read_bytes()),'bytes':report['bytes']}

if __name__=='__main__':print(json.dumps(build(),sort_keys=True))
