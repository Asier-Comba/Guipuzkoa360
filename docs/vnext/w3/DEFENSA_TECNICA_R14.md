# Defensa técnica R14

## Explicación para el jurado

**Qué problema resolvemos.** Queremos que una persona pueda explorar información territorial y entender la carga temporal de una visita sanitaria hipotética. Una distancia al centro no cuenta por sí sola las esperas, el paseo, la consulta y la vuelta. Mostramos esos componentes y los límites de los datos para que una persona pueda revisar el resultado.

**Qué decide el modelo.** Interpreta la pregunta, identifica la operación apropiada, pide los datos que falten y convierte lo solicitado en parámetros. En un seguimiento conserva lo que sigue vigente y cambia lo pedido. Después explica la evidencia recibida. Un valor enviado por el modelo no demuestra que lo haya elegido el usuario: distinguimos petición, supuesto y valor predeterminado.

**Qué calcula el motor.** Valida los parámetros y la cobertura; busca combinaciones de ida y vuelta admitidas por el piloto; incorpora el paseo modelado, los márgenes y la duración hipotética de la consulta; suma los componentes. Devuelve también fuentes, periodos y restricciones. La cifra sanitaria se obtiene de este cálculo determinista. El modelo no tiene autorización para completar una cifra ausente.

**Qué datos usa.** La parte territorial utiliza las tablas preparadas de municipios, demografía y registros de servicios, con sus respectivas fuentes y periodos. Un registro de servicio no acredita personal, capacidad ni cita disponible. El piloto sanitario utiliza el horario GTFS de Goierrialdea, información oficial del centro y una red peatonal derivada de OpenStreetMap, junto con parámetros explícitos del modelo de paseo. La cobertura validada del cálculo sanitario es una fecha concreta, tres orígenes y el destino admitido. Las fuentes no son todas del mismo año o día.

**Por qué cambia la carga al cambiar la hora de la cita.** Los autobuses tienen salidas discretas. Mover una consulta quince minutos puede cambiar la espera y la combinación de regreso; la carga completa no cambia necesariamente quince minutos. Nuestro contraste offline comprobado produce una diferencia de treinta y cinco minutos entre dos escenarios, manteniendo los demás parámetros. Es una diferencia condicionada entre horarios programados y paseos modelados; no es un ahorro observado ni una recomendación de la mejor hora. Todavía no se ha demostrado esa secuencia con el agente corregido en el portal.

**Qué no sabemos.** No sabemos si existe esa cita, si hay capacidad asistencial, qué centro corresponde a una persona o si el trayecto será accesible para ella. La entrada física del centro no está verificada y existe un conflicto de dirección entre fuentes que conservamos visible. Tampoco incorporamos todas las barreras, pendientes o condiciones temporales del paseo. Un dato ausente no demuestra ausencia de servicio o transporte.

**Por qué no es realtime ni door-to-door.** Usamos un horario estático, no la posición ni la puntualidad real del vehículo. El trayecto parte de paradas admitidas y termina en un punto oficial modelado del centro; no parte del domicilio ni llega a una puerta comprobada. Por eso no garantizamos hora de llegada ni acceso físico.

**Por qué RAG no entró.** En la comparación documental con el mismo corpus y preguntas, la alternativa recuperó mejor algunos documentos y redujo contexto, pero empeoró el soporte completo de las respuestas evaluadas: de catorce de quince a once de quince. No bastaba con recuperar más. Se dejó fuera del candidato; esa prueba documental no demuestra un resultado del modelo en producción.

**Cómo sabemos que una cifra es correcta.** Conservamos la petición efectiva, las unidades, los componentes y las fuentes. Comparamos la salida del motor con casos de referencia publicados por ingeniería y contrastamos cálculos seleccionados directamente contra las filas del horario y la geometría usada. Por ejemplo, el total debe coincidir con la suma de sus componentes. Además comprobamos que la nueva interfaz devuelve el mismo resultado completo que la llamada estructurada original. Estas pruebas sostienen la corrección del cálculo dentro de su alcance; no demuestran que las hipótesis describan un viaje real.

## Estado que debemos decir hoy

La interfaz corregida y el motor pasan sus comprobaciones offline y la revisión independiente de Oier. La versión anterior falló al enviar texto libre en vez de parámetros estructurados y respondió reconociendo el error, sin inventar una cifra.

Después de esa aceptación creamos una versión privada distinta y probamos el caso principal una sola vez. El agente eligió la herramienta correcta y envió campos separados, pero añadió un plazo de regreso vacío que la herramienta rechazó. Dos intentos internos devolvieron ese error y el tercero no pudo crear el entorno de ejecución. La respuesta final reconoció que no había un resultado válido y no inventó una duración. No está demostrada una causa en Studio o en el modelo para ese valor vacío.

Por eso detuvimos el lote: siguen sin probarse el cambio de hora, la duración, la explicación numérica de fuentes, el intento adversarial y la sesión limpia. Hemos usado cinco de los doce mensajes autorizados. En un control offline, omitir ese único plazo vacío permite calcular el caso, pero eso no equivale a que el agente lo haya resuelto. Hay que revisar la generación de opcionales y aceptar cualquier candidato nuevo antes de volver al portal. El problema de comunicación de fuentes anterior tampoco queda cerrado sin una respuesta numérica nueva que podamos revisar.

Si esas pruebas pasan, podremos declarar que está listo para recibir feedback. Seguirán pendientes el benchmark final, el holdout y la decisión humana de publicación. El HTML sanitario actual es un artefacto explicativo offline.

## Evidencia para quien quiera comprobarlo

- [Estado actual y gates](RELEASE_READINESS_R14.json).
- [Handoff y ubicación de los artefactos](HANDOFF_R14.md).
- [Plan de los ocho mensajes, congelado](SMOKE_PLAN_R14.json).
- [Paridad de la interfaz](../../../resultados/vnext/r14/parity.json).
- [Contraste de componentes y periodos](../../../resultados/vnext/r14/truth_pack_contrast.json).
