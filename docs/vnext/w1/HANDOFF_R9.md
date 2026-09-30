# W1 · G360 R9 · source governance y handshake

WORK_ID: W1
ROUND: G360-R9

START_SHA: `3bf8e75215c1d75c2fb40f6ea82b9c8a9032af57`
TESTED_HEAD: `2545059a550ce117f1c2a9930c23aef974b06063`
PUBLISHED_HEAD: se registra en PR #15 e Issue #16 tras el cierre; no se autorreferencia.

RUNTIME_CHANGED: NO
RUNTIME_VERSION: R6 0.3.1, `prototypes.ir_y_volver.provider_r6`
R6_PACKAGE_PRESERVED: YES; 129.365 bytes, SHA-256 `c66d44af702eb3410fcea05ae8711f537214f675e83a7fda38c39c3b39a1b910`.

W2_HEAD_CONSUMED: `8272988566f5bca2d65d3119732bf831d11382dc`
W3_HEAD_CONSUMED: `e821341ba1ffd8ed7947cdb97802348919ef502a`

CLEAN_ROOM_STATUS: PASS para el candidato desde raw fijado + derivados fijados; snapshots R4/R5 byte a byte idénticos y claims canónicos idénticos, incluido -2.100 s.
CLEAN_ROOM_MISSING_INPUTS: no es una reproducción íntegramente raw. La reconciliación sanitaria consume `HEALTH_DESTINATION_R4.json`; los bytes OSM históricos de la PoC no están disponibles y no se presentan como input R6.

UPSTREAM_AUDIT_TIMESTAMP: `2026-09-30T08:30:04.683125+00:00`
GTFS_DRIFT_STATUS: `UNCHANGED_BYTES`
HEALTH_REGISTRY_DRIFT_STATUS: `CHANGED_BYTES_SEMANTICALLY_EQUIVALENT_USED_FIELDS`
HEALTH_PAGE_DRIFT_STATUS: `CHANGED_BYTES_SEMANTICALLY_EQUIVALENT_USED_FIELDS`
PADI_DRIFT_STATUS: `UNCHANGED_BYTES`
OSM_DRIFT_STATUS: `CHANGED_BYTES_SEMANTICALLY_EQUIVALENT_USED_FIELDS`; todos los node/way IDs consumidos siguen presentes.

SOURCE_LICENSE_STATUS: auditoría de ingeniería, no asesoramiento jurídico; sin inferencias por oficialidad.
GTFS_LICENSE: `VERIFIED_GENERAL_TERMS_APPLY`; la ficha enlaza las condiciones generales de Open Data Euskadi, sin nombrar una variante específica para el dataset.
HEALTH_REGISTRY_LICENSE: `VERIFIED_GENERAL_TERMS_APPLY`; CC BY 4.0 aparece solo como corroboración secundaria en datos.gob.es.
HEALTH_PAGE_LICENSE: `NOT_VERIFIED`.
PADI_LICENSE: `NOT_VERIFIED`.
OSM_LICENSE: `VERIFIED_SPECIFIC`, ODbL 1.0 con atribución/share-alike aplicable.
REDISTRIBUTION_RISKS: HTML Osakidetza y PDF PADI `HUMAN_REVIEW_REQUIRED`; no incluirlos en el bundle final sin revisión. Los raw restantes no son necesarios en el runtime.

CLAIM_SEMANTICS_STATUS: PASS; los 55 claims R8 están mapeados a siete clases inequívocas R9.
DIRECT_SOURCE_VALUE_POLICY: un valor GTFS directo es horario programado de fuente, nunca observación real.
TIMEPOINT_POLICY: `timepoint=0` significa hora programada aproximada/interpolada; no prometer paso operacional exacto.

HANDSHAKE_PATH: `docs/vnext/w1/integration_r9/W1_HANDSHAKE_R9.json`
HANDSHAKE_BYTES: 9.891
HANDSHAKE_SHA: `090335ab9e18b76a0dea311408aeff2a913289c7368f0801ac02a70031f056d6`

DATA_FREEZE: `docs/vnext/w1/DATA_FREEZE_R9.json`
SOURCE_CHANGE_PLAYBOOK: `docs/vnext/w1/SOURCE_CHANGE_PLAYBOOK_R9.md`
SOURCE_HYGIENE: PASS; `SOURCE_HYGIENE_CHECK`, no auditoría de seguridad completa; 0 Critical/High, sin secretos, rutas locales ni metadata personal inesperada detectada.

NEW_FINDINGS: `W1-R9-F01` Medium: reproducción source-to-claim no es íntegramente raw; está cerrada mediante raw + derivado sanitario fijado. `W1-R9-F02` Medium: licencia específica de HTML/PADI no verificada; distribución final debe excluir o someter a revisión. Drift de bytes de tres fuentes es Low porque los campos usados permanecen equivalentes.
CRITICAL_HIGH: 0
MEDIUM: 2 de gobernanza, sin impacto numérico/runtime.
LOW: 3 observaciones de cambio de bytes con equivalencia semántica usada.

PYTHON: 500/500 PASS (489 anteriores + 11 R9).
NODE: 17/17 PASS.
CI: el run del published head se registra en PR #15 e Issue #16.

V4_PRESERVATION: PASS.
R4_PRESERVATION: PASS.
R5_PRESERVATION: PASS.
R6_RUNTIME_PRESERVATION: PASS.
R7_PRESERVATION: PASS.
R8_PRESERVATION: PASS; hashes históricos fijados por tests.

PORTAL_MUTATIONS: 0
MERGED_OR_PUBLISHED_RELEASE: NO

W2_ACTION_REQUIRED: empezar por `W1_HANDSHAKE_R9.json`; abrir evidencia pesada solo por sus referencias y conservar scheduled/modelled/input como categorías distintas.
W3_ACTION_REQUIRED: fijar candidato con handshake + data freeze; validar wording, gaps de reutilización y contraste raw sin adaptar holdout.
HUMAN_ACTION_REQUIRED: no incluir HTML Osakidetza ni PDF PADI en el bundle de entrega salvo confirmación de términos; mantenerlos como referencia/hash/evidencia de repositorio.

NEXT_EXACT_ACTION: W2/W3 consumen el handshake R9; cualquier drift futuro se tramita mediante el playbook y nunca sustituye silenciosamente el pin.
