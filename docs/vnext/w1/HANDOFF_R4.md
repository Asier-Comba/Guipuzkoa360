WORK_ID: W1

COORDINATION_ROUND: G360-R4

R3_PENDING_INCLUDED: YES

STATUS: READY_FOR_REVIEW_PARTIAL — motor stop-only reparado; HEALTH_DESTINATION_BLOCKED.

START_SHA: c68eb5c55dec72a267b7435b4c364049f6eab408

TESTED_HEAD: 1b52a892efea3206f8b39b6e0ad7ccaf952f979b (código/datos y paquete; commit siguiente solo evidencia/handoff).

PUBLISHED_HEAD: se registra después del commit en PR #15 y en Issue #16; este archivo no autorreferencia su commit.

CONSUMED_W2_SHA: f4615b36d0af93966e6ca0f2044288841e6574b8 — lectura, sin integrar código ajeno.

CONSUMED_W3_SHA: cf9cd0afadc97b255c021a4ff867dab7ae6dabbc — lectura de runner, contrato y casos independientes públicos; holdout no leído.

CONTRACT_VERSIONS_AND_HASHES: 0.2.0. Contrato temprano publicado en 43e0c85d7906b4305d1a377f29f8a4b33a95138b. SHA-256 request `16f65e95dd26e09e65829331739bea4ebb59c9a2ffd12434910663365ba36f0b`; result `8fde2a90c42e0cf20c950bb81902d797f26a8a7a3ff1b9cb5704cf7baf48141e`; capabilities `b28ce4ef94a266ccdad5e4cb9603d486cba0d2259826a0a5bf5ecce362297d46`; comparison `6368ff668ce46bd7cc97447e05d4d2036c1321c63c47e91e5db9cfb141f2f942`. Schemas no cambiados después del hito; ejemplos sintéticos aclarados para reflejar el campo `return` y comparaciones mixtas, sin presentarlos como datos reales.

SOURCE_ACCESS_AND_READING: SOURCE_READING_R4.md enumera lectura real, fuentes live y brechas. GitHub y sistema local lectura/escritura/ejecución comprobados; OSM descargado. Paquete privado START_HERE/master/feedback/PoC no localizado; volcado oficial local no se confunde con ese paquete. No se publican textos privados.

ORIGINAL_ARCHIVE_STATUS: NOT_AVAILABLE. No reproducción del ZIP completo ni de sus 14 tests históricos.

GTFS_COMPONENT_STATUS: GTFS_COMPONENT_IDENTIFIED. Bytes reales 811289; SHA-256 `3276fcae7bfa5002a39a2a094fef6637603de2e50648a46a436b314db27832a4`; coincide con hash histórico indicado por coordinador. CSV leído por oráculo independiente. No implica recuperar otros componentes.

OSM_COMPONENT_STATUS: original NOT_AVAILABLE. Nueva adquisición acotada, 6400 nodos/867 ways, hash original `d70452469ac23b81839417aabda5289f4148d428d2c2b5762347c4f90320a652`. Original conservado local fuera de Git; derivado público sin cuentas de contribuidores/contactos. ODbL 1.0/atribución conservada.

CENTRE_SOURCE_STATUS: IDENTIFIED. entityBC631DA5, Ambulatorio de Beasain, Bernedo Enea 1, 43.04527740634045/-2.1977014177917447; fuente sanitaria 2026-09-20 y nombre/dirección contrastados con Osakidetza 2026-09-29. OSM way 42927929, ref:osakidetza=ambulat_beasain. Dirección/centro no acredita entrada, capacidad, agenda ni asignación.

HEALTH_DESTINATION_GO_NO_GO: BLOCKED. Cero entradas etiquetadas en el edificio de la red adquirida; enlace peatonal y duración no demostrados. No se habilita destino sanitario, ni se conectan componentes a mano, ni se convierte distancia recta en tiempo. Walking sanitario null, no cero. Evidencia HEALTH_DESTINATION_R4.json.

FILES_CHANGED: solo prototypes/ir_y_volver/**, scripts/mobility/**, tests/mobility/**, datos_originales/movilidad/** y docs/vnext/w1/**. Incluye schemas/fixtures candidatos, provider/validación, nuevo snapshot/allowlist, raw GTFS, red OSM pública, oráculo, matriz, pruebas y handoff. Sin cambios en W2/W3/workflows/dependencias globales/v4.

STAGES_COMPLETED: A P0 reproducidos; B contrato temprano publicado y notificado; C centro/red adquiridos y auditados, enlace sanitario bloqueado; D proveedor stop-only corregido (sanitario no completado); E oráculo raw y matriz completados; F pin/paquete consumible para stop-only; G no iniciado porque piloto sanitario no está estable.

REPRODUCTIONS_BEFORE_AFTER: REPRODUCTIONS_R4.md e IMPACT_R4.json. Permisos condicionados dejan de ser ordinarios; fixtures runtime inaccesibles; validación/hash/JSON duplicado/NaN/overflow cerrados; ocho intervalos disjuntos; comparación conserva estados y cambios; multidía/DST explícitos. Diez ejemplos R2 conservan autobuses y aumentan 180 s por presencia inicial; cero viajes GO01 afectados por permisos 2/3 porque no existen en el feed observado.

TEST_COMMANDS_AND_RESULTS: `python -m pytest -o addopts= -q` → 399 PASS / 0 FAIL, 52.65 s en TESTED_HEAD; incluye 135 tests movilidad. `node --test tests/e2e/contract_flow.test.mjs` → 17 PASS. `python scripts/mobility/verify_r4.py` → 135/135 escenarios contra raw GTFS; once casos detallados incluyendo no viable. Schemas/fixtures y outputs plan/compare validados con jsonschema en entorno temporal. Rebuild snapshot byte-identical y ensamblaje aislado sin red incluidos en tests. Doble build ZIP idéntico. Runtime identity antes/después PASS; jury gate PASS; artifact gate PASS; diff --check PASS. PERFORMANCE_R4.json mide Python local, no portal; memoria es asignación Python, no RSS.

KNOWN_FAIL: no fallos conocidos de la suite dentro del alcance stop-only. Gate sanitario BLOCKED por falta de entrada/enlaces peatonales verificados. Adapter W2 y runner W3 0.1.0 incompatibles intencionadamente hasta actualizar contrato y pins.

NOT_RUN: visita sanitaria; ruta OSM hasta entrada; reproducción del ZIP/OSM original; 14 pruebas históricas; otras fechas; realtime/transbordos/multioperador; portal/LLM/holdout; A/B de agente. No se heredan esos PASS ni se repite benchmark masivo v4 sin cambio de runtime.

FINDINGS_AND_OWNERS: W1-H1 destino sanitario bloqueado (dato/validación W1 y proveedor de fuente); W1-S1 paquete privado original ausente (coordinador/fuente original); W1-L1 condiciones particulares GTFS sin SPDX explícito (revisión humana de reutilización, no prohibición automática); W1-C1 migración contractual requerida (W2/W3); W1-T1 horarios aproximados y fecha única (limitación W1 documentada). P0 técnicos corregidos. Ningún defecto Critical/High conocido en alcance stop-only; bloqueo sanitario no se rebaja a visita válida.

PROVIDER_AND_SNAPSHOT_IDENTITIES: provider.py `c97842617f3077c2eec1892653361b4471a18e1c64f8127b808b9968401cb834`; snapshot_validation.py `0773a1a612b366f59ea01f80ea1dc4fc0a4650ebbd339f6b99869c4061a16d42`; snapshot R4 `62e00c04edb96ccde0a5ce4fe81574452ddcacdb4c173b030ca49b000f5a084b`, 812758 bytes. Manifiesto RUNTIME_MANIFEST_R4.json: diez archivos, 855413 bytes sin comprimir. ZIP reproducible 77470 bytes, SHA-256 `fa2ae468c4197259c5a7cce562ad21f3fa41c2c11c678a84f5faa5958c624e45`.

W1_PIN_READY: YES — exclusivamente proveedor scheduled stop-only 0.2.0. No significa HEALTH_DESTINATION_GO ni release aprobado. CONSUMER_R4.md contiene rutas, límites y comandos.

V4_PRESERVATION: identidad 195b4980fa5998b096c308296a55e452380b0371 PASS 14/14 antes/después; suite completa y gates PASS; diff limitado a propiedad W1. Main e integración siguen e213eaa9b73b0f8a4d1893e0269fe92fe6756955 al cierre local.

PR_AND_CI: continúa PR #15 draft hacia integration/vnext-2026-10-04. CI final se registra en comentario tras push del PUBLISHED_HEAD; no se confunde CI R2 con evidencia R4.

REMOTE_MUTATIONS: commits/push solo work/vnext-w1-mobility, comentarios #16/#15 y actualización descriptiva PR #15. Sin force-push, merge ni escritura en ramas ajenas.

PORTAL_MUTATIONS: ninguna.

NEXT_EXACT_ACTION: W2 actualiza consumidor 0.2.0 y construye ensamblaje local por pin; W3 actualiza runner/pin, ejecuta casos independientes sin cambiar corpus. Para desbloquear salud, obtener entrada acreditada y conectores acotados parada/red/centro, validar ambos sentidos, longitudes/perfil/tiempos y publicar nuevo snapshot/pin con tests repetidos. No usar 7214 sin acreditar conectividad.

HUMAN_AUTHORIZATION_REQUIRED: ninguna adicional para el trabajo offline realizado. Falta dato, no permiso, para walking sanitario. Aportar paquete original si se exige su reproducción literal; decisión humana sobre condiciones particulares antes de una distribución que requiera ese gate.

MERGED_OR_PUBLISHED_RELEASE: NO
