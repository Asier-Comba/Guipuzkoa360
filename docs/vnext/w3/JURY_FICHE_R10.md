# Ficha y guion R10 — utilidad sanitaria modelada

**Demostración disponible: productor y producto offline. Agente integrado pendiente.**
No decir que esta conversación ocurrió. No superioridad demostrada frente a v4/CityScope.

1. **0:00–0:40, pregunta:** «Desde las paradas centrales de Zegama al punto oficial
   del Ambulatorio de Beasain, cita el 29/09/2026 a las 09:30, 20 minutos: ¿qué
   combinación programada de ida y vuelta encuentra el modelo?» Abrir `health.html`,
   escenario 09:30. Mostrar 10.691 s = 2 h 58 min 11 s, origen, paradas y horario.
2. **0:40–1:20, variación:** 09:45, conserva 20 minutos. Total 8.591 s y nueva ida
   08:47:37→09:17:06. Comparación −2.100 s = −35 min. Son resultados guardados de
   ejecuciones del productor; botón no es una llamada live a agente ni un recálculo JS.
3. **1:20–2:00, profundizar:** duración 90 min o origen Segura; explicar que cada
   escenario tiene solicitud y resultado propios. Ocultar delta formal al cambiar
   origen/duración: la comparación presentada solo corresponde a 09:30/09:45.
4. **2:00–2:35, límite:** fecha 30/09 → unknown/date_not_validated. No implica que
   no haya autobuses. 22:00 → sin pareja viable en las restricciones del snapshot.
5. **2:35–3:00, cifra y fuente:** abrir fuentes/solicitud. `health_review.json`
   contiene filas GTFS y número de línea, horas/pickup/dropoff, fórmula del paseo,
   reconstrucción total/holgura/delta. Puerta física no verificada; GTFS aproximado,
   no puntualidad ni reserva. Revisión humana antes de uso operativo.

Uso concreto: comparar hipótesis de hora/duración bajo datos programados para
informar una revisión de movilidad al punto oficial. No cita, asignación sanitaria,
accesibilidad universal o viaje garantizado. Dirección Bernedo Enea 1 / Zaldizurreta 2
conservada como conflicto; validar en campo. Paseo: 50 m/min +120 s por enlace
completo y sentido, con red fijada; no velocidad observada de una persona.

Después del gate autorizado, sustituir el primer paso por tool call **real** visible
con traza y pedir la variación al agente. Mantener máximo dos consultas live para el
guion del jurado. Hasta entonces esta ficha no acredita agente funcional en portal.
Si portal falla, mostrar mensaje observado; usar esta evidencia offline etiquetada.
No decir «HTTP 504» sin observarlo. No usuarios reales inventados, tokens/debug/holdout.

RAG: gold R4 30 preguntas intacto; S1/S2/S3 no son el corpus B1 de cuatro documentos
internos del repositorio W2. Mismo corpus antes de comparar; por ahora RAG_NO_GO,
retrieval comparable y generación NOT_RUN. No bloquea el contraste sanitario.
