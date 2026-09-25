# HUGO · Jury handoff

`BASE_SHA`: `46c1a48f63c307654f45fcb5c18883f264b660ed`

`HEAD_SHA`: `8aad017a1d3aa9302d0c7171519d8f61663ae6bb` — HEAD de producto probado. Este handoff se añade en un commit posterior solo documental; la respuesta final registra el HEAD remoto definitivo.

`COMMITS`:

1. `6e8a7ae` — unificación de experiencia y KPIs.
2. `9639e8b` — evidencia reproducible y product tests.
3. `09478c8` — pitches, demo y 44 Q&A.
4. `36d1842` — etiquetado explícito del prototipo y mejoras responsive.
5. `8aad017` — revisión final de navegador y frontera del snapshot NEXT.

`RUNTIME_CHANGED:NO` — `portal/main.py` y `portal/tools.py` no difieren de la base.

`PYTHON_TESTS`: PASS · 183/183 · `python -m pytest -q` ejecutado una vez sobre el HEAD de producto.

`NODE_TESTS`: PASS · 17/17 · `node --test tests/e2e/contract_flow.test.mjs` ejecutado una vez.

`HERO_STATUS`: PASS · primera vista con destinatario, pregunta, 7/88, mapa, fuentes/fechas, límite principal, método y 7 operaciones. Sin rediseño en esta ronda.

`CONTROL_CENTER_STATUS`: PASS · denominadores explícitos: 72.673 checks, 31.545 outputs auditados, 20 inyecciones, 1.000 llamadas sostenidas. Ninguna cifra se presenta como cobertura universal.

`NEXT_SNAPSHOT_SOURCE`: `171b6cb2a366f18509d3432d87f46fa21ea4aefa:analisis/next/quality_kpis.json`, conservado como snapshot histórico. Último commit técnico observado de Work 1: `448009bd97c13f28b85676489ada2a201c362322`.

`NEXT_RECONCILIATION`: `NEXT_RECONCILIATION_REQUIRED=YES`. En `final/work1-engineering-master` no existen todavía `analisis/next/product_snapshot.json`, `docs/internal/WORK1_TECHNICAL_HANDOFF.md` ni `PORTAL_SMOKE_REFRESH.md`. La UI dice que 171b fue superado por trabajo técnico posterior y que la reconciliación final está pendiente.

`THRESHOLD_QUANTILE_COPY`: PASS · el cuantil determina los cortes de envejecimiento y distancia que seleccionan destacados; el umbral en km controla `within_threshold` como referencia adicional y no decide esa selección.

`BROWSER_MATRIX`: PASS en 1920×1080, 1366×768, 1280×720, 1024×768 y 390×844. PASS de reflow equivalente a zoom 125 % (1093×614) y 150 % (911×512). Sin overflow horizontal de página, clipping ni solapes; tablas con scroll interno. El entorno no expuso zoom nativo automatizable. Detalle en `docs/internal/HERO_BROWSER_REVIEW_V2.md`.

`KEYBOARD`: PASS · `Tab`, `Shift+Tab`, `Enter`, `Space`, skip link, navegación, casos 7/4/2, selector municipal y `details`; foco visible. No constituye certificación WCAG.

`VISUAL_REDTEAM`: PASS · copy revisada contra nueve lecturas erróneas: distancia como tiempo; cero registros como cero médicos; destacados como prioridad; 2 km como corte del cuantil; escenario como recomendación; 148 registros como capacidad; 75+ como campo directo; NEXT como producción; mejora como autoedición.

`README`: PASS · destinatario, siete herramientas, demo, datos, limitaciones y equipo visibles; sin ampliar el documento.

`ONE_PAGER`: PASS · cifras reconciliadas con la evidencia final, futuro acotado y riesgo conocido visible.

`PRODUCT_GUIDE`: PASS · NEXT, actualización de fuentes y diferencia umbral/cuantil consistentes.

`JURY_QA_COUNT`: 44 · auditadas sin aumentar volumen; cubren las objeciones críticas solicitadas.

`3MIN_READY`: YES · tool antes del minuto 1; seguimiento en minuto 2; fuente, límite y revisión humana en minuto 3. Máximo dos consultas live y fallback guardado etiquetado.

`6MIN_READY`: YES · añade validación, futuro acotado, q0,85, comparación territorial, ficha de fuente y rechazo fuera de alcance.

`SCREENSHOT_PLAN`: exactamente cinco: (1) tool call real o histórica etiquetada, (2) hero 7/88, (3) seguimiento 4, (4) escenario Aduna, (5) trazabilidad/fiabilidad con frontera futura. No se declaran capturas inexistentes.

`CRITICAL_OPEN`: 0.

`HIGH_OPEN`: 0.

`MEDIUM_OPEN`: 1 hallazgo del benchmark: salida extrema de 20.155 caracteres no demostrada en portal. La reconciliación NEXT se registra aparte como dependencia, sin asignarle severidad del benchmark.

`KNOWN_PORTAL_RISK`: último smoke bloqueado por infraestructura/runner ocupado. No existe `PORTAL_SMOKE_REFRESH.md` final. La posible confusión textual entre threshold 2 km y distance quantile cut no se atribuye al core sin tool output; las superficies de producto ya explican ambos conceptos correctamente.

`FILES_FOR_WORK1`: `resultados/evidencia/next_prototype.json`, `resultados/evidencia/product_evidence.json`, `resultados/control_center.html`, `docs/PRODUCT_GUIDE.md`, `docs/JURY_QA.md`, `docs/internal/HERO_BROWSER_REVIEW_V2.md` y este handoff.

`PRODUCT_GO:YES` — demo y material de jurado listos. Mantener la etiqueta histórica de NEXT hasta recibir un handoff técnico final y regenerar la evidencia.
