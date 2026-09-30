# W1 · G360 R8 · evidencia de entrega y trazabilidad

WORK_ID: W1  
ROUND: G360-R8  
START_SHA: `fbbdc23a956fc3ab1df03b6550028cfa384c455a`  
TESTED_HEAD: `813977137d0e720e37cb95650cb3a4c64e226637`  
PUBLISHED_HEAD: se registra en PR #15 e Issue #16 tras el cierre documental; no se autorreferencia.  
RUNTIME_CHANGED: NO  
RUNTIME_VERSION: R6 0.3.1, entrypoint `prototypes.ir_y_volver.provider_r6`  
R6_PACKAGE_PRESERVED: YES; `c66d44af702eb3410fcea05ae8711f537214f675e83a7fda38c39c3b39a1b910`, 129.365 bytes.  

W2_HEAD_CONSUMED: `8272988566f5bca2d65d3119732bf831d11382dc`  
W3_HEAD_CONSUMED: `e821341ba1ffd8ed7947cdb97802348919ef502a`

CANONICAL_CASES: 6: principal, variación de hora, variación de duración, tres orígenes lado a lado, fecha no validada y petición fuera de catálogo.  
MAIN_CASE: Zegama → Ambulatorio de Beasain, 2026-09-29, 09:30, 20 min; `ok`, 10.691 s.  
VARIATION_CASE: mismos parámetros a las 09:45; `ok`, 8.591 s. La diferencia reproducida es -2.100 s (-35 min). Duración 26 min: 10.372 s.  
LIMIT_CASE: 2026-09-30 → `unknown`; destino fuera de catálogo → `unsupported`.

DIRECTLY_CONTRASTED_CLAIMS: `R8-DELTA-ZEGAMA-0930-0945`, reconstruido desde filas CSV GTFS, geometría/way IDs OSM, anchor sanitario, inputs humanos y fórmula de paseo publicada.  
INDEPENDENT_ORACLE_STATUS: PASS; el esperado no se obtiene de `plan_visit`.

CLAIM_LEDGER: `CLAIM_LEDGER_R8.json`; 55 claims con unidad, clase, periodo, fuente, transformación, supuestos, límites y verificación.  
DERIVATION_DAG: `DERIVATION_DAG_R8.json` + `.md`; 51 nodos, acíclico, rutas a hojas para todos los claims.  
W1_R7_F01_STATUS: `RUNTIME_FINDING_RETAINED / EXPLANATORY_DAG_RESOLVED_EXTERNALLY`; no se declara corregido en runtime.

SOURCE_LEDGER: `SOURCE_LEDGER_R8.json`; 8 entradas efectivas.  
LICENSE_GAPS: licencia específica no verificada para GTFS y fuentes oficiales sanitarias; no se infiere licencia por oficialidad. OSM mantiene ODbL 1.0 documentada.

ANSWERABILITY_MATRIX: `MOBILITY_ANSWERABILITY_R8.json`; 25 capacidades con wording permitido, inferencia prohibida y siguiente acción segura.  
STATUS_SEMANTICS: `STATUS_SEMANTICS_R8.json`; fixtures reproducibles para `ok`, `no_feasible_journey`, `unknown`, `unsupported` y `error`.  
RELATIVE_DATE_POLICY: W2 resuelve lenguaje natural a fecha real; si no es 2026-09-29, la pasa sin sustituir y W1 responde contractualmente.

TIMELINE_EVIDENCE: `TIMELINE_EVIDENCE_R8.json` + `.md`; tres timelines canónicos basados en eventos validados y labels R7.  
CONSUMER_COST_GUIDANCE: `CONSUMER_COST_GUIDANCE_R8.json`; reutiliza R7, no es SLA ni latencia de portal.  
INTEGRATION_MANIFEST: `integration_r8/INTEGRATION_MANIFEST_R8.json`; referencias, roles, bytes y SHA-256; no duplica ni altera el ZIP R6.

NEW_FINDINGS: ninguno Critical/High. Se conserva W1-R7-F01 como Medium conceptual resuelto externamente para explicación.  
CRITICAL_HIGH: 0.  
MEDIUM_LOW: W1-R7-F01 Medium retenido; gaps explícitos de licencia y entrada física no verificada, sin cambio de runtime.

PYTHON: 489/489 PASS (479 previos + 10 R8).  
NODE: 17/17 PASS.  
CI: el run del published head se registra en PR #15 e Issue #16.

V4_PRESERVATION: PASS.  
R4_PRESERVATION: PASS; pin `725a7b73ae0381092cd80edc41b8a25432d75fcd`.  
R5_PRESERVATION: PASS; pin `f4efe1bccd7f33a66fe0598f64787e7b425c020a`.  
R6_RUNTIME_PRESERVATION: PASS; hashes de provider, schema, snapshot, walking, catálogo, manifest y paquete intactos.  
R7_EVIDENCE_PRESERVATION: PASS; conformance y stress byte a byte intactos.

PORTAL_MUTATIONS: 0  
MERGED_OR_PUBLISHED_RELEASE: NO

W2_ACTION_REQUIRED: consumir el manifest R8, usar estados y answerability literalmente, y no convertir horarios programados, paseos modelados o consulta hipotética en observaciones reales.  
W3_ACTION_REQUIRED: usar principal, variación, límite y contraste raw para validar presentación; mantener lado a lado entre orígenes sin delta formal.  
NEXT_EXACT_ACTION: W2/W3 leen `integration_r8/INTEGRATION_MANIFEST_R8.json`; R6 0.3.1 permanece congelado y no se integra automáticamente.
