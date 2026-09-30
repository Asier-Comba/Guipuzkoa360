# W3 R14 — agente real: gate M05 fallido

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

Handoff a ingeniería/agente: revisar generación de opcionales y schema real a partir de M05. No nueva feature, dataset o cambios de math. Cualquier nuevo byte requiere nuevo SHA/ZIP y aceptación independiente W1. No más mensajes contra este candidato tras High. Preservar5/12consumidos y7restantes; no reiniciar presupuesto ni abrir benchmark. Producto continúaoffline con falloR14 visible. Vista actual comprobada en navegador y captura health_R14_status.png; servidor local reiniciado tras conexión rechazada, sin llamadas nuevas al portal. Detener la ronda aquí.

Reproducción: python scripts/vnext_product/replay_m05_r14.py --python <CPython3.12> --candidate <ZIPexactoextraído>. La prueba offline requiere solo librería estándar y no llama al modelo. Defensa humana actualizada en DEFENSA_TECNICA_R14.md.
