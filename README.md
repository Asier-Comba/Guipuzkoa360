# GIPUZKOA 360 — base de datos geoespacial

Base reproducible para analizar dónde coinciden envejecimiento y peores condiciones territoriales de acceso a servicios esenciales en Gipuzkoa.

## Reconstrucción

```bash
python -m pip install -r requirements.txt
python scripts/data/build_all.py
python -m pytest tests/data -q
```

El pipeline descarga fuentes oficiales, prepara 88 municipios, 148 centros sanitarios públicos, métricas transparentes y un runtime ligero. Incluye un contrato legible por máquina, auditoría cruzada, SHA-256 del paquete y golden cases fijos para probar el agente. La proximidad calculada es una distancia euclídea desde un punto representativo municipal; no equivale a tiempo de viaje ni accesibilidad real.

Véanse `FUENTES.md`, `docs/METODOLOGIA_GEOESPACIAL.md`, `docs/HANDOFF_WORK_1_DATA.md` y `docs/HANDOFF_WORK_2_3_DATA_QA.md`.
