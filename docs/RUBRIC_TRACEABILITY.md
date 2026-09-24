# Matriz de trazabilidad de la rúbrica

Pesos oficiales según las bases recogidas el 17/09/2026 en `contexto-principal.md` §11. Estado al 24/09/2026. “Implementado en fixture” no equivale a evidencia de datos reales ni de agente operativo.

| Criterio | Peso | Qué exige | Funcionalidad que lo demuestra | Archivo/código | Prueba que lo verifica | Demo que lo enseña | Estado |
|---|---:|---|---|---|---|---|---|
| Utilidad urbana | 25 % | Pregunta relevante, destinatario y uso claros | Coincidencia, comparación y escenario de atención primaria | `resultados/demo_work2/index.html`, `docs/README_DEMO_JURADO.md` | Revisión de ficha y prueba con destinatario | Actos 1–2 | Demo real integrada; ficha del portal pendiente |
| Análisis, fuentes y trazabilidad | 25 % | Métodos justificados y cifras rastreables | Fuente, periodo, unidad, fila y hash por resultado | `scripts/adapt_agent_tool_result.mjs`, `scripts/build_results.mjs` | E2E Work 2↔Work 1 y cifra Donostia contra original | Actos 2–4 | Datos y tools reales verificados |
| Funcionamiento y herramientas | 25 % | Herramienta ejecutada y respuesta basada en su salida | Dos ejecuciones de `analizar_coincidencia` con cuantiles y refs distintos | `docs/examples/`, `scripts/generate_work2_variation.py`, `scripts/adapt_agent_tool_result.mjs` | Suites Node y Python; prueba del coordinador pendiente | Actos 2–3 | Tools reales; coordinador en portal pendiente |
| Claridad de respuestas y artefactos | 15 % | Explicaciones, unidades, mapas o informes interpretables | Mapa GeoJSON, barras, tabla, detalle e informe | `resultados/demo_work2/*/*.html` | Inspección estructural automatizada; revisión visual en portal pendiente | Actos 2–4 | Implementado con resultados reales |
| Fiabilidad, límites y supervisión | 10 % | Ausencias, incertidumbre, hipótesis separada y juicio humano | `municipality_not_found`, periodos separados, escenario etiquetado | `docs/examples/error_unknown_municipality.json`, `resultados/demo_work2/escenario` | Tests de error, cifras adulteradas y diferencias de escenario | Actos 4–5 | Tool verificada; respuesta metodológica del coordinador pendiente |

No se asigna puntuación interna. Antes de entregar queda crear/probar una versión fija del coordinador, comprobar su respuesta al límite metodológico y revisar los HTML visualmente en el portal. La cifra de Donostia ya se contrastó con la fila original de Eustat.
