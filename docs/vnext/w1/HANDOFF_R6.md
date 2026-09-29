# W1 · R6 · estabilización sanitaria y procedencia

START_SHA: `f4efe1bccd7f33a66fe0598f64787e7b425c020a`  
TESTED_HEAD: se fijará al publicar el commit ejecutable; el cierre documental posterior no altera runtime.  
CONSUMED_W2_HEAD: `8272988566f5bca2d65d3119732bf831d11382dc`  
CONSUMED_W3_HEAD: `e821341ba1ffd8ed7947cdb97802348919ef502a`  
STABLE_R4_PIN: `725a7b73ae0381092cd80edc41b8a25432d75fcd`, contrato 0.2.0.  
BASELINE_R5_PIN: `f4efe1bccd7f33a66fe0598f64787e7b425c020a`, contrato 0.3.0.  
R6_CONTRACT: 0.3.1 opt-in; R4/R5 y snapshot sanitario sin cambios.

## Hitos

- `PROVENANCE_REVIEW_DONE`: default y elección humana ya no se confunden. `USER` hashea solo campos explícitos; `MODEL_DEFAULTS` conserva los aplicados. Cada componente cita entradas efectivas, sin cambiar aritmética.
- `OPERATIONAL_CATALOG_READY`: `datos_preparados/movilidad/operational_catalog_r6.json`, derivado y validado uno-a-uno; schema `contracts/v0.3.1/catalog.schema.json`; consumo en `CONSUMER_R6.md`.
- `HEALTH_BOUNDARY_CASES_READY`: `BOUNDARY_CASES_R6.json`, 14/14 PASS con oráculo CSV independiente en los casos de viaje. Incluye segundo anterior/exacto/posterior, cambio de salida por duración, límite de regreso, fuera de día, fecha/destino/perfil/snapshot y enlace corrupto. La mezcla R4/R6 queda cubierta por test.
- `W1_INTEGRATION_PIN_READY`: paquete determinista 129.365 bytes, SHA-256 `c66d44af702eb3410fcea05ae8711f537214f675e83a7fda38c39c3b39a1b910`; 1.252.907 bytes sin comprimir. Entry point `provider_r6`; sin red.

Schemas: request `911bbbb6…`; result `5408f086…`; comparison `4e03b03f…`; capabilities `718448ca…`; catalog `6bb7b60a…`. Catálogo `c7bd3cc8…`. Snapshot R5 reutilizado `59fcded9…`.

## Comparación, coste y portabilidad

`CROSS_ORIGIN_SCENARIOS_R6.json` fija tres escenarios lado a lado con idénticos fecha, centro, cita, duración y perfil. No se declara comparabilidad numérica entre orígenes. Los deltas del proveedor permanecen limitados al mismo origen.

Medición local, tres muestras, no portal: 1 escenario p50 60,70 ms; 2: 230,58 ms; 8: 971,22 ms; 32: 4.016,69 ms. Pico de asignaciones Python 9.500.940 bytes; payload máximo 767.650 bytes. No se añadió caché.

Extracción limpia sin `.git`, repo padre, fixtures ni red: PASS. Dos builds idénticos. Tests R6: 10/10 PASS; suite completa, Node y gates se registran tras la ejecución final. R4 explícito es byte-equivalente al proveedor histórico; el manifiesto R5 verifica sus hashes.

## Límites y acciones

Centro confirmado y punto oficial confirmado; acceso por red modelado; entrada `NOT_VERIFIED`. Conflicto Bernedo Enea 1/Zaldizurreta 2 conservado. No citas, capacidad, centro asignado, accesibilidad universal, realtime, nuevas fechas, operadores o destinos.

Hallazgos W2 previos: `FIXED_BY_AUTHOR_PENDING_W3_RETEST`; no se declaran abiertos confirmados ni aceptados. W3 debe repetir su revisión sobre el nuevo candidato W2.

W2: puede seguir en 0.2.0; para adoptar 0.3.1, fijar paquete/hash, importar `provider_r6`, leer catálogo y conservar procedencia/limitaciones.  
W3: validar schemas/paquete y `BOUNDARY_CASES_R6.json` sin cambiar expected; comprobar wording modelado y retest W2.  
NEXT_EXACT_ACTION: revisión W2/W3 del pin R6; no merge automático.  
MERGED_OR_PUBLISHED_RELEASE: NO. Portal: 0 mutaciones.
