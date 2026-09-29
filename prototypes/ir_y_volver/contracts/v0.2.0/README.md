# Contrato candidato 0.2.0 · R4

Entradas públicas: `get_capabilities()`, `plan_visit(request)`, `compare_visits(requests)`.
El contrato 0.1.0 queda histórico en el directorio padre. Este candidato requiere
actualizar los consumidores W2/W3; el proveedor 0.1.0 no implementa este contrato.

Petición: conserva los campos de 0.1.0 y añade `return_deadline` (HH:MM[:SS],
opcional, null equivale a fin del día). Fecha ISO literal, zona Europe/Madrid.
No interpreta hoy/mañana. Perfil no soportado se rechaza, no se ignora.

Cambio incompatible: total_s mide presencia necesaria en parada de origen
(salida menos boarding_margin) hasta llegada a parada de regreso. Son paradas
identificadas que pueden ser distintas. No representa domicilio.
`vehicle_span_s` conserva salida del vehículo → llegada de regreso.
`scenario_kind=stop_only` no describe una visita sanitaria completada.

Ocho componentes disjuntos, ordenados y contiguos: initial_wait,
outbound_vehicle, destination_walk_outbound, pre_appointment_wait,
appointment, destination_walk_return, return_wait, return_vehicle.
Cada componente declara start_s, end_s, seconds, kind, basis y derivation.
Todos usan segundos del mismo día civil: total_s=end_s-start_s=suma.
Márgenes de llegada/vuelta ya están incluidos en las esperas respectivas.
`return_slack_s` resta el buffer de embarque de la espera de vuelta; no es
probabilidad ni garantía. Multidía y transiciones DST quedan unsupported.

Solo ok contiene itinerario/componentes. unknown significa datos insuficientes;
no_feasible_journey solo cubre búsqueda directa ordinaria completa y declarada.
Permisos GTFS 2/3 no son viajes ordinarios acreditados. Fuente primaria:
https://gtfs.org/documentation/schedule/reference/#stop_timestxt

Comparación: conserva todos los resultados, registra requested_changes,
held_constant y comparability para cada pareja. Delta solo con dos ok, mismo
snapshot, fecha, zona, origen, destino, perfil y escenario. Horario, duración,
márgenes y límite pueden variar, siempre enumerados sin atribución causal.

Fixtures de examples.json son SYNTHETIC_CONTRACT_ONLY. No son horarios reales,
no alimentan runtime ni demuestran HEALTH_DESTINATION_GO. El manifiesto runtime
publicado posteriormente fijará exclusivamente snapshots oficiales validados.
