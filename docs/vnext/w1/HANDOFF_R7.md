# W1 · G360 R7 · producer conformance y hardening

WORK_ID: W1  
ROUND: G360-R7  
START_SHA: `3e187616c8234343c68d7047ceaa6ad961d9f73b`  
TESTED_HEAD: `fb074c52d43a94fae7f7159100d377f6717773f2`  
PUBLISHED_HEAD: se registra en PR #15 e Issue #16 tras el cierre documental; no se autorreferencia.  
RUNTIME_CHANGED: NO  
RUNTIME_VERSION: R6 0.3.1, entrypoint `prototypes.ir_y_volver.provider_r6`  
R6_PIN_PRESERVED: YES; paquete `c66d44af702eb3410fcea05ae8711f537214f675e83a7fda38c39c3b39a1b910`, 129.365 bytes.  
W2_HEAD_CONSUMED: `8272988566f5bca2d65d3119732bf831d11382dc`  
W3_HEAD_CONSUMED: `e821341ba1ffd8ed7947cdb97802348919ef502a`

CONFORMANCE_PACK: `CONSUMER_CONFORMANCE_R7.json` + `.md`; 14 casos, SHA JSON `4eb364265710336ecdd86b2c541953f130f3b0a80bbefc9cf1f27904bac55dea`. Las cifras observadas del productor se etiquetan `PRODUCER_FIXTURE`; los esperados temporales contrastables usan CSV GTFS independiente. Incluye hashes estables de GTFS, snapshot, schema, catálogo, labels y modelo walking.

CONSUMER_LABELS: `datos_preparados/movilidad/consumer_labels_r7.json`, nueve paradas y GO01 derivados del GTFS, orígenes/municipios del catálogo R6 y centro de la fuente sanitaria. SHA `f0804b646d0473531e4f9ad12e31dc1ee7ee50cab69576bc95a0485b8da62799`; schema cerrado SHA `7687b557137597ca8d918c7522a6da46a13efe454163ee07a78a3a40cf2b53d8`. Consumer-support, fuera del ZIP R6.

PROVENANCE_AUDIT: `PASS_WITH_EXPLICIT_FINDING`. Cobertura, unicidad, roles, hashes, periodos, transformaciones, partición USER/defaults y semántica de componentes PASS. `W1-R7-F01` MEDIUM: `pre_appointment_wait` y `return_wait` citan `DERIVED`, cuyo hash resume `components_s`; no hay ciclo criptográfico ni impacto numérico, pero no es un DAG explicativo estricto. Propuesta futura: representar la derivación como arista/operación. No justifica cambiar 0.3.1 sin coordinación.

MUTATION_RESULTS: 29 mutaciones; 7 `SCHEMA_CAUGHT`, 22 `SEMANTIC_VALIDATOR_CAUGHT`, 0 `NOT_REQUIRED_BY_CONTRACT`, 0 `GAP`; Critical/High gaps 0. Evidencia `MUTATION_MATRIX_R7.json`.

METAMORPHIC_SEED: `360007`  
METAMORPHIC_CASES: 500 solicitudes generadas; no se presentan como 500 tests independientes.  
METAMORPHIC_RESULTS: PASS; distribución 245 ok, 122 no viable, 57 error controlado, 62 unsupported, 14 unknown; cero excepción/no finito/contraejemplo. Defaults omitidos/expresos, determinismo, reordenación, delta permitido, cross-origin sin delta y deadline PASS.

ISOLATION_RESULTS: PASS para A→B→A, válido→error→válido, health→R4→health y single→compare→single.

PACKAGE_INTEGRITY: PASS de integridad/portabilidad, no “seguridad completa”: 26 miembros, rutas relativas, sin `..`, absolutos, duplicados/casefold collisions, symlinks, ejecutables, `.git`, caches, temporales, holdout o marcadores de secretos; bytes/hashes/total exactos; dos ZIP idénticos; import limpio sin red/repo padre/PYTHONPATH.

PERFORMANCE: CPython 3.12.4, Windows 11; siete muestras, no SLA/portal/RSS/red. Medianas: 1=101,88 ms; 2=439,26 ms; 4=731,54 ms; 8=4.113,86 ms; 16=8.046,93 ms; 32=16.005,40 ms. P95 32=16.120,97 ms; payload máximo 767.650 B; pico tracemalloc 9.500.069 B. Variabilidad frente a R6 confirmada; sin cambiar máximo 32 ni añadir caché.

NEW_FINDINGS: `W1-R7-F01` MEDIUM conceptual, arriba. Sin Critical/High. La variabilidad de coste es observación local, no defecto funcional ni SLA.  
FIXES: ninguno en runtime; solo soporte de consumo, validadores y evidencia.  
CONTRACT_CHANGE_REQUIRED: NO.  
W2_ACTION_REQUIRED: ejecutar el pack 14 casos, usar labels, aplicar `CONSUMER_CHECKLIST_R7.json`, conservar límites/procedencia y decidir una vista acotada sin copiar selección interna.  
W3_ACTION_REQUIRED: mutar/contrastar independientemente el pack, revisar el finding conceptual y volver a probar W2 corregido sin adaptar holdout.

PYTHON: 479/479 PASS; R7 dedicado 10/10.  
NODE: 17/17 PASS.  
V4_PRESERVATION: PASS, identidad `195b4980fa5998b096c308296a55e452380b0371` antes/después.  
R4_PRESERVATION: PASS, pin `725a7b73ae0381092cd80edc41b8a25432d75fcd`.  
R5_PRESERVATION: PASS, pin `f4efe1bccd7f33a66fe0598f64787e7b425c020a`.  
CI: R6 36640073703 PASS Ubuntu/Windows; CI del HEAD R7 se comprueba después del push final.

PORTAL_MUTATIONS: 0  
MERGED_OR_PUBLISHED_RELEASE: NO  
NEXT_EXACT_ACTION: W2/W3 consumen el kit R7 y mantienen R6 0.3.1 fijado; no merge automático ni nueva versión salvo reproducción de bug material.
