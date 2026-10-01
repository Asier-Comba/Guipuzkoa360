# GIPUZKOA 360

## Subtítulo

Entender el tiempo que ocupa una visita sanitaria cuando dependemos del autobús.

## Equipo

DeustoAI Labs — Universidad de Deusto

Oier Duñabeitia Berezo · Asier Comba Lopez · Hugo Fernández Díez

## Territorio

Gipuzkoa; visitas sanitarias en el corredor Zegama–Segura–Idiazabal–Beasain.

## Pregunta de investigación

¿Cómo cambia la carga temporal de una visita sanitaria para personas que dependen del transporte público cuando cambia el municipio de origen, la hora de la cita o su duración?

## Quién utilizará el análisis

Equipos técnicos de movilidad, cuidados y planificación territorial que necesitan estudiar el acceso sanitario.

## Para qué servirá el resultado

GIPUZKOA 360 ayuda a equipos técnicos de movilidad, cuidados y planificación territorial a detectar dónde merece estudiar el acceso sanitario y, en corredores con datos disponibles, explorar cómo cambia la carga temporal de una visita sanitaria completa según el origen, la hora de cita y su duración.

## Explicación breve para Entrega

Una consulta de 20 minutos puede ocupar casi tres horas si dependemos del autobús. Desde las paradas centrales de Zegama al punto oficial del Ambulatorio de Beasain, el 29 de septiembre de 2026, la cita de las 09:30 supone 2 h 58 min 11 s (10.691 s), desde las 08:09:37 hasta el regreso a las 11:07:48. Cambiar solo la cita a las 09:45 da 2 h 23 min 11 s (8.591 s): 35 minutos menos entre dos escenarios calculados, no un ahorro observado ni una recomendación. La conversación seleccionada muestra el cálculo, la variación y sus límites. Usa horarios oficiales programados y paseos modelados; no mide tiempo real ni viajes desde el domicilio, y no verifica entradas, citas o capacidad sanitaria. El análisis de visitas admite actualmente Zegama, Segura e Idiazabal. La demo enlazada es una visualización territorial de los 88 municipios, no una prueba del nuevo agente de visitas sanitarias. Fuentes: Moveuskadi/Goierrialdea (horarios del 28/09 al 27/12/2026), Open Data Euskadi (centros, 20/09/2026), Osakidetza (ficha consultada el 29/09/2026) y © OpenStreetMap contributors, ODbL 1.0 (red obtenida el 29/09/2026).

## Cómo funciona

La persona indica origen, fecha, hora y duración de consulta. El agente consulta las opciones disponibles y utiliza herramientas de cálculo para responder con cifras, unidades, fuentes y límites. Para comparar, calcula cada visita por separado y utiliza los resultados reales. El tiempo incluye esperas, autobús, paseo modelado, consulta y regreso: desde la presencia en la parada de origen hasta la llegada a la parada de vuelta, no desde el domicilio.

## Ejemplo principal, variación y cifra contrastada

Pregunta principal: «Desde las paradas del centro de Zegama, quiero ir al Ambulatorio de Beasain el 29 de septiembre de 2026 para una consulta a las 09:30 que dura 20 minutos y regresar. ¿Qué carga temporal completa resultaría con los datos disponibles?»

Resultado: 10.691 segundos, equivalentes a 2 h 58 min 11 s, de 08:09:37 a 11:07:48. El autobús sale a las 08:12:37; los tres minutos anteriores forman parte de la espera inicial del cálculo.

Variación: «Mantén todo igual pero cambia la cita a las 09:45. Recalcula y compara ambos escenarios.»

Resultado: 8.591 segundos, equivalentes a 2 h 23 min 11 s, de 08:44:37 a 11:07:48. Segundo escenario menos primero: −2.100 segundos, o −35 minutos. La diferencia depende de estos horarios y supuestos: no identifica una mejor hora ni acredita un ahorro real.

Ambas cifras coinciden con las herramientas ejecutadas en la conversación seleccionada y con el cálculo contrastado a partir de los datos.

## Datos, fuentes y supuestos

El contexto territorial cubre 88 municipios. El cálculo de visitas sanitarias está acotado a las paradas de Zegama, Segura e Idiazabal, el trayecto directo GO01 y el punto oficial modelado del Ambulatorio de Beasain. Su fecha de cálculo validada es el 29 de septiembre de 2026.

Los horarios oficiales de Moveuskadi/Goierrialdea cubren del 28 de septiembre al 27 de diciembre de 2026. El registro sanitario de Open Data Euskadi tiene referencia del 20 de septiembre de 2026. La ficha del centro de Osakidetza se consultó el 29 de septiembre; su dirección difiere de un listado sanitario de enero de 2026, por lo que la entrada no está verificada. La red de paseo se obtuvo el 29 de septiembre de 2026 de OpenStreetMap: © OpenStreetMap contributors, licencia ODbL 1.0.

El paseo se calcula a 50 metros por minuto, más 120 segundos por enlace completo y sentido. Se aplican márgenes de diez minutos antes de la consulta y tres minutos antes del autobús. Son supuestos del cálculo, no tiempos observados ni elecciones humanas verificadas. La población municipal procede de Eustat, a 1 de enero de 2025; las fechas de las distintas fuentes no son un único retrato temporal homogéneo.

## Un límite que el agente reconoce

«¿Puedes decirme en tiempo real cuál es la mejor hora de cita desde mi casa?»

No con estos datos. El agente no conoce el domicilio, las incidencias en tiempo real ni la disponibilidad de citas. Puede comparar horas concretas desde las paradas admitidas, sin recomendar una cita ni afirmar accesibilidad individual. El registro de un centro tampoco demuestra capacidad, calidad o asignación; cero registros no significa ausencia de atención. Los escenarios no prueban causalidad ni predicen resultados futuros.

## Materiales

- [Visualización territorial](https://asier-comba.github.io/Guipuzkoa360/): mapa y ejemplos municipales; no sustituye la prueba de visitas sanitarias.
- [Código, fuentes y evidencia](https://github.com/Asier-Comba/Guipuzkoa360).
- Conversación seleccionada de visita sanitaria: pregunta principal, variación de hora y explicación de fuentes, cobertura y límites.

## Defensa breve

Una consulta de veinte minutos puede ocupar casi tres horas cuando dependemos del autobús. GIPUZKOA 360 ayuda a equipos técnicos a entender qué parte de ese tiempo corresponde al viaje, al paseo, a la espera y a la consulta.

Desde Zegama hacia el Ambulatorio de Beasain, el 29 de septiembre de 2026, una cita de veinte minutos a las nueve y media da 2 horas, 58 minutos y 11 segundos. Cambiando solo la hora a las nueve y cuarenta y cinco, el cálculo da 2 horas, 23 minutos y 11 segundos. La conversación demuestra que el agente vuelve a calcular: son 35 minutos de diferencia entre escenarios, no un ahorro medido ni una recomendación.

Mostramos también lo que no sabemos: usamos horarios programados y paseo modelado, no tiempos reales desde casa. No verificamos la entrada del centro ni la disponibilidad de citas. La utilidad es hacer visibles cifras y supuestos para decidir qué merece comprobar en campo.
