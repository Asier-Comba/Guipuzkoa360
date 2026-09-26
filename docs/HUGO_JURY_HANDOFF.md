# HUGO · Jury handoff

`BASE_SHA`: `46c1a48f63c307654f45fcb5c18883f264b660ed`

`HEAD_SHA`: `26642ee8eff21360990d2e01fdf6d45b844e3640` — HEAD de producto probado. Este handoff se añade en un commit posterior solo documental; la respuesta final registra el HEAD remoto definitivo.

`COMMITS`:

1. `6e8a7ae` — unificación de experiencia y KPIs.
2. `9639e8b` — evidencia reproducible y product tests.
3. `09478c8` — pitches, demo y 44 Q&A.
4. `36d1842` — etiquetado explícito del prototipo y mejoras responsive.
5. `8aad017` — revisión final de navegador y frontera del snapshot NEXT.
6. `25f629d` — primer handoff para jurado.
7. `6319711` — frontera NEXT localizada.
8. `fdf7477` — reconciliación selectiva del snapshot final de Work 1 y su contrato de producto.
9. `23a38a6` — cierre documental de los dos riesgos Medium.
10. `26642ee` — prueba integral del snapshot y copy de portal/escenario.

`RUNTIME_CHANGED:NO` — los 12 archivos congelados, incluidos `portal/main.py`, `portal/tools.py`, contexto y datos, coinciden byte a byte con `195b4980fa5998b096c308296a55e452380b0371`.

`PYTHON_TESTS`: PASS · 184/184 · `python -m pytest -o addopts= -q` sobre el HEAD de producto.

`NODE_TESTS`: PASS · 17/17 · `node --test tests/e2e/contract_flow.test.mjs` ejecutado una vez.

`PRODUCT_TESTS`: PASS · 32/32 · `python -m pytest tests/test_product_jury.py -o addopts= -q`; incluidos también en los 184 tests Python. La prueba nueva coteja todos los campos del snapshot final publicado mediante su hash canónico.

`FULL_VALIDATION`: 72.673/72.673 checks, 31.545/31.545 salidas numéricas trazables, 20/20 inyecciones y 1.000 llamadas sostenidas según la evidencia publicada por Work 1; el benchmark exhaustivo no se volvió a ejecutar en esta pasada. Los tres casos canónicos y los nueve ataques al artefacto sí se recalcularon y pasaron ahora.

`GITHUB_RECONCILED`: Work 1 `929186f`, Work 2 `70c0e06`, integración `46c1a48` y Work 3 revisados tras fetch/prune; no aparecieron commits posteriores en las ramas finales. PR #9 sigue abierta. El gate de Work 2 ya forma parte de la base común; su antiguo handoff describe incidencias resueltas y se contrasta con `docs/RC2_FINAL_STATUS.md`.

`SOURCE_HEALTH`: se revisó el informe final de Work 1: 412/412 filas de tablas con `source_id` resoluble, 88/88 municipios y 148 registros, con 627 días de separación máxima entre fechas de referencia. Es una comprobación offline publicada por Work 1, distinta de las 31.545 salidas numéricas del benchmark; no se volvió a ejecutar en esta rama.

`HERO_STATUS`: PASS · primera vista con destinatario, pregunta, 7/88, mapa, fuentes/fechas, límite principal, método y 7 operaciones. La Q&A ya exige ver la llamada nueva antes de afirmar una ejecución en directo.

`CONTROL_CENTER_STATUS`: PASS · denominadores explícitos: 72.673 checks, 31.545 outputs auditados, 20 inyecciones, 1.000 llamadas sostenidas. M-01 se identifica como hallazgo del benchmark y M-02 como riesgo conversacional del portal; el KPI Medium=1 conserva su denominador original.

`NEXT_SNAPSHOT_SOURCE`: snapshot final `fddcf05217959ddc347f5d1a1ee9f35245ea9806:analisis/next/product_snapshot.json`, con evidencia `eae3b7026a8608946d31c718fabc10111c3fa16e:analisis/next/quality_kpis.json` y handoff `929186fcb2a04429ee5a68b6081948902668b917`.

`NEXT_RECONCILIATION`: `NEXT_RECONCILIATION_REQUIRED=NO`. Los campos del snapshot final de Work 1 coinciden exactamente; la copia local añade solo commit/ruta de procedencia y estado de reconciliación. El producto declara 77/77 tests acotados y mantiene el prototipo offline, aislado del portal.

`THRESHOLD_QUANTILE_COPY`: PASS · el cuantil determina los cortes de envejecimiento y distancia que seleccionan destacados; el umbral en km controla `within_threshold` como referencia adicional y no decide esa selección.

`BROWSER_MATRIX`: PASS en 1920×1080, 1366×768, 1280×720, 1024×768 y 390×844. En esta pasada se volvieron a probar las cuatro vistas en 1920, 1366, 1024 y 390 px y el reflow equivalente a zoom 125 % (1093×614) y 150 % (911×512). Sin overflow horizontal de página; tablas con scroll interno. El entorno no expuso zoom nativo automatizable. Detalle en `docs/internal/HERO_BROWSER_REVIEW_V2.md`.

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

`MEDIUM_OPEN`: 2 gestionados. M-01 técnico: salida extrema de 20.155 caracteres no demostrada en portal; decisión A, documentar y conservarla íntegra. Aduna usa 3.447 caracteres y dos filas afectadas. M-02 conversacional: la explicación tras el fallo del runner confundió umbral y cuantil sin resultado analítico; no hay evidencia de fallo del core.

`KNOWN_PORTAL_RISK`: `PORTAL_SMOKE_REFRESH.md` confirma `INFRASTRUCTURE_BLOCKED`: hubo tool call, runner ocupado y ningún output analítico. El texto de fallback confundió threshold 2 km con distance quantile cut. No se atribuye al core; demo, Q&A, guía y control center explican ambos conceptos correctamente.

`FILES_FOR_INTEGRATOR`: `resultados/evidencia/next_prototype.json`, `resultados/evidencia/product_evidence.json`, las cuatro vistas en `resultados/`, `scripts/release/build_jury_data.py`, `scripts/build_jury.mjs`, `scripts/jury_view.js`, `tests/test_product_jury.py`, `docs/DEMO.md`, `docs/JURY_QA.md`, `docs/internal/HERO_BROWSER_REVIEW_V2.md` y este handoff.

`PRODUCT_GO:YES` — demo y material de jurado listos; NEXT reconciliado con el handoff técnico final. No se copiaron CI, source health ni NEXT ejecutable de Work 1 a esta rama: pertenecen a su integración y sus resultados se citan con alcance. Una persona debe integrar Work 1 y Work 3 en el orden documentado, ejecutar gates y CI Linux/Windows sobre el commit combinado y aprobar merge/publicación por separado. PR #9 permanece abierto e intacto.
