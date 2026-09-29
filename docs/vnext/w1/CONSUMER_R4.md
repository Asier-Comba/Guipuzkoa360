# Consumir W1 0.2.0

Importar `get_capabilities`, `plan_visit`, `compare_visits` desde
`prototypes.ir_y_volver`. Copiar exclusivamente archivos de
RUNTIME_MANIFEST_R4.json preservando rutas, verificar SHA-256 y fijar el commit
publicado en PR #15. No necesita paquetes Python externos ni red en ejecución.

Entradas y schemas: prototypes/ir_y_volver/contracts/v0.2.0. Snapshot activo:
official-goierrialdea-go01-r4-20260929. Fecha única validada: 2026-09-29.
Destino único activo: beasain_center_stop_pair; scenario_kind=stop_only.
No está habilitado Ambulatorio de Beasain. El catálogo devuelve defaults y
perfiles; perfil distinto se rechaza. return_deadline limita la llegada de
regreso el mismo día. La zona es Europe/Madrid.

W2: adaptar versión, snapshot/hash, top-level result keys, scope y components.
El adapter R2 fijado a 0.1.0 debe rechazar este paquete hasta esa adaptación.
W3: actualizar pin y hash de query_w1_offline; consumir timeline `components`,
mostrar presencia inicial/arribo final y ambas paradas. No añadir el margen
otra vez a components_s ni llamar sanitario al destino entre paradas.

Cambios efectivos en `normalized_request`; unidades en segundos; `itinerary`
incluye total_s, vehicle_span_s, start_s/end_s, return_slack_s, origin_stop_id,
return_stop_id, outbound y return. Cada componente declara intervalo, duración,
basis y derivation. Consulta es parámetro humano; caminar cero es supuesto
stop_only. Fuentes GTFS solo acreditan horarios programados.

Comparación conserva cada resultado, incluidos unknown/no viable; cada pareja
declara requested_changes y held_constant. Delta solo con ambos ok y mismos
snapshot, fecha, origen, destino, zona y perfil. Múltiples cambios nunca se
atribuyen únicamente a la hora. No se calcula media eliminando fallos.

## Reproducir

Desde la raíz del checkout fijado:

```text
python -m pytest tests/mobility -q -o addopts=
python scripts/mobility/verify_r4.py
python scripts/mobility/package_r4.py --output <ruta-temporal>/w1-r4.zip
```

Rebuild desde el GTFS bruto preservado, a un archivo temporal nuevo:

```text
python scripts/mobility/build_goierrialdea_snapshot.py datos_originales/movilidad/goierrialdea-3276fcae.zip <ruta-temporal>/rebuilt.json --metadata docs/vnext/w1/R4_SOURCE_METADATA.json
```

El test de rebuild compara bytes con el snapshot fijado. Para actualizar el
feed se requieren nueva metadata real, snapshot_id, validación de fechas y
nuevo manifiesto/pin; no sobrescribir la identidad anterior. Para auditoría
sanitaria puede ejecutarse audit_health_r4.py con XML OSM original o derivado
público; solo el original reproduce su hash de adquisición.

Ejemplos sintéticos de contrato son para adaptar consumidores, no runtime.
REAL_CASES_R4.json y MATRIX_R4.json contienen las pruebas con GTFS real.
Los documentos sin sufijo R4 son evidencia histórica de R2 salvo HANDOFF.md,
que es el índice actual. HEALTH_DESTINATION_R4 explica el bloqueo peatonal y
el siguiente dato necesario. Ningún PASS local acredita portal o agente W2.
