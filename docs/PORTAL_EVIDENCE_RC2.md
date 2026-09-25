# GIPUZKOA 360 · Evidencia final de portal RC2

Fecha: 2026-09-24

Rama: `fix/portal-runtime-rc2`

SHA de runtime probado: `195b4980fa5998b096c308296a55e452380b0371`

Versión privada: `urban-challenge-rc2-195b498 · v4`
Estado: **PORTAL GO**

No se abrió la sección Entrega, no se publicó ninguna entrega y no se hizo merge.

## Preparación y contenido

- `build_agent`: correcto.
- Siete tools físicas y exactamente siete tools expuestas.
- Ninguna firma pública contiene `detalle`; ninguna llamada observada lo envió.
- Memoria activa e Internet desactivado.
- Sin imports rotos ni archivos de contexto ausentes.
- `main.py` y `tools.py` del borrador se verificaron y sustituyeron por los bytes del runtime probado.
- El portal mantiene además `ejecucion.py` como archivo de infraestructura propio; no forma parte del runtime versionado ni se modificó.

## G-01…G-06

| Caso | Tool observada | Resultado |
|---|---|---|
| G-01, fuente Eustat | `consultar_fuente` | PASS: `EUSTAT_EMH_2025`, institución, periodo y límites identificados. |
| G-02, resumen Donostia | `obtener_resumen_territorial` | PASS: 183.388 total; 48.832 de 65+; 26,628 %. |
| G-03, Eibar vs Tolosa 75+ | `comparar_municipios` | PASS: Eibar 13,744 % / 1.223,6 m; Tolosa 12,131 % / 1.080,5 m. |
| G-04, coincidencia q0,75 | `analizar_coincidencia` | PASS en una llamada, sin `detalle`: 88 filas, 7 destacados, cortes 23,973 % y 2.019,2 m. |
| G-05, aliases «atención primaria» y «65+» | `analizar_coincidencia` | PASS en una llamada con los mismos 7 destacados y 88 filas. |
| G-06, seguimiento 75+, q0,80, 3 km | nueva llamada a `analizar_coincidencia` | PASS: 4 destacados, cortes 12,9796 % y 2.138,6 m. |

El primer G-04 ejecutado sobre el SHA original `c13b848` necesitó corregir el alias natural `65 o más`; la regresión quedó resuelta en `d8ec018` y el candidato final pasó en una sola llamada.

## Cobertura de las siete tools

| Tool | Evidencia real | Resultado |
|---|---|---|
| `consultar_fuente` | Fuente Eustat | PASS |
| `obtener_resumen_territorial` | Donostia, Aduna y Eibar | PASS |
| `comparar_municipios` | Eibar frente a Tolosa | PASS |
| `analizar_envejecimiento` | ranking porcentual con alias `porcentaje` | PASS |
| `analizar_acceso_servicios` | Aduna, atención primaria, 2 km | PASS |
| `analizar_coincidencia` | G-04, G-05 y G-06 | PASS |
| `simular_escenario` | nuevo servicio de atención primaria en Aduna | PASS |

Comprobaciones destacadas:

- Aduna: 0 registros internos de atención primaria y 2.756,2 m al registro más cercano. La respuesta no lo interpretó como ausencia de atención o de médicos.
- Eibar, salud mental: 1 registro, 1.859,7 m, 1,408 por 10.000 habitantes de 65+ y 2,683 por 10.000 de 75+.
- Escenario Aduna: 2.756,2 → 0,0 m; diferencia −2.756,2 m; marcado como **ESCENARIO HIPOTÉTICO**.
- La regresión final en v4 aclaró correctamente que `service_count` 148 → 149 cuenta todos los registros sanitarios, no solo atención primaria.

## Red-team y calidad

Una conversación privada probó conjuntamente las ocho formulaciones hostiles exigidas: inferencia de que Aduna no tiene médicos; conversión de 3 km en 3 minutos; causalidad; recomendación de ubicación; predicción exacta; petición de ignorar tools; precio de vivienda en 2030; y `TEST_FAKE_SOURCE`. Las ocho fueron rechazadas o acotadas correctamente, sin cifras inventadas.

Las respuestas normales fueron directas, usaron una sola tool cuando bastaba, priorizaron 2–5 cifras, citaron fuente y periodo y cerraron con el límite útil. No recitaron el JSON. La única imprecisión observada fue la descripción inicial del contador del escenario; quedó corregida por `195b498` y verificada de nuevo en v4.

## Latencias observadas

- G-04 limpio en v3: tool call y output visibles a los **28,3 s**; respuesta final visible antes de **74,3 s**. El output apareció dentro del límite obligatorio de 60 s.
- G-04 anterior en v2: respuesta completa antes de **34,7 s**.
- Escenario de regresión final en v4: tool, output y respuesta completa visibles antes de **30,4 s**.
- Otras consultas observadas: aproximadamente **26–47 s** hasta respuesta completa.

Hubo dos fallos transitorios de arranque del sandbox en intentos anteriores; ambos pasaron al reintentar sin modificar código. Se conserva como riesgo operativo del runner, no como defecto funcional del agente.

## Validación local del candidato

- Pytest agregado después de las regresiones: **146/146 PASS**.
- Datos: **18/18 PASS**, 88 municipios y 148 registros sanitarios.
- Node/integración: **17/17 PASS**.
- Golden: **4/4 PASS**.
- Casos deterministas A–H: **8/8 PASS**.
- QA conversacional del release: **41/41 PASS**.
- Todos los payloads compactos por debajo de 15.000 caracteres; máximo: `simular_escenario`, 13.664.
- ZIP: 48.355 bytes; SHA-256 `b5b35245aaa08015b2955281b0edb9cc3254fa7fae77966d63d9fa6651b48227`.

## Commits posteriores a `c13b848`

- `d8ec018`: aliases naturales `65 o más` y `75 o más`.
- `ae62080`: normalización de medidas como `porcentaje`.
- `195b498`: precisión del prompt sobre el contador global de escenarios.

Los tres son parches mínimos con regresión. No añaden funcionalidad ni cambian la arquitectura.

## Estado GitHub

La rama `fix/portal-runtime-rc2` está publicada en `origin` con el runtime `195b498`. En el momento de esta validación no existe una Pull Request para esta rama. No se hizo merge ni se modificó `main`.
