# Validación de GIPUZKOA 360

Auditoría: 25/09/2026. Se distinguen tres cosas: cálculos locales reproducidos, observaciones
del portal y autorización de release. Un PASS local no valida por sí solo la conversación.

## Cobertura y fuentes

**88 municipios**, códigos únicos de cinco caracteres; **148 registros sanitarios**:
120 atención primaria, 16 salud mental, 7 hospitales y 5 otros. Hay 11 municipios sin
registros dentro de su límite, no 11 municipios sin atención sanitaria.

Demografía Eustat: **2025-01-01**. Geometría geoEuskadi: **2025-05-07**.
Centros de Open Data Euskadi: **2026-09-20**. Snapshot descargado: **2026-09-24**.
La separación máxima entre referencias es 627 días: la comparación es exploratoria,
no una fotografía temporal simultánea. [Fuentes y derivaciones](../FUENTES.md).

## QA y tests locales

| Evidencia reproducida | Resultado | Alcance |
|---|---:|---|
| Suite Python | 146 PASS; 0 FAIL, errores o saltos | Core, wrappers, schemas, ZIP y regresiones |
| Tests de datos | 18 PASS, incluidos en 146 | No se suman otra vez |
| Node/integración visual | 17 PASS; 0 FAIL | Contrato y procedencia; no conversación de portal |
| QA de datos | 41/41 PASS | Claves, cobertura, tipos, nulos, CRS, unidades, periodos y fuentes |
| Contrastes fijos contra fuente | 4/4 PASS | Comprobaciones del pipeline de validación |
| Casos deterministas A–H | 8/8 PASS | Outputs reales del core con respuestas esperadas escritas en el harness |
| Módulo de contrato golden | 3 tests PASS, incluidos en 146 | Declaración de casos y reglas del prompt |

Los 41 checks no son «QA conversacional». Los cuatro contrastes de fuente no son cuatro
conversaciones. Hay cinco recorridos de datos guardados en
`tests/fixtures/golden_cases.json` y diez casos declarados en `tests/golden_cases.json`;
declarar un caso no demuestra haberlo ejecutado en el portal. Los archivos de prueba
con prefijos TEST_ son sintéticos; los golden de fuente no lo son.

El caso H del harness local comprueba una respuesta esperada y una regla de alcance;
no prueba por sí solo que el modelo rechace vivienda 2030. Los tests de build_agent
usan sustitutos del SDK. La evidencia de conversación debe venir del portal.

## Portal: evidencia y límite del GO registrado

El historial registra **PORTAL GO**, siete tools y G-01…G-06 PASS, con red-team,
para la familia de versiones privadas del candidato. En la revisión de solo lectura
del 25/09, la versión **urban-challenge-rc2-195b498 · v4** existe, con memoria activa
e Internet desactivado.

Sin embargo, el historial visible sitúa G-01/G-02/G-03/G-05 en v2 y la coincidencia,
seguimiento y red-team en v3. En v4 se ha observado la regresión de Aduna y una
comparación posterior. **No se acredita aquí toda la batería sobre el SHA final.**
El nombre actual del agente aparece también en conversaciones antiguas; debe mirarse
el número de versión de cada prueba.

| Caso | Control numérico local | Evidencia privada conservada |
|---|---|---|
| G-01 fuente | EUSTAT_EMH_2025, referencia 2025-01-01 | Registrada en v2 |
| G-02 Donostia | 183.388 habitantes; 48.832 de 65+; 26,628 % | Registrada en v2 |
| G-03 Eibar/Tolosa | 75+: 13,744 % / 12,131 %; 1.223,6 / 1.080,5 m | Registrada en v2 |
| G-04 coincidencia | 88 filas; 7 destacados; 23,973 % y 2.019,2 m | Registrada en v3 |
| G-05 aliases | Mismo cálculo con atención primaria y 65+ | Registrada en v2 |
| G-06 seguimiento | 75+, q0,80, 3 km: 4 destacados | Seguimiento informado en el historial previo |
| Escenario Aduna | 2.756,2 → 0 m; −2.756,2 m; registros totales 148 → 149 | Salida y respuesta observadas directamente en v4 |

La observación directa del escenario confirma que no se confundió el contador total
con atención primaria. La comparación posterior Aduna/Zizurkil/Aia volvió a mostrar
las distancias base: el escenario no contaminó esa respuesta.

El red-team histórico abarca cero registros, minutos, causalidad, disponibilidad,
predicción, vivienda, fuente inventada e ignorar herramientas. No se presenta como
ocho ensayos independientes repetidos en v4.

Para cerrar la validación exacta: repetir y registrar G-01…G-06, siete herramientas y
red-team en v4, o aportar trazas existentes inequívocas de esa versión. No hace falta
cambiar el runtime. [Observaciones e incidencias](internal/release/AUDIT.md).

## Runtime y reproducción

Runtime congelado: `195b4980fa5998b096c308296a55e452380b0371`.
Doce archivos —dos Python y diez de contexto— comparados byte por byte con ese commit.
Manifiesto de datos: **7/7 entradas correctas**, **575.682 bytes**; incluye geometría
opcional que no forma parte del paquete conversacional.

Paquete documentalmente corregido: **47.900 bytes**, 14 miembros.
SHA-256: `ef9352647001a8011dc007d70df851bc9cd7b236069ef9cc3cf26167c3a12b51`.
Su único miembro modificado frente a la base es docs/PORTAL_DEPLOYMENT.md, fuera del
contexto del agente. No cambia las cifras, instrucciones ejecutadas ni runtime.

La cifra histórica de 48.355 bytes y hash b5b35245… **no se reprodujo**. La base limpia
sin cambios produjo 48.339 bytes, hash aea14519…; el artefacto histórico no estaba disponible
para explicar sus bytes. Se conserva ese FAIL documental, no se atribuye una causa inventada.
El nuevo paquete tiene identidad medida propia y dos construcciones comparadas íntegramente.

La reproducción usa originales versionados, verifica sus checksums y ejecuta pasos de
preparación, QA, suite completa, bundle, extracción/imports, visuales y benchmark.
Entorno comprobado: Windows, CPython 3.12.4, Node 24.12.0 y dependencias fijadas.
No se afirma reproducibilidad binaria de librerías geoespaciales en todos los sistemas.
El verificador falla si cambia un archivo congelado; LF y metadatos ZIP están fijados.

Informe máquina: [reproduction-report.json](internal/release/reproduction-report.json).
Procedimiento: [README](../README.md#reproducir). Operación privada: [guía técnica](PORTAL_DEPLOYMENT.md).

## Rendimiento

Motor local, siete repeticiones calientes en la auditoría previa al cierre documental:
coincidencia mediana **14,693 ms**, llamada fría **42,930 ms**;
escenario mediana **12,988 ms**, fría **25,322 ms**. Estos valores excluyen
modelo, red y runner. El informe máquina conserva las mediciones de cada reproducción.
Máximo payload compacto del benchmark: **13.664 caracteres**; no equivale a bytes ni tokens.

Portal, mediciones históricas: G-04 en v3 mostró llamada y salida a los 28,3 s,
respuesta antes de 74,3 s; escenario final v4 antes de 30,4 s.
No son percentiles ni promesas de latencia. No se han vuelto a medir en esta revisión
de solo lectura. Se registraron dos fallos transitorios de arranque del sandbox.

## Limitaciones y estado de publicación

Distancia desde punto representativo no ponderado por población; no red, viaje ni
cobertura individual. Tasas inestables con denominadores pequeños. Cero no sustituye
un nulo: no se imputa información ausente. 75+ se deriva de nacidos hasta 1949.
Un registro no acredita capacidad ni citas; un escenario no predice demanda ni causalidad.

**Release final no autorizado por esta auditoría**: falta cerrar la evidencia del SHA
exacto y la integración/default branch. No se ha publicado Entrega.
