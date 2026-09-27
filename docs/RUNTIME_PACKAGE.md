# Paquete de runtime

## Incluido

- `main.py` y `tools.py` autocontenido, generados bajo `agentes/gipuzkoa360/portal/` para los dos editores Python del portal.
- `FUENTES.md`, `docs/METODOLOGIA.md` y `docs/RESULT_SCHEMA.md`.
- Los archivos reales compactos enumerados en `STUDIO_CONTEXT_FILES`: `municipios.csv`, `demografia.csv`,
  `runtime_municipality_points.csv`, `runtime_servicios.csv`, `metadata_sources.json`, `data_contract.json` y `runtime_manifest.json`.

## Excluido

- `tests/`, fixtures, cachés, capturas, originales voluminosos, notebooks e historia del proyecto.
- Dependencias adicionales: el cálculo usa biblioteca estándar; Studio aporta `langchain` y `studio`.

Ejecutar antes de versionar:

```text
python scripts/agent/build_portal_sources.py
python scripts/agent/build_portal_package.py
```

El paquete no necesita `municipios.geojson`; Work 3 lo consume fuera del runtime conversacional. El ZIP RC2
queda muy por debajo del límite de 24 MB. El constructor fija orden y fecha ZIP para que dos builds del mismo
contenido produzcan el mismo SHA-256. Los valores exactos vigentes se publican en `docs/RC2_FINAL_STATUS.md`.
