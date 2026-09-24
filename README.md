# GIPUZKOA 360

Base reproducible y experiencia de visualización para analizar dónde coinciden envejecimiento y condiciones territoriales de acceso a servicios esenciales en Gipuzkoa.

## Datos y QA

```bash
python -m pip install -r requirements.txt
python scripts/data/build_all.py
python -m pytest tests/data -q
```

El pipeline prepara 88 municipios, 148 registros de centros sanitarios públicos, métricas transparentes y un runtime ligero. Incluye contrato legible por máquina, auditoría cruzada, SHA-256 y golden cases fijos. La proximidad es una distancia euclídea desde un punto representativo municipal; no equivale a tiempo de viaje ni accesibilidad real.

Véanse `FUENTES.md`, `docs/METODOLOGIA_GEOESPACIAL.md`, `docs/HANDOFF_WORK_1_DATA.md` y `docs/HANDOFF_WORK_2_3_DATA_QA.md`.

## Visualización e integración

Los HTML versionados se generan desde una salida real de `comparar_municipios`, adaptada sin cambiar sus cifras y enriquecida con geometría municipal. El banner deja claro que es una ejecución determinista del tool, no una conversación LLM. Para regenerarlos:

```bash
python scripts/agent/build_work3_result.py
node scripts/enrich_work1_result.mjs analisis/work3_agent_result.json analisis/work3_agent_result_with_geometry.json
node scripts/build_results.mjs analisis/work3_agent_result_with_geometry.json resultados
node --test tests/e2e/contract_flow.test.mjs
```

`scripts/enrich_work1_result.mjs` añade contornos municipales reales sin modificar las cifras.

Leer `docs/HANDOFF_WORK_3_INTEGRATION.md` y `docs/SUBMISSION_CHECKLIST.md`. La publicación final requiere autorización humana expresa.

## Agente territorial

La implementación determinista del agente está en `agentes/gipuzkoa360/`. Sus siete herramientas públicas consumen exclusivamente los datos preparados, devuelven resultados estructurados y mantienen periodo, unidades, fuentes, método y limitaciones. Los fixtures de `tests/fixtures/` son sintéticos y se usan solo en pruebas.

```bash
python -m pytest -q
```

Véanse `docs/HANDOFF_WORK_2_AGENT.md`, `docs/RESULT_SCHEMA.md` y `docs/RUNTIME_PACKAGE.md`.

## Release candidate

El candidato actual es `urban-challenge-rc2`; `urban-challenge-rc1` se conserva como histórico. `docs/PORTAL_DEPLOYMENT.md` contiene la secuencia exacta para generar el bundle autocontenido de dos archivos Python, crear una versión privada en el portal y probarla sin publicar la entrega. `docs/JURY_TEST_PLAN.md` define el recorrido de demostración, `analisis/release_e2e_report.json` registra las ocho pruebas A–H y `docs/RC2_FINAL_STATUS.md` concentra la evidencia de congelación.
