"""Close actual M05 failure without promoting deterministic parity to LLM PASS."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'resultados/vnext/r14'
DOCS=ROOT/'docs/vnext/w3'
def read(p):return json.loads(p.read_bytes())
def emit(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def close():
    nodes=read(BASE/'M05_normalized.json')
    calls=[{'name':n['tool'],'arguments':json.loads(n['arguments'])} for n in nodes if n.get('tool')]
    outputs=[]
    for n in nodes:
        if n.get('output'):
            try:outputs.append(json.loads(n['output']))
            except json.JSONDecodeError:outputs.append({'platform_error':n['output'],'producer_result':'NOT_OBSERVED'})
    assert len(calls)==len(outputs)==4
    assert calls[0]['name']=='consultar_capacidades'
    assert all(c['arguments']['return_deadline']=='' for c in calls[1:])
    assert all(o['error']['message']=='mobility:invalid_clock' and not o['claims'] and o['raw_result_sha256'] is None for o in outputs[1:3])
    assert 'Failed to create sandbox' in outputs[3]['platform_error']
    final=nodes[-1]['text'].split('\n',1)[1].strip()
    assert 'No puedo calcular' in final
    plan=read(DOCS/'SMOKE_PLAN_R14.json');smoke=read(BASE/'PORTAL_SMOKE_R14.json')
    dimensions={d:'PASS' for d in plan['score_dimensions']}
    dimensions.update(ARGS='FAIL',RESULT='FAIL',NUMERIC='NOT_APPLICABLE_NO_HEALTH_FIGURE',SOURCE='NOT_OBSERVED_NUMERICAL_SOURCE_EXPLANATION',FOLLOWUP='NOT_APPLICABLE',RECALC='NOT_APPLICABLE',ERROR='FAIL_REPEATED_INVALID_OPTIONAL')
    turn={'id':'M05','session':'R14_A_NEW','status':'FAIL_HIGH','message':plan['turns'][0]['message'],'dimensions':dimensions,'tool_calls':calls,'tool_outputs':outputs,'assistant_final':final,'portal_version_id':'agentv_f6184593cd4f4daf80166122760c4a7f','model_visible_configuration':'openai:gpt-5.6-luna','model_request_identity':'NOT_OBSERVED','model_history':'NOT_OBSERVED','model_call_count':'NOT_OBSERVED','capture_scope':'Actual current conversation DOM; tool args, complete visible output JSON/platform error and final','entity_identity':'PASS; Zegama to modelled Beasain anchor on requested date/time/duration','source_period_review':'Capabilities include source periods; no computed health figure or numerical source/derivation explanation to score','fresh_producer_raw':'NOT_OBSERVED; both domain errors raw hash null; third attempt sandbox creation failed','findings':['R14-EMPTY-DEADLINE','R14-SANDBOX-CREATION']}
    unsubmitted=[{'id':t['id'],'status':'NOT_RUN_STOPPED_HIGH','dimensions':{d:'NOT_OBSERVED' for d in plan['score_dimensions']},'reason':'M05 absolute gate failed; no user retry and no later message sent'} for t in plan['turns'][1:]]
    smoke.update(status='STOPPED_HIGH_M05',w1_independent_acceptance='PASS_EXACT_SHA_ZIP_MANIFEST',new_portal_version=turn['portal_version_id'],messages_total_used=5,messages_remaining=7,new_user_messages_sent=1,historical_observed_tool_calls=7,new_observed_tool_calls=4,total_observed_tool_calls=11,turns=[turn,*unsubmitted],critical=0,high=1,medium=2,main_health='FAIL',variation='NOT_RUN_STOPPED_HIGH',duration='NOT_RUN_STOPPED_HIGH',clean_session='NOT_RUN_STOPPED_HIGH',full_served_schema='NOT_OBSERVED',schema_observation='Preparation displays ten flat parameter names, not full model JSON schema',platform_review_warning='UI summary counts1 error, while two JSON envelopes status:error plus one explicit sandbox error are visible; actual outputs take precedence',observability_gaps=['Full schema sent to model NOT_OBSERVED','Internal model history/request and per-model-call count NOT_OBSERVED','No successful health raw/result in portal','Remaining7 slots not executed by mandatory stop'],full_export='NOT_REQUESTED; complete current conversation DOM retained')
    emit(BASE/'PORTAL_SMOKE_R14.json',smoke)
    findings=[{'id':'R14-EMPTY-DEADLINE','severity':'HIGH','owner':'agent/tool interface','evidence':'M05.json and M05_normalized.json','detail':'Model sends flat fields but sets optional return_deadline empty string. Two actual domain errors mobility:invalid_clock, no claims/raw, third same args cannot create sandbox. Natural main journey not demonstrated.','reproduction':'M05_offline_reproduction.json; actual bad arguments reproduce error; only omission control succeeds offline','cause_limit':'Full served model schema and reason for empty value NOT_OBSERVED; no blame assigned to Studio/Luna/provider math','next_action':'Review optional-field generation against served interface. Any changed candidate needs new identity and W1 acceptance. No further portal messages under this failed gate.'},{'id':'R13-SOURCE-COPY','severity':'MEDIUM','status':'HISTORICAL_UNRESOLVED_REAL_NUMERICAL_RETEST_NOT_COMPLETED','detail':'M05 has no computed health figure. New numerical source/period/derivation communication not established; generic prompt rule alone does not close prior finding.'},{'id':'R14-SANDBOX-CREATION','severity':'MEDIUM','owner':'platform availability risk','detail':outputs[3]['platform_error'],'scope':'Actual third internal attempt, separate from the two reproduced domain errors; not evidence of provider arithmetic defect'}]
    emit(BASE/'TURN_SCORECARD_R14.json',{'classification':'MANUAL_INDEPENDENT_VISIBLE_TURN_REVIEW_NOT_FULL_BENCHMARK','status':'STOPPED_HIGH_M05','dimensions':plan['score_dimensions'],'turns':[turn,*unsubmitted],'critical':0,'high':1,'medium':2,'findings':findings,'historical_r13':'Preserved unchanged; request:string failure remains historical HIGH, not retroactively reclassified','severity_scope':'One current candidate integration High, one unresolved historical source-copy Medium and one observed platform risk Medium; not an average of attempts'})
    readiness=read(DOCS/'RELEASE_READINESS_R14.json')
    readiness.update(state='STOPPED_HIGH_M05_AFTER_W1_PASS',portal_smoke='FAIL_REAL_AGENT',READY_FOR_FEEDBACK='NO',RELEASE_GO='NO',critical=0,high=1,medium=2,findings=findings,budget={'used':5,'maximum':12,'remaining':7,'reset':False},product='Offline calculations retained; actual R14 failure visible; no REAL_AGENT_VERIFIED health claim',next_exact_action='Hand off actual optional-empty-deadline reproduction. Review generation/schema; do not change accepted bytes or spend further messages. A new candidate requires new W1 acceptance and preserves used5/12.',observed_gates={'health_main':'FAIL','variation':'NOT_RUN','duration':'NOT_RUN','sources':'NOT_ESTABLISHED_NUMERICAL_ANSWER','limit':'HONEST_SCOPE_ON_FAILURE_ONLY','adversarial':'NOT_RUN','clean_session':'NOT_RUN','v4':'UNCHANGED'},historical_r13_findings='Unchanged evidence and severities; no retrospective PASS')
    emit(DOCS/'RELEASE_READINESS_R14.json',readiness)
    hotfix=read(BASE/'PORTAL_BINDING_HOTFIX_R14.json');hotfix['w1_independent_acceptance']='PASS';hotfix['portal_upload']='EXACT_CODE_AND15_ASSETS_REHASH_PASS';hotfix['real_agent_acceptance']='FAIL_M05_EMPTY_OPTIONAL_DEADLINE';emit(BASE/'PORTAL_BINDING_HOTFIX_R14.json',hotfix)
    interface=read(BASE/'SERVED_INTERFACE_R14.json');interface.update(portal_version_id=turn['portal_version_id'],model_configuration='openai:gpt-5.6-luna;9tools;memory active;Internet disabled',actual_flat_argument_observation='PASS_FLAT_FIELD_SHAPE_BUT_OPTIONAL_EMPTY_STRING_INVALID',full_model_schema='NOT_OBSERVED');emit(BASE/'SERVED_INTERFACE_R14.json',interface)
    (DOCS/'HANDOFF_R14.md').write_text('''# W3 R14 — agente real: gate M05 fallido

READY_FOR_FEEDBACK=NO. RELEASE_GO=NO. Critical0 / High1 / Medium2.

## Identidad y prerequisite cumplido

Oier publicó W1_R14_FRONTDOOR_ACCEPTANCE=PASS en PR15, PR18 e Issue16. W1 FINAL4bf975511ecea46c25662becfccb65713d381aa0. Hotfix exacto094745b26bc57aee5cc1a5e003401743d96a914f; ZIP9c6fa5c692df178afe36366c6291e7c0e7c3da06134381b09d853f55d6707252; manifest d6c0122b475284c468fdfc3e343b9ab0d9d175cf20513048c915281cedf4e911. Checkpoint completo en resultados/vnext/r14/W1_ACCEPTANCE_R14.json. CI hotfix36765784442 y W1 final36770251523 Windows/Ubuntu SUCCESS. La aceptación determinista independiente no acredita el agente real.

Nueva versión privada GIPUZKOA360 vNext R14 binding094745b · v1, ID agentv_f6184593cd4f4daf80166122760c4a7f. R13v1 conservada sin modificar. Nuevo directorio agentes/gipuzkoa_360_vnext_r14_binding_094745b. main.py y tools.py descargados coinciden;15assets existentes descargados coinciden, incluido ZIPW1. No cambios de datos/math/runtime/tools ni en v4. Preparación visible: gpt-5.6-luna,9tools,memoria activa,Internet desactivado. plan_visit muestra diez nombres planos; schema completo servido NOT_OBSERVED. Version_creation retrasada y descarga inicial demoraron, sin reenviar preguntas. Archivos descargados del trabajo guardados fuera de Descargas.

## Resultado real y presupuesto

Plan congelado intacto. Solo M05 enviado una vez desde sesión nueva vacía. Total5/12 mensajes usados (4 históricos+1nuevo),7restantes. Cuatro llamadas internas observadas: catálogo, dos plan_visit con error de dominio y tercer plan_visit con error de sandbox. Las llamadas internas no son mensajes adicionales. Total observado histórico+nuevo11 llamadas a tools; número de llamadas al modelo/historial interno NOT_OBSERVED.

Intención/tool/entidad/campos planos correctos. El agente añadió return_deadline="" sin que el usuario pidiera deadline. Dos resultados contract_violation / mobility:invalid_clock, effective_request null, claims vacíos y raw hash null. El tercer intento idéntico no pudo crear sandbox. Final honesto: no cifra, no horarios verificados ni recomendación; conserva límites programado/modelado y entrada no verificada. No main sanitaria válida ni cadena completa natural→motor→resultado→respuesta fundada. M05 FAIL_HIGH; M06–M12 NOT_RUN_STOPPED_HIGH.

Replay propio contra mismos bytes reproduce dos fallos. Control offline eliminando únicamente deadline vacío obtiene10691s. Este control NO es respuesta del agente ni cierra el High. No se modifica wrapper para convertir silenciosamente valores inválidos en defaults. La razón del valor vacío y el schema recibido por modelo no se observaron. No afirmar que Studio/Luna rompan nullables ni que la matemática W1 falle.

High actual: generación de opcional inválido impide el caso principal. Medium histórico de fuente/derivación no cerrado: falta respuesta numérica nueva con comunicación comprobable. Medium nuevo: error explícito de creación de sandbox en tercer intento. UI resume1error aunque2envelopeserror y1error de infraestructura son visibles; prevalece evidencia completa. HistóricoR13 se conserva con su severidad y candidato; no se transforma en PASS.

## Artefactos y verificación

M05.json conserva DOM completo, M05_normalized.json argumentos/outputs/final, M05_complete_dom.txt, M05_failure.png. PORTAL_SMOKE_R14 y TURN_SCORECARD_R14 incluyen los8slots y14dimensiones; los7noenviados no puntúanPASS. SERVED_INTERFACE_R14 distingue nombres observados de schema esperado/no observado. W1_ACCEPTANCE_R14, studio_code_hashes, studio_asset_hashes y preparación fijan identidad. M05_offline_reproduction conserva errores reales y control positivo separado.

Verificación final propia: evaluador325Python/37Node PASS; identidad v4 PASS14/14, verify_jury_results PASS, verify_final_artifacts PASS y git diff --check limpio. Hotfix previo378Python/17Node PASS. No se repitió el benchmark completo. V4/jury/artifact identidad siguen siendo gates de regresión, no aceptación LLM. No benchmark completo, holdout, comparación LLM, merge, publicación, Entrega o track. Automatización de espera pausada al obtener PASS, para evitar mensajes duplicados.

## Próximo paso acotado

Handoff a ingeniería/agente: revisar generación de opcionales y schema real a partir de M05. No nueva feature, dataset o cambios de math. Cualquier nuevo byte requiere nuevo SHA/ZIP y aceptación independiente W1. No más mensajes contra este candidato tras High. Preservar5/12consumidos y7restantes; no reiniciar presupuesto ni abrir benchmark. Producto continúaoffline con falloR14 visible. Detener la ronda aquí.

Reproducción: python scripts/vnext_product/replay_m05_r14.py --python <CPython3.12> --candidate <ZIPexactoextraído>. La prueba offline requiere solo librería estándar y no llama al modelo. Defensa humana actualizada en DEFENSA_TECNICA_R14.md.
''',encoding='utf-8')

if __name__=='__main__':close();print('R14 actual M05 failure closed;5/12 used; no later turn executed')
