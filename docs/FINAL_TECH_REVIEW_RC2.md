# Revisión técnica final RC2 · Work 2

Fecha: 2026-09-24  
Base auditada: `fix/portal-runtime-rc2` en `961bd3dd8ff65a53bc38d86bc7f5ff6992dc2374`  
Rama de auditoría: `work/agent-final-audit`  
Alcance: revisión local independiente; no se usó el portal, no se creó release y no se fusionó ninguna rama.

## Veredicto

La eliminación de `detalle` de las firmas Studio corrige la vía principal por la que el modelo podía pedir una
salida completa, pero el commit `961bd3d` no era suficiente por sí solo: una salida compacta aún instruía al
modelo a usar `detalle=true`. Además se detectaron umbrales no finitos serializables como `NaN`, mensajes
numéricos de bajo nivel en escenarios, un benchmark roto y un manifiesto desincronizado. Todos tienen parches
pequeños, separados y cubiertos por regresiones.

Con los commits de esta rama, el contrato público tiene exactamente siete tools compactas, el core completo
sigue disponible solo para procesos Python offline y la suite local queda verde. La mejora del `SYSTEM_PROMPT`
es deliberadamente independiente para que Work 1 pueda decidir su cherry-pick sin mezclarla con correcciones.

## Matriz PASS/FAIL

| Componente | Base `961bd3d` | Con rama de auditoría | Evidencia |
|---|---|---|---|
| 7 tools locales y únicas | PASS | PASS | AST, firmas e identidades verificadas |
| Ninguna firma Studio expone `detalle` | PASS | PASS | inspección dinámica de `main.TOOLS` |
| El modelo no recibe invitación a payload completo | FAIL | PASS | se eliminó «use detalle=true» de la salida compacta |
| Core completo para offline | PASS | PASS | `tools.analizar_coincidencia(..., detalle=True)` devuelve 88 filas |
| Coincidencia q0,75 | PASS | PASS | cortes 23,973% / 2.019,2 m; 7 destacados; `rows_used=88` |
| Follow-up q0,80 / 75+ | PASS | PASS | cortes 12,9796% / 2.138,6 m; 4 destacados; 88 filas unidas |
| Escenario conserva baseline/scenario/differences | PASS | PASS | 148→149 servicios en `add_service`; campos antes/después |
| Fuentes, periodos, unidades y límites | PASS | PASS | presentes en vistas compactas y completas |
| Ausencia de contaminación entre escenarios | PASS | PASS | salida normal byte a byte idéntica antes/después |
| JSON estricto con valores no finitos | FAIL | PASS | `allow_nan=False` y validación finita de umbrales/coordenadas |
| Benchmark RC2 ejecutable | FAIL | PASS | `clear_runtime_cache` obsoleto sustituido por `clear_analysis_cache` |
| Hashes y bytes de `runtime_manifest` | FAIL | PASS | regenerados desde los archivos actuales |
| ZIP, manifiesto del ZIP y contexto Studio | no cubierto de extremo a extremo | PASS | prueba de contenido, bytes y SHA-256 |
| Prompt orientado a conversación de jurado | mejorable | PASS opcional | commit independiente y test de instrucciones clave |

## Revisión del parche `961bd3d`

Las siete funciones decoradas residen físicamente en `main.py`: `obtener_resumen_territorial`,
`comparar_municipios`, `analizar_envejecimiento`, `analizar_acceso_servicios`, `analizar_coincidencia`,
`simular_escenario` y `consultar_fuente`. Ninguna acepta `detalle`; el core no registra tools y mantiene el
parámetro únicamente en funciones Python offline.

La compactación no elimina la evidencia necesaria para responder:

- coincidencia conserva filtros, cortes, agregados sobre 88 municipios y todos los destacados;
- acceso general conserva conteos dentro/fuera, extremos y los diez municipios con mayor distancia;
- escenarios conservan baseline, scenario, changed parameters, diferencias y solo filas afectadas;
- todos conservan `period`, `unit`, `sources`, `method`, `warnings` y `limitations`.

Defecto del parche original: la selección de acceso general decía «use detalle=true para las 88 filas». Aunque
la firma ya no admitía el argumento, esa frase podía inducir al modelo a una llamada inválida. Se sustituyó por
una instrucción de acotar municipios y se añadió una regresión que prohíbe «detalle» en la salida pública.

## Full code review

### Estado y mutabilidad

- **Estados globales: PASS.** Solo hay constantes de configuración y una caché LRU por ruta resuelta.
- **Caché: PASS con riesgo bajo documentado.** `maxsize=8`, clave por ruta absoluta y gancho explícito
  `clear_analysis_cache()`. Los datos se tratan como snapshot inmutable durante el proceso.
- **Mutaciones compartidas: PASS.** Los escenarios copian la lista de servicios y no alteran los diccionarios
  existentes. La prueba añade `TEMP_AUDIT`, ejecuta el escenario y confirma que la consulta normal posterior es
  idéntica y el id no aparece en el repositorio cacheado.
- **Riesgo residual:** los métodos internos de `DataRepository` devuelven listas mutables. Ninguna tool pública
  entrega esas referencias —serializa a JSON—, pero un consumidor offline que las modifique directamente puede
  contaminar su propio proceso. No se cambió la arquitectura porque no existe ese uso en el runtime.

### Determinismo, números y texto

- **Orden: PASS.** Rankings, fuentes y opciones tienen orden explícito; JSON usa `sort_keys=True`; las llamadas
  repetidas son byte a byte idénticas.
- **Floating point: FAIL corregido.** `NaN` e infinitos podían atravesar comparaciones y producir JSON no estándar.
  Los umbrales y coordenadas ahora requieren números finitos; el serializador prohíbe `NaN`.
- **Unicode: PASS.** Se usa UTF-8 y normalización NFKD para búsqueda; «Oñati», acentos, mayúsculas, espacios,
  guiones y guiones bajos se resuelven sin perder el nombre presentado.
- **Aliases: PASS.** Los aliases documentados son inequívocos. Entradas no resueltas devuelven error controlado
  y opciones, no una coincidencia aproximada silenciosa.

### Errores, contrato y selección

- **Serialización: PASS.** Ninguna tool pública normal supera 15.000 caracteres.
- **Excepciones: PASS tras corrección.** Errores de contrato se devuelven como JSON; umbral y coordenadas no
  filtran mensajes Python ni tracebacks.
- **Nombres y docstrings: PASS.** Los nombres describen la intención y los docstrings separan resumen,
  comparación, acceso, coincidencia, escenario y fuente. No se añadieron tools redundantes.
- **Follow-up: PASS tras mejora opcional del prompt.** Un cambio de parámetro obliga a recalcular y una consulta
  sencilla debe usar una sola tool.

## Revisión del `SYSTEM_PROMPT`

El prompt anterior era correcto en no alucinar y en los límites, pero favorecía respuestas rígidas con cinco
secciones y permitía de una a tres tools incluso para preguntas sencillas. También dejaba implícito el recálculo
de follow-ups y no impedía narrar el plan antes de actuar.

El commit opcional `b310db3` añade solo instrucciones conductuales verificables:

- ejecutar sin describir antes el proceso;
- una sola tool cuando basta y ninguna segunda llamada redundante;
- recalcular follow-ups que cambian un parámetro;
- no pedir payload completo si el resumen compacto basta;
- empezar por el hallazgo, usar 2–5 cifras y 100–180 palabras normalmente;
- explicar el cálculo, citar fuente/periodo y cerrar con el límite importante;
- no volcar JSON ni forzar una plantilla burocrática.

Conserva las prohibiciones sobre invención, causalidad, capacidad, acceso real, periodos heterogéneos y fixtures.
La matriz de 30 casos está en `docs/CONVERSATIONAL_QA_RC2.md`.

## Rendimiento y payload

Medición local reproducible con once repeticiones calientes en `analisis/agent_runtime_benchmark.json`:

| Tool | Cold ms | Warm mediana ms | Completo chars | Compacto chars | Reducción |
|---|---:|---:|---:|---:|---:|
| `consultar_fuente` | 0,840 | 0,247 | 8.975 | 4.896 | 45,4% |
| `obtener_resumen_territorial` | 7,272 | 0,411 | 3.571 | 2.537 | 29,0% |
| `comparar_municipios` | 8,259 | 1,516 | 4.484 | 2.867 | 36,1% |
| `analizar_envejecimiento` | 1,669 | 0,267 | 2.691 | 2.181 | 19,0% |
| `analizar_acceso_servicios` | 8,513 | 3,231 | 17.059 | 3.632 | 78,7% |
| `analizar_coincidencia` | 11,723 | 5,490 | 36.838 | 5.216 | 85,8% |
| `simular_escenario` | 11,869 | 6,514 | 26.719 | 13.664 | 48,9% |

La mayor salida pública es `simular_escenario`, con 13.664 caracteres: queda bajo 15k y necesita ese espacio
para baseline, scenario, 41 cambios municipales en el caso benchmark, diferencias, fuentes y límites. Reducirla
más exigiría retirar evidencia útil o paginar; no se recomienda para RC2. Las consultas q0,75/2 km y
q0,80/75+/3 km miden aproximadamente 5,2k y 4,1k caracteres, respectivamente.

El benchmark de wrappers, cinco repeticiones, da 7,364 ms de carga fría y 6,682 ms como peor mediana de wrapper;
estado PASS frente al límite de 1.000 ms.

## Manifest y paquete

El manifiesto original tenía tamaños y SHA anteriores para `demografia.csv` y `runtime_servicios.csv`. Tras
regenerarlo:

- `demografia.csv`: 6.250 bytes, SHA-256
  `8dc7850baf6794678743fd51e63d85d55706bebfffa2e2352d9a07ad2a669dc4`;
- `runtime_servicios.csv`: 25.407 bytes, SHA-256
  `214871b1b410f0fb7a0266d32fbc6f3f494f829d2650803af81e47c59cc9d958`;
- total de activos del manifiesto: 575.920 bytes, dentro de 24 MiB.

El ZIP reproducible actual contiene 14 archivos, ocupa 47.995 bytes y tiene SHA-256
`f02c15a010742c8a697fdd041b8ab327ec509035ade07a8bddfec572fb35ed88`. La prueba verifica que su manifiesto
coincide con bytes, hash y nombres y que todo `STUDIO_CONTEXT_FILES` existe y está empaquetado.
`runtime_municipios.geojson` está en el manifiesto de activos compartidos pero deliberadamente fuera del ZIP y
del contexto conversacional: lo consume Work 3 para visualización, tal como documenta `docs/RUNTIME_PACKAGE.md`.

## Trazabilidad comprobada

El resumen de Donostia / San Sebastián devuelve 183.388 habitantes, 48.832 personas de 65+ y 24.884 de 75+.
Esos valores coinciden con la fila preparada y fijada en los golden cases, cuyo `source_id` es
`EUSTAT_EMH_2025`, institución Eustat y periodo 2025-01-01. Esta auditoría comprueba la cadena interna y el
snapshot documentado; no afirma haber vuelto a descargar la fuente en vivo.

## Pruebas

- Python: **136 passed** tras las nuevas regresiones.
- Integración JavaScript Work 3: **17 passed**.
- QA de datos: 41 controles PASS al regenerar activos.
- Casos nuevos relevantes: core completo offline; ausencia de `detalle` público; q0,75 y q0,80/75+; escenario
  sin contaminación; `NaN`/infinitos; errores numéricos controlados; coherencia ZIP/manifiesto/contexto; reglas
  del prompt.

No se declaran pruebas de portal: por instrucción expresa, Work 2 no lo utilizó.

## Defectos y commits

| Commit | Tipo | Contenido | Recomendación |
|---|---|---|---|
| `5c8841e` | corrección | elimina sugerencia `detalle`, JSON estricto y regresiones del contrato compacto | cherry-pick |
| `c97032a` | corrección | valida umbrales/coordenadas de escenario y evita mensajes Python | cherry-pick |
| `d514138` | QA | repara y actualiza el benchmark RC2 | cherry-pick |
| `d45256b` | datos/release | refresca manifiesto y verifica ZIP/contexto | cherry-pick |
| `b310db3` | comportamiento | prompt breve, answer-first, una tool y follow-ups recalculados | opcional recomendado |

## Riesgos abiertos

- Solo Work 3 puede confirmar el comportamiento real del coordinador y del modelo en el portal.
- Los periodos de demografía, servicios y geografía difieren; ninguna respuesta debe tratarlos como una foto
  temporal homogénea.
- La distancia es euclídea desde un punto representativo municipal; no mide red viaria, tiempo ni barreras.
- Los registros de centros no contienen capacidad, disponibilidad, citas, horarios, calidad o demanda.
- La QA conversacional define resultados esperados, pero la redacción exacta del modelo debe evaluarse en la
  versión privada del portal por su operador autorizado.

## Recomendación exacta a Work 1

Cherry-pick, en este orden, `5c8841e`, `c97032a`, `d514138` y `d45256b`. Añadir `b310db3` si se acepta la mejora
conversacional; está aislada y no cambia cálculos ni firmas. Después ejecutar la suite completa, reconstruir el
ZIP y entregar a Work 3 el SHA resultante. No es necesario reimplementar la arquitectura ni recuperar `detalle`
en las firmas Studio.
