# HISTÓRICO — Handoff de datos para Work 2 y Work 3

Registro conservado del 24/09/2026; no es la guía ni el estado actual del release.
Consulte [validación vigente](../../VALIDATION.md) y [plan de integración](../release/INTEGRATION_PLAN.md).
Los estados pendientes, cifras de paquete y mediciones siguientes describen su ejecución original;
no deben trasladarse como hechos actuales sin contrastarlos con la auditoría vigente.

Contrato de datos: **1.1.0**. Snapshot de fuentes: **2026-09-24**. Este documento complementa `HANDOFF_WORK_1_DATA.md`; ante una diferencia, prevalece `datos_preparados/data_contract.json` porque se valida automáticamente.

## Paquete que debe consumirse

| Consumidor | Archivo | Uso |
|---|---|---|
| Work 2 | `datos_preparados/municipios.csv` | búsqueda, población 65+/75+, comparación, conteos, tasas y distancias |
| Work 2 | `datos_preparados/demografia.csv` | periodos y medidas demográficas consumidas por `DataRepository` |
| Work 2 | `datos_preparados/runtime_municipality_points.csv` | punto representativo en EPSG:4326/25830 para acceso y escenarios |
| Work 2 | `datos_preparados/runtime_servicios.csv` | detalle de centros y simulación de altas/bajas hipotéticas |
| Work 2 | `datos_preparados/metadata_sources.json` | títulos, URL, periodo, licencia, método y linaje |
| Work 2 | `datos_preparados/data_contract.json` | schema, unidades, invariantes y mapping de salida |
| Work 3 | `datos_preparados/runtime_municipios.geojson` | contornos EPSG:4326 y atributos municipales |
| Ambos | `datos_preparados/runtime_manifest.json` | tamaños, SHA-256 y lista mínima de archivos |

No subir al runtime `datos_originales/`, `analisis/`, la geometría maestra ni las tablas redundantes. Son material de regeneración/auditoría para el repositorio. El paquete recomendado ocupa menos de 1 MB; el manifiesto lo compara con el presupuesto de 24 MB documentado por Work 3.

## Claves y significado de fila

- `municipality_code`: clave territorial, texto de cinco dígitos `20xxx`; 88 valores, sin nulos ni duplicados. No convertir a entero.
- `service_id`: clave de registro sanitario; 148 valores únicos. Dos IDs pueden compartir coordenada y seguir siendo registros distintos.
- `municipios.csv`: una fila por municipio.
- `runtime_servicios.csv`: una fila por registro oficial de centro/tipo de servicio, con coordenadas WGS84 y EPSG:25830.
- `runtime_municipality_points.csv`: una fila por municipio; punto interior de cálculo, no ubicación de la población.
- `runtime_municipios.geojson`: una Feature por municipio; `Polygon` o `MultiPolygon` en EPSG:4326.

La relación es `runtime_servicios.municipality_code -> municipios.municipality_code`. Todos los servicios pasan una unión espacial `within`; 11 municipios no contienen ningún registro sanitario y conservan todos sus conteos a cero.

## Columnas de `municipios.csv`

| Grupo | Columnas | Tipo/unidad |
|---|---|---|
| identidad | `municipality_code`, `municipality_name` | texto |
| demografía | `population_total`, `population_65_plus`, `population_75_plus` | entero, personas |
| porcentajes | `pct_65_plus`, `pct_75_plus` | decimal, 0–100 |
| territorio | `area_km2` | km² |
| conteos | `services_<category>`, `services_total` | entero, registros |
| tasas | `<category>_per_10000_65_plus`, `<category>_per_10000_75_plus` | registros por 10.000 personas del grupo |
| punto de cálculo | `representative_point_longitude`, `representative_point_latitude` | grados, EPSG:4326 |
| proximidad | `distance_to_nearest_<category>_m` | metros euclídeos, cálculo EPSG:25830 |
| tiempo/linaje | `reference_period`, `metrics_reference_period`, `source_id`, `source_ids` | texto |

`<category>` es `primary_care`, `hospital`, `mental_health` u `other_health`. El listado exacto, orden, tipo lógico y mapping está en `data_contract.json`.

## Invariantes que el agente puede asumir

1. Existen exactamente 88 municipios y los conjuntos de códigos coinciden entre CSV y GeoJSON.
2. `population_75_plus <= population_65_plus <= population_total` y las poblaciones son positivas.
3. Los porcentajes y tasas se redondean a tres decimales.
4. `services_total` es la suma de las cuatro categorías y suma 148 en Gipuzkoa.
5. Coordenadas de servicio y punto representativo están en EPSG:4326; toda distancia se calcula en EPSG:25830.
6. No hay nulos en el snapshot. Un nulo futuro es error, no cero.
7. Un conteo cero significa ausencia de registro dentro del municipio, no ausencia de acceso.
8. `source_ids` se divide por `|`; cada ID existe en `metadata_sources.json`.

## Mapping a Work 3 v1.0.0

| Work 3 | Work 1 | Conversión |
|---|---|---|
| `unit_id` | `municipality_code` | ninguna; conservar string |
| `name` | `municipality_name` | ninguna |
| `population` | `population_total` | ninguna |
| `age_65_count` | `population_65_plus` | ninguna |
| `age_75_count` | `population_75_plus` | ninguna |
| `service_count` | `services_<selected_category>` | seleccionar categoría explícita |
| `service_distance_km` | `distance_to_nearest_<selected_category>_m` | dividir entre 1000 |
| `period` | `metrics_reference_period` | conservar los tres periodos |
| `source_ids` | `source_ids` | `split('|')` |

Compatibilidad comprobada con `docs/EXPECTED_RESULT_SCHEMA.md` de Work 3, ya integrado en `main` mediante PR #2. El adaptador conserva los valores originales y etiqueta la distancia como geométrica.

`scripts/data/export_work3_smoke_result.py <salida.json>` genera un resultado determinista con tres municipios para probar el contrato y el renderizador de Work 3. Usa datos reales, pero se etiqueta explícitamente como **prueba de integración que no acredita una ejecución del agente**.

## Soporte de Work 2

- 65+/75+: seleccionar las columnas de conteo y porcentaje correspondientes; no recalcular 75+ restando grupos.
- Comparación municipal: usar códigos como clave y devolver el denominador junto al porcentaje.
- Servicio seleccionado: formar los campos desde la misma `<category>` para evitar cruzar conteo de una categoría con distancia de otra.
- Coincidencia de indicadores: combinar por `municipality_code`, no por nombre.
- Escenario de alta: transformar ubicación hipotética a EPSG:25830 y usar la mínima distancia entre base y punto nuevo. Mantener resultado base, escenario, delta y supuestos.
- Escenario de baja: retirar el `service_id` solicitado en memoria y recalcular; no modificar los CSV.

Work 2 está en `work/agent-engine`/PR #3. Su suite completa de 38 tests pasa al sustituir únicamente `datos_preparados/` por este contrato QA; su paquete del portal se genera correctamente con 42.430 bytes. Se añadieron `runtime_municipality_points.csv`, coordenadas EPSG:25830 en `runtime_servicios.csv` y el alias de linaje `input_source_ids` sin eliminar campos anteriores.

PR #3 sigue basado en una historia anterior a la fusión de Work 3 y presenta conflicto en `README.md`. La resolución segura es integrar primero la rama QA de datos, actualizar PR #3 contra `main`, conservar los módulos `agentes/gipuzkoa360/`, tests y ejemplos de Work 2, y mantener las versiones QA de datos/scripts. Véase `docs/INTEGRATION_STATUS_2026-09-24.md`.

## Golden cases

`tests/fixtures/golden_cases.json` contiene cinco casos fijos:

1. Donostia / San Sebastián, población 65+ y porcentaje.
2. Comparación 75+ entre Eibar y Tolosa.
3. Aduna sin atención primaria registrada y distancia al centro de Villabona.
4. Salud mental de Eibar: conteo, tasas y distancia.
5. Escenario hipotético de alta en el punto representativo de Aduna.

Cada caso declara pregunta, inputs, filas/keys, fórmula y resultado. `test_golden_cases_against_fixed_source_snapshot` los vuelve a calcular. No se regeneran automáticamente: una actualización de fuentes debe fallar hasta que se contraste y apruebe el nuevo valor.

## Regeneración y validación

```bash
python -m pip install -r requirements.txt
python scripts/data/build_all.py
python -m pytest tests/data -q
```

`build_all.py` descarga/copias las fuentes, reconstruye datos, ejecuta validaciones básicas, escribe metadatos y genera el informe exhaustivo/manifiesto. El resultado esperado actual es 41 controles de auditoría y 18 tests automáticos correctos.

Artefactos de QA:

- `analisis/data_quality_report.json`: controles, cobertura, extremos y municipios sin registros.
- `analisis/validation_report.json`: resumen básico y verificaciones contra originales.
- `analisis/verificaciones_manuales.csv`: cifras de contraste fuente/pipeline.
- `analisis/compatibilidad_temporal.csv`: separación de periodos.
- `tests/fixtures/golden_cases.json`: casos end-to-end fijos.

## Limitaciones obligatorias en respuesta

- La distancia parte de un punto interior no ponderado por población y no representa tiempo de viaje.
- El conteo no mide capacidad, horario, citas, calidad ni accesibilidad universal.
- Los periodos difieren hasta 627 días; no se afirma simultaneidad perfecta.
- La población 75+ se deriva de nacidos hasta 1949 para la fecha 2025-01-01.
- Un escenario es una hipótesis geométrica, no una recomendación de localización.
