# QA de la vista offline R4 · 29/09/2026

Entorno: navegador integrado de Codex, servidor HTTP local en
`127.0.0.1:8771`, `resultados/vnext/index.html`. Son observaciones de la
vista local; no se escribió ni probó el portal del hackathon.

| Prueba | Resultado observado |
|---|---|
| 390, 768, 1024 y 1366 px de ancho, 768 px de alto salvo 390×844 | `documentElement.scrollWidth` igual a `clientWidth`; botones de ejemplos con ancho ≥44 px. No se observó overflow horizontal de página. |
| Selección por clic y Enter | Cambiar de 09:30 a 10:00 actualizó total de 8411 s a 8392 s y los viajes. |
| `details` de fuentes | Se abrió y mostró emisor, feed, versión, SHA-256, snapshot y enlace HTTPS oficial. |
| Fuente hostil `javascript:void(0)` delante de la oficial | Rechazada sin renderizar el enlace; el resultado previo permaneció. |
| Importación local válida repetida | Mostró 10511 s, rotuló procedencia no verificada y ocultó comparación predefinida ajena. |
| Fuentes duplicadas en importación posterior | Rechazadas; permaneció el resultado válido anterior de 10511 s. |

Los tests de contrato cubren además tipos, límites, fuente completa,
parámetros efectivos, estado y estructura de legs/componentes. La
comprobación de ancho es geométrica; no certifica lectura, contraste ni WCAG.
No se probó aquí una sesión completa con lector de pantalla, navegación
Shift+Tab/Space, tráfico de red ni todos los tamaños/zooms. La interfaz
actual, fijada a W1 0.1.0, presenta `departure_time` y `arrival_time` para ida y
vuelta, cita/duración solicitadas, desglose y fuentes. Esa versión no expone
holgura de vuelta. W1 0.2.0 sí expone `return_slack_s`, preparado aparte en
`w1_r4_product_components.json`; todavía no se muestra en este HTML, que
conserva su etiqueta y pin histórico. Ninguna versión acredita rutas puerta a
puerta. El estado de error/unknown se explica desde el error
observado, sin convertir ausencia de datos en cero.
