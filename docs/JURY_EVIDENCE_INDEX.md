# Índice de evidencia para los cinco criterios

Los pesos proceden de la rúbrica conservada en `contexto-principal.md` y `docs/RUBRIC_TRACEABILITY.md`. No se autoasignan puntos. «Mostrar live» puede ser navegar por evidencia guardada, siempre identificada como tal; no equivale a ejecución live del agente.

## 1. Utilidad urbana — 25 %

**WHAT WE CLAIM:** permite a personal técnico explorar coincidencias territoriales y contrastar municipios con criterios explícitos.

**WHY IT MATTERS:** facilita formular dónde profundizar, en vez de presentar una cifra sin contexto.

**EVIDENCE:** 88 municipios, control Aduna, comparación Eibar/Tolosa y escenarios, `analisis/jury_coincidence_results.json`, `tests/golden_cases.json`.

**HOW TO SHOW IT LIVE:** abrir hero guardada, preguntar por los 7 destacados y cambiar al caso 75+ (4). Si el portal funciona, repetir con nuevos parámetros y comprobar llamada nueva.

**LIMIT:** utilidad propuesta, sin estudio de impacto ni validación de usuarios; no prioriza inversión ni mide necesidad individual.

## 2. Análisis, fuentes y trazabilidad — 25 %

**WHAT WE CLAIM:** los cálculos proceden de snapshots oficiales y transformaciones inspeccionables.

**WHY IT MATTERS:** una cifra puede contrastarse con sus filas, unidades, periodo y criterio.

**EVIDENCE:** FUENTES, METODOLOGIA, manifests, [source health](../analisis/ops/source_health.json); 31.545/31.545 outputs numéricos trazables según definición explícita del benchmark, no toda posible respuesta.

**HOW TO SHOW IT LIVE:** Donostia: 48.832 / 183.388 × 100 = 26,628 %; abrir CSV oficial y transformación. Mostrar cortes 23,973 % / 2.019,2 m.

**LIMIT:** fechas distintas (627 días entre referencias extremas); geografía simplificada; 75+ derivado de cohorte de nacimiento; source_id resoluble no prueba precisión de cada observación.

## 3. Funcionamiento y herramientas — 25 %

**WHAT WE CLAIM:** siete operaciones deterministas, registradas en el agente; no siete agentes autónomos.

**WHY IT MATTERS:** el modelo selecciona una operación comprobable en lugar de inventar cálculos.

| Operación | Pregunta | Cálculo / evidencia | Límite |
|---|---|---|---|
| Resumen territorial | ¿Qué muestra Aduna? | Selecciona municipio, demografía e indicadores con periodo/fuente | Cero registros no significa cero médicos |
| Comparar municipios | ¿En qué difieren Eibar y Tolosa? | Alinea grupo/criterio, recuentos, porcentajes y distancias | Fuentes no simultáneas; denominadores distintos |
| Envejecimiento | ¿Dónde pesa más 75+? | Ranking por porcentaje o recuento, numerador y total | No explica causas ni necesidades |
| Acceso a servicios | ¿Qué distancia geométrica hay? | Mínimo euclídeo y within_threshold con registros | No minutos ni accesibilidad real |
| Coincidencia | ¿Dónde se cumplen ambos cortes? | Cruce de 88 filas, cuantiles, destacados y límites | Umbral no sustituye cuantil; no causalidad |
| Escenario | ¿Qué cambia si añadimos/retiramos registro? | Baseline, escenario y diferencias con supuestos | Hipótesis, no predicción ni recomendación |
| Consultar fuente | ¿De dónde sale el dato? | Catálogo, institución, URL, periodo, unidad y límites | No descarga nuevas versiones ni inventa fuentes |

**EVIDENCE:** [matrix técnica completa](architecture/TOOL_EVIDENCE_MATRIX.md), CI remota Linux/Windows, suites actuales y benchmark; historial de plataforma delimitado por versión.

**HOW TO SHOW IT LIVE:** abrir pregunta→tool→args→output y contrastar respuesta. Si runner falla, usar evidencia guardada rotulada y mostrar error, no afirmar ejecución exitosa.

**LIMIT:** [smoke actual](operations/PORTAL_SMOKE_ENGINEERING.md) bloqueado. NEXT es prototipo offline con inputs estructurados, no prueba del LLM en portal.

## 4. Claridad de respuestas y artefactos — 15 %

**WHAT WE CLAIM:** mapa, tablas, escenarios y cifras pueden mostrar el mismo resultado guardado y sus límites.

**WHY IT MATTERS:** el jurado puede revisar qué criterio cambió y por qué cambian 7→4→2.

**EVIDENCE:** `resultados/demo.html`, `analisis/jury_visual_data.json`, 9 corrupciones deliberadas rechazadas por el gate visual. El producto nuevo de Work 3 tiene auditoría e integración separadas.

**HOW TO SHOW IT LIVE:** cambiar criterio, seleccionar un municipio y abrir fuente; mostrar Aduna 2.756,2→0,0 m con rótulo hipotético.

**LIMIT:** HTML guardado no conversa ni recalcula una pregunta libre. No dar por integrado material de otra rama. Ver [cuantil vs umbral](architecture/THRESHOLD_VS_QUANTILE.md).

## 5. Fiabilidad, límites y supervisión — 10 %

**WHAT WE CLAIM:** checks explícitos rechazan corrupción y guardan límites/versiones; promoción humana obligatoria.

**WHY IT MATTERS:** fallar de forma visible protege frente a respuestas numéricamente convincentes pero sin sustento.

**EVIDENCE:** 20/20 fault injections del core, 1.000 soak sin drift/excepciones; runtime congelado byte a byte; propuestas de actualización sin autopromoción; NEXT 16/16 ataques de su batería acotada.

**HOW TO SHOW IT LIVE:** «3 km son 3 minutos» y «Aduna no tiene médicos»: explicar límites, no convertir indicadores en afirmaciones clínicas. Mostrar tests negativos, manifiesto y estado de portal.

**LIMIT:** payload extremo pendiente; fallback de error puede confundir criterios; estado INFRASTRUCTURE_BLOCKED. No se publica ni mergea automáticamente. [Gobierno del release](RELEASE_GOVERNANCE.md).
