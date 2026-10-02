# GIPUZKOA 360

## Subtítulo

Entender cuánto tiempo ocupa una visita sanitaria cuando dependemos del autobús.

## Equipo

DeustoAI Labs — Universidad de Deusto

Oier Duñabeitia Berezo · Asier Comba Lopez · Hugo Fernández Díez

## Territorio

Gipuzkoa.

## Pregunta de investigación

¿Cómo cambia la carga temporal de una visita sanitaria para personas que dependen del transporte público cuando cambia el municipio de origen, la hora de la cita o su duración?

## Quién utilizará el análisis

Equipos técnicos de movilidad, cuidados y planificación territorial.

## Para qué servirá el resultado

Exploramos los 88 municipios y calculamos visitas completas donde hay datos suficientes. Una consulta de 20 minutos desde Zegama ocupa 2 h 58 min 11 s en el ejemplo calculado. Incluye viaje, esperas, paseo y regreso; usamos horarios programados, no tiempos reales desde casa.

## Explicación breve para Entrega

Hemos construido GIPUZKOA 360 para entender cuánto ocupa una visita sanitaria cuando dependemos del autobús: no solo el viaje, también las esperas, el paseo, la consulta y el regreso. Primero exploramos los 88 municipios para detectar dónde merece la pena estudiar el acceso. Después calculamos la visita completa en los trayectos con datos suficientes. La distancia desde un punto municipal no permite saber qué proporción de vecinos vive cerca de un servicio.

En la conversación seleccionada, una consulta de 20 minutos desde las paradas de Zegama al Ambulatorio de Beasain el 29 de septiembre de 2026, a las 09:30, ocupa 2 h 58 min 11 s (10.691 s): de 08:09:37 a 11:07:48. El autobús sale a las 08:12:37; los tres minutos anteriores son espera inicial. Manteniendo todo igual y cambiando la cita a las 09:45, nuestro agente vuelve a calcular: 2 h 23 min 11 s (8.591 s). Son 35 minutos menos entre dos escenarios programados, no un ahorro observado ni una recomendación.

El cálculo de visitas admite Zegama, Segura e Idiazabal y la fecha indicada. Usamos horarios programados y paseo modelado; empezamos y terminamos en paradas, no en el domicilio. No conocemos disponibilidad de citas ni capacidad asistencial, y no hemos verificado la entrada física del centro: conservamos un conflicto de dirección entre fuentes.

Fuentes: Moveuskadi/Goierrialdea (horarios del 28/09 al 27/12/2026), Open Data Euskadi (centros, 20/09/2026), Osakidetza (ficha consultada el 29/09/2026) y © OpenStreetMap contributors, ODbL 1.0 (red obtenida el 29/09/2026). La población procede de Eustat, a 01/01/2025; son fuentes con fechas distintas, no una fotografía temporal homogénea.

El primer enlace es una visualización del análisis territorial inicial, no una demo de la visita sanitaria. El segundo contiene el código y las fuentes. Hemos contrastado las cifras de la conversación con los datos del cálculo.

Somos DeustoAI Labs — Universidad de Deusto: Oier Duñabeitia Berezo, Asier Comba Lopez y Hugo Fernández Díez.

## Cómo funciona

La persona indica origen, fecha, hora y duración de consulta. Nuestro agente comprueba qué puede calcular y usa herramientas de cálculo antes de responder. Para comparar, vuelve a calcular cada visita y utiliza los resultados reales. Explicamos las cifras con unidades, fuentes y límites.

## Ejemplo principal y variación

Pregunta: «Desde las paradas del centro de Zegama, quiero ir al Ambulatorio de Beasain el 29 de septiembre de 2026 para una consulta a las 09:30 que dura 20 minutos y regresar. ¿Qué carga temporal completa resultaría con los datos disponibles?»

Resultado contrastado: 10.691 segundos, equivalentes a 2 h 58 min 11 s, de 08:09:37 a 11:07:48. El autobús sale a las 08:12:37; los tres minutos anteriores son espera inicial.

Variación: «Mantén todo igual pero cambia la cita a las 09:45. Recalcula y compárala con la anterior.»

Resultado contrastado: 8.591 segundos, equivalentes a 2 h 23 min 11 s, de 08:44:37 a 11:07:48. El segundo escenario ocupa 2.100 segundos menos, o 35 minutos. Es una diferencia condicional, no un ahorro observado ni una recomendación. Ambas cifras coinciden con las herramientas ejecutadas en la conversación seleccionada y con los datos del cálculo.

## Datos, fuentes y supuestos

Exploramos 88 municipios con población de Eustat (1 de enero de 2025), límites municipales de geoEuskadi (7 de mayo de 2025) y registros sanitarios de Open Data Euskadi (20 de septiembre de 2026). Las fechas son distintas: no representan una evolución ni una única fotografía temporal. El porcentaje de 75 o más años se obtiene sumando nacidos hasta 1949 y dividiendo por la población total; son recuentos agregados por año, no cumpleaños individuales.

La visita sanitaria está acotada a las paradas de Zegama, Segura e Idiazabal, al trayecto directo GO01 y al punto oficial modelado del Ambulatorio de Beasain. La fecha de cálculo validada es el 29 de septiembre de 2026.

Usamos horarios oficiales de Moveuskadi/Goierrialdea del 28 de septiembre al 27 de diciembre de 2026. La ficha de Osakidetza se consultó el 29 de septiembre; su dirección difiere de un listado sanitario de enero de 2026, por lo que no afirmamos haber verificado la entrada. La red de paseo se obtuvo el 29 de septiembre de 2026: © OpenStreetMap contributors, licencia ODbL 1.0.

Calculamos el paseo a 50 metros por minuto, más 120 segundos por enlace completo y sentido. Aplicamos márgenes de diez minutos antes de la consulta y tres antes del autobús. Son supuestos del cálculo, no tiempos observados ni elecciones humanas comprobadas.

## Un límite que reconocemos

«¿Puedes decirme en tiempo real cuál es la mejor hora de cita desde mi casa?»

No con estos datos. No conocemos el domicilio, las incidencias en tiempo real ni la disponibilidad de citas. Podemos comparar horas concretas desde las paradas admitidas, sin recomendar una cita ni garantizar accesibilidad individual. El registro de un centro tampoco acredita capacidad, calidad o asignación; cero registros no significa ausencia de atención. Los escenarios no prueban causalidad ni predicen resultados futuros.

## Materiales

- [Visualización del screening territorial](https://asier-comba.github.io/Guipuzkoa360/): mapa y ejemplos municipales; no es una demo de la visita sanitaria ni una conversación en vivo.
- [Código y fuentes](https://github.com/Asier-Comba/Guipuzkoa360).
- Conversación sanitaria revisada: pregunta principal, recálculo de la variación, fuentes y límites.

## Defensa breve

Hemos construido GIPUZKOA 360 para mostrar el tiempo que una visita sanitaria ocupa cuando dependemos del autobús. Primero exploramos el territorio; después, donde tenemos datos suficientes, reconstruimos el viaje completo.

Una consulta de veinte minutos desde Zegama a Beasain, a las nueve y media, ocupa 2 horas, 58 minutos y 11 segundos en el escenario calculado. Cambiando solo la cita a las nueve y cuarenta y cinco, nuestro agente vuelve a calcular y obtiene 2 horas, 23 minutos y 11 segundos: 35 minutos menos bajo los mismos supuestos, no un ahorro medido ni una recomendación.

También dejamos claro qué no sabemos: usamos horarios programados y paseo modelado, no tiempos reales desde casa. No verificamos la entrada del centro ni la disponibilidad de citas. El valor es hacer visibles cifras, fuentes y límites para decidir qué merece comprobar en campo.
