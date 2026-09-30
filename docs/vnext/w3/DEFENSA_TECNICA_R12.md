# GIPUZKOA 360 · defensa técnica R12

**Producto offline comprobado; conversación sanitaria en Studio bloqueada. No es una release aprobada.**

## Problema y utilidad

Ayudamos a equipos municipales a explorar envejecimiento y presencia de servicios con fuentes, unidades y límites. El screening territorial de 88 municipios identifica coincidencias descriptivas: el cuantil determina los cortes destacados; el umbral es una referencia de distancia. La distancia geométrica no es tiempo de viaje ni prioridad de inversión.

La ampliación sanitaria añade una pregunta concreta: ¿permite un horario programado ir desde unas paradas catalogadas hasta el punto oficial del Ambulatorio de Beasain y volver, incluyendo paseo modelado y consulta? Recibimos como base el screening y sus datos preparados; construimos el coordinador de nueve tools, contrato de evidencia, productor sanitario, validación independiente y visualización importable. Esta atribución describe el repositorio, no acredita lectura de formación privada ni una solución desplegada.

## Recorrido real

Pregunta → modelo proporcionado por Studio → selección de tool y argumentos → cálculo determinista → validación de identidad, fuentes y correspondencia de solicitud → vista acotada para el modelo → respuesta. Los seguimientos deben llamar de nuevo a las tools. El modelo interpreta y explica; las tools calculan. El HTML actual muestra resultados offline guardados y permite importar JSON compatible; no contiene un agente conectado ni recalcula rutas en el navegador.

Fuentes territoriales: Eustat, población a 01/01/2025; geoEuskadi, límites a 07/05/2025; Open Data Euskadi, centros a 20/09/2026. Los 75+ se derivan del año de nacimiento; registros de centros no equivalen a médicos, capacidad ni citas. La visita usa el snapshot GTFS GO01 validado para 29/09/2026, red peatonal OSM fijada, punto sanitario oficial y un perfil modelado de 50 m/min más 120 s por enlace. Las fechas de las fuentes se conservan por función; no se presentan como una observación simultánea.

## Demostración defendible, 2–3 minutos

1. Mostrar **offline** Zegama, 09:30, consulta de 20 min: total 10.691 s, ida y regreso con paradas, paseo y esperas.
2. Seleccionar 09:45: total 8.591 s; diferencia −2.100 s (35 min). El proveedor vuelve a calcular cada solicitud; la página muestra esas salidas guardadas. La cifra se contrastó con filas GTFS, cronología y geometría fijadas en R10 y se conservó igual en el ZIP W2 exacto R12.
3. Mostrar fecha no cubierta: estado desconocido y causa, sin itinerario. Abrir fuentes y límite: puerta no verificada, direcciones conflictivas, paseo estimado y horarios programados aproximados/interpolados (`timepoint=0`). Se requiere revisión humana; no hay reserva ni garantía de puntualidad.

Validación del ZIP baseline `b4feb978…`: 34 casos deterministas, secuencia health→legacy→health, comparaciones, tres orígenes, errores, vista de la tool generada y positivos territoriales. Un Medium: nombre ausente de parada legacy 7214. Suite W3: 312 Python y 34 Node PASS; identidad v4 y artefactos PASS. No son conversaciones ni fiabilidad universal.

Studio: borrador privado separado, código/19 assets comprobados por bytes, nueve tools y preparación visible. **No se creó versión ni se enviaron mensajes (0/12)**: la lista congelada omite dependencias y la reproducción falla. El parche W2 `9dbb2d74…` conserva esa omisión; sus cambios semánticos aún requieren aceptación independiente. No hacer una demo live sobre este montaje.

## Siete respuestas para el jurado

- **¿Por qué no es solo una demo?** Hay fuentes fijadas, pipeline, contratos, regresiones y cálculo reproducible. La ampliación conversacional todavía tiene un bloqueo de despliegue explícito.
- **¿Qué decide el modelo?** Intención, tool y argumentos dentro del catálogo; no inventa datos ni decide políticas públicas.
- **¿Qué calculan las tools?** Métricas territoriales y escenarios programados/modelados con estados y trazabilidad.
- **¿Cómo comprobáis una cifra?** Solicitud y salida exactas, filas/horarios de origen, unidades y reconstrucción independiente; un hash prueba identidad de bytes, no verdad.
- **¿Qué ocurre con otra fecha?** Devuelve falta de evidencia validada; no extrapola ni cambia silenciosamente la fecha.
- **¿Qué no podéis asegurar?** Cita, capacidad, centro asignado, puerta, puntualidad, accesibilidad universal o trayecto desde el domicilio.
- **¿Por qué RAG no está incluido?** El experimento no demuestra mejora comparable con el mismo corpus y citas correctas. RAG sigue **NO_GO**; no hay vector DB ni segundo agente añadido al candidato.

Siguiente validación: corregir cierre de dependencias y raíz en W2, revisar nuevo ZIP, preparar versión privada y ejecutar el plan de **máximo 12 mensajes**, ya autorizado. Comparación v4/vNext, benchmark completo, holdout y aprobación humana siguen pendientes y requieren el alcance incremental correspondiente.
