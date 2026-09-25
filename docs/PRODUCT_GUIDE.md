# Guía de producto · GIPUZKOA 360

## Para qué sirve y cómo empezar

Para personal técnico municipal y territorial que explora patrones y contrasta municipios antes de profundizar con información sectorial. No hay una implantación administrativa o validación de usuarios acreditada.

Abra **[la hero](../resultados/demo.html)** localmente. Verá pregunta, 7/88, mapa, criterios, fuentes y límite. Los resultados están guardados: funcionan sin red, con JavaScript permitido. Una nueva pregunta en lenguaje natural requiere el portal. Los enlaces externos a fuentes sí necesitan Internet.

### Tres niveles, una experiencia

- **Primera lectura:** pregunta, hallazgo, mapa y explicación del límite.
- **Análisis:** botones de criterios, selector municipal, tabla, comparación y escenario.
- **Auditoría:** «Cómo se obtuvo» muestra herramienta, parámetros, periodo, unidad, filas, fuentes, método y límites. El JSON completo está en un segundo desplegable.

## Qué preguntar

| Pregunta | Operación que puede resolverla |
|---|---|
| ¿Qué población e indicadores tiene Aduna? | Resumen territorial |
| Compara Eibar y Tolosa para 75+ y atención primaria | Comparación |
| ¿Qué proporción municipal tiene 65 o más años? | Envejecimiento |
| ¿A qué distancia geométrica está el registro más cercano? | Distancia a registros |
| ¿Dónde coinciden envejecimiento y mayor distancia? | Coincidencia |
| ¿Qué cambia si añadimos o retiramos un registro? | Escenario hipotético |
| ¿De dónde sale esta cifra y qué limita su uso? | Fuentes |

En una conversación nueva, especifique grupo de edad, categoría, periodo y criterio. Ejemplo completo: «Coincidencia de 65+, atención primaria, cuantil 0,75, umbral 2 km y periodo 2025-01-01». En un seguimiento puede decir «Ahora para 75+, cuantil 0,80 y 3 km; mantén periodo y categoría». Compruebe que aparece una llamada nueva con esos parámetros.

## Cambiar edad y criterio

Los tres botones del HTML seleccionan ejecuciones guardadas, no vuelven a calcular. Permiten contrastar 7 → 4 → 2. Para otro criterio, use el agente y revise el nuevo output; esta vista no lo incorporará automáticamente.

**65+ / 75+:** proporción del grupo sobre el total municipal. El 75+ se deriva de nacidos hasta 1949 para 01/01/2025; la transformación se explica en la ficha.

**Cuantil:** cada indicador se ordena y se calcula su corte por interpolación. Se destaca quien iguala o supera ambos cortes. q0,75 no significa que aparezca exactamente el 25 % de municipios: hay empates y se intersectan dos condiciones.

**Umbral:** referencia adicional en kilómetros. La columna «Dentro de 2 km» indica si el registro más cercano queda dentro de esa distancia. **No sustituye los cuantiles ni decide qué municipio queda destacado.** Dos kilómetros es un parámetro exploratorio, no un estándar sanitario acreditado.

**Orden de tabla:** alfabético, no prioridad de inversión. El patrón rayado del mapa equivale a «cumple ambos cortes»; el borde señala el municipio consultado.

## Municipio, registro y distancia

Use el selector para municipios pequeños. En la vista «Evidencia», filtre por nombre; admite tildes o su omisión, por ejemplo Oñati/onati. Un filtro sin coincidencias habla de esa lista, no de ausencia de población o servicios.

Un **registro** es una entrada del catálogo sanitario de la categoría indicada. No equivale a personal, capacidad, calidad o citas. Puede haber varios registros asociados a ubicaciones próximas. Los 148 registros no son 148 unidades de capacidad asistencial.

La **distancia geométrica** se mide en línea recta desde un punto representativo municipal. No está ponderado por población ni usa rutas. «Proximidad» aquí se refiere únicamente a esa distancia. No permite convertir kilómetros a minutos.

## Verificar fuentes y una cifra

Abra «Fuentes»: Eustat 2025, geoEuskadi 2025 y registros sanitarios 2026. Son tres fechas distintas. La ficha añade transformación, unidad, licencia y límites; el identificador técnico está en esa capa y en la traza.

En «Evidencia», Donostia muestra 48.832 personas de 65+ sobre 183.388 habitantes: 26,628 %. Los recuentos se contrastan directamente con el CSV oficial versionado, no solo entre dos pantallas. Los decimales de la interfaz permiten cotejar la salida, no acreditan precisión de atención individual.

## Qué es el escenario de Aduna

**Base:** registro más cercano a 2.756,2 m del punto representativo. **Cambio:** añadir hipotéticamente un registro en ese mismo punto. **Resultado:** 0,0 m; diferencia −2.756,2 m. También cambia Zizurkil.

El cero es consecuencia de la ubicación elegida para el cálculo. No significa que todos los residentes estén a cero metros, que exista un centro nuevo o que debamos construirlo ahí. Se mantienen constantes los demás datos. Una persona debe revisar demanda, rutas, presupuesto, capacidad y viabilidad.

Cero registros de atención primaria dentro de Aduna no implica cero médicos o atención: el catálogo y la medida tienen un alcance más estrecho.

## Qué no preguntar como si ya estuviera cargado

No hay tiempos de viaje, citas, capacidad, demanda futura, precios de vivienda ni predicciones. La coincidencia no demuestra causalidad. Una pregunta fuera del alcance necesita una explicación, no una cifra inventada.

| Situación | Mensaje y siguiente paso |
|---|---|
| Municipio desconocido | Revisar nombre en el selector; no convertirlo en cero. |
| Categoría inválida | Revisar las categorías disponibles: atención primaria, hospital, salud mental y otros registros sanitarios. |
| Fuente no cargada | Consultar fichas; no inventar referencias. |
| Periodo no soportado | Usar la fecha disponible o explicar que hace falta otra instantánea. |
| Capacidad / previsión solicitada | Explicar que esos datos o modelos no están disponibles. |
| Runner ocupado | Pasar a evidencia guardada, identificarla y conservar la traza del intento. |

## Cómo leer validación y futuro

El [centro secundario](../resultados/control_center.html) explica cada KPI con definición, numerador, denominador, origen y límite. «31.545/31.545 trazables» se limita al benchmark; no acredita todas las respuestas posibles. Los tests Python/Node mostrados son los de la base documentada; los tests nuevos de producto se reportan por separado en el handoff.

La salida extrema de 20.155 caracteres sigue sin demostración en portal. El último smoke quedó bloqueado por infraestructura. Las latencias del motor local no representan la conversación completa.

«Cuando la pregunta cambia» separa **HOY** de **EVOLUCIÓN PROPUESTA** y **REQUIERE NUEVOS DATOS**. Actualización supervisada y mejora con aprobación humana son propuestas. No hay autoactualización ni autoedición activa. El prototipo publicado en `171b6cb` separa planificación, cálculo, verificación y composición deterministas. Recibe intenciones estructuradas: no interpreta lenguaje natural ni ejecuta cuatro modelos. Se muestra como prototipo offline, no activo en el portal. Las siete herramientas actuales no son siete agentes.

## Teclado y pantalla pequeña

Tab recorre navegación, criterios, selector y desplegables; Enter/Espacio activan botones y detalles. El selector ofrece la alternativa al click en polígonos. Las tablas tienen desplazamiento horizontal dentro de su región cuando no caben, sin desplazar toda la página. No se afirma certificación WCAG completa.

Para presentar, use el [guion de 3 minutos y extensión de futuro](DEMO.md). Para objeciones, [44 respuestas con evidencia](JURY_QA.md).
