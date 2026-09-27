# Actualizaciones de datos sin autopromoción

Snapshot actual: 3 fuentes oficiales, 1 entrada derivada, 88 municipios y 148 registros sanitarios. [Counters ejecutables](../../analisis/ops/source_health.json): 412/412 filas con identificadores resolubles, 7/7 archivos de manifiesto, cero nulos obligatorios/duplicados/coordenadas inválidas/referencias huérfanas detectados. Periodos 2025-01-01, 2025-05-07 y 2026-09-20; dispersión **627 días**, no fotografía temporal homogénea. No existe quality score agregado.

`compute_source_health.py` solo lee los snapshots; escribe su informe fuera de datos. La cobertura cuenta intersección de claves entre municipios/demografía/puntos; los servicios no tienen que existir en todos los municipios. Coordenadas se revisan por finitud/rangos generales y QA existente por contratos; este contador no demuestra precisión geodésica.

## Flujo con puntos de parada

Fuente oficial → watcher → candidato aislado → validar → transformar → QA → diff → benchmark → revisión humana → nueva versión.

El watcher implementado **no descarga Internet**. Recibe metadata conocida y candidata ya obtenida por un operador autorizado; no confunde ausencia de metadatos con ausencia de cambio. Nunca sustituye un CSV ni reescribe un manifiesto estable. La adquisición futura debe registrar URL oficial, respuesta/fecha de extracción, licencia, periodo de referencia y SHA del archivo original, sin secretos ni tokens en logs.

```sh
python scripts/ops/source_watcher.py --known known.json --candidate candidate.json
```

Entradas JSON objeto: `source_id`, `official_url`, `period` ISO fecha, `sha256` hexadecimal de 64 caracteres, `schema` objeto campo→tipo, `primary_key` nombre de campo; opcional `rows` lista de objetos para diff por clave y `available:false` para indisponibilidad. Los hashes son declarados: este comparador no autentica ni descarga su contenido.

| Estado | Condición / acción |
|---|---|
| NO_CHANGE | Identidad/periodo/schema sin cambio; no acredita disponibilidad remota |
| POTENTIAL_UPDATE | Hash o periodo distinto; aislar y validar candidato |
| SCHEMA_CHANGE | Diferencias de campos/tipos; riesgo HIGH hasta revisar transformación |
| SOURCE_UNAVAILABLE | Indisponibilidad declarada; mantener snapshot y explicar antigüedad |
| REVIEW_REQUIRED | Metadata incompleta, identidad/URL/clave cambiada, retroceso temporal o diff contradictorio |

`UpdateProposal` contiene `source_id`, `old_period`, `new_period`, `schema_diff`, `rows_added`, `rows_removed`, `rows_changed`, `coverage_change`, `validation_status`, `benchmark_status`, `risk`, `human_actions`. Counts sin filas comparables son **null**, no cero. Validación y benchmark empiezan NOT_RUN. `coverage_change` es delta del número de claves, no porcentaje de territorio ni garantía de correspondencia municipal. `automatic_promotion=false` siempre.

## Aprobación / rollback

Antes de aprobar: verificar bytes contra hashes; claves/municipios/CRS/unidades/periodos; explicar altas, bajas y cambios; regenerar en un directorio candidato; correr QA, goldens y benchmark; revisar qué respuestas cambian; guardar DATA_VERSION nueva y aprobarla expresamente. Si cambia un contexto v4, su evidencia deja de aplicarse: nueva versión privada y nueva batería. Rollback es volver al paquete aprobado anterior, no mutar silenciosamente el snapshot ni borrar historia.

Pruebas: `tests/next/test_source_ops.py` cubre los cinco estados, diff, metadata incompleta, datos huérfanos, duplicados, coordenada NaN, fuente falsa, hash y manifiesto vacío. Ninguna prueba obtiene fuentes nuevas.
