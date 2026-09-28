# Validación de GIPUZKOA 360

Esta síntesis separa la suite integrada, el benchmark exhaustivo del core, la evidencia visual y la
conversación privada. Sus denominadores no se suman: un test o check de propiedad no equivale a una
conversación ni demuestra impacto social.

## Suite integrada del candidato generalizado

Validación local reproducible sobre `feature/generalized-capabilities` (28/09/2026):

- **271/271 tests Python** de datos, contratos, runtime, integración, artefactos, paquete y NEXT;
- **17/17 Node** en tests del flujo contractual;
- sintaxis válida de `jury_view.js`, `build_jury.mjs` y `build_results.mjs`;
- CI remota pendiente del commit del candidato; el resultado local no se presenta como ejecución remota;
- runtime identificado y comprobado antes y después de regeneraciones;
- source health: 88/88 municipios, 148 registros sanitarios, 412/412 filas con `source_id` resoluble,
  0 nulos obligatorios, duplicados, coordenadas inválidas o referencias huérfanas, y 8/8 archivos de
  manifiesto íntegros, incluido el registro de capacidades;
- NEXT: 77/77 dentro de su alcance de prototipo offline con intents estructurados.

## Benchmark exhaustivo del core

El harness publicado conserva **72.797/72.797 checks**, **31.545/31.545 outputs numéricos trazables**,
**20/20 inyecciones controladas** y **1.000 llamadas sin deriva ni excepciones**. La trazabilidad se
define como output analítico numérico correcto con periodo, unidad, método y `source_id` resoluble.
No cubre todas las preguntas posibles. La ejecución exhaustiva actual es local; la prueba conversacional
del portal se registra aparte y no se sustituye por este benchmark determinista.

Severidad propia del benchmark: 0 Critical, 0 High, **1 Medium**, 0 Low. M-01 es un escenario extremo
de 20.155 caracteres que conserva 66 filas afectadas de 88; no se ha probado en portal. El release
completo conoce además M-02: un fallback del portal bajo fallo de runner confundió umbral y cuantil,
sin output de tool ni evidencia de fallo numérico del core.

## Evidencia visual y reproducibilidad

El gate de artefactos recalcula cada fila, porcentaje, distancia, fuente, geometría y escenario y
rechaza nueve mutaciones deliberadas. La revisión Chromium comprobó 7/4/2, mapa, trazabilidad, Aduna,
teclado y reflow hasta 390 px; no es una certificación WCAG.

La identidad SHA-256 del runtime es `441409ca68e3c5708eb9a1f66eef34c47bbfe558e3e801ab53e1605cf028528b`.
El paquete canónico contiene 15 archivos, ocupa **53.661 bytes** y tiene SHA-256
`fbca22e677f8b9b67967c4e103c9cc0a8fa4acab83abb2549fb5021a7111cf4b`. Dos builds consecutivos
producen el mismo hash bajo la misma toolchain. La identidad del paquete reproducible y la versión
privada del portal son controles distintos.

## Límites

Distancia geométrica no es tiempo de viaje; registro no es capacidad ni disponibilidad; coincidencia
no demuestra causalidad; escenario no es predicción. Las fuentes tienen periodos distintos y los
municipios pequeños exigen interpretar denominadores. En el smoke final de v4, P1 y P2 ejecutaron
`analizar_coincidencia` con resultados 7 y 4, y P3 rechazó predicción de citas/capacidad. La evidencia
guardada se etiqueta como local o histórica. Ninguna validación técnica autoriza publicar la Entrega.
