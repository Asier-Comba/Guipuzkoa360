# Investigación realtime acotada

Decisión R2: **PENDING / NO_GO para runtime**. El proveedor 0.1.0 permanece `time_basis=scheduled` y no realiza HTTP.

## Evidencia obtenida el 2026-09-29

- Índice GTFS-RT: `data-index-gtfs-rt.json`, 16.997 bytes, SHA-256 `29922076ae424f2739594a2535bd4c61849b3091e10adcb71fb4ff622ff8909f`.
- Índice SIRI: `data-index-siri.json`, 16.924 bytes, SHA-256 `d411fa801160ebe764b04faf899697e200ca4b3af653517678e54b9dc7c6ea9f`.
- Timestamps del índice de Goierrialdea: 2026-09-29 16:30:34–16:30:36.
- GTFS-RT publica `vehicle_positions`, `trip_updates` y `alerts` en protobuf.
- SIRI publica `vehicle_monitoring`, `estimated_timetable` y `situation_exchange` en XML.

Endpoints oficiales:

- <https://opendata.euskadi.eus/transport/moveuskadi/lurraldebus/goierrialdea/gtfsrt_goierrialdea_vehicle_positions.pb>
- <https://opendata.euskadi.eus/transport/moveuskadi/lurraldebus/goierrialdea/gtfsrt_goierrialdea_trip_updates.pb>
- <https://opendata.euskadi.eus/transport/moveuskadi/lurraldebus/goierrialdea/gtfsrt_goierrialdea_alerts.pb>
- <https://opendata.euskadi.eus/transport/moveuskadi/lurraldebus/goierrialdea/siri_goierrialdea_vehicle_monitoring.xml>
- <https://opendata.euskadi.eus/transport/moveuskadi/lurraldebus/goierrialdea/siri_goierrialdea_estimated_timetable.xml>
- <https://opendata.euskadi.eus/transport/moveuskadi/lurraldebus/goierrialdea/siri_goierrialdea_situation_exchange.xml>

## Bloqueos antes de un GO

1. Validar licencia específica y estabilidad de cada endpoint.
2. Decodificar mensajes y demostrar correspondencia `trip_id`/`stop_id` con el snapshot estático fijado.
3. Definir frescura, reloj, zona horaria, ausencia de entidades y degradación controlada.
4. Probar operador, horizonte y semántica de retrasos; un feed actual no se aplicará a citas futuras.
5. Versionar un contrato separado y evaluarlo con fixtures capturados legalmente.

No se ha hecho polling persistente, no se simula realtime y estos endpoints no forman parte del paquete de ejecución.
