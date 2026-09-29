# Revisión de navegador · superficie vNext offline

Fecha: 29/09/2026. Entorno: navegador integrado de Codex, servidor HTTP local
en Windows, `resultados/vnext/index.html` generado desde evidencia fijada. Esta
revisión comprueba presentación e interacción básica; **no** es certificación
WCAG ni prueba con usuarios.

| Vista | Interacción y resultado |
|---|---|
| 1920 × 1080 | Primera vista y cinco botones visibles; `scrollWidth <= innerWidth`; sin solapamiento observado. |
| 1366 × 768 | Composición de dos columnas; `scrollWidth <= innerWidth`. |
| 1024 × 768 | Tarjetas y fuentes legibles; `scrollWidth <= innerWidth`. |
| 390 × 844 | Una columna, botones a ancho completo; `scrollWidth <= innerWidth`; sin recorte observado. |

Teclado probado: Tab desde el primer ejemplo al segundo, Shift+Tab de vuelta;
Enter activa el segundo ejemplo y el estado `unknown`; Space activa el caso
Segura de 180 min; Enter abre el bloque `<details>`. El foco visible se comprobó
en la vista de escritorio. Las tablas tienen contenedor de desplazamiento
horizontal propio.

Estados revisados visualmente: `ok` muestra total, tramos y componentes;
`no_feasible_journey` y `unknown` ocultan total, tramos y tabla. Fuente y
huellas se muestran en el detalle. No se probaron lectores de pantalla,
navegadores alternativos, zoom 125/150 %, ni el resultado de una conversación
LLM. Esos puntos siguen pendientes si se pretende una afirmación más amplia
de accesibilidad o compatibilidad.
