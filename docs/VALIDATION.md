# Validación de GIPUZKOA 360

Esta síntesis separa la suite integrada, el benchmark exhaustivo del core, la evidencia visual y la
conversación privada. Sus denominadores no se suman: un test o check de propiedad no equivale a una
conversación ni demuestra impacto social.

## Suite integrada del candidato

Sobre `final/gipuzkoa360-ultimate`:

- **263/263 tests Python** de datos, contratos, runtime, integración, artefactos, paquete y NEXT;
- **17/17 Node** en tests del flujo contractual;
- sintaxis válida de `jury_view.js`, `build_jury.mjs` y `build_results.mjs`;
- fast CI en Ubuntu 24.04 y Windows latest: PASS en el pre-cierre; el head documental final se valida
  otra vez antes de abrir la PR;
- runtime congelado comprobado antes y después de regeneraciones;
- source health: 88/88 municipios, 148 registros sanitarios, 412/412 filas con `source_id` resoluble,
  0 nulos obligatorios, duplicados, coordenadas inválidas o referencias huérfanas, y 7/7 archivos de
  manifiesto íntegros;
- NEXT: 77/77 dentro de su alcance de prototipo offline con intents estructurados.

## Benchmark exhaustivo del core

El harness publicado conserva **72.673/72.673 checks**, **31.545/31.545 outputs numéricos trazables**,
**20/20 inyecciones controladas** y **1.000 llamadas sin deriva ni excepciones**. La trazabilidad se
define como output analítico numérico correcto con periodo, unidad, método y `source_id` resoluble.
No cubre todas las preguntas posibles. El benchmark se vuelve a ejecutar por GitHub Actions sobre el
SHA final exacto; su run se registra en la PR para no cambiar ese SHA.

Severidad propia del benchmark: 0 Critical, 0 High, **1 Medium**, 0 Low. M-01 es un escenario extremo
de 20.155 caracteres que conserva 66 filas afectadas de 88; no se ha probado en portal. El release
completo conoce además M-02: un fallback del portal bajo fallo de runner confundió umbral y cuantil,
sin output de tool ni evidencia de fallo numérico del core.

## Evidencia visual y reproducibilidad

El gate de artefactos recalcula cada fila, porcentaje, distancia, fuente, geometría y escenario y
rechaza nueve mutaciones deliberadas. La revisión Chromium comprobó 7/4/2, mapa, trazabilidad, Aduna,
teclado y reflow hasta 390 px; no es una certificación WCAG.

El runtime congelado es `195b4980fa5998b096c308296a55e452380b0371`. El paquete canónico contiene
14 archivos, ocupa **48.338 bytes** y tiene SHA-256
`2808110d14e0bc30a53018cab1ec39b926e1e6ca1f1be19f0b2c9cf21106680a`. Dos builds consecutivos
producen el mismo hash bajo la misma toolchain. La identidad del paquete reproducible y la versión
privada del portal son controles distintos.

## Límites

Distancia geométrica no es tiempo de viaje; registro no es capacidad ni disponibilidad; coincidencia
no demuestra causalidad; escenario no es predicción. Las fuentes tienen periodos distintos y los
municipios pequeños exigen interpretar denominadores. En el smoke final de v4, P1 y P2 ejecutaron
`analizar_coincidencia` con resultados 7 y 4, y P3 rechazó predicción de citas/capacidad. La evidencia
guardada se etiqueta como local o histórica. Ninguna validación técnica autoriza publicar la Entrega.
