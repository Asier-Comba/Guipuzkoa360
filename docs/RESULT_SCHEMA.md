# Contrato JSON para Work 3

Cada herramienta devuelve JSON UTF-8. Éxito:

```json
{
  "status": "ok",
  "question": "...",
  "filters": {},
  "period": "2025",
  "metric": "...",
  "unit": "...",
  "rows_used": 0,
  "data": [],
  "method": "...",
  "sources": [],
  "warnings": [],
  "limitations": []
}
```

Error:

```json
{
  "status": "error",
  "error_code": "missing_file",
  "message": "...",
  "available_options": []
}
```

## Adaptación estable para la interfaz

Work 3 puede transformar cualquier salida satisfactoria sin reinterpretar cálculos:

```json
{
  "title": "question",
  "question": "question",
  "summary": "texto del coordinador, no calculado por la interfaz",
  "metrics": [{"name": "metric", "unit": "unit", "period": "period"}],
  "comparison": "data",
  "map_layers": [{"id": "municipalities", "source": "datos_preparados/runtime_municipios.geojson", "join_key": "municipality_code"}],
  "scenario": null,
  "sources": "sources",
  "method": "method",
  "limitations": "limitations"
}
```

Las filas de acceso usan `nearest_distance_m` y `within_threshold`. La etiqueta metodológica que debe mostrar
la interfaz es **distancia geométrica aproximada desde el punto representativo municipal**. La unidad es metros;
no renombrarla como tiempo, distancia viaria o accesibilidad real.

Para `simular_escenario`, el campo adicional `scenario` contiene `baseline`, `scenario`,
`changed_parameters`, `affected_metric`, `assumptions` y `limitations`. Las filas incluyen diferencias
absolutas (`difference_absolute_m`) y relativas. Work 3 debe unir por `municipality_code`, no por nombre.

## Archivos de visualización

- Polígonos: `datos_preparados/runtime_municipios.geojson` (EPSG:4326).
- Servicios: `datos_preparados/runtime_servicios.csv`.
- Puntos de cálculo: `datos_preparados/runtime_municipality_points.csv`; sirven para auditoría y escenarios,
  no como ubicación de población.

## Ejemplos reproducibles

- `docs/examples/comparison_tolosa_beasain_azpeitia.json`
- `docs/examples/coincidence_primary_care_65.json`
- `docs/examples/scenario_add_primary_care_beasain.json`

Se regeneran con `py scripts/agent/generate_examples.py`. Contienen datos reales preparados, periodos, fuentes,
método y limitaciones; el escenario es explícitamente hipotético.
