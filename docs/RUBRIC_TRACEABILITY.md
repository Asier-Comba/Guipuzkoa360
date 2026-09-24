# Matriz de trazabilidad de la rúbrica

Pesos oficiales según las bases recogidas el 17/09/2026 en `contexto-principal.md` §11. Estado al 24/09/2026. “Implementado en fixture” no equivale a evidencia de datos reales ni de agente operativo.

| Criterio | Peso | Qué exige | Funcionalidad que lo demuestra | Archivo/código | Prueba que lo verifica | Demo que lo enseña | Estado |
|---|---:|---|---|---|---|---|---|
| Utilidad urbana | 25 % | Pregunta relevante, destinatario y uso claros | Pregunta de atención primaria, comparación y variación | `resultados/demo_real/index.html`, `docs/README_DEMO_JURADO.md` | Revisión de ficha y prueba con destinatario | Actos 1–2 | Demo real local; ficha del portal pendiente |
| Análisis, fuentes y trazabilidad | 25 % | Métodos justificados y cifras rastreables | Fuente, periodo, unidad, fila y hash en cada vista | `scripts/run_local_analysis.mjs`, `scripts/build_results.mjs` | `node --test tests/e2e/*.test.mjs`; Donostia contra fuente original | Actos 2, 4 | Datos reales y cálculo local verificados |
| Funcionamiento y herramientas | 25 % | Herramienta ejecutada y respuesta basada en su salida | Dos ejecuciones locales con argumentos y `result_ref` distintos; envelope para agente | `scripts/run_local_analysis.mjs`, `scripts/adapt_work2_envelope.mjs` | E2E local pasa; versión fija del agente pendiente | Actos 2–3 | Tool local real; agente no integrado |
| Claridad de respuestas y artefactos | 15 % | Explicaciones, unidades, mapas o informes interpretables | Mapa GeoJSON, barras, tabla, detalle e informe | `resultados/demo_real/*/*.html` | Inspección estructural automatizada; revisión visual en portal pendiente | Actos 2–4 | Implementado con datos reales |
| Fiabilidad, límites y supervisión | 10 % | Ausencias, incertidumbre, hipótesis separada y juicio humano | Caso 0/88, fechas separadas, advertencias de distancia | `resultados/demo_real/limite`, `docs/README_DEMO_JURADO.md` | Tests de umbral extremo, nulo y códigos duplicados | Acto 5 | Local verificado; respuesta del agente pendiente |

No se asigna puntuación interna. Antes de entregar queda integrar la versión fija del agente, comprobar su respuesta a la pregunta límite y probarla en el portal. La cifra de Donostia ya se contrastó con la fila original de Eustat.
