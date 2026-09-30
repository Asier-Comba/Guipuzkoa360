# Checklist mecanizable W2 · W1 0.3.1

Antes de aceptar un resultado sanitario, W2 debe validar versión, snapshot, escenario, destino, estado, procedencia completa, fuentes, totales, identidades GTFS y semántica de comparación. La definición mecanizable está en `CONSUMER_CHECKLIST_R7.json`.

La vista mínima para el modelo debe conservar: autobús y hora; parada de bajada; parada y hora de regreso; paseo en ambos sentidos; esperas; duración de consulta; márgenes; cambio solicitado; qué es modelado; qué no está verificado; fuentes y limitaciones.

Reglas de comunicación:

- acceso modelado no significa entrada física verificada;
- horario estático no significa realtime;
- identidad del centro no significa capacidad ni cita disponible;
- escenarios de orígenes distintos son lado a lado, no un delta poblacional ni una recomendación individual.

W1 no implementa aquí el adapter W2.
