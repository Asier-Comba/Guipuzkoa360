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
  "map_layers": [],
  "scenario": null,
  "sources": "sources",
  "method": "method",
  "limitations": "limitations"
}
```

Para `simular_escenario`, el campo adicional `scenario` contiene `baseline`, `scenario`,
`changed_parameters`, `affected_metric`, `assumptions` y `limitations`. Las filas incluyen diferencias
absolutas y relativas. `map_layers` queda vacío hasta que Work 1 proporcione geometrías publicables; la
interfaz no debe inventarlas.
