# GIPUZKOA 360

Agente y análisis territorial reproducible de población mayor y proximidad geométrica a servicios sanitarios públicos en Gipuzkoa. La base contiene 88 municipios y 148 centros. La distancia se calcula desde un punto representativo municipal; no equivale a tiempo de viaje ni acceso individual.

## Datos

Las fuentes, periodos, licencias y transformaciones están en `FUENTES.md`, `docs/METODOLOGIA_GEOESPACIAL.md` y `docs/HANDOFF_WORK_1_DATA.md`.
El contrato de datos 1.1.0, el manifiesto SHA-256, 41 controles de calidad y los casos de referencia de la rama QA están en `datos_preparados/data_contract.json`, `datos_preparados/runtime_manifest.json`, `analisis/data_quality_report.json` y `tests/fixtures/golden_cases.json`.

```powershell
python -m pip install -r requirements.txt
python scripts/data/build_all.py
python -m pytest
```

## Producto y demo

El agente está en `agentes/gipuzkoa360/` y dispone de siete herramientas deterministas. Su salida original sigue `docs/RESULT_SCHEMA.md`; `scripts/adapt_agent_tool_result.mjs` la conecta con el contrato de producto en `docs/EXPECTED_RESULT_SCHEMA.md`. `scripts/enrich_work1_result.mjs` añade contornos municipales y `scripts/build_results.mjs` genera HTML autocontenidos. `scripts/adapt_work2_envelope.mjs` queda preparado para una futura traza observada del coordinador en el portal.

```powershell
node scripts/build_results.mjs tests/fixtures/synthetic_agent_result.json resultados/dev_sintetico
node --test tests/e2e/*.test.mjs
node scripts/build_work2_demo.mjs
```

El fixture se genera en `resultados/dev_sintetico/` y lleva una marca visible. Los tres HTML principales de `resultados/` ya proceden de las herramientas reales de Work 2. La demo recomendada se abre en `resultados/demo_work2/index.html`; incluye dos cálculos por cuantil, comparación, escenario y error controlado. La prueba privada del coordinador en el portal detectó un bloqueo del runtime y está documentada en `docs/PORTAL_PRIVATE_TEST_2026-09-24.md`.

Seguir `docs/README_DEMO_JURADO.md`, `docs/HANDOFF_WORK_2_AGENT.md`, `docs/INTEGRATION_PLAYBOOK.md` y `docs/SUBMISSION_CHECKLIST.md` antes de preparar la entrega en el portal.
