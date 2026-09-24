# Handoff Work 3 · integración

## Artefactos

- `scripts/build_results.mjs`: valida contrato y genera tres HTML autocontenidos.
- `scripts/enrich_work1_result.mjs`: añade geometría de Work 1 a un resultado del agente sin cambiar sus cifras.
- `scripts/run_local_analysis.mjs`: cálculo reproducible sobre las 88 filas de Work 1, marcado como herramienta local.
- `scripts/build_jury_demo.mjs`: cuatro ejecuciones reales locales y recorrido HTML en `resultados/demo_real/index.html`.
- `scripts/adapt_work2_envelope.mjs`: puente preparado para salida observada de Work 2.
- `resultados/demo.html`: explorador de prueba.
- `resultados/informe_principal.html`: informe reusable para una consulta.
- `resultados/scenario_comparison.html`: vista de base y escenario.
- `tests/fixtures/synthetic_agent_result.json`: **sintético**, jamás resultado territorial.
- `tests/e2e/contract_flow.test.mjs`: continuidad del contrato.
- `docs/`: schema, rúbrica, consultas, playbook, checklist y auditoría.

## Schema y fixtures

Contrato v1.0.0 en `docs/EXPECTED_RESULT_SCHEMA.md`. Todos los nombres `MUNICIPIO_TEST_*`, servicios, cifras y periodos del fixture son ficticios. Los HTML generados muestran la marca obligatoria. Una salida de Work 2 debe conservar su JSON original y convertirse mediante adaptador si difiere el contrato.

## Integración Work 1

La rama `work/data-foundation` (PR #1) aporta 88 municipios, demografía, servicios y geometría, y es base de esta rama dependiente. `scripts/run_local_analysis.mjs` usa `municipality_code` como `unit_id`, convierte metros a kilómetros explícitamente `/1000` y conserva el periodo por fuente. La distancia es desde un punto representativo municipal; no es tiempo de viaje. El script de enriquecimiento añade contornos de las 2–5 unidades comparadas. Si Work 2 usa otra métrica, adaptar contrato y etiquetas antes de renderizar.

## Integración Work 2

Todavía no hay rama/PR de Work 2. Entregar pregunta, parámetros, versión fija, salida observada de tool, `data_refs`, resultado JSON y limitaciones. `docs/WORK2_AGENT_ENVELOPE.md` y `scripts/adapt_work2_envelope.mjs` fijan el puente. Dos preguntas distintas deben producir dos llamadas y `output_ref` diferentes. No basta con cambiar un selector en el HTML.

## E2E

Ejecutar `node --test tests/e2e/*.test.mjs`. La suite comprueba el fixture, las 88 filas reales, el mapa, cambios de umbral y la cifra de Donostia contra la fuente Eustat original. Después repetir la cadena con una versión fija del agente en el portal.

## Demo y rúbrica

Secuencia de tres minutos y cuatro consultas en `docs/DEMO_QUERIES.md`. Cobertura y estado por criterio en `docs/RUBRIC_TRACEABILITY.md`; gaps y ensayo hostil en `docs/JURY_READINESS.md`.

## Riesgos priorizados

1. Falta todavía el dataset real y su definición semántica.
2. Falta el agente y la prueba de una nueva llamada de herramienta.
3. Los HTML sintéticos de la raíz siguen siendo fixtures; usar `resultados/demo_real/index.html` para datos reales.
4. El escenario de servicio del fixture no es un contrafactual real; no presentarlo al jurado como tal.
5. La versión del portal y el paquete de 24 MB requieren validación.

## Entrega

Completar ficha, subir datos/agente, crear versión, ejecutar prueba fija, seleccionar versión y track, revisar materiales y vista previa. La publicación final queda para autorización humana expresa. Seguir `docs/SUBMISSION_CHECKLIST.md`.
