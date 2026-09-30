# GIPUZKOA 360 · W3 R3 · handoff

WORK_ID: W3

ROUND: G360-R3

STATUS: PARTIAL — producto y evaluación offline revisables; aceptación conversacional y sanitaria conjunta pendiente.

COMMON_ANCESTOR: `e213eaa9b73b0f8a4d1893e0269fe92fe6756955`

R3_START_SHA: `2e86e41dec9a6acc3ef6d5e4cc84678d1089a5eb`

CURRENT_BRANCH: `work/vnext-w3-product-redteam`, [PR #14](https://github.com/Asier-Comba/Guipuzkoa360/pull/14), base `integration/vnext-2026-10-04`.

TESTED_HEAD: `d912347a783189a268c90306ab1990c66b7344c0` para código/producto; los commits posteriores son solo documentales.

PUBLISHED_HEAD: registrado tras push en comentario del PR #14 y respuesta final para evitar autorreferencia.

CODE_TREE_OR_BLOB_IDENTITIES: tree probado `bde11e2a00730e0d93097be0831cfe82f5e20df5`; evidencia W1 SHA-256 `57738bd27f6bbd78cc399d862235df13c1d8d9d2f3f46eaf6e367230e853b0db`; HTML SHA-256 `fcd342b875554e486760c116a50b4b051f59dea81bbb7ecc2a1a6464f0888f74`.

CONSUMED_WORK_HEADS: W1 PR #15 `c68eb5c55dec72a267b7435b4c364049f6eab408`; W2 PR #17 `f4615b36d0af93966e6ca0f2044288841e6574b8`. Leídos en checkouts aislados, sin integrar commits ajenos. `main` e integración observadas en `e213eaa`.

CONTRACT_VERSIONS_AND_HASHES: W1 `ir_y_volver` 0.1.0; snapshot `30fc9d638f3576ae0e1084ee1e0c7b0268469bffc8af1dd15fd12430019d968b`; proveedor archivo `4cf6b5645c63bdf2bb6c26f0d125c3669ca187d57461b8f59417de9f4acb2678`. W2 Evidence 1.0.0 `81f1162cb90a65394d96e8735f6403050094eea29a9c17648426282dfc3dc191`; Capability 1.0.0 `1ad14eb4a825d426958d29fde54104f6d4b45e60f2e25ccc5920af23df435d4c`. W3 trace `W3_TRACE_2.0.0`, scoring 2.0.0. Ver [contrato](TRACE_CONTRACT_R3.md) y [mapeo visual](PRODUCT_CONTRACT_R3.md).

SOURCE_COVERAGE_AND_GAPS: [matriz](SOURCE_AUDIT.md). GTFS GO01 oficial, W2 publicado y portal leído. No disponibles paquete privado 00–12, literal M4/M5, PoC completa ni feedback/correos; no se afirma su lectura. Progreso histórico 55/73 intacto. Incidente 50+/504 `REPORTED_NOT_REPRODUCED`.

FILES_CHANGED: solo `resultados/vnext/**`, `scripts/vnext_product/**`, `tests/vnext_redteam/**`, `docs/vnext/w3/**` desde ancestro.

COMPLETED_BY_STAGE: P0 contrato de trazas, scorer por identidad/evidencia y fixture `NO_LLM`; P1 corpus/holdout preservados y nueve casos C-R3 de desarrollo; P2 consultas W1 permitidas fuera de las cinco tarjetas, importación offline y revisión visual; P4 límites/versiones del portal documentados en lectura y gate preparado. P3 [protocolo documental](RAG_EVAL_R3.md) bloqueado por fuentes; P5 agente real `NOT_RUN`.

RED_GREEN_REPRODUCTIONS: test inicial del scorer falló por `ImportError`; tras implementar contrato/scorer, suite especializada `18/18 PASS`. Consulta W1 Zegama→Beasain 09:30, 30 min, márgenes 15/8: `ok`, 10.511 s, output SHA-256 `f0ddb1a6dcabb1a2096084374d38e216df999389caaebc14cb327a945a1ab35e`. Directa determinista, sin LLM.

TEST_COMMANDS_ENVIRONMENT_AND_RESULTS: Windows 29/09/2026; Python QA `product-jury-qa-env`: `python -m pytest -q -o addopts=` **282/282 PASS** (14,56 s); W3 especializado **18/18 PASS** (incluido en 282). Node `node --test tests/e2e/contract_flow.test.mjs` **17/17 PASS**. `verify_runtime_identity.py` **14/14 PASS**; `verify_jury_results.py` y `verify_final_artifacts.py` **PASS**. `build_visual.py` regeneró HTML con SHA anterior. `score_runs.py` con/sin holdout: `NOT_RUN`, cero intentos. [Navegador](BROWSER_REVIEW_R3.md): escritorio 1280, móvil 390, teclado Enter/Space, estados no viable/desconocido e importación. No es certificación WCAG.

TESTS_NOT_RUN_AND_REASON: 60 individuales pareados, 20 conversaciones ×3, holdout ejecutado, latencias LLM/portal y revisión humana `NOT_RUN`: falta candidato conjunto W1+W2 fijado y autorización de escritura portal. RAG 0/30 `BLOCKED` por falta de M4/M5 autorizados. Zoom 125/150, lector de pantalla y otros tamaños no probados en R3. No se repitió benchmark completo.

FINDINGS_OPEN_CLOSED_AND_OWNER: W3-F01 existencia W2 **CLOSED**; candidato sanitario conjunto **HIGH OPEN**, W1/W2/coordinación. W3-F02 fuentes privadas/M4/M5 **MEDIUM OPEN**, coordinación. W3-F03 50+/504 **MEDIUM OPEN, REPORTED_NOT_REPRODUCED**, portal/coordinación. W3-F04 stop-only/centro de Beasain **MEDIUM mitigado** con copy, W3/W1. W3-F05 unidad `highlighted_count=7` «registros» entre 88 municipios **MEDIUM OPEN**, W2; [reproducción comunicada](https://github.com/Asier-Comba/Guipuzkoa360/pull/17#issuecomment-5895766224). Critical confirmados: 0. `PRODUCT_HEALTH_GO=NO`.

V4_PRESERVATION_EVIDENCE: runtime congelado `195b4980fa5998b096c308296a55e452380b0371`, 14/14 identidades PASS; verificadores v4 PASS; diffs solo W3. Portal: Entrega en borrador privado con v4 seleccionada; 19 ejecuciones terminadas indicadas, no evaluadas por W3.

ASSEMBLY_AND_PACKAGE_IDENTITIES: ZIP W2 R2 SHA-256 `1992cc739e8e89cd4512ad45919d1ebc102a6385628f82689a23de49de6f2661` (55.455 bytes), sin movilidad empaquetada. Paquete integrado W1+W2 `PENDING`. La `v6` listada en portal no expone fingerprint; no se atribuye a W2.

CORPUS_HASH_AND_COUNTS: 48 desarrollo `40ec6a2e25331a2e040b7fedfd3ad75ff7245b508ef30c605d9cc6fdeb5e046a`; 20 conversaciones de tres turnos `ca1dcb321bc92d2efa42c871e9730926421a375bfeab77edfee696e5ed09f413`; 12 holdout privado `4dda59721932f620cba53e5686df288f7cf0e0e968ec30540216ffb1f52ec5c0`. C-R3 nueve casos conocidos adicionales, no holdout.

HOLDOUT_STATUS: archivo privado fuera de GitHub, hash revalidado, no compartido con W1/W2 ni ejecutado. Candidato aún no congelado.

SCORING_VERSION: 2.0.0; tipos `SINGLE_CASE`/`CONVERSATION`, identidad, hashes, continuidad, intentos y comparabilidad. Fixtures sintéticos no demuestran conversación.

V4_VS_VNEXT: `NOT_RUN` (0/60 individuales, 0/20 conversaciones). Sin afirmación de mejora.

MODEL_AND_PORTAL_EXECUTED_COUNTS: modelo 0; conversaciones 0; pruebas portal nuevas 0; versiones portal nuevas 0. Cinco outputs W1 guardados y una consulta adicional, todos deterministas offline.

LATENCY_AND_FAILURE_COUNTS: n=0 latencias/fallos A/B de LLM/portal; p50/p95 `NOT_RUN`. No se infiere causa del 504.

PR_CI_HEAD_AND_MERGE_REF: PR #14 draft/mergeable; dos checks Linux/Windows `SUCCESS` en HEAD previo `36d01f9` al leer. CI del HEAD final se informará en comentario PR; merge ref no aceptado como candidato.

REMOTE_MUTATIONS: commits W3 R3 `76c4fbf`, `36d01f9`, `8dd30c2`, `d912347` y cierre documental; comentario del bug en PR #17; PR #14 e Issue #16 se actualizan tras push. Sin cambios en W1/W2, main o gh-pages.

PORTAL_MUTATIONS: 0. Lectura de ayuda, Agentes y Entrega; sin seleccionar, guardar, probar ni publicar. [Evidencia](PORTAL_LIMITS_EVIDENCE_R3.md).

BLOCKED_TASKS_AND_SAFE_ALTERNATIVES: candidato sanitario/`HEALTH_DESTINATION_GO` pendiente → producto de paradas offline etiquetado; portal sin autorización → [solicitud](PORTAL_TEST_REQUEST_R3.md), sin ejecución; RAG sin M4/M5 → protocolo bloqueado, sin gold inventado; 50+/504 sin traza → causa desconocida.

NEXT_EXACT_COMMAND_OR_ACTION: leer próximos HEAD y `CANDIDATE_READY_FOR_W3` por SHA, verificar paquete conjunto y corrección de unidad, congelar identidad y preflight. Solo entonces solicitar autorización específica de versión privada y 12 pruebas de humo. Si falla gate sanitario, conservar v4 y evaluar únicamente capacidades realmente expuestas.

HUMAN_ACTION_REQUIRED: facilitar M4/M5 y paquete privado 00–12 para auditoría completa; revisar PR #14; autorizar por separado versión privada/pruebas portal cuando haya paquete exacto, alcance y presupuesto.

MERGED_OR_PUBLISHED_RELEASE: NO

## Gates con denominador

| Gate | Estado | Evidencia y alcance |
|---|---|---|
| Producto offline W1 | PASS | 5/5 salidas fijadas y una consulta distinta; paradas GO01, sin destino sanitario. |
| Suite local | PASS | 282/282 Python, 17/17 Node, 14/14 archivos v4. |
| Candidato sanitario | BLOCKED | 0 paquetes conjuntos fijados; ZIP W2 R2 sin movilidad. |
| Conversaciones/A-B | NOT_RUN | 0/60 individuales, 0/20 conversaciones; modelo 0, portal 0. |
| RAG documental | BLOCKED | 0/30 preguntas con gold; faltan M4/M5. |
| Revisión humana LLM | NOT_RUN | 0 respuestas LLM para juzgar. |
