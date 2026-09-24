# Handoff Work 3 · integración

## Artefactos

- `scripts/build_results.mjs`: valida contrato y genera tres HTML autocontenidos.
- `scripts/enrich_work1_result.mjs`: añade geometría de Work 1 a un resultado del agente sin cambiar sus cifras.
- `scripts/run_local_analysis.mjs`: cálculo reproducible sobre las 88 filas de Work 1, marcado como herramienta local.
- `scripts/build_jury_demo.mjs`: cuatro ejecuciones reales locales y recorrido HTML en `resultados/demo_real/index.html`.
- `scripts/adapt_work2_envelope.mjs`: puente preparado para salida observada de Work 2.
- `scripts/adapt_agent_tool_result.mjs`: mapea el JSON real de `docs/RESULT_SCHEMA.md` y coteja distancias/porcentajes con Work 1.
- `scripts/build_work2_demo.mjs`: demo recomendada con herramientas reales de Work 2 en `resultados/demo_work2/index.html`.
- `resultados/demo.html`: explorador de prueba.
- `resultados/informe_principal.html`: informe reusable para una consulta.
- `resultados/scenario_comparison.html`: vista de base y escenario.
- `tests/fixtures/synthetic_agent_result.json`: **sintético**, jamás resultado territorial.
- `tests/e2e/contract_flow.test.mjs`: continuidad del contrato.
- `docs/`: schema, rúbrica, consultas, playbook, checklist y auditoría.

## Schema y fixtures

Contrato v1.0.0 en `docs/EXPECTED_RESULT_SCHEMA.md`. Todos los nombres `MUNICIPIO_TEST_*`, servicios, cifras y periodos del fixture son ficticios. Los HTML generados muestran la marca obligatoria. Una salida de Work 2 debe conservar su JSON original y convertirse mediante adaptador si difiere el contrato.

## Integración Work 1

La rama `work/data-qa-integration` (PR #4) endurece los datos del PR #1 con contrato 1.1.0, auditoría de 41 controles y manifiesto SHA-256. Esta integración incorpora ambos trabajos. `scripts/run_local_analysis.mjs` usa `municipality_code` como `unit_id`, convierte metros a kilómetros explícitamente `/1000` y conserva el periodo por fuente. La distancia es desde un punto representativo municipal; no es tiempo de viaje. El script de enriquecimiento añade contornos de las 2–5 unidades comparadas.

## Integración Work 2

Work 2 está en `work/agent-engine` (PR #3), incorporado en esta rama dependiente. Su contrato `docs/RESULT_SCHEMA.md` y tres ejemplos oficiales alimentan el adaptador real. Una cuarta salida con cuantil 0,85 se genera con `scripts/generate_work2_variation.py`. Las tools producen 7/88 y 2/88 destacados, con `output_ref` diferentes. `docs/WORK2_AGENT_ENVELOPE.md` describe la traza adicional que debe capturarse cuando el coordinador se pruebe en el portal.

## E2E

Ejecutar `node --test tests/e2e/*.test.mjs` y `python -m pytest -q` en un entorno con dependencias. Las suites comprueban el fixture, 88 filas reales, tool de Work 2, mapa, cambios de cuantil, escenario, errores y la cifra de Donostia contra la fuente Eustat original. Después repetir la cadena con una versión fija del coordinador en el portal.

## Demo y rúbrica

Secuencia de tres minutos y cuatro consultas en `docs/DEMO_QUERIES.md`. Cobertura y estado por criterio en `docs/RUBRIC_TRACEABILITY.md`; gaps y ensayo hostil en `docs/JURY_READINESS.md`.

## Riesgos priorizados

1. El PR de datos QA aún debe integrarse en la rama final; esta rama ya incluye su contenido y supera sus pruebas.
2. Falta probar la selección y observación de herramientas por el coordinador en una versión fija del portal; las tools ya se ejecutaron directamente.
3. Los HTML principales de `resultados/` son reales pero proceden de ejecución directa de tools, no del coordinador del portal. Usar `resultados/demo_work2/index.html` para la presentación.
4. El escenario de Work 2 es hipotético y solo cambia una distancia en el ejemplo de Beasain; no es predicción ni recomendación.
5. La versión del portal y el paquete de 24 MB requieren validación.

## Entrega

Completar ficha, subir datos/agente, crear versión, ejecutar prueba fija, seleccionar versión y track, revisar materiales y vista previa. La publicación final queda para autorización humana expresa. Seguir `docs/SUBMISSION_CHECKLIST.md`.
