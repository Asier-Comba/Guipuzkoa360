# W1 · decisión de datos R2

Fecha de auditoría: 2026-09-29. Esta decisión solo cubre el proveedor determinista `Ir y volver`; no amplía el screening territorial ni certifica accesibilidad real.

| Elemento | Estado | Evidencia | Límite operativo |
|---|---|---|---|
| GTFS estático Goierrialdea | **GO** | Open Data Euskadi, ZIP 811.289 bytes, SHA-256 `3276fcae7bfa5002a39a2a094fef6637603de2e50648a46a436b314db27832a4` | Fuente externa mutable; la ejecución usa un derivado fijado por hash. |
| Piloto GO01, 2026-09-29 | **GO** | 162 viajes, 10 casos con oráculo independiente y filas `stop_times` identificadas | Solo viajes directos, horarios programados y pares de paradas catalogados. |
| Zegama, Segura e Idiazabal → centro de Beasain | **GO** | Paradas de origen/retorno separadas y preservadas en cada resultado | `origin_id` representa las paradas declaradas, no todas las viviendas del municipio. |
| Ambulatorio de Beasain de la PoC histórica | **BLOCKED** | El ZIP original y sus conectores OSM no están disponibles | El destino actual es el par de paradas del centro; no se presenta como reproducción del ambulatorio. |
| Reproducción de 135 escenarios y 14 tests históricos | **BLOCKED** | Falta `poc_DeustoAILabs_horarios.zip` y no hay bytes GTFS/OSM originales verificables | No se hereda ningún PASS histórico. |
| Otras fechas cubiertas por el feed | **PENDING** | Cobertura nominal 2026-09-28–2026-12-27 | Se responde `unknown/date_not_validated` hasta validar cada fecha y sus excepciones/festivos. |
| GTFS-RT / SIRI | **PENDING** | Índices y endpoints oficiales existen | Sin adaptador, validación de IDs/horizonte ni HTTP en runtime; no bloquea scheduled. |
| Transbordos, multioperador y puerta a puerta | **NO_GO R2** | Fuera del contrato 0.1.0 | Requiere contrato y evaluación nuevos. |

## Procedencia y reutilización

- Catálogo oficial: <https://opendata.euskadi.eus/catalogo/-/moveuskadi-datos-de-la-red-de-transporte-publico-de-euskadi-operadores-horarios-paradas-calendario-tarifas-etc/>.
- Índice GTFS: <https://opendata.euskadi.eus/transport/moveuskadi/data-index-gtfs.json>.
- ZIP usado: <https://opendata.euskadi.eus/transport/moveuskadi/lurraldebus/goierrialdea/gtfs_goierrialdea.zip>.
- Términos generales: <https://opendata.euskadi.eus/como-reutilizar/-/reutilizar-datos-abiertos/>. Indican que, con carácter general, las licencias abiertas permiten redistribución, reutilización y uso comercial, sujeto a la ficha concreta.
- La ficha enlaza a “Información legal”, pero no publica un identificador SPDX específico. Se conserva atribución y URL; se distribuye el derivado mínimo, no el ZIP bruto. Riesgo residual: **MEDIUM**, propietario humano/legal.

## Identidad del derivado

- `snapshot_id`: `official-goierrialdea-go01-20260928`
- fichero: `prototypes/ir_y_volver/snapshots/official-goierrialdea-go01-20260928.json`
- bytes: 804.348
- SHA-256: `30fc9d638f3576ae0e1084ee1e0c7b0268469bffc8af1dd15fd12430019d968b`
- `feed_version`: `20260928054818`
- `feed_start_date`: `20260928`
- `feed_end_date`: `20261227`
- fecha validada en R2: `2026-09-29`

El derivado se regenera con:

```text
python scripts/mobility/build_goierrialdea_snapshot.py <gtfs.zip> prototypes/ir_y_volver/snapshots/official-goierrialdea-go01-20260928.json
```

La reproducción exacta exige que `<gtfs.zip>` tenga el SHA-256 indicado arriba.
