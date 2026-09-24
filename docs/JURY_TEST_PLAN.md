# Recorrido corto para el jurado

Duración objetivo: 6–8 minutos. Usar la versión `urban-challenge-rc1` y mostrar la traza de tool cuando el portal la ofrezca.

## 1. Pregunta principal

**Pregunta:** «¿Dónde coinciden una proporción alta de población de 65 años o más y una mayor distancia geométrica a atención primaria en Gipuzkoa? Usa el cuantil 0,75 y umbral de 2 km.»

Debe llamar `analizar_coincidencia` con `primary_care`, `65`, `2.0`, `2025-01-01`, `0.75`. La respuesta debe separar porcentaje y metros, citar Eustat, Open Data Euskadi y geoEuskadi y decir que coincidencia no implica causalidad ni acceso real.

## 2. Seguimiento que cambia el criterio

**Pregunta:** «Repítelo para 75+, cuantil 0,80 y 3 km.»

Debe conservar la intención del turno anterior, cambiar los tres argumentos y recalcular. El caso de aceptación local devuelve cuatro municipios destacados; no debe reciclar el resultado anterior.

## 3. Comparación municipal

**Pregunta:** «Compara Eibar y Tolosa para 75+ y atención primaria.»

Cifra de control: Eibar `13,744 %` y `1.223,6 m`; Tolosa `12,131 %` y `1.080,5 m`. Periodo demográfico `2025-01-01`; la distancia combina servicios `2026-09-20` y geometría `2025-05-07`.

## 4. Profundización verificable

**Pregunta:** «Consulta el indicador de salud mental de Eibar y explica qué mide.»

Cifra de control: `1` registro, `1,408` registros por 10.000 personas de 65+, `2,683` por 10.000 de 75+ y `1.859,7 m`. Debe aclarar que no mide capacidad, citas ni disponibilidad.

## 5. Golden case y simulación

**Pregunta:** «¿Tiene Aduna atención primaria registrada y qué pasaría si añadimos hipotéticamente un centro justo en su punto representativo?»

Puede usar `obtener_resumen_territorial`, `analizar_acceso_servicios` y `simular_escenario`. Control: `0` registros municipales, distancia observada `2.756,2 m`, escenario `0,0 m`, diferencia `−2.756,2 m`. Debe decir literalmente que cero registros no significa ausencia de atención sanitaria y etiquetar la simulación como hipotética.

## 6. Artefacto territorial

Abrir `resultados/informe_principal.html`. Mostrar que la traza identifica `comparar_municipios`, que las cifras proceden del resultado real `analisis/work3_agent_result.json` y que el banner dice «resultado determinista del tool; no es una ejecución LLM». El mapa usa geometría real tras el enriquecimiento y no representa una red de transporte.

## 7. Límite

**Pregunta:** «¿Cuál será el precio de la vivienda en Donostia en 2030?»

Debe rechazar la petición sin tool irrelevante ni cifra inventada y explicar el alcance disponible.

## Cierre

Mostrar `FUENTES.md`, `analisis/release_e2e_report.json` y el SHA-256 del paquete. La idea clave: cada afirmación numérica se puede recorrer de pregunta → tool → fila → transformación → fuente oficial.
