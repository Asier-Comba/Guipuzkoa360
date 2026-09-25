# Siete tools: contrato, operación, evidencia y límites

Autoridad de firmas: `agentes/gipuzkoa360/portal/main.py` en `195b498…`. Siete wrappers físicos; `build_agent(model)` síncrono. Ninguna firma pública de Studio acepta `detalle`. Las pruebas offline del core pueden acceder a detalle completo; no se debe sugerir al usuario del portal.

## Sobre común

JSON estricto (sin NaN/Infinity). Éxito: status, question, filters, period, metric, unit, rows_used, data, method, sources, warnings, limitations, y resumen compacto cuando aplica. Error: status=error/error_code y explicación, no completar data con ceros. `rows_used` es el contador definido por operación; acceso/escenario pueden incluir registros de entrada, no llamarlo municipios afectados. La selección compacta no implica que se hayan usado solo las filas mostradas.

Datasets: municipios.csv y demografia.csv por municipality_code (5 caracteres); runtime_municipality_points.csv, coordenadas WGS84 y EPSG:25830; runtime_servicios.csv por service_id y municipio/categoría; metadata_sources.json y manifiesto. Datos: población 2025-01-01, geografía 2025-05-07, catálogo sanitario 2026-09-20. Fuente derivada G360_DERIVED_MUNICIPAL_METRICS_V1 enlaza las oficiales. Métodos completos en METODOLOGIA/RESULT_SCHEMA (congelados).

| TOOL | USER QUESTION | INPUT | OUTPUT | REAL CONTROL | SOURCE | TRACEABILITY | TEST EVIDENCE | PORTAL EVIDENCE | LIMIT |
|---|---|---|---|---|---|---|---|---|---|
| `obtener_resumen_territorial` | ¿Qué muestra Aduna? | municipio, periodo | población, edades e indicadores de registro/distancia | Aduna: 507; 75 de 65+; primaria 0 registros internos y 2.756,2 m | Eustat + catálogo/geografía derivados | código, periodos de métricas, unidad/método/fuentes | summary/aliases/goldens/NEXT | Donostia histórico v2; Aduna histórico. Refresh v4: error, no output | cero registros ≠ cero médicos; tasa ≠ capacidad |
| `comparar_municipios` | ¿En qué difieren Eibar y Tolosa? | 2–20 municipios, edad, categoría, km, periodo | filas comparables, denominadores y distancia opcional | 75+ primaria: 13,744 %/1.223,6 m vs 12,131 %/1.080,5 m | Eustat, geoEuskadi, ODE | mismo criterio por código; sobre común | 3.828 pares + integración/NEXT | G-03 histórico v2 | fechas/tamaños distintos; no causalidad |
| `analizar_envejecimiento` | ¿Dónde pesa más 75+? | edad, percentage/count, periodo, top_n | ranking con numerador/total | ranking 75+ top 5, regenerable | Eustat | grupo, medida, periodo, personas/% | 88 municipios + aliases/NEXT | ranking histórico v3 | ranking ≠ necesidad ni predicción |
| `analizar_acceso_servicios` | ¿A qué distancia está el registro más cercano? | categoría, km, periodo, municipios | nearest_distance_m y within_threshold | Aduna primaria: 2.756,2 m | geoEuskadi + ODE | EPSG:25830, ids/periodos, método | matriz 1.760 + adversarial/NEXT | Aduna histórico; no refresh PASS | distancia geométrica ≠ minutos/acceso/citas |
| `analizar_coincidencia` | ¿Dónde se alcanzan ambos cortes? | categoría, edad, km, periodo, cuantil | cortes, 88 unidas, count y destacados | q0,75: 7; 23,973 %; 2.019,2 m | las tres oficiales + derivada | argumentos, filas, cortes, sources | 320 configuraciones + jury/NEXT | G-04/G-06 históricos v3; refresh v4 con call pero runner ocupado | umbral solo within_threshold; coincidencia ≠ causalidad |
| `simular_escenario` | ¿Qué cambia al añadir/retirar un registro? | acción, categoría, umbrales, coords/id, periodo | baseline, scenario, differences, supuestos | Aduna: 2.756,2→0,0 m; −2.756,2 m | baseline oficial + SCENARIO_INPUT | parámetros cambiados, filas, sources y etiqueta hipotética | 352 add/148 remove/80 threshold + NEXT | regresión histórica v4 | hipótesis, no predicción/recomendación; payload extremo pendiente |
| `consultar_fuente` | ¿De dónde sale la cifra? | source_id opcional | institución, URL, licencia, periodo, unidad y límites | EUSTAT_EMH_2025 | metadata_sources.json | source_id y ficha versionada | data access/release/NEXT/fake-source | G-01 histórico v2 | no comprueba disponibilidad o actualización actual |

**Separación obligatoria:** “TEST EVIDENCE” es cálculo determinista local/versionado; “PORTAL EVIDENCE” es observación histórica por versión. Un error de runner no se convierte en PASS de portal.

## obtener_resumen_territorial

- **USER INTENT:** describir un municipio y sus indicadores.
- **INPUT CONTRACT:** municipio:str requerido; periodo:str|null=None. Nombres/aliases/código pasan por normalización existente.
- **OUTPUT CONTRACT:** una fila: population_total, population_65_plus/75_plus, pct_65_plus/75_plus, service_indicators por categoría, services_in_municipality y metrics_reference_period. Unidad mixta explícita: personas, %, registros, tasas/10.000, m.
- **DATA USED / TRACEABILITY:** municipio y demografía, servicios e indicadores derivados; código+periodo y catálogo. El sources compacto puede mostrar Eustat mientras la fila contiene indicadores sanitarios: usar también metrics_reference_period y FUENTES/metadata para procedencia completa.
- **REAL CONTROL CASE:** Aduna 507 habitantes, 75 de 65+, 0 registros internos primary_care, distancia 2.756,2 m. Donostia 183.388 / 48.832 / 26,628 %.
- **TEST COVERAGE:** test_analysis, test_real_data_integration, test_golden_contract, tests/next/test_next, evaluación summary_aduna y alias.
- **PORTAL EVIDENCE:** Donostia histórico v2; Aduna en registro histórico; smoke actual hizo una llamada innecesaria a Donostia y devolvió error, no revalidación.
- **FAILURE MODE:** municipio desconocido o periodo no disponible → error controlado. No elegir un municipio por su cuenta.
- **LIMITATION:** 0 registros no significa ausencia de médicos; tasas no son capacidad.

## comparar_municipios

- **USER INTENT:** comparar un conjunto municipal con el mismo criterio.
- **INPUT CONTRACT:** municipios:list[str] (2–20); grupo_edad:str="65"; categoria_servicio:str|null=None; umbral_km:float=1; periodo:str|null=None.
- **OUTPUT CONTRACT:** filas municipales con denominadores, población/porcentaje del grupo; opcional categoría y distancia/umbral. Summary conserva total de filas.
- **DATA USED / TRACEABILITY:** demografía por código/periodo y opcional servicios+punto; sources, método y advertencias conservados.
- **REAL CONTROL CASE:** Eibar/Tolosa, 75+, primaria: 13,744 % / 12,131 % y 1.223,6 m / 1.080,5 m.
- **TEST COVERAGE:** test_analysis, test_real_data_integration, test_release_e2e; benchmark 3.828 pares únicos y variaciones; NEXT comparison_eibar_tolosa prueba además salud mental.
- **PORTAL EVIDENCE:** G-03 histórico v2; no nuevo PASS v4 en esta misión.
- **FAILURE MODE:** lista inválida, código desconocido, grupo/periodo no soportado → error, no selección silenciosa.
- **LIMITATION:** diferente tamaño poblacional y fechas de fuentes; no mezclar tasas con recuentos ni inferir causalidad.

## analizar_envejecimiento

- **USER INTENT:** ordenar por proporción o número de personas mayores.
- **INPUT CONTRACT:** grupo_edad:str="65" (65/75 y aliases soportados), medida:str="percentage" (percentage/count y aliases), periodo:str|null=None, top_n:int=10.
- **OUTPUT CONTRACT:** ranking ordenado, numeradores y denominador municipal, personas o porcentaje según medida; rows_used y total_result_rows distinguen universo y selección.
- **DATA USED / TRACEABILITY:** demografia.csv, EUSTAT_EMH_2025; cálculo porcentaje=grupo/total×100.
- **REAL CONTROL CASE:** ranking 75+, top 5; regenerable en evaluación NEXT aging75; Donostia permite cotejar el porcentaje con originales.
- **TEST COVERAGE:** test_analysis, test_parameter_normalization, test_compact_outputs y NEXT; benchmark demografía 88 municipios.
- **PORTAL EVIDENCE:** ranking con alias porcentaje histórico v3; no humo actual convertido en PASS.
- **FAILURE MODE:** medida/grupo/top_n/periodo inválidos → error explícito.
- **LIMITATION:** 75+ derivado de nacidos hasta 1949; ranking no es necesidad sanitaria ni previsión.

## analizar_acceso_servicios

- **USER INTENT:** saber distancia al registro más cercano y comparar con umbral.
- **INPUT CONTRACT:** categoria_servicio:str; umbral_km:float=1 finito no negativo; periodo:str|null=None; municipios:list[str]|null=None. Categorías: primary_care, hospital, mental_health, other_health y aliases soportados.
- **OUTPUT CONTRACT:** nearest_distance_m, registro seleccionado, within_threshold y recuentos; m y booleano, no minutos. Compacto puede devolver subset y summary del universo.
- **DATA USED / TRACEABILITY:** puntos y registros con easting_m/northing_m EPSG:25830; mínimo euclídeo. Sources geografía/sanitario y advertencias temporales.
- **REAL CONTROL CASE:** Aduna primaria, 3 km: 2.756,2 m dentro del umbral, aunque cero registros internos.
- **TEST COVERAGE:** test_analysis, test_real_data_integration, test_adversarial_core, NEXT access_aduna; matriz benchmark 1.760 combinaciones.
- **PORTAL EVIDENCE:** Aduna histórico registrado; smoke presente no reejecuta esta tool exitosamente.
- **FAILURE MODE:** farmacia no es categoría cargada; NaN/infinito/umbral negativo se rechazan; no fabricar distancia.
- **LIMITATION:** punto no ponderado por residentes; sin red viaria, transporte, horarios, capacidad ni citas.

## analizar_coincidencia

- **USER INTENT:** detectar municipios que cumplen a la vez los cortes relativos de edad y distancia.
- **INPUT CONTRACT:** categoria_servicio:str; grupo_edad:str="65"; umbral_km:float=1; periodo:str|null=None; cuantil:float=.75 dentro del dominio admitido, finito.
- **OUTPUT CONTRACT:** summary con age_cut_percent, distance_cut_m, joined_rows, highlighted_count; data compacta con destacados. within_threshold es referencia independiente.
- **DATA USED / TRACEABILITY:** unión por municipality_code de demografía y distancia; cuantil interpolado de cada indicador, AND de >=. EUSTAT/geografía/catálogo y método.
- **REAL CONTROL CASE:** 65/q.75/2 km: 88 filas, 23,973 %, 2.019,2 m, 7; 75/q.80/3 km: 4; 65/q.85: 2.
- **TEST COVERAGE:** test_jury_results_gate, test_final_artifacts, test_parameter_normalization; 320 configuraciones benchmark; NEXT y seguimiento.
- **PORTAL EVIDENCE:** G-04/G-06 históricos v3. P1 v4 actual tool/args correctos sin detalle, pero runner ocupado: INFRASTRUCTURE_BLOCKED, no output numérico.
- **FAILURE MODE:** grupo/categoría/cuantil inválido → error; fallback del modelo actual puede confundir threshold/cuántiles (M-02).
- **LIMITATION:** coincidencia no causalidad; consultar [explicación de umbral](THRESHOLD_VS_QUANTILE.md).

## simular_escenario

- **USER INTENT:** recalcular un cambio hipotético manteniendo constantes los demás datos.
- **INPUT CONTRACT:** accion:str, categoria_servicio:str, umbral_km:float=1, periodo:str|null=None, latitud/longitud:float|null=None, service_id:str|null=None, nuevo_umbral_km:float|null=None. add_service requiere coordenadas válidas; remove_service id existente; change_threshold nuevo umbral.
- **OUTPUT CONTRACT:** escenario explícito, baseline/scenario/changed_parameters/assumptions; filas con baseline_distance_m, scenario_distance_m, difference_absolute_m, difference_relative_pct y estados de umbral; summary separa 88 evaluados y afectados. `service_count` cuenta TODOS los registros sanitarios.
- **DATA USED / TRACEABILITY:** misma matriz espacial antes/después; SCENARIO_INPUT para punto hipotético, fuentes baseline conservadas. No persiste cambios.
- **REAL CONTROL CASE:** alta en punto representativo de Aduna: 2.756,2→0 m, diferencia −2.756,2 m; 148→149 registros totales. El ejemplo NEXT usa coordenadas declaradas distintas y no se etiqueta como este golden de cero.
- **TEST COVERAGE:** test_release_e2e, test_adversarial_core, test_compact_outputs; 352 altas, 148 bajas, 80 cambios de umbral benchmark; NEXT geometric_effect.
- **PORTAL EVIDENCE:** regresión del contador en v4 histórica; payload extremo no probado (M-01).
- **FAILURE MODE:** coordenadas no finitas, id ausente/desconocido, umbral inválido → error, nunca predicción.
- **LIMITATION:** no recomienda ubicación ni estima demanda/impacto/capacidad. Métricas marginales/removal NEXT son agregados geométricos offline.

## consultar_fuente

- **USER INTENT:** explicar procedencia y limitaciones.
- **INPUT CONTRACT:** source_id:str|null=None; null devuelve catálogo, desconocido devuelve error.
- **OUTPUT CONTRACT:** fichas de institución, título, URL, licencia, referencia temporal, unidad, transformación y límites; periodo global puede ser null al mezclar fuentes con periodos propios.
- **DATA USED / TRACEABILITY:** metadata_sources.json y catálogo versionado; no búsqueda web en ejecución.
- **REAL CONTROL CASE:** EUSTAT_EMH_2025 y referencia 2025-01-01; comprobar derivación 75+.
- **TEST COVERAGE:** test_data_access, test_public_tools, test_release_e2e; NEXT source y ataques fuente falsa.
- **PORTAL EVIDENCE:** G-01 histórico v2, no nuevo PASS actual.
- **FAILURE MODE:** id inventado se rechaza; no inventar URL ni citar fuente no cargada.
- **LIMITATION:** ficha local no acredita disponibilidad actual del sitio ni que no exista edición posterior.

La evidencia histórica está corregida por versión en [PORTAL_EVIDENCE_RC2](../PORTAL_EVIDENCE_RC2.md). La actual está en [smoke refresh](../internal/PORTAL_SMOKE_REFRESH.md). Ninguna tool NEXT se añade al agente v4.
