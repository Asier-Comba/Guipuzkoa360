# Informe de tamaño del runtime

El runtime recomendado usa `runtime_municipios.geojson` y `runtime_servicios.csv`.
La geometría runtime se simplifica a 25 m en EPSG:25830 conservando topología; el maestro no se modifica.

| Archivo | Bytes | Papel |
|---|---:|---|
| `datos_preparados\demografia.csv` | 6,250 | maestro/auditoría |
| `datos_preparados\metadata_sources.json` | 3,741 | maestro/auditoría |
| `datos_preparados\municipios.csv` | 17,741 | maestro/auditoría |
| `datos_preparados\municipios.geojson` | 12,902,356 | maestro/auditoría |
| `datos_preparados\README.md` | 384 | maestro/auditoría |
| `datos_preparados\runtime_municipality_points.csv` | 11,117 | runtime |
| `datos_preparados\runtime_municipios.geojson` | 446,114 | runtime |
| `datos_preparados\runtime_servicios.csv` | 25,407 | runtime |
| `datos_preparados\servicios.csv` | 36,913 | maestro/auditoría |
