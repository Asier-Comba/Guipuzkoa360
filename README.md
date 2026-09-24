# GIPUZKOA 360

Base reproducible y agente territorial para analizar dónde coinciden envejecimiento y peores condiciones
territoriales de acceso a servicios esenciales en Gipuzkoa.

## Reconstrucción

```bash
python -m pip install -r requirements.txt
python scripts/data/build_all.py
python -m pytest
```

El pipeline descarga fuentes oficiales, prepara 88 municipios, 148 centros sanitarios públicos, métricas transparentes y un runtime ligero. La proximidad calculada es una distancia euclídea desde un punto representativo municipal; no equivale a tiempo de viaje ni accesibilidad real.

El agente está en `agentes/gipuzkoa360/`; usa siete herramientas deterministas y conserva fuentes,
periodos, unidades, método y limitaciones. Véanse `FUENTES.md`, `docs/METODOLOGIA_GEOESPACIAL.md`,
`docs/RESULT_SCHEMA.md`, `docs/HANDOFF_WORK_1_DATA.md` y `docs/HANDOFF_WORK_2_AGENT.md`.

Los fixtures `TEST_*` son solo pruebas y no describen Gipuzkoa.
