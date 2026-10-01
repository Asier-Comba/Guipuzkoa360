# GIPUZKOA 360

DeustoAI Labs — Universidad de Deusto

Oier Duñabeitia Berezo · Asier Comba Lopez · Hugo Fernández Díez

## Resumen listo para pegar

GIPUZKOA 360 ayuda a equipos técnicos de movilidad, cuidados y planificación territorial a detectar dónde merece estudiar el acceso sanitario y, en corredores con datos disponibles, explorar cómo cambia la carga temporal de una visita sanitaria completa según el origen, la hora de cita y su duración.

**Pregunta:** ¿Cómo cambia la carga temporal de una visita sanitaria para personas que dependen del transporte público cuando cambia el municipio de origen, la hora de la cita o su duración?

**Territorio:** Gipuzkoa. Análisis municipal y ejemplo sanitario acotado al corredor GO01, con orígenes en Zegama, Segura e Idiazabal y destino en el punto oficial modelado del Ambulatorio de Beasain.

## Cómo se utiliza

Se plantea una pregunta en lenguaje cotidiano indicando origen, fecha, hora y duración de consulta. Las herramientas calculan el escenario con los datos disponibles y permiten revisar sus componentes, fuentes y límites. Cambiar un dato requiere un cálculo nuevo; no convierte el escenario en una recomendación. Para comparar escenarios, el agente ejecuta cada visita individualmente, observa sus resultados y solo compara salidas válidas; no envía un lote de visitas a una única tool. Si cambia el origen, presenta los resultados lado a lado, sin calcular una diferencia numérica entre orígenes.

## Qué permite comprender

No basta con saber que hay un centro cerca: la combinación de horarios de ida, consulta, paseo modelado y regreso puede cambiar la carga temporal completa. En el cálculo offline contrastado del 29/09/2026 desde Zegama, una consulta de 20 minutos a las 09:30 supone 10.691 s; a las 09:45, 8.591 s. La diferencia programada/modelada es −2.100 s / −35 min. No es un ahorro observado ni demuestra una «mejor hora».

## Qué no puede afirmar

Los horarios son GTFS estático, no tiempo real. El origen es una parada y el paseo está modelado: no es un viaje real puerta a puerta. El punto oficial del centro no es una entrada física verificada. Un registro sanitario no informa de capacidad, citas ni calidad; el destino tampoco implica centro asignado. Un escenario no es una recomendación; correlación no es causalidad y cero registros no significa ausencia de atención.

## Diferenciación acotada

Nos diferenciamos del alcance publicado de CityScope Gipuzkoa al centrar el análisis en la sincronización temporal de una visita sanitaria ida/vuelta. Es una diferencia de enfoque, no una afirmación de primacía, superioridad ni ausencia de trabajos ajenos. [Alcance publicado por MIT](https://www-prod.media.mit.edu/projects/cityscope-gipuzkoa-accesibility-tool/overview/).

## Defensa técnica de 60–90 segundos

Una consulta de veinte minutos puede ocupar bastante más tiempo cuando dependemos del autobús. GIPUZKOA 360 ayuda a entender dónde merece estudiar ese problema y, donde hay datos, qué parte de la carga temporal corresponde al viaje, al paseo, a la espera y a la consulta.

Nuestro ejemplo es Zegama–Ambulatorio de Beasain, el 29 de septiembre de 2026. Manteniendo origen y duración, el cálculo programado y modelado pasa de 10.691 a 8.591 segundos al cambiar la cita de las nueve y media a las nueve y cuarenta y cinco. Son 35 minutos de diferencia entre dos escenarios, no un ahorro medido ni una recomendación de cita.

Cada cifra puede revisarse contra horarios oficiales, el punto registrado del centro, la red peatonal y la fórmula del paseo. No afirmamos tiempo real, entrada verificada, disponibilidad médica ni centro asignado. La utilidad es hacer visibles los supuestos para que un equipo técnico decida qué merece comprobar en campo.

La matemática está contrastada offline; la última prueba del agente real, R14/M05, falló al generar un parámetro opcional vacío. El candidato R15 elimina esos opcionales de la interfaz pública, pero todavía debe superar aceptación independiente y una nueva prueba real. No presentamos el HTML ni este cálculo como prueba de que el agente real ya funciona.

## Materiales seleccionables tras cerrar el gate

- [Demo pública](https://asier-comba.github.io/Guipuzkoa360/): visualización explicativa, no prueba del agente sanitario real.
- [Repositorio](https://github.com/Asier-Comba/Guipuzkoa360): cálculo, fuentes y evidencia reproducible.
- Una conversación real de principal, variación y límite **cuando exista y esté validada**; no sustituirla por HTML.

El prototipo RAG no mejoró suficientemente el soporte sobre el corpus pequeño y quedó fuera. No está «roto» ni se exige RAG para este problema.

BORRADOR: agente PENDING_FINAL_AGENT_GREEN; track PENDING_HUMAN_SELECTION; confirmación/publicación PENDING_HUMAN_GATE. Este texto no cambia campos del portal.
