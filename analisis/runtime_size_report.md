# Informe de tamaño del runtime

El runtime recomendado usa `runtime_municipios.geojson` y `runtime_servicios.csv`.
La geometría runtime se simplifica a 25 m en EPSG:25830 conservando topología; el maestro no se modifica.

| Archivo | Bytes | Papel |
|---|---:|---|
| `datos_preparados\data_contract.json` | 5,274 | maestro/auditoría |
| `datos_preparados\demografia.csv` | 6,161 | maestro/auditoría |
| `datos_preparados\metadata_sources.json` | 4,833 | maestro/auditoría |
| `datos_preparados\municipios.csv` | 30,075 | maestro/auditoría |
| `datos_preparados\municipios.geojson` | 12,902,261 | maestro/auditoría |
| `datos_preparados\README.md` | 396 | maestro/auditoría |
| `datos_preparados\runtime_manifest.json` | 1,594 | runtime |
| `datos_preparados\runtime_municipality_points.csv` | 8,689 | runtime |
| `datos_preparados\runtime_municipios.geojson` | 495,392 | runtime |
| `datos_preparados\runtime_servicios.csv` | 25,258 | runtime |
| `datos_preparados\servicios.csv` | 31,418 | maestro/auditoría |
