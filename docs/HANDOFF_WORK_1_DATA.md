# HANDOFF WORK 1 — Data & Geospatial

## Estado

- Terminado: ingesta oficial, demografía, servicios sanitarios, límites municipales, métricas nivel 1/2, runtime, metadatos, pruebas y verificaciones.
- Parcial: `population_75_plus` derivada por año de nacimiento <=1949.
- Bloqueado/pendiente: no estaban visibles los tres documentos `contexto-principal.md`, `revision-completa-17-09-2026.md` y `comprobacion-adicional-portal.md`. El portal oficial solo mostraba las nueve plantillas base y ningún archivo propio.
- Endurecimiento posterior: contrato 1.1.0, métricas para las cuatro categorías, 38 controles QA, 15 tests y cinco golden cases. Handoff detallado en `docs/HANDOFF_WORK_2_3_DATA_QA.md`.

## Fuentes utilizadas

- `EUSTAT_EMH_2025`: población municipal, referencia 2025-01-01.
- `ODE_HEALTH_CENTRES_2026`: 148 centros sanitarios públicos de Gipuzkoa, 2026-09-20.
- `GEOEUSKADI_MUNICIPIOS_2025`: límites municipales EPSG:25830, 2025-05-07.

Detalle completo en `FUENTES.md` y `datos_preparados/metadata_sources.json`.

## Archivos producidos

- `datos_preparados/municipios.csv`: tabla municipal analítica con demografía y métricas.
- `datos_preparados/demografia.csv`: población total, 65+, 75+ y porcentajes.
- `datos_preparados/servicios.csv`: catálogo completo normalizado.
- `datos_preparados/municipios.geojson`: geometría maestra.
- `datos_preparados/runtime_municipios.geojson`: geometría simplificada + métricas.
- `datos_preparados/runtime_servicios.csv`: campos mínimos de los servicios.
- `resultados/metricas_municipales.csv`: copia de consumo analítico.
- `analisis/validation_report.json`, `verificaciones_manuales.csv`, `compatibilidad_temporal.csv`.

## Contrato de columnas

`municipality_code` es texto de 5 dígitos. `reference_period` es ISO. Poblaciones son enteros; porcentajes están en 0–100. Distancias terminadas en `_m` son metros euclídeos en EPSG:25830. `service_category` admite `primary_care`, `hospital`, `mental_health`, `other_health`. Cada tabla conserva `source_id`; las métricas derivadas usan `G360_DERIVED_MUNICIPAL_METRICS_V1`, ahora registrado con su linaje. El schema ejecutable completo está en `datos_preparados/data_contract.json`.

## Cómo reconstruir

```bash
python -m pip install -r requirements.txt
python scripts/data/build_all.py
python -m pytest tests/data -q
```

## Tests

Validan 88 municipios, formato/unicidad de códigos, joins completos, desigualdad 75+ <= 65+ <= total, porcentajes, 148 IDs de servicio únicos, coordenadas, asignación espacial, categorías, recálculo de tasas/distancias, CRS, geometrías, periodos, fuentes, runtime, SHA-256 y golden cases. El último pipeline terminó `PASS`.

## Cifras manualmente verificadas

- Donostia / San Sebastián: 183.388 habitantes; fuente y pipeline coinciden.
- Eibar: 27.118; coinciden.
- Tolosa: 20.048; coinciden.
- Centros sanitarios públicos filtrados a Gipuzkoa: 148; fuente y pipeline coinciden.

Registro: `analisis/verificaciones_manuales.csv`.

## Limitaciones

- Proximidad desde punto representativo municipal, no desde población real.
- Distancia euclídea, no viaria/peatonal ni tiempo.
- Conteo de centros no mide capacidad ni calidad.
- Periodos no idénticos (máximo 627 días).
- Sin red viaria/GTFS ni cobertura poblacional defendible en esta versión.
- La cartografía trae 3 entidades territoriales no municipales, excluidas explícitamente.

## Decisiones técnicas

- Municipio como unidad máxima defendible.
- EPSG:25830 para cálculos; EPSG:4326 para intercambio.
- Dos categorías principales: atención primaria y hospital; se conservan las demás sin mezclarlas.
- Sin índice compuesto opaco.
- Simplificación runtime de 25 m preservando topología y sin alterar el maestro.

## Qué necesita Work 2

Usar `municipios.csv` y `demografia.csv` para consultas, `runtime_municipality_points.csv` para puntos de cálculo y `runtime_servicios.csv` para escenarios de alta/baja hipotética. Mantener las etiquetas metodológicas exactas de las distancias. Compatibilidad validada contra `work/agent-engine`/PR #3; seguir `HANDOFF_WORK_2_3_DATA_QA.md`.

## Qué necesita Work 3

Usar `runtime_municipios.geojson` para mapa y `runtime_servicios.csv` para puntos. Mostrar periodo y fuente; ofrecer componentes separados, no un índice único.

## Próximos pasos

1. Incorporar una malla o sección censal 65+/75+ solo si cobertura y licencia se verifican.
2. Calcular distancia por red peatonal a partir de una red oficial/OSM documentada.
3. Añadir GTFS únicamente tras auditar cobertura y calendario.
4. Revisar los tres documentos oficiales ausentes cuando estén disponibles.
5. Revalidar periodos justo antes de la entrega.
