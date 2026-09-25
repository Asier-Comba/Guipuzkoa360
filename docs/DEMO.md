# Demostración de GIPUZKOA 360

Para personal técnico que compara municipios y necesita explicar una cifra, no solo verla.
Abrir la versión privada verificada y mostrar su número. Usar el guion como ensayo;
un resultado esperado no sustituye la salida real de la herramienta.

## Recorrido

Prever 6–8 minutos más margen del runner. Si falta tiempo, usar los tres primeros pasos
y el límite; no acelerar ocultando trazas ni prometer respuestas en milisegundos.

| Paso | Pregunta | Qué comprobar |
|---|---|---|
| Principal | ¿Dónde coinciden una proporción alta de 65+ y mayor distancia geométrica a atención primaria? Cuantil 0,75, 2 km y población a 2025-01-01. | analizar_coincidencia; 88 filas, 7 destacados; cortes 23,973 % y 2.019,2 m |
| Variación | Repítelo para 75+, cuantil 0,80 y 3 km. | Nueva llamada con los tres cambios; 4 destacados, no reutilizar 7 |
| Comparación | Compara Eibar y Tolosa para 75+ y atención primaria. | 13,744 % / 12,131 %; 1.223,6 / 1.080,5 m |
| Profundización | ¿Qué mide el indicador de salud mental de Eibar? | 1 registro; 1,408 por 10.000 de 65+; 2,683 por 10.000 de 75+; 1.859,7 m |
| Contrafactual | Simula atención primaria en el punto representativo de Aduna (43.2134915, −2.0593393), 2 km, 2025-01-01. | 2.756,2 → 0 m; −2.756,2 m; hipótesis, no ubicación recomendada |
| Límite | Entonces Aduna no tiene médicos, ¿no? ¿Y cuánto costará allí la vivienda en 2030? | No inferir ausencia de atención ni inventar predicciones |

Para cada turno, abrir tool, argumentos y output antes de aceptar la respuesta.
Comprobar periodo, unidad, source_id y límites. La base de edad es 2025; centros y
geometría tienen referencias 2026-09-20 y 2025-05-07. El umbral en km y el corte de
cuantil no son el mismo criterio.

## Cifra verificable

Donostia, código 20069: 48.832 / 183.388 × 100 = **26,628 %** de 65+, redondeado a
tres decimales. Recorrido: output del resumen → fila 20069 de municipios.csv →
demografia.csv → CSV de Eustat y metadatos → checksum del original.
[Fuentes](../FUENTES.md) y [validación](VALIDATION.md) fijan los archivos y periodos.

## Visual opcional, sin confundir resultados

Los HTML de ingeniería existentes comparan **tres municipios** con datos reales del core.
Sus controles aplican un corte local fijo del 25 %: **no representan** los siete
destacados de la consulta provincial por cuantil. No usarlos como mapa principal de
esa respuesta ni afirmar que sus controles llamaron al agente.

La visual pública final se incorporará cuando pase la revisión de la rama de Hugo.
Hasta entonces, la salida real de la herramienta y la tabla de comparación bastan
como evidencia. Ningún mapa es preferible a un mapa que represente otra consulta.

## Preguntas del jurado

| Pregunta difícil | Respuesta verificable |
|---|---|
| ¿Qué problema y para quién? | Comparar envejecimiento y proximidad geométrica para personal técnico; no asigna recursos ni mide necesidad individual. |
| ¿Qué añade a un dashboard? | Traduce intención a parámetros y encadena seguimientos con nueva ejecución; las vistas aportan otra forma de explorar el resultado. |
| ¿Cómo sé que recalcula? | La variación cambia tool args y pasa de 7 a 4 destacados. Ver output, no solo texto del modelo. |
| ¿Cómo sé que no inventa? | Core determinista, fuentes versionadas, QA y pruebas adversarias; no se garantiza infalibilidad del modelo. Revisar la traza y los límites de validación. |
| ¿De dónde sale la cifra? | Ejemplo Donostia anterior y cadena fila–transformación–original–checksum. |
| ¿Por qué mezcláis años? | Son snapshots disponibles con 627 días de separación; se explicita y no se infiere evolución ni simultaneidad. |
| ¿Qué significa acceso? | En este producto, proximidad geométrica aproximada; no accesibilidad real. |
| ¿Por qué distancia euclídea? | Cálculo simple y reproducible en EPSG:25830. No se ha verificado red, horarios o distribución residencial. |
| ¿Cómo tratáis ausencias? | Sin imputar. El snapshot pasa validaciones de nulos; cambios incompatibles fallan. Cero significa cero registros en la fuente. |
| ¿Y los municipios pequeños? | Mostrar personas, porcentaje y denominador: tasas altas no equivalen a más personas ni mayor necesidad. |
| ¿Qué supervisa una persona? | Selección de fuentes/periodos, interpretación, posible actualización, uso administrativo y publicación. |
| ¿Qué rompe el sistema? | Claves, schemas, coordenadas, periodos o archivos incompatibles; categorías no admitidas; cambios del runner/SDK; errores de interpretación del modelo. |
| ¿Es una predicción? | No. El escenario cambia entradas manteniendo el resto fijo y no pronostica uso, costes o impacto. |

No publicar Entrega durante la demostración. Cerrar mostrando [Validación](VALIDATION.md),
[Fuentes](../FUENTES.md) y [Metodología](METODOLOGIA.md), no historiales de desarrollo.
