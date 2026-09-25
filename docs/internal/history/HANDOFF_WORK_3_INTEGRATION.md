# HISTÓRICO — Handoff Work 3 · integración

Registro conservado del 24/09/2026; no es la guía ni el estado actual del release.
Consulte [validación vigente](../../VALIDATION.md) y [plan de integración](../release/INTEGRATION_PLAN.md).
Los estados pendientes, cifras de paquete y mediciones siguientes describen su ejecución original;
no deben trasladarse como hechos actuales sin contrastarlos con la auditoría vigente.

## Artefactos

- `scripts/build_results.mjs`: valida contrato y genera tres HTML autocontenidos.
- `scripts/enrich_work1_result.mjs`: añade geometría de Work 1 a un resultado del agente sin cambiar sus cifras.
- `resultados/demo.html`: explorador de prueba.
- `resultados/informe_principal.html`: informe reusable para una consulta.
- `resultados/scenario_comparison.html`: vista de base y escenario.
- `tests/fixtures/synthetic_agent_result.json`: **sintético**, jamás resultado territorial.
- `tests/e2e/contract_flow.test.mjs`: continuidad del contrato.
- `docs/`: schema, rúbrica, consultas, playbook, checklist y auditoría.

## Schema y fixtures

Contrato v1.0.0 en `docs/EXPECTED_RESULT_SCHEMA.md`. Todos los nombres `MUNICIPIO_TEST_*`, servicios, cifras y periodos del fixture son ficticios. Los HTML generados muestran la marca obligatoria. Una salida de Work 2 debe conservar su JSON original y convertirse mediante adaptador si difiere el contrato.

## Integración Work 1

La rama `work/data-qa-integration` sustituye funcionalmente al PR #1 bloqueado y aporta 88 municipios, demografía, servicios, geometría, contrato 1.1.0 y QA exhaustivo. Usar `municipality_code` como `unit_id`, metros a kilómetros solo con conversión explícita `/1000`, y periodo por fuente. La distancia es desde un punto representativo municipal; no es tiempo de viaje. El script de enriquecimiento añade contornos de las 2–5 unidades comparadas. Requeridos también ficha de origen, licencia, transformaciones, nulos y auditoría de uniones. Si Work 2 usa otra métrica, adaptar contrato y etiquetas antes de renderizar.

## Integración Work 2

Entregar pregunta, parámetros, versión fija, `tool_calls` con argumentos y `output_ref`, `data_refs`, `result_ref`, resultado JSON y limitaciones. Dos consultas de edad deben disparar dos cálculos rastreables. No basta con cambiar un selector en el HTML.

## E2E

Ejecutar `node --test tests/e2e/contract_flow.test.mjs`; después repetir la cadena con una versión fija del portal, dato real y una cifra verificada manualmente. El test local solo prueba fixture y validaciones estructurales.

## Demo y rúbrica

Secuencia de tres minutos y cuatro consultas en `docs/DEMO_QUERIES.md`. Cobertura y estado por criterio en `docs/RUBRIC_TRACEABILITY.md`; gaps y ensayo hostil en `docs/JURY_READINESS.md`.

## Riesgos priorizados

1. Falta fusionar la rama QA de datos y actualizar PR #3 contra `main`.
2. Falta una prueba conversacional de una versión fija del agente en el portal.
3. Los HTML versionados siguen siendo sintéticos; la cadena local con geometría real ya pasa como `local_tool`.
4. La métrica de escenario visual actual es una perturbación numérica de prueba; el agente sí admite ubicación hipotética.
5. El paquete de Work 2 se construye localmente por debajo del límite; falta validarlo en una versión privada del portal.

## Entrega

Completar ficha, subir datos/agente, crear versión, ejecutar prueba fija, seleccionar versión y track, revisar materiales y vista previa. La publicación final queda para autorización humana expresa. Seguir `docs/SUBMISSION_CHECKLIST.md`.
