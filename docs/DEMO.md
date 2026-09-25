# Demostración de GIPUZKOA 360

La vista principal es `resultados/demo.html`. Reutiliza el diseño territorial del equipo y añade las tres
consultas provinciales verificadas y el escenario de Aduna. Es un HTML autocontenido con resultados
calculados y guardados. La conversación en directo se enseña en el portal; nunca se presenta el HTML como
una ejecución en vivo.

## En diez segundos

«GIPUZKOA 360 permite preguntar dónde coinciden envejecimiento y mayor distancia a servicios sanitarios,
recalcular los criterios y comprobar cada cifra en su fuente.»

## En treinta segundos

«Combinamos población, geometría municipal y 148 registros sanitarios de fuentes oficiales. El agente
elige entre siete operaciones deterministas y responde con cifras, periodo y límites. Esta consulta
analiza los 88 municipios y destaca siete; cambiar el grupo de edad y el cuantil cambia el resultado.
No confundimos distancia con tiempo de viaje ni coincidencia con causalidad: es apoyo exploratorio para
una persona técnica, con trazabilidad y supervisión.»

## Recorrido de tres minutos

| Tiempo | Acción | Mensaje |
|---|---|---|
| 0:00–0:25 | Presentar pregunta y destinatario | Personal técnico que necesita contrastar diferencias municipales. |
| 0:25–0:35 | Enviar pregunta principal en la versión privada validada | 65+, atención primaria, q0,75, 2 km, 2025-01-01. |
| 0:35–1:15 | Mientras calcula, mostrar mapa y fuentes del HTML | Aclarar que son resultados guardados; explicar periodos y punto representativo. |
| 1:15–1:45 | Volver a la traza del portal si hay output | Leer herramienta, argumentos y siete municipios; 88 filas y dos cortes. |
| 1:45–2:00 | Enviar «Ahora para 75+, q0,80 y 3 km» | Debe existir una llamada nueva. |
| 2:00–2:35 | Mostrar el escenario guardado de Aduna | Es una hipótesis geométrica; 2.756,2→0,0 m, no una predicción. |
| 2:35–3:00 | Contrastar los cuatro municipios del seguimiento | Cerrar con la limitación y el uso bajo supervisión. |

## Recorrido de seis minutos

1. Minuto 0–1: pregunta, datos y primera llamada; enseñar las fuentes mientras procesa.
2. Minuto 1–2: mostrar output real y respuesta; contrastar lista, cortes y filas con la hero.
3. Minuto 2–3: cambiar a 75+, q0,80, 3 km; enseñar nueva llamada y cuatro municipios.
4. Minuto 3–4: elegir el resultado guardado 65+, q0,85: quedan Legazpi y Hondarribia. Explicar que cambia
   el cuantil, no un corte fijo del 25 %. Abrir tabla completa y seleccionar un municipio en el mapa.
5. Minuto 4–5: escenario Aduna, baseline, hipótesis y diferencia; explicar por qué cero registros internos
   no acredita ausencia de atención. Si se ejecuta en portal, enseñar sus argumentos y output.
6. Minuto 5–6: una pregunta hostil de `JURY_QA.md`, reproducibilidad y supervisión. Mostrar validación,
   sin recitar el recuento de tests como si fueran conversaciones.

## Plan de latencia y recuperación

Las observaciones históricas del portal suelen ocupar 26–47 segundos. Un caso tardó 74,3 segundos en
completar la respuesta aunque su output ya era visible a 28,3 segundos. No prometer un SLA. El cálculo
local medido en milisegundos no incluye inferencia, coordinación ni arranque del sandbox.

Si aparece «runner ocupado», explicarlo, conservar la traza y pasar al cálculo guardado claramente
rotulado. No cambiar código ni lanzar llamadas concurrentes. Como máximo tres intentos separados. Sin
output real, no declarar completada la cadena conversacional. Si pasan 60 segundos sin output, detener
el ensayo y documentar en qué etapa quedó. El paquete offline permite seguir explicando sin fingir live.

## Cifras de control

| Caso | Control |
|---|---|
| 65+, q0,75, 2 km | 7; 23,973 %; 2.019,2 m; 88 filas |
| 75+, q0,80, 3 km | 4; 12,9796 %; 2.138,6 m; 88 filas |
| 65+, q0,85, 2 km | 2; 25,3557 %; 2.308,7 m; 88 filas |
| Donostia | 183.388 habitantes; 48.832 de 65+; 26,628 % |
| Eibar/Tolosa, 75+ | 13,744 % / 1.223,6 m; 12,131 % / 1.080,5 m |
| Aduna hipotético | 2.756,2→0,0 m; diferencia −2.756,2 m |

Mostrar: pregunta, argumentos, output, fuente, mapa y una limitación útil. No mostrar versiones antiguas
como si fueran actuales, paneles internos innecesarios, códigos de prueba, previsiones no soportadas ni
la sección de publicación durante el ensayo. El dato de 148→149 del escenario cuenta todos los registros
sanitarios, no únicamente atención primaria.
