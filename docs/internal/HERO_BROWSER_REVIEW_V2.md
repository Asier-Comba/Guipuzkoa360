# Hero browser review V2

Fecha: 2026-09-25. Entorno: navegador integrado de Codex basado en Chromium sobre Windows, páginas servidas desde `127.0.0.1:8766`, escala del sistema observada `devicePixelRatio=1.1`.

Esta revisión comprueba la presentación y las interacciones enumeradas. No es una certificación WCAG ni un test con usuarios.

## Matriz de navegador

| Viewport CSS | Zoom / reflow | Interacción probada | Resultado | Incidencia conocida |
|---|---:|---|---|---|
| 1920 × 1080 | 100 % | Carga de las cuatro páginas, hero, mapa, tablas y trazabilidad | PASS: sin desbordamiento horizontal de página, texto cortado ni tarjetas superpuestas | Las tablas anchas usan scroll interno intencional |
| 1366 × 768 | 100 % | Carga de las cuatro páginas y navegación | PASS | Ninguna observada |
| 1280 × 720 | 100 % | Carga de las cuatro páginas y navegación | PASS | Ninguna observada |
| 1024 × 768 | 100 % | Reflow, mapa, controles, detalles y tablas | PASS | Las tablas anchas usan scroll interno intencional |
| 390 × 844 | 100 % | Orden de lectura, 7/4/2, mapa, selector municipal, trazabilidad y tablas | PASS: sin scroll horizontal de página; mapa, etiquetas y controles legibles | La tabla requiere scroll interno |
| 1093 × 614 | Equivalente de reflow a 125 % sobre 1366 × 768 | Las cuatro páginas | PASS | El entorno no expuso zoom nativo automatizable; se verificó el viewport CSS equivalente |
| 911 × 512 | Equivalente de reflow a 150 % sobre 1366 × 768 | Las cuatro páginas | PASS | El entorno no expuso zoom nativo automatizable; se verificó el viewport CSS equivalente |

En todas las combinaciones se comprobó `clientWidth == scrollWidth`, un único `h1` visible y ausencia de texto `undefined` o `NaN`.

## Teclado

| Control | Prueba | Resultado |
|---|---|---|
| Skip link | `Tab` y `Enter` | Lleva a `#main` |
| Navegación | `Tab` y `Shift+Tab` | El foco recorre los controles en ambos sentidos |
| Casos 7/4/2 | `Enter` y `Space` | Recalcula la vista guardada; se verificó 7 → 4 y su nuevo corte |
| Selector municipal | Teclas de navegación, `End` y `Enter` | Seleccionó Zumarraga y actualizó la alternativa textual |
| Desplegables `details` | `Space` | Expande y contrae el contenido; se verificó el bloque 7 → 4 → 2 |
| Foco | Recorrido por controles | El contorno de foco permanece visible |

## Red team visual

| Lectura errónea intentada | Copy que la impide | Resultado |
|---|---|---|
| Distancia = tiempo de viaje | «Distancia geométrica» y «Sin rutas, tiempo de viaje…» | Cerrada |
| 0 registros = no hay médicos | El escenario explica que registros y profesionales no son equivalentes | Cerrada |
| Destacado = prioridad | «No es un ranking de necesidad» y orden alfabético | Cerrada |
| 2 km = corte del cuantil de distancia | Los dos cortes del cuantil aparecen juntos; el umbral se etiqueta como referencia adicional | Cerrada |
| Escenario = recomendación | «No es una predicción ni una recomendación de ubicación» | Cerrada |
| 148 registros = capacidad | «Registros públicos; no capacidad asistencial» | Cerrada |
| 75+ = campo directo de la fuente | Se declara que se deriva de nacidos hasta 1949 para 01/01/2025 | Cerrada |
| NEXT = producción activa | «OFFLINE · NO ACTIVO EN EL PORTAL» y snapshot histórico pendiente de reconciliación | Cerrada |
| Mejora = autoedición | «No se autoedita en producción» y aprobación humana explícita | Cerrada |

## Dictamen

Hero y superficies secundarias: **PASS con límites declarados**. La única carencia de esta matriz es que el navegador de automatización no permitió fijar zoom nativo; se comprobó el mismo reflow con viewports CSS equivalentes. No se observó un defecto visual que bloquee la demostración.
