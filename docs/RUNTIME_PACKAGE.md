# Paquete de runtime

## Incluido

- `agentes/gipuzkoa360/`: `main.py`, `tools.py`, `schemas.py`, `data_access.py`, `metrics.py` y README.
- `FUENTES.md`, `docs/METODOLOGIA.md` y `docs/RESULT_SCHEMA.md`.
- Los archivos reales compactos de `datos_preparados/` enumerados en `STUDIO_CONTEXT_FILES`.

## Excluido

- `tests/`, fixtures, cachés, capturas, originales voluminosos, notebooks e historia del proyecto.
- Dependencias adicionales: el cálculo usa biblioteca estándar; Studio aporta `langchain` y `studio`.

Ejecutar antes de versionar:

```text
python -c "from pathlib import Path; p=Path('.'); print(sum(f.stat().st_size for f in p.rglob('*') if f.is_file()))"
```

El límite observado del portal es 24 MB para el paquete de agente. Si los datos reales lo superan, reducirlos
mediante selección de columnas, tipos y granularidad documentada; no eliminar trazabilidad ni extrapolar una
muestra.
