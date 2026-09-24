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

Los HTML versionados se generan con el fixture sintético de desarrollo y no deben presentarse como resultados territoriales. Para probarlos:

```bash
node scripts/build_results.mjs
node --test tests/e2e/contract_flow.test.mjs
```

`scripts/enrich_work1_result.mjs` añade contornos municipales reales a un resultado compatible sin modificar sus cifras. `scripts/data/export_work3_smoke_result.py` genera una prueba local con datos reales, marcada expresamente como cálculo local y no como ejecución del agente.

Leer `docs/HANDOFF_WORK_3_INTEGRATION.md` y `docs/SUBMISSION_CHECKLIST.md`. La publicación final requiere autorización humana expresa.
