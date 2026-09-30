# GIPUZKOA 360 · defensa técnica R13

**Cálculo y producto offline comprobados. Agente sanitario privado bloqueado por argumentos incompatibles. READY_FOR_FEEDBACK=NO; no hay release aprobada.**

## Problema, destinatario y diferencial

Los equipos municipales necesitan explorar dónde coinciden envejecimiento y distancia a servicios, con fuentes y límites que permitan revisar una decisión. El screening de 88 municipios ofrece una primera comparación descriptiva. El cuantil determina los cortes destacados; el umbral es una referencia de distancia. Un destacado no es una prioridad de inversión y la distancia geométrica no es tiempo de viaje.

La ampliación concreta la pregunta: **¿qué carga temporal supondría ir desde unas paradas catalogadas hasta el punto oficial del Ambulatorio de Beasain y volver, incluyendo paseo modelado y consulta?** Así pasamos de screening territorial a un escenario sanitario temporal acotado. No resolvemos asignación de centro, capacidad ni reserva de citas.

## Arquitectura y responsabilidades

Pregunta natural → coordinador LLM → selección de una de nueve tools y argumentos → cálculo determinista → validación y evidencia → respuesta. El modelo interpreta y explica; las tools calculan. Cambiar hora o duración debe provocar una nueva ejecución, no una cifra reutilizada.

- **W1:** datos, productor, horarios, red peatonal, matemáticas y estados de resultado.
- **W2:** coordinador, contratos, paquete de Studio, proyección acotada para el modelo y procedencia de parámetros.
- **W3:** comprobación independiente desde datos fuente, red team, portal privado, producto visual y gate del jurado.

El HTML es autocontenido: muestra salidas offline guardadas y permite importar un JSON compatible. No tiene un agente conectado ni calcula rutas en el navegador. Compatibilidad del archivo no prueba su autoría ni procedencia.

## Qué ocurrió en la prueba real

Evaluamos el candidato final patch3, sin heredar el fallo de R12 ni el PASS de otro evaluador. El paquete exacto pasa 36 casos en cuatro layouts, incluidos datos declarados, carpeta anidada y directorio de trabajo ajeno. Son 144 ejecuciones de casos offline, **no conversaciones**.

En Studio creamos una versión privada separada, con código y quince assets contrastados por bytes. El modelo configurado visible es `openai:gpt-5.6-luna`, con memoria y sin Internet. Se enviaron **cuatro de los doce mensajes** previstos:

1. Aduna: población y explicación correcta de qué significa cero registros.
2. Seguimiento con Tolosa para 75+: selección de datos nuevos y comparación coherente.
3. Transición sanitaria: pide origen, hora y duración, y explica los límites.
4. Pregunta completa Zegama–Beasain: elige la tool adecuada, pero envía texto donde se exige objeto/lista. Dos intentos internos reciben `arguments:request:invalid_value`; el final reconoce el error sin inventar cifras.

Este **High de integración agente/tool** bloquea la demo sanitaria conversacional. Paramos el lote: variaciones, fecha no validada y sesión limpia quedan sin ejecutar. El schema completo enviado al modelo no es observable; no atribuimos la causa a la plataforma, a red ni a W1. W2 tiene una reproducción con argumentos reales; cualquier paquete nuevo necesita reaceptación W1 antes de reanudar.

## Ejemplo defendible hoy, 2–3 minutos

Presentar expresamente el **producto offline**, sin simular conversación live:

1. Zegama, 29/09/2026, cita 09:30, consulta 20 min: **10.691 s = 2 h 58 min 11 s**. Mostrar autobús, paradas, paseo, consulta y esperas.
2. Seleccionar cita 09:45: **8.591 s = 2 h 23 min 11 s**. Diferencia condicionada: **−2.100 s, 35 min**. Ambas salidas se reconstruyeron independientemente contra filas GTFS, cronología y geometría fijadas. No son un ahorro garantizado ni un resultado obtenido del agente en R13.
3. Seleccionar fecha 30/09: falta evidencia validada; itinerario oculto. Abrir fuentes y recordar revisión humana.

Una cifra sí contrastada del agente real: **Aduna, 36/507 × 100 = 7,101 % de 75+** en la fila demográfica exacta. El texto final omite la fuente explícita y la derivación 75+ disponibles en la tool: Medium pendiente.

## Fuentes y límites

Eustat aporta población a 01/01/2025; 75+ se deriva del año de nacimiento. geoEuskadi aporta geografía; Open Data Euskadi, registros sanitarios. Los periodos son distintos. Registros no equivalen a médicos, capacidad, apertura o disponibilidad; ausencia de registros no demuestra ausencia de atención.

La visita combina GTFS GO01 programado, red OSM fijada, punto sanitario oficial y perfil modelado de **50 m/min + 120 s por enlace completo**. El total va desde presencia en la parada de origen hasta llegada a la parada de regreso. No es desde el domicilio, ni tiempo real. Los horarios son aproximados/interpolados; la puerta física no está verificada. El conflicto de dirección Bernedo Enea 1 / Zaldizurreta 2 exige revisión humana.

## Validación y elección de RAG

Suite final: **321 Python y 37 Node PASS**, gates de artefactos e identidad v4 PASS. Son regresiones deterministas; no certifican fiabilidad del LLM, memoria interna ni accesibilidad WCAG. La revisión visual cubre cinco tamaños, teclado, fuentes largas, importación, estados nulos y comparación.

El A/B documental W2 usa los mismos cuatro documentos y 18 preguntas, sin LLM: retrieval mejora de 14/15 a 15/15, pero soporte completo cae de 14/15 a 11/15. Menor contexto no compensa perder soporte. **RAG_NO_GO**: cálculo estructurado mediante tools y consulta documental acotada; RAG entra solo si mejora soporte, citas y abstención de forma medida.

v4 permanece intacta. Comparación pareada futura, benchmark completo, holdout privado y decisión humana siguen pendientes. No afirmamos superioridad conversacional de vNext ni publicamos entrega.
