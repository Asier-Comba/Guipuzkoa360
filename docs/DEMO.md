# GIPUZKOA 360 · Guion de demostración

**Entrada única:** `resultados/demo.html`. Las vistas de evidencia, escenario y validación son ampliaciones, no tres alternativas de inicio. Los HTML contienen resultados reales guardados y funcionan sin red; una pregunta nueva en lenguaje natural se ejecuta en el portal.

**Destinatario:** personal técnico municipal y territorial que necesita detectar patrones y contrastar diferencias entre municipios antes de profundizar con información sectorial adicional. No se afirma uso real por una administración ni validación con usuarios.

Equipo: Oier Duñabeitia · Asier Comba · Hugo Fernández Díez.

## Pitches

**10 segundos:** «GIPUZKOA 360 ayuda a equipos técnicos a explorar envejecimiento y distancia a servicios, cambiar criterios y comprobar cada cifra con datos oficiales.»

**30 segundos:** «Para detectar patrones territoriales hay que cruzar datos, fijar criterios y entender sus límites. GIPUZKOA 360 convierte una pregunta en una operación sobre población y registros sanitarios oficiales. Podemos cambiar la edad o el criterio y comprobar qué municipios aparecen. Cada respuesta conserva fuentes, parámetros y el significado exacto de la distancia.»

**60 segundos:** «¿Dónde coinciden más envejecimiento y mayor distancia geométrica a atención primaria? El agente interpreta la pregunta, elige una de siete herramientas y calcula sobre datos oficiales de 88 municipios. Con el criterio inicial aparecen siete; al pasar a 75 o más y cambiar el cuantil aparecen cuatro. Podemos revisar la llamada, sus argumentos, las filas usadas y la fuente de una cifra. Esta página muestra cálculos reales guardados; una consulta nueva se ve en el portal. El mapa no clasifica necesidades ni mide tiempo de viaje, capacidad o citas. Sirve para formular una siguiente comprobación humana, con fechas y límites visibles.»

**Frase diferencial:** «Le preguntas al territorio, cambia el cálculo y puedes seguir el rastro de la respuesta».

## Caso estrella

**Coincidencia 65+**, con seguimiento 75+ y sensibilidad q0,85.

| Alternativa | Comprensión y recuerdo | Visual / utilidad urbana | Seguimiento y método | Riesgo |
|---|---|---|---|---|
| Coincidencia 65+ | Una pregunta; 7 → 4 → 2 | Mapa provincial y tabla | Cortes explícitos y parámetros distintos | Interpretarlo como prioridad; aviso junto al hallazgo |
| Aduna | 2.756,2 → 0,0 m, muy memorable | Explica el punto representativo | Cambio hipotético verificable | Confundirlo con atención universal o ubicación recomendada |
| Eibar, salud mental | Preciso, pero requiere explicar dos denominadores | Bueno para profundizar | 1 registro y dos tasas | Confundir presencia con capacidad |

Narrativa: **problema** de cruzar e interpretar datos → **pregunta** territorial concreta → **hallazgo** 7/88 con dos cortes → **utilidad** de contrastar sensibilidad → **límite** de una distancia geométrica → **siguiente pregunta humana** sobre rutas, población dispersa y disponibilidad.

## Preparación

1. Abrir la hero y las tres ampliaciones locales. Dejar la inicial en 65+, q0,75, 2 km.
2. En una sesión autorizada, preparar antes de empezar el portal y la versión probada. Esta rama no toca el portal. El último smoke documentado quedó bloqueado por infraestructura; no prometer disponibilidad.
3. Tener preparada evidencia histórica de tool call si se desea mostrarla. Identificar su versión y fecha; las pruebas previas se repartieron entre versiones.
4. Diferenciar tres etiquetas: **EN DIRECTO**, **CÁLCULO LOCAL GUARDADO**, **EVIDENCIA HISTÓRICA DEL PORTAL**. Un click en el HTML nunca es un recálculo en directo.
5. Ensayar el cambio entre superficies. No leer JSON completo: mostrar operación, parámetros, cifra, fuente y límite.

## Tres minutos · secuencia literal

Máximo **dos consultas live**, sin llamadas simultáneas. El reloj organiza la explicación; no exige una latencia fija.

| Tiempo | Acción | Mensaje / evidencia |
|---|---|---|
| 00:00–00:15 | Problema, destinatario y pregunta | Hero: título, mapa, 7/88. |
| 00:15–00:25 | Enviar la pregunta inicial si el portal está preparado | **EN DIRECTO**; parámetros explícitos. Si sigue bloqueado, anunciar Plan B. |
| 00:25–00:45 | Mostrar mapa y fechas mientras procesa | **GUARDADO**; distancia geométrica, sin rutas. |
| 00:45–01:00 | Enseñar tool + args + salida disponible | Si llegó, portal. Si no, abrir «Cómo se obtuvo» de la hero: una llamada real calculada localmente y guardada. Antes del minuto uno se ve la operación real; no se finge live. |
| 01:00–01:10 | Cotejar 7/88, ambos cortes y selección | Se eligen por cuantiles; 2 km es referencia aparte. |
| 01:10–01:20 | Enviar seguimiento solo si terminó la primera llamada | **EN DIRECTO**: 75+, q0,80, 3 km. Si no, usar evidencia guardada y decirlo. |
| 01:20–01:40 | Explicar qué cambia mientras calcula | Edad y cuantil cambian selección; el umbral no la decide. |
| 01:40–02:05 | Mostrar cuatro municipios y nuevos cortes | Nueva llamada del portal si existe. En la hero, botón de 75+: **GUARDADO**. |
| 02:05–02:35 | Abrir Aduna: base → cambio → resultado | **GUARDADO**: 2.756,2 → 0,0 m. Coincide con el punto de cálculo; no atención universal ni recomendación. |
| 02:35–02:50 | Fuente, periodo y una cifra verificable | Fuente Eustat; opcional Donostia 48.832 / 183.388 × 100 = 26,628 %. |
| 02:50–03:00 | Límite y supervisión humana | Distancia no es tiempo, capacidad o citas. Siguiente pregunta: qué rutas y datos sectoriales faltan. |

**Pregunta inicial:** «¿Qué municipios coinciden en envejecimiento de 65 o más y mayor distancia a atención primaria, con cuantil 0,75, umbral de 2 km y periodo 2025-01-01? Muestra herramienta, criterios, municipios, filas usadas, fuentes y límites.»

**Seguimiento:** «Ahora para 75+, con cuantil 0,80 y umbral de 3 km. Mantén periodo y atención primaria; recalcula y muestra los nuevos cortes y municipios.»

No lanzar una segunda consulta sobre una ejecución pendiente. Si no hay output nuevo, el componente live de esa sesión sigue pendiente aunque la presentación offline continúe.

### Extensión de 30–45 segundos: profundidad y futuro

03:00–03:15: abrir «Validación y evolución»: «Auditamos 31.545 de 31.545 salidas numéricas en un benchmark definido. No son todas las preguntas posibles y conservamos un riesgo de salida extensa».

03:15–03:45: «Cuando cambia la pregunta, cambia qué debemos comprobar. Hoy exploramos distancia y escenarios geométricos. Para medir evolución hacen falta series comparables; para acceso efectivo, movilidad, capacidad y demanda. Proponemos actualización supervisada, con controles y aprobación humana. Eso es evolución propuesta, no una capacidad activa».

## Seis minutos

| Tiempo | Acción | Modo |
|---|---|---|
| 00:00–01:00 | Problema, consulta y tool real antes del minuto uno con recuperación explícita | Una llamada live si es posible; alternativa local guardada |
| 01:00–02:05 | Output inicial, seguimiento y cuatro municipios | Segunda y última llamada live |
| 02:05–03:00 | Aduna, fuente, límite y supervisión | Guardado |
| 03:00–03:15 | Benchmark, definición de trazabilidad y riesgo conocido | Evidencia de validación previa |
| 03:15–03:45 | «Cuando la pregunta cambia» y actualización supervisada | Propuesta, no live |
| 03:45–04:15 | q0,85: quedan Legazpi y Hondarribia; cortes nuevos | Guardado, tercer botón |
| 04:15–04:45 | Comparación Eibar / Tolosa; control Donostia | Guardado |
| 04:45–05:15 | Tool de fuente y ficha Eustat, fechas y 75+ derivado | Guardado en «Cómo se obtuvo» → Fuente demográfica |
| 05:15–05:45 | «¿Cuánto costará la vivienda de Donostia en 2030?» | Explicar fuera de alcance. Usar historia del rechazo solo si se preparó; no fingir una consulta nueva. |
| 05:45–06:00 | Qué necesita una persona para decidir; cierre | Hero |

El límite solicitado de tres consultas live se respeta usando solo dos. Las operaciones restantes se explican con salidas verificables guardadas.

## Latencia y recuperación

Historia: normalmente 26–47 s; un caso mostró output a 28,3 s y terminó antes de 74,3 s. El motor local en milisegundos no es la latencia del portal. No hay SLA demostrado.

Mientras espera: **fuente (15 s) → punto representativo (15 s) → cuantiles (15 s) → límite (15 s)**. No dejar más de 5–10 s de silencio ni inventar porcentaje de avance. A 00:45 abrir la traza guardada si no llegó tool/output; a 60 s sin output mantener el resto de demo en modo guardado.

**Copy exacta para runner ocupado:** «Tenemos la versión probada congelada; el runner está ocupado en este momento. Esta vista muestra el cálculo guardado de la misma herramienta y está contrastada automáticamente con el core. No la presentamos como ejecución live».

| Incidente | Recuperación |
|---|---|
| Sandbox falla | Decir que no hay resultado nuevo; pasar a la misma herramienta guardada. No editar código. |
| Tool tarda | Método/fuente mientras calcula; luego Plan B. No acumular llamadas. |
| Portal sigue pensando tras output | Mostrar el output verificable; distinguirlo de la explicación pendiente. |
| Internet falla | HTML locales; fuente conservada, no fingir apertura del enlace externo. |
| Visual no abre | Abrir la vista secundaria o evidencia JSON. Llevar capturas previstas como respaldo. |
| Selector de versión tarda | Empezar con evidencia guardada; no elegir otra versión sin identificarla. |

No reintentar repetidamente durante los tres minutos. Recuperar la sesión después de la exposición.

## Controles numéricos

| Caso | Valor | Puntero en `resultados/evidencia/product_evidence.json` |
|---|---|---|
| Inicial | 7/88; 23,9730 %; 2.019,2 m | `calls.main.output.summary` |
| 75+, q0,80, 3 km | 4/88; 12,9796 %; 2.138,6 m | `calls.followup.output.summary` |
| 65+, q0,85, 2 km | 2/88; 25,3557 %; 2.308,7 m | `calls.strict.output.summary` |
| Donostia | 183.388 total; 48.832 de 65+; 26,628 % | `calls.donostia.output.data[0]` |
| Eibar / Tolosa, 75+ | 13,744 % / 1.223,6 m; 12,131 % / 1.080,5 m | `calls.comparison.output.data` |
| Aduna | 0 registros internos; 2.756,2 m al más cercano | `calls.aduna.output.data[0].service_indicators.primary_care` |
| Escenario Aduna | 2.756,2 → 0,0 m; −2.756,2 m | `calls.scenario.output.data` |

Metros con un decimal en tablas; porcentajes con tres y cortes con cuatro para cotejar las salidas. Al hablar, «aproximadamente 2,76 km» es válido. Los decimales no son precisión sanitaria. El escenario analiza 88 municipios, afecta a dos y conserva 209 filas usadas: los tres recuentos significan cosas distintas.

## Plan de exactamente cinco capturas

1. **Tool call:** pregunta, operación, argumentos y salida reales. Portal histórico identificado si existe captura limpia autorizada; alternativa «Cómo se obtuvo» etiquetada cálculo local guardado. No fabricar un portal.
2. **Hero 7/88:** pregunta, mapa, ambos cortes, fuentes/fechas y límite. Recorte de contenido sin cambiar cifras.
3. **Seguimiento 4:** opción 75+, q0,80, 3 km, cuatro municipios y cortes 12,9796 % / 2.138,6 m. Etiqueta guardado visible.
4. **Aduna:** título hipotético, base, cambio, resultado y advertencia del cero.
5. **Trazabilidad y fiabilidad:** 31.545/31.545 con definición y riesgo conocido; sin afirmar fiabilidad universal.

Excluir tokens, debug, nombres internos de trabajo, chats del equipo, errores irrelevantes y datos personales. Son capturas de evidencia, no montajes. Este es el plan; no se da por creada ninguna captura que no exista en la entrega.

## Ensayo conceptual con jurado hostil

A los 3 minutos: destinatario y utilidad (00:00), fuente (00:25), tool real explícita (00:45), seguimiento y distinción live/guardado (01:10–02:05), límite y persona (02:50). Antes del minuto 4: definición de trazabilidad, riesgo y futuro etiquetado.

Objeciones ensayadas: «eso solo cambia una vista» → mostrar llamada nueva o reconocer que se usa evidencia guardada; «siete son los prioritarios» → cortes descriptivos y tabla alfabética; «Aduna queda atendida» → punto coincidente, sin capacidad; «100 % fiable» → denominador auditado, no universo de preguntas. Es un ensayo conceptual, no un test con usuarios ni una medición de exposición oral.

## Qué mostrar y qué reservar

Mostrar 2–5 cifras por intervención, unidades, fuente, nueva llamada cuando exista y una limitación. Reservar JSON, hashes y nombres de campo para una objeción. No mostrar el portal de entrega, historial interno, todos los tests como si fueran conversaciones ni el roadmap como producto activo.

Reproducción: `python scripts/release/build_jury_data.py`, después `node scripts/build_jury.mjs`. El gate canónico compara todos los valores con el core; los tests de producto comprueban las evidencias adicionales y la presentación.
