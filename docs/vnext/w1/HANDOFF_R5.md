# W1 · R5 · acceso sanitario modelado

WORK_ID: W1  
COORDINATION_ROUND: G360-R5  
STATUS: HEALTH_PROVIDER_READY_FOR_W2_W3_REVIEW; no aceptación integrada ni portal.  
R5_START_SHA: `725a7b73ae0381092cd80edc41b8a25432d75fcd`  
STABLE_R4_STOP_ONLY_SHA: `725a7b73ae0381092cd80edc41b8a25432d75fcd`  
TESTED_HEAD: `fa95fbf3e1bc273ae736f9dad36a675d50f0b5d0`; cierre posterior añade evidencia y una aserción de coordenadas no finitas, sin cambiar runtime/paquete.  
PUBLISHED_HEAD: SHA del cierre documental registrado en PR15/Issue16 después del push; sin autorreferencia.  
CONSUMED_W2_SHA: `f4615b36d0af93966e6ca0f2044288841e6574b8`  
CONSUMED_W3_SHA: `e821341ba1ffd8ed7947cdb97802348919ef502a`, leído al cierre tras avance desde cf9cd0a: handoff R4, componentes 0.2.0 y hallazgos W2; no holdout.

CONTRACT_VERSION: 0.3.0 opt-in; 0.2.0 congelado.  
SCHEMA_HASHES:

| Schema 0.3.0 | SHA-256 |
|---|---|
| request | d4a3c8bdf33f084e2ef2c60482db1694ede8a8886df6a53cab65f746990b0a07 |
| result | db535eb2a335e3c90c791c5af5a0886ebeea59e86db9a9edf206dadcac642b85 |
| capabilities | 530d27225509f38960c7224fab2a31a65096f3d3e1ba696d98b8e660dab9e672 |
| comparison | dd78e711a226222d03d36284817e77c0ff8ab9e3b2f7974d038dc100c53784c2 |

CURRENT_POINTER_SHA: `7394b63779b6dd58fd224523bc4e10c57fd2c7b24f3d15d56c4e4180cf9d96b6`.

CENTRE_IDENTITY_STATUS: CONFIRMED (entityBC631DA5, Ambulatorio de Beasain).  
CENTRE_ANCHOR_STATUS: CONFIRMED_OFFICIAL_POINT, EPSG:4326 `[43.04527740634045,-2.1977014177917447]`.  
ADDRESS_SOURCE_CONFLICT_STATUS: conflicting_current_sources; ficha específica/registro Bernedo Enea 1 frente a PADI enero 2026 Zaldizurreta 2, mismo teléfono. Revisión humana pendiente, sin inferir traslado.  
MODELLED_NETWORK_ACCESS_STATUS: PASS para tres paradas y ambos sentidos.  
ENTRANCE_VERIFICATION_STATUS: NOT_VERIFIED.  
HEALTH_MODELLED_ACCESS_GO: YES.  
HEALTH_VERIFIED_ENTRANCE_GO: NO.  
PRODUCT_HEALTH_JOURNEY_GO: YES_WITH_MODELLED_ACCESS_LIMIT, **gate técnico W1**, no aceptación del producto W3 ni del agente combinado.

«El paseo termina en un punto de referencia modelado del centro; no representa una puerta física verificada». No puerta-a-puerta ni certificación de accesibilidad.

GTFS_SHA: `3276fcae7bfa5002a39a2a094fef6637603de2e50648a46a436b314db27832a4`.  
OSM_ACQUISITION_SHA: `d70452469ac23b81839417aabda5289f4148d428d2c2b5762347c4f90320a652`, R4 intacto. Derivado público con LF canónico: `0f09edd3324ab4feceddaf0392a33723244404881d3d3efb0a591991ea3df865`.  
HEALTH_SNAPSHOT_ID: `official-goierrialdea-go01-health-r5-20260929`.  
HEALTH_SNAPSHOT_SHA: `59fcded9e4236ee094eeb0881c4eb94f521b96fb6c8c89c881c3e9f6d5140901`.  
WALKING_PROFILE: `poc_reference_50m_min_plus_120s`, `ceil(metros_crudos/50)*60+120`, por enlace completo y sentido.  
CONNECTOR_POLICY: nodo admisible más próximo, desempate ID; cada conector <=100 m; rechazo fuera del bbox/red vacía/desconectada; no resnap para fabricar conectividad.  
CANDIDATE_STOPS: once GO01 Beasain auditadas, incluidas 7215/7218/7219.  
EXCLUDED_STOPS_AND_REASON: 7214 disconnected_network; 7200/7203/7206/7207/7208/7209/7213 outside_network_bbox. Esto no prueba ausencia real de caminos.

| Parada | Conector parada (m) | Red (m) | Total (m) | Modelo por sentido (s) |
|---|---:|---:|---:|---:|
| 7219 | 3,869 | 187,978 | 205,080 | 420 |
| 7215 | 11,031 | 614,442 | 638,705 | 900 |
| 7218 | 4,420 | 668,463 | 686,116 | 960 |

Conector del punto sanitario: 13,232 m, nodo 537657326. Tabla redondeada solo para presentación; snapshot conserva metros crudos y ambas rutas. El grafo admite sentidos explícitos aunque la adquisición no contiene oneway:foot/foot:forward/backward. Incline, bridge, tunnel, layer, access, crossing, sidewalk y nodos de corredor auditados; no se atribuyen tiempos de pendiente/semáforos no modelados.

FILES_CHANGED: exclusivamente nuevas rutas R5 bajo prototypes/ir_y_volver, scripts/mobility, tests/mobility, docs/vnext/w1 y fuentes públicas datos_originales/movilidad/r5; índice HANDOFF actualizado. Archivos exactos ejecutables en RUNTIME_MANIFEST_R5.json. No rutas W2/W3 ni v4.  
STAGES_COMPLETED: preflight; fuentes privadas 12/12 hashes; propuesta pública previa; identidad/conflicto; red y enlaces; snapshot separado; contrato cerrado; dispatcher; oracle/matriz; paquete; preservación; handoff.  
RED_GREEN_REPRODUCTIONS: CI Ubuntu 36630418307 detectó hash OSM dependiente de CRLF/LF; corregido fa95fbf, CI 36630925794 PASS en Ubuntu/Windows. Regresión de reconstrucción mantiene igualdad byte por byte. Detalle en REPRODUCTIONS_R5.md. Los demás negativos son pruebas de rechazo, no bugs históricos inventados.  
INDEPENDENT_ORACLE_RESULTS: geometría atan2 vs haversine con tolerancia 0,0001 m; nodos/vías/continuidad/endpoints; fórmula desde longitud independiente; Floyd–Warshall en fixture frente a Dijkstra; eliminación de tramo crítico; 7214 real; oráculo CSV independiente para 135 visitas. PASS.  
HEALTH_MATRIX_RESULTS: 135/135 PASS, todos ok en esa cuadrícula; pruebas dirigidas cubren no viable. Análisis exhaustivo de pares de un cambio por origen: diferencias nulas, máximo absoluto 6.000 s, 831 cambios de vuelta y 828 de ida entre esos pares. No son otros tantos tests independientes.  
POC_METHOD_COMPARISON: método reconstruido sobre OSM nuevo, no reproducción exacta. GTFS idéntico; faltan bytes OSM histórico; Idiazabal conserva paradas R4 distintas a PoC; 7200 fuera del bbox. En Zegama nuevo cálculo 09:30/20→09:45/20: 10.691→8.591 s; diferencia 2.100 s calculada, no assertion histórica. Con 40 min: 10.691→10.372 s.

TEST_COMMANDS_AND_RESULTS:

- `python -m pytest -o addopts= -q`: 459 PASS en fa95fbf; 195 movilidad incluidos, no sumar dos veces. Cierre añade únicamente aserción en test existente y vuelve a ejecutarlo: 33/33 walking PASS.
- `python -m scripts.mobility.verify_health_r5`: 135/135 oracle; resultados, filas CSV, fuentes, conectores y componentes en HEALTH_MATRIX_R5.json.
- Validación externa `jsonschema.Draft202012Validator`: cuatro schemas/ejemplos PASS; evaluador interno probado por fixtures corruptos y toda la matriz.
- `node --test tests/e2e/contract_flow.test.mjs`: 17 PASS.
- `python scripts/ops/verify_runtime_identity.py`: PASS 14/14.
- `python scripts/benchmark/verify_jury_results.py --output <temporal>/jury-r5.json`: PASS.
- `python scripts/release/verify_final_artifacts.py`: PASS.
- `python -m scripts.mobility.package_r5 --output <temporal>/w1-r5-a.zip` y segundo ZIP: mismo hash/bytes; extracción aislada con socket bloqueado PASS.
- Comparación de 135 outputs R4 entre provider original y dispatcher: JSON serializado idéntico. Manifiesto R4 diez archivos/hash intactos.
- `git diff --check`: PASS; ownership limitado a W1. CI final del cierre en PR15, sin nuevo runtime.

TESTS_NOT_RUN_AND_REASON: portal/LLM/aceptación W3/ensamblaje W2 no ejecutados: fuera de esta misión. Sin reproducción exacta OSM histórico por falta de bytes; sin validación física de puerta, pendiente/cruces o accesibilidad.  
PERFORMANCE: 30 warm p50 125,93 ms/p95 179,38 ms; primeras llamadas en tres intérpretes nuevos 62,89/59,64/61,00 ms; pico de asignaciones Python 5.554.194 B, no RSS; respuesta 14.897 B; snapshot 103.969 B; seis enlaces dirigidos. Medición local variable, no latencia portal. R4 registró 163,33/175,46 ms en otra muestra: solo referencia técnica, no comparación controlada ni claim de mejora.

PROVIDER_SHA: `7a775dfd6f7ba2cb19a1e9a40b531ee626e26462f726226fbf62a1a1dd34f013`.  
PACKAGE_SHA: `ab7b7ac4f7c426bcf5aaf8c1e0b67ad18fadb1e2d94a876ce9a9ea0a74220120`.  
PACKAGE_BYTES: 109.882 comprimidos; 1.110.158 sin comprimir; 19 archivos.  
W1_HEALTH_PIN_READY: YES para consumo offline explícito 0.3.0; no ensamblaje ni portal.

KNOWN_FAIL: ningún test W1 pendiente; W2 mantiene tres defectos raíz reportados por W3: CRITICAL binding municipal, HIGH procedencia de tasa, MEDIUM unidad. No se han corregido aquí.  
OPEN_FINDINGS_AND_OWNER: W2 adapta contratos y corrige defectos antes del ensamblaje; W3 revisa de manera independiente salud/wording y aceptación, actualmente aún NO_GO integrado; humano confirma dirección/entrada y condiciones reales.  
SOURCE_CONFLICTS: Bernedo Enea 1 vs Zaldizurreta 2 conservado, precedencia explícita, human_review_required=true. PADI es listado dental, no evidencia suficiente para declarar dos sedes o traslado.  
LICENSE_STATUS: OSM © colaboradores, ODbL 1.0 y derivados atribuidos; GTFS/centros bajo condiciones de reutilización del catálogo, sin inventar SPDX específico. Revisión de condiciones particulares antes de republicación comercial/documental adicional; formación/correos privados no publicados.

V4_PRESERVATION: PASS, congelado 195b4980fa5998b096c308296a55e452380b0371.  
R4_PIN_PRESERVATION: PASS, contrato/snapshot/provider/paquete intactos, 135 outputs iguales.  
PR_AND_CI: PR15 draft hacia integration/vnext-2026-10-04. Código fa95fbf: CI 36630925794 Ubuntu/Windows PASS; enlace final del cierre se publica sin autorreferencia en PR15/Issue16.  
REMOTE_MUTATIONS: commits/push solo work/vnext-w1-mobility, propuesta e hitos Issue16, actualización PR15.  
PORTAL_MUTATIONS: 0.

NEXT_EXACT_ACTION: W2/W3 fijar este paquete opt-in y revisar la semántica; no merge automático.  
W2_ACTION_REQUIRED: mantener R4 estable si lo necesita; adaptar 0.3 explícitamente con source_role/escenario/destino, corregir Critical/High, empaquetar proveedor real y repetir binding/provenance.  
W3_ACTION_REQUIRED: consumir fixtures públicos R5, validar esquema/paquete y derivaciones sin ajustar holdout; distinguir gate técnico modelado de entrada verificada y de aceptación integrada.  
HUMAN_ACTION_REQUIRED: validar discrepancia de direcciones y recorrido/puerta antes de ofrecer indicaciones reales; no es necesario autorizar portal para consumir este paquete offline.  
MERGED_OR_PUBLISHED_RELEASE: NO.
