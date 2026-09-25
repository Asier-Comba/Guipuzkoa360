# Preguntas difíciles del jurado

Respuestas orientadas a 15–25 segundos hablados. Las referencias son comprobables en el repositorio;
ninguna respuesta atribuye una ejecución local a una conversación del portal.

1. **¿Por qué no basta un dashboard?** Un dashboard presenta vistas previstas. Aquí la conversación
   selecciona una de siete operaciones, normaliza los parámetros y vuelve a calcular. El mapa acompaña:
   al cambiar edad o cuantil debe verse una llamada nueva. Evidencia: trazas privadas y casos A–H.
2. **¿Cómo sé que no inventa?** Las cifras proceden de herramientas deterministas, con periodo, unidades,
   método y fuentes. Contrastamos salidas con los datos versionados e introducimos errores deliberados.
   Eso hace la respuesta auditable; la persona sigue revisando el razonamiento del modelo.
3. **¿Cómo sé que recalcula?** En el portal miramos una nueva llamada y sus argumentos. El caso 65+, q0,75
   destaca siete; el seguimiento 75+, q0,80 destaca cuatro. La demo guardada permite contrastarlos, pero
   no demuestra por sí sola que haya ocurrido una nueva conversación.
4. **¿Por qué esos años?** Son las referencias de los snapshots oficiales disponibles: población de
   enero de 2025, geometría de mayo de 2025 y servicios de septiembre de 2026. Declaramos la diferencia;
   no los presentamos como una fotografía simultánea. Cada fuente y transformación está documentada.
5. **¿Qué significa acceso aquí?** Es proximidad geométrica desde un punto representativo municipal al
   registro más cercano. No son trayectos, minutos, citas ni capacidad. Por eso preferimos mostrar metros
   y explicar el método antes de interpretar necesidades sanitarias.
6. **¿Esto demuestra causalidad?** No. Encontramos municipios que alcanzan dos cortes estadísticos a la
   vez. No controlamos variables de confusión ni tenemos un diseño causal. El resultado orienta nuevas
   preguntas; no demuestra que el envejecimiento cause peor atención.
7. **¿Es una predicción?** No. El escenario modifica un supuesto y recalcula la distancia dejando el
   resto constante. No modela demanda, comportamiento ni efectos sanitarios. Se rotula como hipotético
   y conserva situación inicial, resultado y diferencia.
8. **¿Dónde deberíamos construir?** Estos datos no bastan para recomendar una ubicación. Faltan demanda,
   capacidad, red de transporte, costes y conocimiento local. Podemos explorar un punto hipotético y
   explicar su efecto geométrico; la decisión necesita evaluación profesional y participación.
9. **¿Qué ocurre con municipios pequeños?** Una variación pequeña en personas puede mover bastante el
   porcentaje. Por eso mantenemos denominadores y recuentos y evitamos interpretar una tasa aislada
   como necesidad. La selección es territorial y exploratoria, no una clasificación de habitantes.
10. **¿Qué pasa con datos ausentes?** El core valida columnas, tipos, claves y periodos. Una ausencia
    produce un error o advertencia controlada según el contrato, no un cero inventado. Veinte inyecciones
    de corrupción fueron rechazadas; no se extrapolan primeras filas.
11. **¿Qué ocurre si cambia la fuente?** El resultado actual usa un snapshot versionado. Una actualización
    requiere repetir preparación, validación, hashes y casos de referencia. No sustituyemos fuentes
    silenciosamente ni afirmamos que los resultados guardados representen datos nuevos.
12. **¿Cómo se reproduce?** El repositorio contiene datos, código y comandos de validación. La demo se
    regenera con el mismo core y se compara íntegramente con sus salidas. El benchmark explicita semilla,
    combinaciones y denominadores; el paquete fija sus bytes y metadatos.
13. **¿Qué supervisa una persona?** La pertinencia de la pregunta, la comparación entre fechas, los
    supuestos del escenario y la interpretación final. También contrasta cifras y fuentes. El agente
    agiliza cálculos; no sustituye una decisión sanitaria o administrativa.
14. **¿Por qué un punto representativo?** Ofrece un origen reproducible dentro del municipio y evita
    algunas geometrías problemáticas del centroide. No representa dónde vive la población. Mantenemos
    esa limitación visible y no atribuimos la distancia a cada vecino.
15. **¿Por qué distancia euclídea?** Es una medida simple, transparente y reproducible en coordenadas
    métricas. Sirve para explorar diferencias geométricas. La orografía y las redes pueden cambiar mucho
    un trayecto real; por eso no convertimos metros en minutos.
16. **¿Qué pasa si el runner tarda?** Lo mostramos como un límite operativo. Mientras procesa, explicamos
    mapa, fuentes y método guardados. Si está ocupado, conservamos la traza y hacemos intentos limitados.
    Nunca presentamos un resultado precalculado como una ejecución en vivo.
17. **¿Por qué confiar en las cifras?** Además del contrato, recalculamos los casos desde los datos
    oficiales conservados, revisamos uniones y geometría e intentamos romper las validaciones. La
    trazabilidad permite comprobar cada número. No afirmamos infalibilidad ni impacto social validado.
18. **¿Puede usar datos no cargados?** El agente privado tiene Internet desactivado y un contexto
    explícito de archivos. No puede afirmar vivienda, capacidad o demanda futura que no figure allí.
    Una fuente desconocida debe producir un rechazo controlado, no metadatos inventados.
19. **¿Qué no puede responder?** No puede predecir precios, garantizar citas, medir calidad asistencial
    ni recomendar inversiones con esta evidencia. Sí compara estructura demográfica y proximidad,
    explica fuentes y recalcula escenarios geométricos dentro del alcance cargado.
20. **¿Cuál es la mayor limitación?** La distancia desde un único punto municipal no describe la
    accesibilidad real de las personas. Las fechas tampoco son simultáneas. Es útil para formular y
    contrastar preguntas territoriales, con límites explícitos y revisión humana.
21. **¿Aduna no tiene médicos?** No podemos concluirlo. Hay cero registros internos de atención primaria
    en este snapshot y el más cercano está a 2.756,2 metros del punto de cálculo. Un registro municipal
    no describe profesionales disponibles, desplazamientos, cobertura ni atención efectiva.
22. **¿Los siete municipios se eligieron a mano?** No. El cuantil 0,75 se calcula sobre las 88 filas y se
    exigen ambos cortes. Elevarlo a 0,85 reduce el conjunto a Legazpi y Hondarribia. Las listas completas
    se verifican automáticamente; no hay una regla fija del 25 %.
23. **¿Veinte mil caracteres no son demasiados?** El caso extremo de umbral 1→10 km cambia 88 municipios
    y conserva su evidencia. El escenario de Aduna es menor y tiene ejecución privada histórica. La
    latencia del extremo en portal no está demostrada: mantenemos ese riesgo visible sin truncar filas.
24. **¿Lo habéis hecho sin IA?** No hacemos esa afirmación. El equipo utilizó asistencia de IA para
    desarrollo y evaluación. Las contribuciones se documentan por artefactos y commits, sin inventar
    horas ni autoría manual exclusiva. Las personas revisan la evidencia y asumen las decisiones.
