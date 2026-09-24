# Paquete de runtime

## Incluido

- `agentes/gipuzkoa360/`: `main.py`, `tools.py`, `schemas.py`, `data_access.py`, `metrics.py` y README.
- `FUENTES.md`, `docs/METODOLOGIA.md` y `docs/RESULT_SCHEMA.md`.
- Los archivos reales compactos enumerados en `STUDIO_CONTEXT_FILES`: `municipios.csv`, `demografia.csv`,
  `runtime_municipality_points.csv`, `runtime_servicios.csv` y `metadata_sources.json`.

## Excluido

- `tests/`, fixtures, cachés, capturas, originales voluminosos, notebooks e historia del proyecto.
- Dependencias adicionales: el cálculo usa biblioteca estándar; Studio aporta `langchain` y `studio`.

Ejecutar antes de versionar:

```text
python -c "from pathlib import Path; p=Path('.'); print(sum(f.stat().st_size for f in p.rglob('*') if f.is_file()))"
```

El paquete no necesita `municipios.geojson`; Work 3 lo consume fuera del runtime conversacional. El límite
observado del portal es 24 MB. Si los datos reales lo superan, reducirlos
mediante selección de columnas, tipos y granularidad documentada; no eliminar trazabilidad ni extrapolar una
muestra.
