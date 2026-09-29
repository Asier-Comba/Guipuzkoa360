# Revisión interna de interfaz R3 · 29/09/2026

**Entorno:** navegador integrado de Codex, servidor local de los archivos W3,
`resultados/vnext/index.html` generado desde `template.html` y evidencia W1
fijada. Revisión automatizada de UI; no prueba con usuarios ni certificación
WCAG. No se abrió ninguna versión del portal para ejecutar consultas.

| Prueba | Resultado observado |
|---|---|
| Escritorio 1280 px | Cinco ejemplos visibles; el primero muestra 8.411 s, ida, vuelta, componentes, márgenes 10/3, fuente y límites. Sin desbordamiento horizontal de documento (`scrollWidth=1265`, `innerWidth=1280`). |
| Móvil 390 × 844 | El texto de la ruta de importación producía `scrollWidth=394`; se corrigió con partición de `code`. Nueva medición `scrollWidth=375`, `innerWidth=390`. |
| Consulta externa al conjunto guardado | Se ejecutó el proveedor W1 HEAD `c68eb5c` con Zegama→Beasain, 09:30, 30 min y márgenes 15/8; el JSON importado mostró 10.511 s y los nuevos márgenes. SHA del output `f0ddb1a6dcabb1a2096084374d38e216df999389caaebc14cb327a945a1ab35e`. No es LLM ni live. |
| Teclado | `Enter` en el botón de 10:00 cambió `aria-pressed` y mostró 8.392 s. `Space` en Segura 180 min ocultó total/tramos y mostró no viable. `Enter` en fecha no validada mostró desconocido. `Enter` abrió el `details` de fuente. El foco permaneció en el control activado. |
| Trazabilidad y copia | La página etiqueta la evidencia como offline, `stop_only` no acredita paseo nulo, y −19 s no se presenta como ahorro empírico. Fuente SHA y solicitud estructurada son inspeccionables. |

**Límites de esta revisión:** no se midieron 1920/1366/1024, zoom 125/150,
lector de pantalla, contraste formal ni recorrido completo `Tab`/`Shift+Tab`.
La carga de JSON comprueba estructura y compatibilidad básica, pero un archivo
local no acredita por sí mismo la autenticidad del cálculo. La prueba de agente
real, paquete conjunto y destino sanitario siguen pendientes.
