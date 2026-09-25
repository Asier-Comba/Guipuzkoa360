# HISTÓRICO — Estado de integración · 2026-09-24

Registro conservado del 24/09/2026; no es la guía ni el estado actual del release.
Consulte [validación vigente](../../VALIDATION.md) y [plan de integración](../release/INTEGRATION_PLAN.md).
Los estados pendientes, cifras de paquete y mediciones siguientes describen su ejecución original;
no deben trasladarse como hechos actuales sin contrastarlos con la auditoría vigente.

## Estado remoto observado

- `main` contiene Work 3 tras la fusión de PR #2 (`1f9fbd9`).
- PR #1 (`work/data-foundation`) permanece abierto y presenta conflicto en `README.md` respecto a `main`.
- PR #3 (`work/agent-engine`) permanece abierto, contiene Work 1 y Work 2, y presenta el mismo conflicto en `README.md`.
- `work/data-qa-integration` incorpora `main`, resuelve el README de forma combinada y añade la capa de datos endurecida. No fusiona ni modifica ramas ajenas.

## Pruebas cruzadas realizadas

| Componente | Resultado |
|---|---:|
| Pipeline desde cero | PASS |
| Auditoría de datos | 41/41 PASS |
| Tests de datos/contrato | 18/18 PASS |
| Suite de Work 2 usando este `datos_preparados/` | 38/38 PASS |
| Construcción del paquete Work 2 | PASS, 42.430 bytes de 24 MB |
| Suite de Work 3 actual | 17/17 PASS |
| Resultado real local → geometría → 3 HTML | PASS |

La prueba de Work 3 usa `trace.execution_mode=local_tool` y declara que no es una ejecución del agente. No sustituye la prueba conversacional de una versión fija del portal.

## Compatibilidad y solapamientos

Work 2 consume `municipios.csv`, `demografia.csv`, `runtime_municipality_points.csv`, `runtime_servicios.csv` y `metadata_sources.json`. La rama QA conserva sus campos requeridos y añade controles. Los módulos del agente ignoran columnas adicionales de forma compatible.

Las modificaciones de PR #3 sobre `scripts/data/04_prepare_services.py`, `05_build_metrics.py` y `07_write_metadata.py` quedan funcionalmente incluidas en la versión QA: coordenadas proyectadas, puntos representativos y linaje derivado. Al actualizar PR #3, debe conservarse la versión QA de esos scripts y de sus salidas, no reaplicar la versión anterior.

## Orden recomendado

1. Revisar y fusionar el nuevo PR de datos QA contra `main`.
2. Actualizar `work/agent-engine` contra el nuevo `main`.
3. En conflictos, conservar:
   - de datos QA: `.gitattributes`, `datos_*`, `scripts/data/`, `tests/data/`, `FUENTES.md` y documentación QA;
   - de Work 2: `agentes/gipuzkoa360/`, `scripts/agent/`, `tests/test_*`, `docs/RESULT_SCHEMA.md`, ejemplos y documentación del agente;
   - de Work 3: `scripts/*.mjs`, `tests/e2e/`, HTML y documentación de visualización.
4. Ejecutar conjuntamente `python -m pytest` y `node --test tests/e2e/contract_flow.test.mjs`.
5. Generar el paquete del portal y probar una versión privada con golden cases conversacionales.
6. Publicar la entrega únicamente con autorización humana expresa.
