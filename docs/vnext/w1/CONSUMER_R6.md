# Consumo W1 R6

R6 es opt-in. Importar `prototypes.ir_y_volver.provider_r6` y usar `plan_visit`, `compare_visits` o `get_capabilities`. R4 (`provider`) y R5 (`provider_r5`) siguen congelados.

Antes de construir una petición, leer `datos_preparados/movilidad/operational_catalog_r6.json`. El catálogo deriva IDs, municipios, paradas, destino, fecha, perfil, defaults, rangos y restricciones de los pins publicados. Su schema cerrado es `prototypes/ir_y_volver/contracts/v0.3.1/catalog.schema.json`.

```python
from prototypes.ir_y_volver.provider_r6 import plan_visit
result = plan_visit({"origin_id": "zegama_center_stops",
  "destination_id": "beasain_official_centre_anchor", "date": "2026-09-29",
  "appointment_time": "09:45", "duration_minutes": 20})
```

`parameter_provenance` distingue valores expresos de defaults. No atribuir `MODEL_DEFAULTS` al usuario. Conservar `sources`, `components[*].source_refs`, `assumptions` y `limitations` al comunicar el resultado.

Comparación: `compare_visits` admite 2–32 escenarios. El delta numérico solo es comparable si origen, destino, fecha, snapshot y perfil coinciden. Para orígenes distintos usar `CROSS_ORIGIN_SCENARIOS_R6.json`; no inventar un delta agregado ni inferir población o recomendación individual.

Alcance: centro y punto oficial confirmados; paseo modelado; entrada física no verificada; conflicto Bernedo Enea 1/Zaldizurreta 2 pendiente de revisión humana. No equivale a centro asignado, citas disponibles, accesibilidad universal, realtime ni puerta a puerta.

Regeneración: `python -m scripts.mobility.build_r6`; `python -m scripts.mobility.verify_r6`; `python -m scripts.mobility.package_r6 --output <ruta.zip>`.
