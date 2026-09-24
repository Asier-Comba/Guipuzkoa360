# Contrato de resultado esperado · v1.0.0

El agente entrega un objeto JSON a `scripts/build_results.mjs`. `schema_version` sigue SemVer. El renderizador rechaza resultados reales sin procedencia y traza de herramienta. Los campos numéricos ausentes son `null`, nunca cero implícito.

## Campos obligatorios

| Campo | Tipo | Regla |
|---|---|---|
| `schema_version` | string | `1.0.0` |
| `data_mode` | enum | `synthetic` o `real` |
| `title`, `question`, `summary` | string | Texto visible y verificable |
| `generated_at`, `period`, `geography` | string | Fecha ISO, periodo medido y unidad territorial |
| `parameters` | object | `age_group`, `service`, `distance_threshold_km` |
| `analysis` en datos reales | object | `total_units`, `matched_count`, `matched_unit_ids`, `older_population_total`; el recuento se calcula sobre las 88 filas, no sobre el top cinco |
| `metrics` | array | Cada métrica: `id`, `label`, `value`, `unit`, `period`, `source_ids` |
| `comparison` | array | 2–5 unidades para vista inicial; cada una tiene `unit_id`, `name`, `population`, `age_65_count`, `age_75_count`, `service_distance_km`, `service_count`, `period`, `source_ids` |
| `map_layers` | array | Cada capa: `id`, `label`, `metric`, `unit`, `period`, `source_ids` |
| `scenario` | object o null | `label`, `change`, `unit_id`, `distance_delta_km`, `assumptions`; solo hipótesis |
| `sources` | array | `source_id`, `title`, `url`, `period`, `unit`, `license`, `method` |
| `method`, `limitations` | string, array | Fórmula y advertencias interpretativas |
| `trace` | object | `execution_mode` (`synthetic_fixture`, `local_tool`, `agent_tool`, `agent`), `question_id`, `agent_version`, `tool_calls` con `tool`, `arguments`, `output_ref`; `data_refs`, `result_ref` |

`map_features` es opcional: array de `unit_id`, `geometry` GeoJSON `Polygon`/`MultiPolygon` en EPSG:4326 y `source_ids`. Si se proporciona, el HTML dibuja los contornos reales de las 2–5 unidades comparadas. Si no se proporciona, muestra celdas esquemáticas y lo indica expresamente. `scripts/enrich_work1_result.mjs` añade geometría desde `datos_preparados/runtime_municipios.geojson` de Work 1 conservando la fuente cartográfica. No modifica cifras del agente.

Cada `source_id` referenciado debe existir en `sources`. `trace.data_refs` debe incluir las fuentes usadas por las métricas y la comparación. Una respuesta real exige al menos una llamada de herramienta y un `output_ref` que coincida con `result_ref`; la cifra manual contrastada se registra aparte en la prueba de integración. En datos reales, `url` debe resolver al origen documentado o usarse un identificador de fichero original verificable. Nunca se deben introducir URLs de fuentes ficticias.

`comparison.service_distance_km` es *distancia geométrica* en kilómetros en el fixture. Si Work 1 suministra servicios por 10.000 mayores, tiempo de viaje u otra variable, se debe crear un adaptador con nombres y unidades nuevos; no renombrar la métrica como “accesibilidad”. La geometría real, si existe, debe añadirse como GeoJSON validado y no confundirse con los polígonos abstractos de la demo.

En la integración de Work 1, `parameters.older_share_threshold_pct` es 0–100 cuando se usa un umbral porcentual fijo. Para la tool `analizar_coincidencia` de Work 2 es `null` y `parameters.criteria_label` explica el doble cuantil; el parámetro `threshold_km` de esa tool **no** determina la selección destacada. `comparison` contiene solo 2–5 filas destacadas, cada una con `row_ref`; el recuento global y la suma de personas mayores se toman de `analysis`. Los controles locales se ocultan en resultados reales fijos: variar un criterio requiere una nueva ejecución y produce un nuevo `result_ref`.

## Adaptación de Work 2

Mapear la salida real a este contrato en un módulo separado, conservando el JSON original, nombres originales de herramientas, argumentos, identificadores de datos, periodo y ausencias. No modificar los valores para que “encajen” en la interfaz. Si faltan campos obligatorios, fallar con un mensaje específico y acordar el cambio del contrato.
