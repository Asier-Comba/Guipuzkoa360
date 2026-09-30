# W3 R12 · aceptación independiente y cierre Studio

**RELEASE_GO_NO_GO: NO_GO. READY_FOR_FEEDBACK: NO para el candidato conversacional. MERGED_OR_PUBLISHED_RELEASE: NO.**

## Identidad y resultado

- START_SHA: `281f92a25170c5082c5772c0130d2275e57edaaf`.
- TESTED_HEAD: `0601367e11ce0e869d3042e55623409d20aac203`.
- PUBLISHED_HEAD: SHA final exacto en el comentario de publicación del [PR14](https://github.com/Asier-Comba/Guipuzkoa360/pull/14), para evitar un hash autorreferente.
- PACKAGE_TESTED: baseline W2 `2321e03e…`, ZIP `b4feb978b625b34f9d7331ce8d376a34a29e84e4783868f83ce48a0c0d1011be`, 219.354 bytes.
- W1 soporte `c9cb37f6…`; runtime Git real `cb061a9e00a6496c40488a596bd94834bc2c49b2`; ZIP `c66d44af…` inalterado. La errata histórica `cb061a97…` se conserva solo en R10.
- Nuevo parche W2 `6693cbce605484dc48eca9ed7de867e32c5f3aa7`, ZIP `9dbb2d7421e2468e44949f94ad1ef5b9011430601d34dd76057fb1720e0bfb1b`: integridad y reproducción con archivos declarados comprobadas; aceptación semántica completa **NOT_RUN**. No se cargó ese parche en Studio.

## CURRENT_FINDINGS / HARNESS_VS_PRODUCT_FINDINGS

**High, W2: cierre de dependencias de Studio.** La preparación del baseline muestra “Lista para crear versión”, nueve tools y 13 datos declarados. La misma UI explica que congela los módulos Python del agente y **solo los datos declarados**. Faltan assets y pruebas referenciadas por la validación de capacidades. Un proceso limpio con exactamente esos archivos devuelve `contract_violation / capability:stale_validation_evidence`. El parche `9dbb…` conserva los mismos 13 paths y reproduce el fallo. No se creó una versión destinada a fallar.

**High del baseline, W2: propagación de raíz.** En cwd del ZIP, health y legacy funcionan. En cwd W1 con `execute(root=ZIP)` y proyección que vuelve a resolver raíz, reaparecen legacy sin raw y etiquetas numéricas. W2 reconoce un defecto de producto y comunica un fix en `9dbb…`; W3 aún no ha validado semánticamente ese fix. La mezcla del evaluador explica R11, pero no acredita portabilidad del candidato.

**Medium del baseline, W2:** parada legacy 7214 sin nombre, conserva ID correcto. Nombre en GTFS fijado: Beasain - Zaldizurreta 7. Tres casos afectados representan un único defecto. W2 comunica corrección derivada del GTFS en el nuevo parche; pendiente retest independiente.

`KeyError('transformation')` **no apareció en `public_result` de W3**. W2 lo atribuye al evaluador W1 aplicando un requisito sanitario a legacy 0.2.0. Se separa ese informe de los fallos de producto observados. Los errores iniciales del harness W3 y el primer intento de edición que no persistió se corrigieron antes de emitir aceptación; no son incidentes LLM.

Reproducciones, resultados y límites: [estado único R12](RELEASE_READINESS_R12.json). Hallazgos enviados a W2 en [comentario baseline](https://github.com/Asier-Comba/Guipuzkoa360/pull/17#issuecomment-5914732632) y [comentario del parche](https://github.com/Asier-Comba/Guipuzkoa360/pull/17#issuecomment-5914876930).

## OFFLINE_RESULTS

Baseline completo en CPython 3.12, proceso aislado, cwd propio, red denegada: **34 casos**, 31 PASS y 3 WARN por 7214; cero fallos High/Critical en ese modo. Health sola, legacy sola, secuencia, comparación sanitaria y mixta, tres orígenes, errores y positivos territoriales pasan. Tres llamadas directas a la tool generada y un probe de sustitución municipal se registran aparte. Eso prueba contrato/proyección, **no autonomía del modelo**.

Raw cotejado con productor incluido y ocho salidas W3 R10 previamente contrastadas contra GTFS/geometría, sin usar el veredicto W1 como oráculo. Delta condicionado: −2.100 s. Aduna no expone tasas sin trazabilidad; Tolosa conserva ocho tasas válidas; 7 destacados usan unidad municipios.

Suite en TESTED_HEAD: **312 Python PASS, 34 Node PASS**; jury gate, artifact gate e identidad v4 PASS. [CI del código probado](https://github.com/Asier-Comba/Guipuzkoa360/actions/runs/36739794998): PASS. Los siguientes archivos son documentación/capturas/evidencia adicional; no se cambió código después de ese SHA.

## PORTAL_VERSION_ID / AUTHORIZATION_USED / SMOKE_RESULTS

- Borrador nuevo: **GIPUZKOA 360 vNext R12 b4feb978**, `agentes/gipuzkoa_360_vnext_r12_b4feb978`.
- Dos editores descargados y hash exacto del baseline: PASS. Primer intento AX no persistió; edición real y descarga posterior sí.
- Ocho archivos comunes reutilizados sin escribirlos: bytes idénticos. Once assets nuevos descargados tras carga: bytes idénticos. Tres rutas nuevas: `contracts/vnext`, `datos_preparados/vnext`, `scripts/vnext_agent`. No sobrescribir `mobility_sources.json` con el parche en este espacio mientras representa el baseline.
- `ejecucion.py` fue creado automáticamente por Studio, no importado por el código aprobado. Inclusión efectiva en una versión: **NOT_OBSERVED**.
- Preparación visible: PASS; modelo `openai:gpt-5.6-luna`, nueve tools, memoria activada, Internet desactivado. Esto es configuración visible, no prueba de conversación ni de memoria enviada.
- PORTAL_VERSION_ID: **NOT_OBSERVED / no creado**.
- USER_MESSAGES_USED_OF_12: **0**. MODEL_CALLS_OBSERVED en Pruebas: **0**. Invocaciones internas de preparación: NOT_OBSERVED.
- SMOKE_RESULTS: **BLOCKED por montaje congelado incompleto**. No assistant final, IDs de conversación, tokens, historial o schema completo inventados. Solo nombres de parámetros de nueve tools observados.
- Plan fijado antes de cualquier envío: [SMOKE_PLAN_R12.json](SMOKE_PLAN_R12.json), 11 mensajes en sesión A y uno en sesión B. Reintentos cuentan dentro de 12.
- Autorización utilizada: borrador, carga exacta y preparación separados. **No hace falta pedir de nuevo permiso para la misma versión privada y lote de hasta 12 mensajes** cuando los gates pasen.

## Producto y defensa

`resultados/vnext/health.html` usa exclusivamente el baseline aceptado offline y el runtime Git corregido; `health_r10.html` preserva bytes/evidencia históricos. Importación R12 acepta su identidad y rechaza la antigua sin mezclar pins. La pantalla dice offline y atribución de entrada no comprobada.

Browser IAB local: 1366×768 y 390×844 sin overflow horizontal de página; variación 8.591 s, fecha no cubierta con itinerario/tabla ocultos, importación compatible con procedencia no comprobada y español legible. No se recertifica accesibilidad ni la matriz completa R10. [Defensa única](DEFENSA_TECNICA_R12.md): recorrido, fuentes, demo de 2–3 minutos y siete respuestas. RAG permanece NO_GO; corpus 48/20/12 y gold30 preservados; holdout no abierto.

## V4_PRESERVATION / siguiente acción exacta

Runtime local v4 sin diferencias y gate PASS. Agente v4 del portal no editado, reset no usado, archivos comunes no sobrescritos. Rehash de la versión v4 inmutable del portal: NOT_OBSERVED; no se atribuye esa prueba al gate local.

1. W2 publica nuevo artefacto con **cierre completo de archivos congelados y raíz compatible con la carpeta de agente de Studio**. No basta una lista externa de dependencias que `main.py` no declara.
2. W3 conserva estos históricos y retesta identidad nueva, raw/proyección/positivos y aislamiento con el framework existente. El intake R12 actual fija `b4feb978`; no usarlo fingiendo que aceptó otro SHA.
3. Cargar en espacio separado compatible; verificar bytes, preparación, inclusión efectiva y schema observable; crear versión privada y ejecutar hasta 12 mensajes del plan. Parar expansión ante High/Critical.
4. Preservar trazas parciales tal cual y revisar lo observable con W3_TRACE_2.1.0/scorer, sin convertir datos ausentes en aprobación.

**ADDITIONAL_AUTHORIZATION_NEEDED:** ninguna para ese mismo lote; sí para más mensajes, comparación LLM v4/vNext, benchmark completo, recursos nuevos o publicación. La comparación está preparada por dimensiones comunes territoriales/fuentes/contexto, con utilidad sanitaria evaluada aparte; presupuesto incremental se debe fijar en mensajes reales e intentos, no inferirlo de 12 plantillas. Aprobación humana y gates completos siguen pendientes. No merge, Entrega o publicación realizados; no actividad de fondo prometida.
