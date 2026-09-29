# Revisión de producto vNext · lectura honesta para jurado

**Destinatario inicial:** equipos técnicos de movilidad, cuidados y territorio.
**Estado:** evidencia determinista **offline**, fijada al proveedor W1
`c68eb5c`; aún no es una conversación del agente W2 ni una comparación A/B con
v4. Abrir [`resultados/vnext/index.html`](../../../resultados/vnext/index.html)
localmente; los cinco botones seleccionan respuestas guardadas y no hacen una
consulta nueva.

## Recorrido de 2–3 minutos

1. **Pregunta y alcance (0:00–0:35).** Mostrar «¿Permite el horario programado ir
   a la visita y volver?» y el aviso offline. GO01 conecta paradas catalogadas
   con el centro de Beasain para la fecha validada 29/09/2026. No es trayecto
   domicilio–Ambulatorio ni reserva de cita.
2. **Cambio de hora (0:35–1:15).** Abrir Zegama 09:30 y luego 10:00, ambas citas
   de 30 min. El proveedor devuelve 8.411 s y 8.392 s, respectivamente;
   `compare_visits` devuelve una diferencia de **−19 s**. La diferencia procede
   del output guardado, no de una resta de la interfaz. Enseñar ida, vuelta y
   componentes con segundos y márgenes descritos.
3. **Cambio de duración (1:15–2:00).** Abrir Segura 19:00, 30 min (9.143 s), y
   luego la misma cita de 180 min. El segundo estado es
   `no_feasible_journey`; no se muestra un total ni una vuelta ficticia. Esta
   prueba cambia la duración de consulta, **no** prueba retrasos en tiempo real.
4. **Dato ausente y fuente (2:00–2:45).** Abrir Zegama 2026-10-04:
   `unknown`, sin convertirlo en cero o «no hay autobús». Expandir «Fuente
   oficial y huellas» y «Supuestos y límites». El feed es GTFS estático;
   fuente, snapshot, proveedor y contrato tienen huellas fijadas.

La cifra directamente contrastable es el total de 8.411 s del caso Zegama
09:30: el output del proveedor conserva nueve componentes que suman 8.411 s.
El test de integridad comprueba esa suma para cada respuesta `ok`. Este
contraste **no** valida clínicamente la visita ni predice fiabilidad real.

## Qué falta para afirmar mejora frente a v4

La rama de agente W2, su paquete/versión y una autorización de pruebas de portal
todavía no están fijados. El corpus de 48 casos públicos, 12 de holdout privado
y 20 conversaciones está congelado; el scorer responde `NOT_RUN` con cero
ejecuciones LLM. Cuando exista candidato: fijar huella, ejecutar el mismo
corpus con condiciones comparables contra v4, conservar todos los intentos y
revisar manualmente las respuestas y causas. Los gates 57/60 y p95 son criterios
del proyecto, no garantías oficiales ni resultados actuales.

## Lectura adversaria resuelta en la interfaz

- Un estado `no_feasible_journey` solo cubre fecha, paradas y viajes directos
  del piloto; no prueba ausencia de transporte en general.
- `unknown` significa cobertura no validada; no equivale a cero.
- Paseo modelado de 0 s en `stop_only` no demuestra que la persona no camine.
- Los márgenes de llegada/embarque restringen la búsqueda; no se suman otra vez
  como si fueran espera.
- Horarios programados no son llegada garantizada, capacidad, disponibilidad
  sanitaria ni accesibilidad universal.
