# GIPUZKOA 360 · Preguntas del jurado

44 respuestas breves, pensadas para 15–25 segundos a ritmo normal (algunas requieren menos). **★** identifica las 13 objeciones críticas. Los punteros son para quien presenta; no hay que leer rutas en voz alta.

**E** = [evidencia guardada](../resultados/evidencia/product_evidence.json). **P** = [validación conversacional previa del portal](PORTAL_EVIDENCE_RC2.md), realizada el 24/09/2026 en distintas versiones de la familia del runtime congelado. **H** = [hero](../resultados/demo.html). Los cálculos E son ejecuciones locales reales; P es evidencia histórica, no una nueva ejecución durante esta revisión. El smoke posterior quedó bloqueado por infraestructura, según `docs/FINAL_RELEASE_GATE.md`.

## Problema y producto

### 01 · PROBLEM · ¿Qué problema resolvéis?

Convertimos una pregunta territorial en un cálculo que se puede revisar. Cruzamos envejecimiento y distancia geométrica a registros sanitarios para explorar patrones. Una persona puede cambiar el criterio y comprobar qué cambia antes de plantear un estudio más profundo.

**EVIDENCE POINTER:** H, pregunta y tarjetas de cambio; E → `calls.main`, `calls.followup`.

### 02 · DASHBOARD · ★ ¿Por qué no un dashboard?

El agente interpreta la consulta y elige una herramienta con parámetros explícitos. Una nueva pregunta puede producir una llamada diferente. El HTML es una explicación de resultados guardados; la prueba del comportamiento conversacional está en las llamadas y el seguimiento del portal.

**EVIDENCE POINTER:** P → G-04 y G-06; E → argumentos iniciales y de seguimiento.

### 03 · PUBLIC ADMINISTRATION · ¿Para quién sería útil?

Para equipos que exploran diferencias territoriales y necesitan explicar cómo obtuvieron una cifra. Podría ayudar a preparar una reunión técnica. Todavía necesitaría validación con usuarios de la administración, sus procedimientos y datos de movilidad y capacidad antes de integrarse en decisiones reales.

**EVIDENCE POINTER:** H → método y siguiente pregunta humana; [metodología](METODOLOGIA.md), límites. Es un uso propuesto, no una implantación acreditada.

### 04 · TOOLS · ¿Qué herramientas tiene?

Siete: fuente, resumen territorial, comparación, envejecimiento, distancia a servicios, coincidencia y escenario. Cada una devuelve datos y contexto verificable. Elegimos dos llamadas para la demo en directo; ejecutar todas consumiría tiempo sin explicar mejor el producto.

**EVIDENCE POINTER:** P → cobertura de las siete tools; `agentes/gipuzkoa360/portal/main.py`.

## Datos, fechas y fuentes

### 05 · DATA · ¿Qué datos usáis?

La instantánea preparada contiene 88 municipios y 148 registros sanitarios públicos. Combina población de Eustat, geometría de geoEuskadi y un catálogo sanitario de Open Data Euskadi. Son agregados municipales y registros de centros, no historiales clínicos ni ubicaciones de pacientes.

**EVIDENCE POINTER:** `datos_preparados/runtime_manifest.json`; E → `sources`; `tests/test_real_data_integration.py`.

### 06 · YEARS · ★ ¿Por qué mezcláis años?

Son las fechas de las fuentes disponibles en esta instantánea, y las mostramos por separado. La población es de enero de 2025 y los registros sanitarios se recogieron en septiembre de 2026. El cruce describe una aproximación territorial; no demuestra evolución ni simultaneidad exacta.

**EVIDENCE POINTER:** H → «Tres fuentes, tres fechas distintas»; E → `sources`, `reference_period` y metadatos de cada salida.

### 07 · SOURCES · ¿Puedo consultar el origen?

Sí. Cada ficha conserva institución, fecha, unidad, licencia, límites y enlace original. La traza incluye el identificador de fuente utilizado por el cálculo. Podemos abrir Eustat o consultar la ficha local si falla Internet, distinguiendo ambos casos.

**EVIDENCE POINTER:** E → `calls.source.output` y `sources`; H → fuentes y trazabilidad.

### 08 · DATA · ¿El grupo de 75+ es un dato directo?

Se suman las personas nacidas en 1949 o antes para la fecha 01/01/2025. Así se evita incluir a quienes cumplen 75 durante 2025, aunque no recoge posibles nacimientos del propio 1 de enero de 1950. La transformación y ese límite se conservan en la ficha.

**EVIDENCE POINTER:** E → `calls.source.output`, `sources[0]`; [FUENTES.md](../FUENTES.md) y [metodología](METODOLOGIA.md).

### 09 · UPDATES · ★ ¿Qué pasa si cambian los datos?

La demo no se actualiza sola. Habría que volver a preparar y validar datos, recalcular resultados y regenerar los HTML, comprobando cambios de cobertura y metodología. Las huellas de los archivos permiten detectar que una evidencia pertenece a otra instantánea.

**EVIDENCE POINTER:** E → `input_sha256`; `scripts/release/build_jury_data.py`; `tests/test_product_jury.py` → fingerprints y reproducibilidad.

## Método y distancia

### 10 · ACCESS · ★ ¿Qué significa exactamente acceso?

Nuestro indicador mide distancia geométrica desde un punto municipal hasta un registro sanitario. Por eso lo llamamos distancia. El acceso efectivo también depende de transporte, capacidad, citas y barreras personales; esas dimensiones no se calculan aquí.

**EVIDENCE POINTER:** H → método y fuentes; E → `calls.main.output.method` y `limitations`.

### 11 · DISTANCE · ★ ¿Por qué un punto representativo?

Permite una medida municipal común y reproducible con los datos disponibles. No representa la distribución de residentes ni está ponderado por población. En municipios extensos o dispersos puede ocultar diferencias grandes; habría que medir desde núcleos habitados para estudiar acceso efectivo.

**EVIDENCE POINTER:** `datos_preparados/runtime_municipality_points.csv`; [metodología geoespacial](METODOLOGIA_GEOESPACIAL.md); H → aviso del método.

### 12 · METHOD · ¿Cómo elegís los municipios señalados?

Ordenamos los valores de cada indicador y calculamos un corte por cuantil. Un municipio se señala si iguala o supera ambos. En el criterio inicial son 23,9730 % de población de 65+ y 2.019,2 metros. No calculamos una puntuación de necesidad.

**EVIDENCE POINTER:** E → `calls.main.output.summary`, `method`; H → tabla alfabética.

### 13 · METHOD · ¿Dos kilómetros es el criterio que los selecciona?

No. Los dos cuantiles determinan la coincidencia. El umbral de kilómetros solo clasifica si el registro más cercano queda dentro o fuera. Por eso mostramos ambas cosas por separado y guardamos los parámetros exactos, para no atribuir al umbral un efecto que no tiene.

**EVIDENCE POINTER:** E → `calls.followup.output.data[*].within_threshold`; H → explicación junto a tabla.

### 14 · DISTANCE · ¿Tres kilómetros son tres minutos?

No podemos convertirlos en minutos. La distancia es en línea recta y no usa carreteras, pendientes ni transporte. Haría falta un cálculo de rutas con un modo y condiciones de viaje definidos; no tenemos esa medida en esta demo.

**EVIDENCE POINTER:** H → «Sin red viaria»; P → red-team, conversión de kilómetros a minutos.

### 15 · METHOD · ¿Por qué tantos decimales?

Las tablas conservan la resolución necesaria para cotejar la salida del cálculo. No es una promesa de precisión sobre la experiencia de una persona. Para hablar podemos redondear a 2,76 kilómetros; el criterio usa el valor del cálculo, no el texto redondeado.

**EVIDENCE POINTER:** [DEMO.md](DEMO.md) → unidades; E → cifras originales; H → nota bajo tabla.

### 16 · BIAS · ★ ¿Por qué confiar en ese mapa?

Los contornos proceden de geoEuskadi y las marcas de la salida de la herramienta. Comprobamos los códigos de los 88 municipios y que mapa y tabla compartan selección. La tabla permite consultar municipios pequeños. El mapa orienta; no modela rutas ni distribución de población.

**EVIDENCE POINTER:** `resultados/evidencia/jury_visual_data.json` → `geometry`, `cases[0].output`; `tests/test_product_jury.py` → map rows; H → leyenda y selector.

### 17 · SMALL MUNICIPALITIES · ★ ¿Qué ocurre con un municipio pequeño?

Un porcentaje puede variar mucho con pocas personas y el tamaño del polígono dificulta verlo. Ofrecemos un selector y una tabla para inspeccionarlo. Aduna ilustra otro límite: cero registros dentro del municipio no significa que su población no reciba atención en otro lugar.

**EVIDENCE POINTER:** [informe](../resultados/informe_principal.html) → Aduna; E → `calls.aduna.output`; H → selector.

### 18 · MISSING DATA · ¿Y si un municipio no tiene datos?

Hay que distinguir una búsqueda sin coincidencias, un municipio no reconocido y un valor ausente. No convertimos esos casos en cero. El ejemplo de Villa GPT devuelve un error estructurado y ninguna fila. Un filtro sin resultados solo habla de esa salida guardada.

**EVIDENCE POINTER:** E → `calls.missing.output`; informe → filtro; `tests/test_product_jury.py` → missing municipality.

## Causalidad, escenarios y control humano

### 19 · CAUSALITY · ¿Más envejecimiento causa peor atención?

No se puede concluir eso. Aquí observamos coincidencia de dos indicadores agregados. Ni medimos calidad de atención ni aislamos causas. La coincidencia sirve para plantear una comprobación posterior con más variables y contexto local.

**EVIDENCE POINTER:** H → límites del método; P → red-team de causalidad.

### 20 · SCENARIOS · ★ ¿Esto predice?

No. El escenario introduce un registro hipotético y recalcula una distancia manteniendo el resto constante. No estima demanda futura ni cómo cambiaría la atención. Base, cambio y resultado aparecen separados y el título dice expresamente «escenario hipotético».

**EVIDENCE POINTER:** [escenario](../resultados/scenario_comparison.html); E → `calls.scenario.arguments` y `output`.

### 21 · DECISION MAKING · ★ ¿Dónde construirías un centro?

Con estos datos no elegiría una ubicación. Puedo mostrar cómo cambia este indicador bajo una hipótesis concreta. Para recomendar una obra faltan demanda, rutas, capacidad, personal, costes y viabilidad; la decisión necesita responsables y validación local.

**EVIDENCE POINTER:** escenario → supuestos; P → red-team sobre recomendación de ubicación.

### 22 · DECISION MAKING · ★ ¿Puede recomendar decisiones?

Puede aportar evidencia para explorar una pregunta y explicar sus límites. Esta demo no acredita recomendaciones automáticas de inversión o cobertura. Una persona decide qué criterios son apropiados, qué información falta y si el análisis sirve para el problema público concreto.

**EVIDENCE POINTER:** H → siguiente pregunta humana; escenario → supuestos; P → límites de recomendaciones.

### 23 · HUMAN OVERSIGHT · ★ ¿Qué controla una persona?

Define la pregunta, elige o revisa criterios, comprueba la herramienta y su salida, valida fuentes y decide si hacen falta más datos. También controla la publicación y cualquier decisión real. El agente deja evidencia para esa revisión; no sustituye esa responsabilidad.

**EVIDENCE POINTER:** E → preguntas y argumentos; H → trazabilidad; [DEMO.md](DEMO.md) → preparación y cierre.

### 24 · SCENARIOS · ¿Aduna pasa a tener atención universal al quedar a cero metros?

No. Añadimos el registro exactamente en el punto desde el que se mide Aduna, por eso ese indicador da cero. No dice dónde vive cada residente ni si el centro podría atenderle. Es una demostración del supuesto geométrico, no de cobertura universal.

**EVIDENCE POINTER:** E → `calls.scenario.arguments` y fila Aduna; escenario → explicación bajo cifras.

### 25 · ACCESS · ¿Cero centros significa cero médicos?

No. Cero significa que el catálogo usado no contiene registros de esa categoría dentro del municipio. No es un censo de profesionales. Aduna tiene cero registros internos de atención primaria, mientras que el registro más cercano está a 2.756,2 metros del punto representativo.

**EVIDENCE POINTER:** E → `calls.aduna.output.data[0].service_indicators.primary_care`; informe → caso Aduna.

### 26 · SCENARIOS · ¿El escenario solo cambia Aduna?

No. Ese punto añadido también reduce la distancia geométrica de Zizurkil. La salida evalúa 88 municipios y muestra dos con cambios. El contador de filas usadas incluye registros de entrada; no debemos interpretarlo como el número de municipios afectados.

**EVIDENCE POINTER:** E → `calls.scenario.output.summary`, `rows_used`, `data`; escenario → tabla de dos filas.

## Comprobación y confianza

### 27 · HALLUCINATION · ★ ¿Cómo sé que no inventa?

No prometemos ausencia absoluta de errores. Comprobamos la herramienta, sus argumentos y salida, fuentes, periodo, unidad y filas usadas. Los tests cotejan resultados con datos reales, y el red-team previo probó peticiones de inventar. Ante una afirmación concreta, abrimos su evidencia.

**EVIDENCE POINTER:** E → cada `calls.*.output`; `tests/test_product_jury.py`; P → ocho formulaciones hostiles.

### 28 · REPRODUCIBILITY · ★ ¿Cómo sé que recalculó?

Si el portal completa el seguimiento, comprobamos una llamada nueva con grupo 75+, cuantil 0,80 y umbral de 3 kilómetros antes de presentarla como ejecución en directo. Los cálculos guardados muestran que cambian los cortes y aparecen cuatro municipios frente a siete. En el HTML cambiamos entre esas salidas guardadas; el botón no ejecuta una llamada nueva.

**EVIDENCE POINTER:** P → G-04/G-06; E → `calls.main` frente a `calls.followup`; H → banner.

### 29 · REPRODUCIBILITY · ¿Podemos verificar una cifra ahora?

Sí: Donostia tiene 183.388 habitantes y 48.832 de 65 o más en el CSV oficial conservado. Dividir 48.832 entre 183.388 y multiplicar por cien da 26,628 % al redondear. El test compara ambos recuentos con el archivo original y la salida mostrada.

**EVIDENCE POINTER:** informe → control Donostia; `tests/test_product_jury.py` → official CSV; `datos_originales/eustat_demografia_2025.csv`.

### 30 · TOOLS · ¿Los números los calcula el modelo de lenguaje?

Los indicadores los calculan herramientas deterministas. El agente interpreta la consulta y redacta la explicación a partir del resultado. Por eso comprobamos separadamente que la salida numérica sea correcta y que la respuesta conversacional no la exagere.

**EVIDENCE POINTER:** `agentes/gipuzkoa360/tools.py`, `metrics.py`; P → calidad de respuestas; E → salida íntegra.

### 31 · PRIVACY · ¿Tratáis datos de pacientes?

Esta instantánea usa población agregada y registros públicos de centros sanitarios. No incluye historias clínicas ni ubicaciones individuales de pacientes. Cualquier ampliación con datos personales exigiría otro diseño y revisión; no es una capacidad acreditada por este prototipo.

**EVIDENCE POINTER:** `datos_preparados/data_contract.json`; [FUENTES.md](../FUENTES.md); E → fuentes.

### 32 · BIAS · ¿Qué sesgos puede tener?

Un punto municipal oculta dispersión y el catálogo no refleja necesariamente toda la oferta efectiva. La mezcla de fechas y la agregación también condicionan la lectura. Los hacemos visibles para que el patrón no se confunda con una evaluación exhaustiva de necesidades.

**EVIDENCE POINTER:** H → fuentes y método; E → `limitations`; [metodología geoespacial](METODOLOGIA_GEOESPACIAL.md).

### 33 · LIMITATIONS · ¿Qué no puede responder?

No calcula tiempos de viaje, citas, capacidad, calidad asistencial ni precios futuros de vivienda. Ante una pregunta fuera del alcance, debe explicarlo en lugar de inventar una cifra. Esa conducta se probó en la validación conversacional previa, con sus límites de cobertura.

**EVIDENCE POINTER:** P → red-team de vivienda 2030, predicción y minutos; [DEMO.md](DEMO.md) → pregunta imposible.

### 34 · LATENCY · ¿Por qué tarda?

Observamos respuestas habitualmente entre 26 y 47 segundos y algún caso más lento. No tenemos una medición que reparta ese tiempo entre componentes. Mientras llega la salida mostramos fuente y método; si falla, pasamos a evidencia guardada claramente etiquetada.

**EVIDENCE POINTER:** P → latencias; [DEMO.md](DEMO.md) → plan de espera y recuperación.

### 35 · METHOD · ¿Por qué Eibar tiene dos tasas de salud mental?

El mismo registro se divide por dos poblaciones diferentes: personas de 65 o más y de 75 o más. Por eso las tasas por 10.000 son distintas. No son capacidad ni disponibilidad del servicio; siempre debe verse el denominador junto al número.

**EVIDENCE POINTER:** E → `calls.eibar.output.data[0].service_indicators.mental_health`; informe → caso Eibar.

### 36 · LIMITATIONS · ¿Qué está demostrado y qué queda por demostrar?

Hay cálculos reproducibles con datos oficiales, controles numéricos y una validación previa de las siete herramientas en conversación. La experiencia puede enseñarse sin red con resultados guardados. Quedan la validación con usuarios reales y las variables necesarias para evaluar acceso efectivo o decidir inversiones.

**EVIDENCE POINTER:** P → cobertura; `tests/test_product_jury.py`; [auditoría de experiencia](HUGO_JURY_HANDOFF.md) → alcance y riesgos.

## Evolución y alcance de la validación

### 37 · METHOD · ¿Por qué dos kilómetros?

Es un umbral explícito para explorar esta consulta, no un estándar sanitario ni una recomendación universal. Se puede cambiar en la herramienta. La selección destacada sigue dependiendo de ambos cuantiles; el umbral solo indica si el registro más cercano queda dentro o fuera.

**EVIDENCE POINTER:** E → `calls.main.arguments`, `calls.followup.arguments`; H → tabla y explicación de criterios.

### 38 · UPDATES · ¿Se actualiza solo?

Hoy usa una instantánea fija. Proponemos una actualización supervisada: fuente, candidato, controles, benchmark, revisión humana y versión. Esa secuencia explica cómo debería incorporarse un cambio; no afirmamos que exista una actualización automática activa ni que las cifras se refresquen solas.

**EVIDENCE POINTER:** [Validación y evolución](../resultados/control_center.html) → «Actualización supervisada»; etiqueta «EVOLUCIÓN PROPUESTA · NO ACTIVA».

### 39 · HUMAN OVERSIGHT · ¿Se automejora?

No se autoedita en producción. La evolución propuesta consiste en observar fallos, medir, proponer cambios y probarlos antes de una aprobación humana. La versión presentada permanece congelada. No atribuimos al agente actual un sistema autónomo de mejora que no esté demostrado.

**EVIDENCE POINTER:** centro de validación → «Mejora bajo supervisión»; E → `runtime_sha`; `docs/FINAL_RELEASE_GATE.md` → identidad.

### 40 · TOOLS · ¿Por qué subagentes?

Existe un prototipo offline con planificación, cálculo, verificación y composición separadas. Son responsabilidades deterministas, no cuatro modelos de IA: recibe intenciones estructuradas y comparte el core. Las siete herramientas actuales no son siete agentes. El prototipo no está activo en el portal.

**EVIDENCE POINTER:** E → `inventory.tools`, `next_prototype`; centro de validación → «PROTOTIPO DE EVOLUCIÓN». Snapshot final publicado en `fddcf05`, con evidencia de `eae3b70`: 77/77 tests del prototipo offline.

### 41 · EVOLUTION · ¿Qué pasa cuando la cobertura mejora?

Primero comprobaríamos qué ha mejorado realmente: menor distancia geométrica no demuestra más capacidad ni mejores citas. Después podrían explorarse las diferencias restantes o la retirada hipotética de un registro. Medir evolución exige series comparables y estudiar acceso efectivo requiere datos adicionales.

**EVIDENCE POINTER:** centro de validación → «Cuando la pregunta cambia»; escenarios del core; E → límites de `calls.scenario.output`.

### 42 · PUBLIC ADMINISTRATION · ¿Cómo lo escalaríais?

Separaríamos cobertura de datos y operación del servicio. Ampliar territorio exige fuentes compatibles, códigos, unidades y controles; operar para más usuarios requiere medir concurrencia, costes y latencia. Son trabajos por validar: el benchmark local actual no acredita un despliegue a gran escala.

**EVIDENCE POINTER:** E → `validation` y `inventory`; [Benchmark](BENCHMARKS.md) → metodología local; [guía](PRODUCT_GUIDE.md) → alcance.

### 43 · REPRODUCIBILITY · ¿Qué significan 72.673 checks y 31.545 trazables?

Los checks son evaluaciones de sujeto por propiedad dentro de un benchmark definido. La trazabilidad cubre 31.545 de 31.545 salidas numéricas auditadas, con periodo, unidad, método y fuentes resolubles. No son conversaciones, ni demuestran que todas las preguntas posibles sean correctas.

**EVIDENCE POINTER:** E → `validation.checks`, `validation.traceability`; centro de validación → definiciones y denominadores; `analisis/final/full_validation.json`.

### 44 · LIMITATIONS · ¿Qué riesgo conocido sigue abierto?

Hay dos riesgos Medium gestionados. M-01: un escenario extremo conserva 66 filas afectadas y genera 20.155 caracteres; no afecta al escenario normal de Aduna y no se trunca para preservar trazabilidad. M-02: en el último smoke, bloqueado por runner ocupado y sin output analítico, el texto de fallback confundió 2 km con el corte de distancia por cuantil. No demuestra un fallo del core. La demo corrige esa lectura y distingue evidencia local, historia conversacional y ejecución nueva.

**EVIDENCE POINTER:** `analisis/final/full_validation.json → issues`; `docs/internal/PORTAL_SMOKE_REFRESH.md` en el handoff final de Work 1; centro de validación → riesgo conocido.
