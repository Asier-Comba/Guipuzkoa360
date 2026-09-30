# Producto W3 R3 · contrato visual y límite sanitario

**PRODUCT_CONTRACT_READY:** interfaz offline de W1 0.1.0 y mapeo del sobre W2
1.0.0 revisados por SHA. **PRODUCT_HEALTH_GO=NO:** W1 R2 llega a paradas del
centro de Beasain, no al Ambulatorio, y W2 R2 no empaqueta la movilidad. No se
etiqueta ninguna parte como agente live. No se dibuja mapa de ruta sin
geometría observada.

| Concepto visual | Procedencia exigida | Comportamiento seguro |
|---|---|---|
| Origen/destino/fecha/cita/duración/márgenes | `normalized_request` W1 y `normalized_input.arguments` W2 | Mostrar códigos y nombres del catálogo sin convertir paradas en domicilios o centro asignado. |
| Ida, vuelta, total y componentes `s` | `status=ok`, `itinerary`, `components_s` W1; claims W2 con `evidence_path` | Mostrar segundos exactos y presentación h/min/s. La UI no elige rutas ni añade márgenes al total. |
| Fuente y fecha | `sources` W1; `claims[].source_ids`, `period`, `versions` W2 | Cada cifra afirmada debe enlazarse a una salida de esa ejecución. Un catálogo disponible no prueba una cifra no atribuida. |
| No viable | W1 `no_feasible_journey` | Solo «sin ida y vuelta viable» bajo fecha, paradas y búsqueda directa. Sin cifra total o vuelta ficticia. |
| Desconocido | W1 `unknown`; adapter W2 R2 lo transporta como `error` con origen `data` y conserva el raw | Preferir el estado bruto W1 `unknown` para copy; nunca «no existe autobús». |
| No soportado/error | W1 `unsupported`/`error`; W2 `unsupported`/`error` | Abstención y próxima acción segura. Sin atribuir HTTP/504 cuando no hay traza de transporte. |
| Escenario comparado | `compare_visits` W1 y requests exactos | Mostrar parámetros conservados/cambiados, ambos estados y delta **solo cuando ambos son comparables y `ok`**. |

W2 R2 expone ocho herramientas territoriales y `consultar_capacidades`; su
`mobility_adapter.py` consume `plan_visit` y `compare_visits` W1 en pruebas
aisladas, pero su ZIP no incluye proveedor ni snapshot. El contrato Evidence
v1.0.0 exige `request_id`, `normalized_input`, `execution`, `status`, `claims`,
`method`, `assumptions`, `limitations`, `error`, `versions` y `raw_result_json`.
Una vista W3 que consuma ese sobre debe validar el binding request→tool→raw,
la fuente por claim, unidad, periodo y denominador antes de mostrar cifras.
No debe marcar como conversación un `execute()` directo.

**Hallazgo W3 R3 abierto en W2:** en `f4615b36`, `analizar_coincidencia`
devuelve `highlighted_count=7` sobre `joined_rows=88` municipios, pero el
claim asigna `unit="registros"`. Se notificó en [PR #17](https://github.com/Asier-Comba/Guipuzkoa360/pull/17#issuecomment-5895766224).
W3 no lo corrige en código ajeno; la vista no debe publicar ese claim como
«7 registros» ni inferir que representa centros o capacidad.

Los cinco botones de [`index.html`](../../../resultados/vnext/index.html)
siguen siendo outputs guardados del proveedor W1. Para una pregunta fuera de
esas tarjetas, W3 añade `query_w1_offline.py`, que ejecuta **el mismo proveedor
fijado** y exporta un JSON importable. Esto permite variar campos permitidos
sin inventar resultados. Sigue siendo un cálculo offline y no prueba el
coordinador W2.

El caso de −19 s permanece como diferencia técnica exacta del horario
programado. La página advierte que no es ahorro empírico ni precisión
garantizada. Los márgenes son restricciones de selección, no minutos de espera
sumados dos veces. La consulta de 30 min es un supuesto humano, no una
duración certificada por GTFS. El paseo `stop_only=0` es cero **modelado**,
no acceso puerta a puerta conocido.

Cuando W1 publique `HEALTH_DESTINATION_GO`, se requerirá identidad de centro,
fuente, fecha, paseo y comienzo/fin de intervalo antes de añadir una timeline
sanitaria o una matriz cita × duración. Si el walking sigue bloqueado,
`PRODUCT_HEALTH_GO` permanece `NO`.
