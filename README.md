# GIPUZKOA 360

Agente y análisis territorial reproducible de población mayor y proximidad geométrica a servicios sanitarios públicos en Gipuzkoa. La base contiene 88 municipios y 148 centros. La distancia se calcula desde un punto representativo municipal; no equivale a tiempo de viaje ni acceso individual.

## Datos

Las fuentes, periodos, licencias y transformaciones están en `FUENTES.md`, `docs/METODOLOGIA_GEOESPACIAL.md` y `docs/HANDOFF_WORK_1_DATA.md`.

```powershell
python -m pip install -r requirements.txt
python scripts/data/build_all.py
python -m pytest
```

## Producto y demo

El agente está en `agentes/gipuzkoa360/` y dispone de siete herramientas deterministas. Su salida original sigue `docs/RESULT_SCHEMA.md`; `scripts/adapt_work2_envelope.mjs` prepara el enlace con el contrato de producto en `docs/EXPECTED_RESULT_SCHEMA.md`. `scripts/enrich_work1_result.mjs` añade contornos municipales y `scripts/build_results.mjs` genera HTML autocontenidos.

```powershell
node scripts/build_results.mjs tests/fixtures/synthetic_agent_result.json resultados
node --test tests/e2e/*.test.mjs
node scripts/build_jury_demo.mjs
```

Los HTML del fixture llevan una marca visible de **datos sintéticos de desarrollo**. La demo real local se abre en `resultados/demo_real/index.html` y sus cuatro consultas se calculan con una herramienta local reproducible. La versión fija del agente todavía debe probarse en el portal; esta demo no sustituye esa prueba.

Seguir `docs/README_DEMO_JURADO.md`, `docs/HANDOFF_WORK_2_AGENT.md`, `docs/INTEGRATION_PLAYBOOK.md` y `docs/SUBMISSION_CHECKLIST.md` antes de preparar la entrega en el portal.
