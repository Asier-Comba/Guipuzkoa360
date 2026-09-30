# W3 R13 · cierre de aceptación real de patch3

**READY_FOR_FEEDBACK=NO. RELEASE_GO=BLOCKED_REAL_AGENT; después siguen pendientes revisión humana, benchmark completo y holdout. No merge, publicación, Entrega o track.**

## Identidad

- START_SHA: `1d60cdf81d3eb7661bc1d97c12425b9bdcf69b8d`.
- TESTED_HEAD: `23aacb9f790e91ed9332f607c5fd5b962a9baec5` (código final y evidencia; commits posteriores solo documentan cierre).
- FINAL_SHA: SHA exacto del comentario final de [PR14](https://github.com/Asier-Comba/Guipuzkoa360/pull/14), evitando hash autorreferente.
- W1_PIN: soporte `7f434a469d7f94fdff8ae7d2665644426a217250`; runtime `cb061a9e00a6496c40488a596bd94834bc2c49b2`; ZIP `c66d44af702eb3410fcea05ae8711f537214f675e83a7fda38c39c3b39a1b910`.
- W2_RUNTIME: `8c94f8c3cf9d732c4ce94af7b4bef8f6e154c243`; handoff `fa679248a6239604f56368f384e708a022c09e95`; soporte R13 posterior `f7a376b3cee79078cbc8b3f878f6eea3a53fcebb`, sin cambiar candidato.
- W2_ZIP: `3951b290b6ca59c336886a3f0acee77a68036d4fbcbc06c2cedfe22400c08616`; manifest `a672bf9a2afece58c468a1f762c860f0217536a2a4fa18737ba768cab755c70a`.
- V4: `195b4980fa5998b096c308296a55e452380b0371`. RUNTIME_CHANGED: **NO**.
- Commits nuevos R13: `111aff0` aceptación independiente y plan congelado; `23aacb9` evidencia real, corte del lote y producto actualizado; commit de cierre documental identificado por FINAL_SHA en el comentario final.

## Aceptación offline independiente

**PASS: 36 casos por cuatro layouts**, 144 ejecuciones offline; no LLM. Paquete completo, solo quince assets declarados, cwd ajeno y carpeta Studio anidada con cwd ajeno; raíz implícita ligada al paquete, raíz inválida rechazada sin fallback. Tres vistas directas de tool por layout registradas aparte. ZIP exterior: 25 miembros; productor interior: 26 miembros; hashes exactos. Legacy, health, tres orígenes, etiquetas, source lookup, positivos territoriales, comparaciones, fallos, payload y atribución pasan.

Se compara raw con productor **y** se reconstruyen dos cifras desde el ZIP GTFS original fijado y geometría: 10.691 s / 8.591 s, diferencia −2.100 s. Cero hallazgos High/Critical offline. No se ha heredado el veredicto W1 ni el NO_GO R12. La parada legacy 7214 conserva el nombre GTFS Beasain - Zaldizurreta 7.

## Studio y observabilidad

- Borrador **GIPUZKOA 360 vNext R13 patch3 3951b290**; carpeta `agentes/gipuzkoa_360_vnext_r13_patch3_3951b290`.
- PORTAL_VERSION_ID: **`agentv_c51dbaf6651f484bbbc435d4f8e27b4a`**, v1 privada creada.
- REAL_MODEL: configuración visible **`openai:gpt-5.6-luna`**; identidad de cada request al modelo **NOT_OBSERVED**.
- Nueve tools, memoria activada, Internet apagado; máximo ocho iteraciones en código. Historial realmente enviado, session ID, schema completo, timestamps/latencia de plataforma: **NOT_OBSERVED**.
- Descarga y hash de **dos módulos + quince assets**: PASS. Dos assets vNext cambiaron; sus bytes R12 se preservaron en `datos_preparados/vnext_r12_baseline`. Otros trece son idénticos entre candidatos; ningún módulo de v4 editado. No afirmar que el draft baseline sigue ejecutable contra la raíz cambiada: es histórico; su restauración usaría sus dos assets archivados y sus bytes propios.
- `ejecucion.py` es plantilla automática no importada; membresía completa de versión **NOT_OBSERVED**. R13 no reconstruyó el ZIP ni alteró main/tools aprobados.
- La tool territorial y capacidades se ejecutan. **Montaje/ejecución efectiva del productor sanitario en portal NOT_OBSERVED**: la validación de argumentos se detuvo antes del raw. Las pruebas de layout offline y la preparación no reemplazan esa prueba.
- Interfaz: nombres y parámetros de nueve tools observados; tipos, required y nested schema servido **NOT_OBSERVED**. Clasificación **PARTIAL_OBSERVED**; la forma usada en M04 sí está observada y es incorrecta.
- Export por UI no proporcionó una ruta de descarga dentro del tiempo de captura. Se conservaron DOM, JSON completos de tools y final; no se inventó un export o historial de modelo. La cifra visible de tokens/llamadas es un badge de UI, no un contador certificado del lote.

## Resultado real y reproducción obligatoria

**USER_MESSAGES_USED_OF_12: 4.** Una sesión A; siete llamadas a herramientas observadas. La segunda llamada a plan_visit fue un intento interno del agente, no otro mensaje de usuario. El plan quedó congelado en `111aff0` antes del primer envío; no se ajustó tras resultados.

M01: Aduna, cifras correctas y cero registros explicado. M02: Aduna/Tolosa 75+, herramientas nuevas y contexto correcto. M03: catálogo sanitario, pide parámetros decisivos, no sustituye Aduna. **M04: FAIL_HIGH_REQUEST_BINDING**.

Pregunta literal completa en [M04](../../../resultados/vnext/r13/M04.json). El agente selecciona plan_visit, pero en dos intentos manda `request` como string; contrato esperado: objeto/lista. Ambos outputs: `status:error`, `invalid_arguments`, `arguments:request:invalid_value`, `origin:domain`, claims vacíos y raw hash null. El final reconoce el error y no inventa cifras. El [replay offline](../../../resultados/vnext/r13/request_binding_reproduction.json) reproduce exactamente el rechazo.

**CRITICAL: 0. HIGH: 1, owner W2**, integración agente/interfaz. No se atribuye a W1 ni a plataforma/red sin schema/trace que lo demuestre. [Enviado a PR17](https://github.com/Asier-Comba/Guipuzkoa360/pull/17#issuecomment-5916928096).

**MEDIUM: 1, owner W2**, copy de fuente y derivación 75+ omitidas en finales M01/M02 aunque estén en los outputs. El resumen de revisión del portal dice “no se observan errores” pese a los dos envelopes error: WARN de plataforma documentado aparte, sin reemplazar la evidencia semántica.

M05–M12, incluida sesión B, **NOT_RUN_STOPPED_HIGH**. No hay prueba sanitaria main+variation, recálculo multiturno sanitario ni fecha unknown del agente. Sí hay una cifra real directamente contrastada: 36/507 × 100 = 7,101 % en fila Eustat de Aduna. No se fuerza éxito usando un prompt con JSON o IDs.

## Producto, browser, defensa y RAG

`health.html` actualizado al ZIP patch3 **offline**, con bloqueo real R13 visible. `health_r12.html` preserva la versión anterior; R10 también permanece histórico. Se rechaza importar una identidad R12 en R13 o un envelope de error de tool como viaje. No hay integración live oculta y no se muestran 35 minutos como resultado del agente real.

Browser IAB Windows: **320×780, 390×844, 768×1024, 1366×768, 1920×1080**. Sin overflow de página medido; tabla móvil con overflow auto interno. Fuentes largas e identidades se envuelven; unknown/no viable ocultan itinerario y tabla, sin cero sustituto. Comparación −2.100 s y JSON local actual/histórico probados. Tab/Shift+Tab entre escenarios, Enter/Space activan escenarios y details; foco visible. Sin errores/warnings en consola capturada del visor. Sin certificación WCAG; zoom nativo no observado ni modificado; override de viewport restaurado.

[Defensa técnica](DEFENSA_TECNICA_R13.md): demo offline honesta, arquitectura y límites; no demo sanitaria live. RAG A/B consumido del soporte W2 R13: mismo corpus, 18 preguntas, sin LLM; soporte baja 14/15→11/15. **RAG_NO_GO** defendido con evidencia, sin introducir RAG al candidato.

## Validación y preservación

- Python: **321 PASS**, suite completa en TESTED_HEAD, 14,86 s. Primera ejecución tuvo un defecto de selección del test nuevo: confundía catálogo de capacidades con resultado municipal por substring. Se corrigió el selector por capability_id, retest focal PASS y suite completa PASS; ninguna salida de agente se alteró.
- Node: **37 PASS**, cero skips: contrato end-to-end y suites vNext.
- Jury verifier y final artifacts: PASS; runtime v4 idéntico. No benchmark completo nuevo.
- Desarrollo 48, conversaciones 20 y gold30 conservan hashes originales. Holdout privado 12: solo rehash de bytes, **no contenido abierto**; SHA `4dda59721932f620cba53e5686df288f7cf0e0e968ec30540216ffb1f52ec5c0`.
- Comparación LLM v4/vNext **NOT_RUN**; [plan pareado futuro](PAIRED_PLAN_R13.json): 8 prompts comunes ×2 versiones = **16 mensajes adicionales**, dos sesiones por versión, sin retries previstos; cualquier retry cuenta. Requiere alcance adicional, sin afirmar superioridad por diseño.

## NEXT_EXACT_ACTION

W2 reproduce request/schema servido y generación estructurada sobre la evidencia M04, entrega fix mínimo con nuevo pin/ZIP si procede; W1 reacepta el candidato cambiado. W3 valida bytes e interfaz antes de retomar el lote, manteniendo **4/12 ya consumidos** y registrando cualquier ajuste futuro del protocolo. No tratar ocho slots restantes como presupuesto nuevo de doce. La comparación pareada, benchmark, holdout y publicación siguen fuera del alcance autorizado de este smoke.

FILES_FOR_WORK1/W2: M04.json, request_binding_reproduction.json, PORTAL_SMOKE_R13.json, SERVED_INTERFACE_R13.json, TURN_SCORECARD_R13.json, offline_review.json y cuatro reportes de layout. Estado único: [RELEASE_READINESS_R13.json](RELEASE_READINESS_R13.json). Capturas de fallo son evidencia interna; para el jurado no mostrar tokens/debug ni conversación ajena. Sin trabajo de fondo prometido.
