# W1 · G360 R10 · cierre del productor y paridad con agente

WORK_ID: W1  
ROUND: G360-R10

START_SHA: `6ebf41e2f1fe24f1c3678c4be13c6c44cf8cb62b`  
TESTED_HEAD: `3399cce4d69fd48ad56176970986a7ed806c394e`  
PUBLISHED_HEAD: el commit documental final se registra en PR #15 e Issue #16; este archivo no se autorreferencia.

RUNTIME_CHANGED: NO  
RUNTIME_VERSION: R6 `0.3.1`, `prototypes.ir_y_volver.provider_r6`  
R6_PACKAGE_PRESERVED: YES · 129.365 bytes · SHA-256 `c66d44af702eb3410fcea05ae8711f537214f675e83a7fda38c39c3b39a1b910`.

CONSUMED_W2_HEAD: `8272988566f5bca2d65d3119732bf831d11382dc`  
CONSUMED_W3_HEAD: `e821341ba1ffd8ed7947cdb97802348919ef502a`

SUPPORT_ERRATA: FIXED en `docs/vnext/w1/ERRATA_R9_R10.json`. R9 se conserva como evidencia histórica. El generador ya no puede recrear el contador ambiguo: 25 entradas descritas = 3 `AVAILABLE_DIRECT` + 5 `DERIVABLE_EXACT` + 1 `ESTIMABLE_WITH_ASSUMPTIONS` + 11 `UNAVAILABLE` + 5 `OUT_OF_SCOPE`; disponibles = 9. Estas entradas no son tools. El productor expone tres interfaces deterministas: `get_capabilities`, `plan_visit`, `compare_visits`.

UNKNOWN_SEMANTICS: FIXED mediante `status + error.code` en `STATUS_ERROR_SEMANTICS_R10.json`. Incluye fixtures observados para `date_not_validated`, `invalid_health_snapshot`, `catalog_scope`, salida del día civil, petición inválida y búsqueda completa sin pareja. El fallback desconocido conserva código/mensaje técnico y no inventa fecha, HTTP, red ni ausencia de servicio.

CALLER_PROVENANCE: `human_explicit` se preserva, pero significa caller-supplied; un LLM caller no acredita autoría humana. `CALLER_PROVENANCE_R10.json` demuestra default omitido, default explícito igual y valor distinto. Los dos primeros mantienen la aritmética y difieren en procedencia.

HANDSHAKE_VERSION_AND_HASH: `r10.0-support` · `docs/vnext/w1/integration_r10/W1_HANDSHAKE_R10.json` · 11.842 bytes · SHA-256 `ac2657cede8dfdf2487fe71d53c245700c8a259dac688df852eb6f4c857f151c`. Schema y manifest R10 están en el mismo directorio. El handshake referencia R7/R8/R9 por hashes; no los duplica.

PARITY_RUNNER: `scripts/mobility/verify_candidate_parity_r10.py`. Entradas: `--package`, `--manifest`, `--w1-pin`, `--output`. Verifica ZIP/manifiesto/members, extracción segura, pin/contrato R6, interfaces reales y 14 casos R7, incluido principal, variaciones, márgenes, estados y comparación. Clasifica `INTENDED_PROJECTION`, `MISSING_REQUIRED_INFORMATION`, `WRONG_VALUE`, `WRONG_SEMANTICS`, `NOT_RUN`. No exige igualdad byte a byte del envelope, pero sí los hechos comunicados y la evidencia bruta cuando el contrato la ofrece.

CANDIDATE_PACKAGE_TESTED: identidad, integridad y política de distribución del W2 R4 publicado, desde extracción temporal limpia. ZIP 153.456 bytes, SHA-256 `366cdc7d160ee6743cb125c6709f57e48f6ddfb91ead812a92eb881570233357`; no contiene HTML/PDF crudos.  
PARITY_RESULTS: `NOT_RUN`. El paquete fija W1 `0.2.0` / `725a7b73ae0381092cd80edc41b8a25432d75fcd`, no R6 `0.3.1` / `cb061a97e78d6b5c967104fef6b935132fdc450f`. No es un fallo de paridad y no autoriza `W1_PARITY_PASS`.

TEST_COMMANDS:

- `python -m pytest tests/mobility/test_r10.py -q -o addopts=` → 8/8 PASS.
- `python -m pytest -q -o addopts=` → 508/508 PASS; una advertencia no funcional de estilo XLSX.
- `node --test tests/e2e/contract_flow.test.mjs` → 17/17 PASS.
- `python scripts/ops/verify_runtime_identity.py` → PASS 14/14.
- `python scripts/benchmark/verify_jury_results.py --output work/jury-gate-r10.json` → PASS.
- `python scripts/release/verify_final_artifacts.py` → PASS.
- doble `python -m scripts.mobility.build_r10` → mismo handshake SHA-256.
- `git diff --check` → PASS.

CI: Release fast CI `36696885312` PASS Ubuntu/Windows sobre TESTED_HEAD.

KNOWN_FAIL: ninguno en soporte R10.  
NOT_RUN: paridad semántica productor→adapter→paquete W2 R6; W2 todavía no ha publicado `DEPLOYABLE_PACKAGE_READY` compatible. Modelo/LLM, portal y aceptación independiente W3 están fuera del alcance y no se declaran ejecutados.

SOURCE_LIMITS: se mantienen R9: reproducción desde raw + derivado sanitario fijado, no íntegramente raw; no identidad del OSM histórico de la PoC; snapshot estático programado; entrada física `NOT_VERIFIED`; no realtime ni puerta a puerta; HTML Osakidetza y PDF PADI no deben incluirse sin revisión de reutilización.

V4_PRESERVATION: PASS · identidad `195b4980fa5998b096c308296a55e452380b0371`.  
MERGED_OR_PUBLISHED_RELEASE: NO  
PORTAL_MUTATIONS: 0

W1_R10_READY: YES  
W1_PARITY_PASS: NOT_RUN

NEXT_EXACT_ACTION: W2 consume `W1_HANDSHAKE_R10.json`, publica `DEPLOYABLE_PACKAGE_READY` con SHA y hash exactos y entonces W1 ejecuta el runner sin modificar runtime; W3 conserva la aceptación independiente.
