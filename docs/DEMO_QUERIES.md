# Consultas de demostración y guion de 3 minutos

La demo reproducible actual usa datos reales y salidas ejecutadas directamente por las tools de Work 2: `resultados/demo_work2/index.html`. La prueba del coordinador en una versión fija del portal sigue pendiente. El fixture sintético está aislado en `tests/fixtures/` y `resultados/dev_sintetico/`.

| Consulta | Qué debe mostrar | Evidencia mínima |
|---|---|---|
| 1. Panorama territorial: “¿Qué unidades combinan una proporción elevada de personas de 65 años o más y peor valor de la métrica territorial del servicio seleccionado?” | Cálculo, mapa, tabla, fuente | Llamada de herramienta, parámetros, resultado, periodo, unidad y origen |
| 2. Variación/comparación: “Repite el análisis para mayores de 75 años y compara entre dos y cinco unidades.” | Filtro interpretado y nueva ejecución | Nueva llamada con argumento `age_group=75+`, nuevo identificador de resultado y cifras recalculadas |
| 3. Escenario: “¿Qué cambia si modificamos el umbral o añadimos hipotéticamente un servicio en la ubicación propuesta?” | Base, hipótesis, diferencia y supuestos | Herramienta de escenario ejecutada; nunca presentar hipótesis como observación |
| 4. Seguridad metodológica: “¿Esto demuestra que una persona mayor concreta no puede acceder al servicio?” | Respuesta negativa y explicación precisa | Límite sobre distancia/indicador, disponibilidad y situación individual |

## Recorrido canónico

1. **0:00–0:25 — Problema.** Presentar la necesidad de estudiar conjuntamente población mayor y servicio territorial. Evitar afirmar una distribución desigual hasta comprobarla con datos reales.
2. **0:25–1:10 — Pregunta principal.** Ejecutar consulta 1. Mostrar herramienta, parámetro, resultado, mapa y fuente con periodo y unidad.
3. **1:10–1:40 — Variación.** Repetir `analizar_coincidencia` con cuantil 0,75 → 0,85; enseñar 7/88 → 2/88 y dos `output_ref` distintos.
4. **1:40–2:05 — Profundización.** Preguntar por qué una unidad aparece en el resultado; abrir sus cifras, denominador y fuente.
5. **2:05–2:35 — Escenario.** Ejecutar consulta 3; señalar “OBSERVADO” y “ESCENARIO HIPOTÉTICO”, cambio, resultado y diferencia.
6. **2:35–2:50 — Fiabilidad.** Ejecutar consulta 4; mostrar el límite interpretativo.
7. **2:50–3:00 — Cierre.** “GIPUZKOA 360 permite pasar de un mapa estático a una investigación territorial interactiva y trazable.”

Plan B si el agente falla en directo: usar una ejecución fija previamente verificada, declararlo y mostrar la traza y el HTML generado para esa ejecución. No simular una ejecución nueva.
