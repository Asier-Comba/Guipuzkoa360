# GIPUZKOA 360

Análisis territorial reproducible de población mayor y proximidad geométrica a servicios sanitarios públicos en Gipuzkoa. La base de Work 1 contiene 88 municipios y 148 centros; la distancia se calcula desde un punto representativo municipal, no como tiempo de viaje ni acceso individual.

## Datos

Las fuentes, periodos, licencias y transformaciones están en `FUENTES.md`, `docs/METODOLOGIA_GEOESPACIAL.md` y `docs/HANDOFF_WORK_1_DATA.md`.

```powershell
python -m pip install -r requirements.txt
python scripts/data/build_all.py
python -m pytest tests/data -q
```

## Producto y demo

`scripts/build_results.mjs` genera tres HTML autocontenidos desde un resultado JSON validado. `scripts/enrich_work1_result.mjs` incorpora contornos municipales del runtime de Work 1 sin alterar las cifras del agente. El contrato está en `docs/EXPECTED_RESULT_SCHEMA.md`.

```powershell
node scripts/build_results.mjs tests/fixtures/synthetic_agent_result.json resultados
node --test tests/e2e/contract_flow.test.mjs
```

Los HTML del fixture llevan una marca visible de **datos sintéticos de desarrollo**. Una demo con datos reales debe indicar si su cálculo proviene de una herramienta local reproducible o de una ejecución del agente. La interfaz local no demuestra por sí sola que el agente haya recalculado.

Seguir `docs/DEMO_QUERIES.md`, `docs/INTEGRATION_PLAYBOOK.md` y `docs/SUBMISSION_CHECKLIST.md` antes de preparar la entrega en el portal.
