# W3 · handoff R4

WORK_ID: W3  
COORDINATION_ROUND: G360-R4  
STATUS: OFFLINE_PRODUCT_AND_EVALUATION_READY_PARTIAL; PRODUCT_HEALTH_GO=NO  
START_SHA: `cf9cd0afadc97b255c021a4ff867dab7ae6dabbc`  
TESTED_HEAD: `688e68b` más el cierre documental, validado al final  
PUBLISHED_HEAD: registrar tras push en PR #14 e Issue #16 para evitar autorreferencia  
CONSUMED_W1_SHA: R2 `c68eb5c55dec72a267b7435b4c364049f6eab408`; R4 `725a7b73ae0381092cd80edc41b8a25432d75fcd`  
CONSUMED_W2_SHA: `f4615b36d0af93966e6ca0f2044288841e6574b8`

CONTRACT_VERSIONS_AND_HASHES: W3 trace `W3_TRACE_2.1.0`, scorer `2.1.0`; `TRACE_CONTRACT_R4.md` SHA-256 `4895820cac74b5fb09291d33a74c47a6b6b06ace372fc6c71269680a6b6af45f`, `score_runs.py` SHA-256 `89d3570a8d3c5cdb6afc4c3d718633c227072e13ecb7853431b2083dc96745fb`. W1 0.1.0 y 0.2.0 separados; W2 R2 adapter 0.1.0.

SOURCE_ACCESS_AND_READING: paquete privado 00–12 buscado en adjuntos/workspace, no encontrado (`SOURCE_ACCESS_GAP`), no declarado leído. Revisadas fichas públicas S1 salud, S2 Moveuskadi y especificación S3 GTFS con secciones y límites en `PUBLIC_SOURCE_REVIEW_R4.md`; S4 Eustat sin gold por acceso fallido. Licencias particulares pendientes antes de ingestión/republicación. W1 R4 identifica el Ambulatorio, pero `HEALTH_DESTINATION_GO_NO_GO=BLOCKED` por entrada/enlace peatonal no verificado.

FILES_CHANGED: solo `resultados/vnext/**`, `scripts/vnext_product/**`, `tests/vnext_redteam/**`, `docs/vnext/w3/**`. Commits R4: `3a611e7`, `5dabdd0`, `2e9aa15`, `45fa4db`, `0e7ee26`, `688e68b` y cierre documental.

STAGES_COMPLETED: IMPORTER_HARDENED; TRACE_REVISION_READY; SCORER_REGRESSIONS_READY; INDEPENDENT_CASES_EXECUTED; PACKAGE_REVIEW_READY; DOCUMENT_GOLD_READY; W1_R4_COMPONENTS_PREPARED. HTML rotulado en R2 0.1.0, sin aparentar visita sanitaria o agente live.

REPRODUCTIONS_BEFORE_AFTER: el importador aceptaba una primera fuente `javascript:void(0)` seguida de la oficial; ahora rechaza toda fuente discrepante sin alterar el resultado previo. Rechaza tipos/URL/arrays/tamaño, `09:30:59` frente a `09:30`, márgenes/perfil/snapshot cambiados y `ok` incompleto; acepta `unknown` legítimo sin normalización y muestra su causa observada. Browser: import válido 10511 s, rechazo posterior conserva 10511 s. El scorer aceptaba checks autoafirmados sin llamada y no contabilizaba fallo de invocación sin respuesta; tests de propiedad rojos previos y verdes con 2.1.0. Compatibilidad no equivale a autenticidad.

TEST_COMMANDS_AND_RESULTS: `product-jury-qa-env/Scripts/python.exe -m pytest -q -o addopts=` → **296 PASS**; `node --test tests/e2e/contract_flow.test.mjs tests/vnext_redteam/import_contract.test.mjs` → **24 PASS** (17+7). `verify_runtime_identity.py` → **14/14 PASS**, `verify_jury_results.py` → PASS, `verify_final_artifacts.py` → PASS. `review_w1_r4.py` contra archive W1 725a7b7 → C-R3-05–08 **4 PASS**. `run_independent_cases.py` contra W1 R2/W2 R2 → **4 PASS, 5 KNOWN_FAIL, 9 conversaciones NOT_RUN**. Package review → PASS estático 13 miembros; no aceptación funcional. `git diff --check` PASS.

KNOWN_FAIL: C-R3-01 CRITICAL, W2 acepta resultado Tolosa para solicitud Aduna bajo sustitución de output de tool; C-R3-02/04/09 HIGH, ocho tasas por 10.000 sobreviven sin fuente del numerador en salida Aduna; C-R3-03 MEDIUM, `highlighted_count=7` con unidad `registros` en lugar de municipios. Cinco casos, tres defectos raíz, sobre W2 R2. Comunicados en PR #17 y conservados en `r4_independent/c_r3_report.json`. La sustitución es una inyección de prueba, no un fallo observado del pipeline normal ni del portal.

NOT_RUN: nueve conversaciones C-R3, v4↔vNext, 48+20 con modelo, holdout con modelo, portal, candidato combinado W1 0.2.0+W2 actualizado, ruta sanitaria, retrieval B0/B1/B2 y generación documental. W2 0.1.0 debe rechazar W1 0.2.0 hasta adaptación.

FINDINGS_AND_OWNERS: W2 corrige identidad municipal, linaje de tasas, unidad y adaptación 0.2.0; W1/fuente de red resuelve acceso sanitario; W3 repite C-R3 por pins y conecta UI tras contrato compatible; humano revisa reutilización antes de ingestión/republicación. `PRODUCT_HEALTH_GO=NO`.

CORPUS_AND_HOLDOUT: 48 desarrollo SHA `40ec6a2e25331a2e040b7fedfd3ad75ff7245b508ef30c605d9cc6fdeb5e046a`; 20 conversaciones SHA `ca1dcb321bc92d2efa42c871e9730926421a375bfeab77edfee696e5ed09f413`; 12 holdout privado SHA `4dda59721932f620cba53e5686df288f7cf0e0e968ec30540216ffb1f52ec5c0`. Bytes revalidados, contenido holdout no publicado ni compartido.

PACKAGE_IDENTITIES: W2 R2 ZIP reconstruido con CPython 3.12 desde `f4615b3`, SHA `1992cc739e8e89cd4512ad45919d1ebc102a6385628f82689a23de49de6f2661`, 55.455 B; 13 miembros y 208.515 B descomprimidos. Manifest W2 SHA `bdbdb0cf0b5ff88eb6619390c53dab11f451d7ef4494068feceaac76475cc9cb`; assembly W3 temporal SHA `7111e7b3aa9c6895931bde0d6707ae249e3301cd790246e05ef8358ab0a70bfa`. W1 R4 provider SHA `c97842617f3077c2eec1892653361b4471a18e1c64f8127b808b9968401cb834`, snapshot SHA `62e00c04edb96ccde0a5ce4fe81574452ddcacdb4c173b030ca49b000f5a084b`. ZIP R2 no incluye W1 R4.

MODEL_AND_PORTAL_EXECUTIONS: LOCAL_LLM=0; PORTAL_LLM=0; portal mutations=0. Gold documental: 18 respondibles, 6 abstenciones, 6 adversarias, todo `PROPOSED_NOT_RUN`; corpus aún no indexado por W2.

V4_PRESERVATION: runtime `195b4980fa5998b096c308296a55e452380b0371`, 14/14 hashes PASS; sin cambios propios en runtime, datos v4, main, gh-pages o integración.

PR_AND_CI: draft PR #14 hacia `integration/vnext-2026-10-04`; verificar CI del nuevo HEAD tras push. R3 CI histórico no sustituye R4.

REMOTE_MUTATIONS: commits/push solo rama W3, comentarios de defectos en PR #17 y actualizaciones de hitos en PR #14/Issue #16. Sin merges, force-push ni escritura en ramas ajenas.

PORTAL_MUTATIONS: ninguna.

NEXT_EXACT_ACTION: tras W2 publicar adapter 0.2.0 y paquete combinado, fijar SHA/manifest, repetir C-R3-01–09 y exigir correcciones Critical/High antes de conectar JSON a UI 0.2.0; solo entonces considerar solicitud concreta de smoke privado en portal.

HUMAN_AUTHORIZATION_REQUIRED: autorización separada para escritura/ejecución en portal; no se solicita mientras candidato combinado y defectos W2 sigan pendientes. Revisión de licencia antes de ingestión/republicación documental.

MERGED_OR_PUBLISHED_RELEASE: NO
