# Matriz de trazabilidad de la rúbrica

Pesos oficiales según las bases recogidas el 17/09/2026 en `contexto-principal.md` §11. Estado al 24/09/2026. “Implementado en fixture” no equivale a evidencia de datos reales ni de agente operativo.

| Criterio | Peso | Qué exige | Funcionalidad que lo demuestra | Archivo/código | Prueba que lo verifica | Demo que lo enseña | Estado |
|---|---:|---|---|---|---|---|---|
| Utilidad urbana | 25 % | Pregunta relevante, destinatario y uso claros | Pregunta, respuesta breve y comparación de unidades | `resultados/demo.html`, `docs/DEMO_QUERIES.md` | Revisión de ficha y prueba con destinatario | Actos 1–2 | Fixture; falta validar utilidad con datos reales |
| Análisis, fuentes y trazabilidad | 25 % | Métodos justificados y cifras rastreables | Fuente, periodo, unidad, fórmula y traza en cada vista | `scripts/build_results.mjs`, `docs/EXPECTED_RESULT_SCHEMA.md` | `node --test tests/e2e/contract_flow.test.mjs`; contraste manual pendiente | Actos 2, 4 | Contrato probado; fuentes reales pendientes |
| Funcionamiento y herramientas | 25 % | Herramienta ejecutada y respuesta basada en su salida | Panel de traza y contrato de llamada | `trace` del JSON, `docs/INTEGRATION_PLAYBOOK.md` | E2E final con agente y versión fija pendiente | Actos 2–3 | Mock trazable; agente real pendiente |
| Claridad de respuestas y artefactos | 15 % | Explicaciones, unidades, mapas o informes interpretables | Mapa esquemático, barras, tabla, informe y escenario | `resultados/*.html` | Inspección visual y prueba de navegación | Actos 2–5 | Implementado en fixture |
| Fiabilidad, límites y supervisión | 10 % | Ausencias, incertidumbre, hipótesis separada y juicio humano | Banner sintético, bloque de límites, base vs escenario | `scripts/build_results.mjs`, `resultados/*.html` | Test de marca sintética y ensayo de pregunta límite | Acto 6 | Implementado en fixture; comprobar agente real |

No se asigna puntuación interna. La prioridad antes de entrega es ejecutar una versión fija con datos reales, comprobar una cifra manualmente y sustituir la traza sintética por la traza de ejecución.
