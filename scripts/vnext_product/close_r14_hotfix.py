"""Publish offline hotfix evidence, retaining the independent portal gate."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
def sha(data): return hashlib.sha256(data).hexdigest()
def emit(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')

def close(hotfix):
    head = subprocess.check_output(['git','rev-parse','HEAD'],cwd=hotfix,text=True).strip()
    source = hotfix/'resultados/vnext/r14'
    out = ROOT/'resultados/vnext/r14'
    docs = ROOT/'docs/vnext/w3'
    fuzz = json.loads((source/'fuzz.json').read_bytes())
    assert fuzz['cases']==5000 and fuzz['crashes']==0 and fuzz['mapping_failures']==0
    report = json.loads((source/'PORTAL_BINDING_HOTFIX_R14.json').read_bytes())
    assert report['status']=='PASS_OFFLINE_NOT_PORTAL'
    report.update(hotfix_sha=head,branch='hotfix/r14-portal-binding',base_sha='8c94f8c3cf9d732c4ce94af7b4bef8f6e154c243',w1_support_pin='106879509a667b75baec4860e28a16b9720fdc71',w2_documental_pin='5e3b43cce61e29693d8b11a01beaeb0e497c97d6',python_tests={'full_hotfix':378,'evaluator':321,'result':'PASS','python_hotfix':'3.12.14'},node_tests={'hotfix':17,'evaluator':37,'result':'PASS'})
    for name in ['parity.json','fuzz.json','SERVED_INTERFACE_R14.json','truth_pack_contrast.json','historical_m04_replay.json']:
        out.mkdir(parents=True,exist_ok=True);(out/name).write_bytes((source/name).read_bytes())
    emit(out/'PORTAL_BINDING_HOTFIX_R14.json',report)
    plan=json.loads((docs/'SMOKE_PLAN_R14.json').read_bytes())
    states=[{'id':t['id'],'status':'NOT_RUN','reason':'W1 exact SHA/ZIP independent acceptance not yet published','dimensions':{d:'NOT_RUN' for d in plan['score_dimensions']}} for t in plan['turns']]
    smoke={'status':'BLOCKED_W1_ACCEPTANCE','portal_upload':'NOT_RUN','new_portal_version':None,'old_portal_version':'agentv_c51dbaf6651f484bbbc435d4f8e27b4a','old_candidate_zip':'3951b290b6ca59c336886a3f0acee77a68036d4fbcbc06c2cedfe22400c08616','historical_m04':'resultados/vnext/r13/M04.json','historical_classification':'HIGH_BINDING_FAIL_RETAINED','messages_total_used':4,'messages_max':12,'messages_remaining':8,'new_model_calls':0,'historical_observed_tool_calls':7,'turns':states,'plan_sha256':sha((docs/'SMOKE_PLAN_R14.json').read_bytes()),'observability_gaps':['Studio served schema for new candidate NOT_OBSERVED','Internal model history NOT_OBSERVED','Private new version NOT_CREATED','Full benchmark and holdout NOT_RUN']}
    emit(out/'PORTAL_SMOKE_R14.json',smoke)
    emit(out/'TURN_SCORECARD_R14.json',{'status':'NOT_RUN_R14','aggregation':'no averaging across failed gates','historical_m04_severity':'HIGH','turns':states})
    readiness={'round':'R14','state':'PORTAL_BINDING_HOTFIX_READY_WAIT_W1','hotfix':report,'w1_independent_acceptance':'PENDING_EXACT_SHA_ZIP','portal_smoke':'NOT_RUN','READY_FOR_FEEDBACK':'NO','RELEASE_GO':'NO','critical':0,'high':1,'medium':1,'findings':[{'id':'R13_M04_BINDING','severity':'HIGH','status':'FLAT_HOTFIX_PASSES_OFFLINE_REAL_AGENT_RETEST_PENDING'},{'id':'R13_M01_M02_SOURCE_COPY','severity':'MEDIUM','status':'GENERIC_PROMPT_RULE_ADDED_REAL_RESPONSE_RETEST_PENDING'}],'v4_identity':'PASS_UNCHANGED','product':'UNCHANGED_OFFLINE; REAL_AGENT_VERIFIED not granted','budget':smoke['messages_total_used'],'next_exact_action':'W1 independently accepts HOTFIX_SHA and ZIP_SHA; only then create separate private version and execute frozen M05–M12 with stop-on-High','full_benchmark':'NOT_RUN_NOT_AUTHORIZED','holdout':'UNCHANGED_NOT_OPENED'}
    emit(docs/'RELEASE_READINESS_R14.json',readiness)
    handoff=f'''# W3 R14 — corrección lista; aceptación independiente pendiente

PORTAL_BINDING_HOTFIX_READY. READY_FOR_FEEDBACK=NO. RELEASE_GO=NO.

## Identidad

- W3 base: 46657c9fc966052dce8b5de75959f8c68282cfb4.
- Hotfix separado: hotfix/r14-portal-binding, {head}.
- Base runtime exacta: {report['base_sha']}.
- ZIP: {report['zip_sha256']}.
- Manifest: {report['manifest_sha256']}.
- main.py: {report['main_sha256']}.
- tools.py: {report['tools_sha256']} (byte-idéntico).
- ZIP/manifest nuevos en scripts/vnext_agent/dist/r14 de la rama hotfix.
- Único miembro del paquete cambiado: main.py. Quince assets, productor W1 y nested ZIP intactos. Double-build PASS.
- W1 soporte final: {report['w1_support_pin']}; W2 documental: {report['w2_documental_pin']}.

## Evidencia

Firma: cinco campos requeridos y cinco opcionales planos. None opcional se omite; sin defaults nuevos ni parser. La llamada interna sigue siendo _run("plan_visit", {{"request": request}}). Nueve tools. Dos reglas genéricas añadidas al prompt, sin respuestas gold.

Paridad completa de public_result (status, effective request, raw hash, claims, mobility, fuentes y límites), con ID de prueba fijo: siete casos truth pack y fixtures de tres orígenes, márgenes, duración, legacy, errores y None. Contraste numérico/semántico contra el truth pack final PASS. 5.000 combinaciones, seed360014, 10.000 ejecuciones direct/wrapper, sin crashes ni fallos de mapping o claims autoritativos en errores. No implica cobertura exhaustiva ni aceptación del LLM.

Hotfix: 378 Python y 17 Node PASS. Evaluador: 321 Python y 37 Node PASS. V4, jury y artifact gates PASS. Tests focales 76 PASS; recorder actualizado 1 PASS adicional tras la suite para evitar regenerar el ZIP histórico. Los tests de comparación continúan llamando al contrato interno: no se expone una interfaz nested al modelo. Los tests incluidos dentro del ZIP son auditoría histórica patch3 preservada; los tests planos actuales viven fuera del paquete.

Intentos previos conservados como incidencias del verificador: assertion demasiado estricta para error con evidencia explicativa, Python3.14 no reproduce ZIP W1, mezcla de numpy3.14/Python3.12 y callers de firma histórica. Corregidos sin tocar datos/math/tools.py. Un recorder antiguo regeneraba artefactos históricos durante tests; ahora usa el constructor R14. Las copias locales generadas por ese test fueron restauradas a sus bytes base exactos.

## Portal y gates

W1_R14_FRONTDOOR_ACCEPTANCE=PENDING. No candidato nuevo cargado. No mensajes nuevos: 4/12 consumidos, 8 restantes. R13 M04 se conserva como HIGH real; el hotfix offline no lo reclasifica. Medium de fuentes/derivación pendiente de retest real. Critical0 / High1 / Medium1. Schema Studio completo NOT_OBSERVED; firma/esquema local esperado no se presenta como schema servido.

El usuario exige PASS independiente W1 sobre SHA y ZIP exactos antes de cargar Studio. Esta es la única dependencia que impide continuar el portal. No corresponde pedir otra autorización al usuario ni consumir mensajes para probar sin W1. Después: nueva versión privada identificable, rehash de dos módulos y quince assets, observar parámetros planos, ejecutar plan congelado M05–M12 y detenerse ante High/Critical. No tocar R13v1, Entrega, track, main, v4 ni holdout.

## Reanudación exacta

1. Leer PR15/Issue16 y comprobar W1_R14_FRONTDOOR_ACCEPTANCE=PASS para esta identidad; fetch y verificar que no hay candidato posterior.
2. Crear una versión privada independiente: GIPUZKOA 360 vNext R14 binding {head[:8]}.
3. Conservar presupuesto histórico, usar SMOKE_PLAN_R14.json, 14 dimensiones por turno. M05 debe ejecutar productor; M06/M07 requieren nuevas llamadas; M12 sesión nueva real.
4. Actualizar evidencia/producto solo sobre capacidades realmente observadas. No confundir HTML offline con chat conectado.
5. Con 0 Critical/High y gates clave PASS: READY_FOR_FEEDBACK=YES y STOP. Benchmark/holdout/release requieren alcance posterior.

Para W1: ZIP/manifest R14, constructor build_r14_binding.py, verify_r14_binding.py, parity.json, fuzz.json, truth_pack_contrast.json, historical_m04_replay.json y firma esperada. Reproducción: python -m scripts.vnext_agent.verify_r14_binding --oracle docs/vnext/w3/r14/FINAL_ORACLE_R13.json --output resultados/vnext/r14. No necesita credenciales ni red ni framework/modelo. No benchmark completo ejecutado.
'''
    (docs/'HANDOFF_R14.md').write_text(handoff,encoding='utf-8',newline='\n')
    (docs/'DEFENSA_TECNICA_R14.md').write_text('''# Defensa técnica R14

Observado en M04: dos request:string y dos invalid_arguments, sin raw productor ni cifra sanitaria. El final fue honesto. No observado: schema completo recibido por el modelo. No está demostrada una causa en Studio o Luna.

La corrección reduce la interfaz externa a campos planos, conserva el mismo contrato interno y omite None opcionales. La atribución sigue distinguiendo provider_default, caller de procedencia no acreditada y usuario acreditado; un argumento enviado por el agente no demuestra elección humana. Comparación nested del productor permanece offline.

El único byte ejecutable cambiado pertenece a main.py. Los datos, tools.py y ZIP W1 se mantienen idénticos. Paridad de objeto público completo y fuzz dirigido sostienen compatibilidad determinista. No prueban selección de tools, memoria ni respuestas del modelo.

La aceptación real sigue bloqueada hasta W1 independiente y M05–M12. El fallo histórico y el Medium de copy conservan su severidad. Totales programados/modelados y diferencias condicionadas no son ahorro observado, recomendación, cita real, capacidad, tiempo real ni entrada física verificada. Producto HTML sigue offline. No release automático.
''',encoding='utf-8',newline='\n')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--hotfix-root',type=Path,required=True)
    print(json.dumps(close(p.parse_args().hotfix_root)))
