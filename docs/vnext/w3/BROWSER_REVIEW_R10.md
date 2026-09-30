# Browser review R10 — vista sanitaria

Entorno: Codex IAB / Chromium, Windows; servidor local 127.0.0.1:8772;
30/09/2026. Página `resultados/vnext/health.html`. No certificación WCAG.

El navegador conservó escala observada 1,10. El intento Ctrl+0 no la cambió;
se registran tamaños CSS **efectivos**, no se certifica 100%, 125% o 150%.

| Tamaño solicitado | CSS observado | Ancho página | Tabla visible/contenido | Resultado |
|---|---|---:|---:|---|
|1920×1080|1745×982|1732|1115/1115|PASS sin overflow de página|
|1366×768|1242×698|1228|1115/1115|PASS|
|1280×720|1164×654|1150|1060/1060|PASS|
|1024×768|931×698|917|828/828|PASS|
|390×844|355×767|341|274/387|PASS tabla con scroll interno|

Inspección visual móvil y DOM: botones apilados, límites legibles, tarjetas sin
superposición, campos sin overflow; no clipping observado. No mapa nuevo sin fuente.
Captura móvil en `resultados/vnext/r10/health_mobile.jpg`.

Teclado probado: Tab del escenario 09:30→09:45; Enter recalcula la presentación
al resultado guardado de 8.591 s; Shift+Tab vuelve a escenario anterior; Space
activa fecha no cubierta; Enter activa no pareja viable. Outline de foco observado
≈2,91 px. Enter abre Fuentes por función; Space abre Límites y parámetros.
El selector es una colección de botones con estado aria-pressed, no un select.

Importación por chooser real: `example_health_query.json` carga 8.591 s y oculta
comparación; JSON con clave duplicada rechazado; conserva título/total/estado de
comparación de la importación anterior. Ningún assistant inventado. Fuentes visibles
con href HTTPS fijados y texto legible; no se midió disponibilidad remota de cada URL.
Console error/warn: 0 observados. No auditoría exhaustiva de red o de lectores de pantalla.

Red team visual: punto oficial no implica puerta; parada no implica domicilio;
paseo es hipótesis, no accesibilidad universal; horarios aproximados no son puntualidad;
no pareja viable no es inexistencia de transporte; unknown muestra código real;
−2.100 s no es ahorro garantizado; snapshot 29/09 no cubre 30/09;
HTML offline no es conversación ni routing; entrada JSON compatible no es evidencia
verificada de su cálculo. Todos estos límites aparecen en la página.

Conocido: UX de datos importados puede conservar texto técnico en detalles de auditoría.
Matriz de zoom 125%/150% no ejecutada en R10; no se hereda una certificación previa.
