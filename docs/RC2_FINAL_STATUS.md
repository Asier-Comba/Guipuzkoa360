# GIPUZKOA 360 · Estado final local de RC2

Fecha: 2026-09-24  
Versión privada: `urban-challenge-rc2-195b498 · v4`
Rama: `fix/portal-runtime-rc2`  
Commit de runtime auditado y probado en portal: `195b4980fa5998b096c308296a55e452380b0371`

Este documento registra la congelación local y la validación privada en portal. Los commits posteriores que
solo actualicen evidencia o este documento no cambian `main.py`, `tools.py`, los datos ni el contenido del
paquete probado.

## Paquete reproducible

- Archivo: `dist/gipuzkoa360-urban-challenge-rc2.zip`.
- Tamaño: **48.355 bytes** de un máximo de 25.165.824.
- SHA-256: `b5b35245aaa08015b2955281b0edb9cc3254fa7fae77966d63d9fa6651b48227`.
- Reproducibilidad: dos construcciones consecutivas produjeron el mismo tamaño y SHA-256.
- Entrada: `main.py:build_agent`, síncrona.
- Dependencias añadidas: ninguna; Studio aporta `langchain` y `studio`.

## Arquitectura congelada

- `main.py`: coordinador, guardas semánticas y siete wrappers `@tool` físicos.
- `tools.py`: bundle autocontenido generado desde el core determinista.
- Las firmas públicas de Studio no incluyen `detalle`; siempre entregan la vista compacta.
- El core conserva `detalle=True` solo para auditoría offline.
- `STUDIO_CONTEXT_FILES`: diez archivos físicos, sin Internet, secretos ni rutas locales.
- Datos: 88 municipios, 148 registros sanitarios, contrato `1.1.0` y cálculo métrico EPSG:25830.

## Validación local

| Puerta | Resultado | Duración observada |
|---|---:|---:|
| Pipeline completo, incluidos QA y regeneración del manifiesto | PASS | 25,191 s |
| QA exhaustivo | 41/41 PASS | incluido en pipeline |
| Suite Python agregada tras las regresiones | 146/146 PASS | ejecución local completa |
| Tests de datos | 18/18 PASS | 7,727 s |
| Golden contract/fuente fija | 4/4 PASS | ejecución local |
| Node/E2E | 17/17 PASS | 3,574 s |
| Casos deterministas A–H | 8/8 PASS | incluido en la suite |
| Extracción ZIP y smoke real de coincidencia | PASS | incluido en la suite Python |

No hay fallos, saltos ni excepciones aceptadas como conocidas.

## Contrato funcional

- Coincidencia 65+, q0,75, 2 km: 88 filas unidas, 7 municipios destacados.
- Seguimiento 75+, q0,80, 3 km: nueva ejecución y 4 municipios destacados.
- Escenario: devuelve solo municipios con cambio material y conserva resumen sobre las 88 filas.
- Las salidas compactas preservan `rows_used`, cortes, unidad, periodo, fuentes, método, warnings y límites.

## Rendimiento

Medición local reproducible de `scripts/agent/benchmark_tools.py`, siete repeticiones calientes:

| Tool | Fría | Mediana caliente | Payload compacto |
|---|---:|---:|---:|
| `analizar_coincidencia` | 16,164 ms | 7,433 ms | 5.216 caracteres |
| `simular_escenario` | 17,321 ms | 7,975 ms | 13.664 caracteres |

Todos los payloads normales quedan por debajo de 15.000 caracteres; `simular_escenario` es el mayor con
13.664. No se aplicaron optimizaciones adicionales.

## Manifiesto runtime

`datos_preparados/runtime_manifest.json` fue regenerado desde cero. Sus siete entradas coinciden exactamente
con los bytes y SHA-256 de los archivos físicos; total declarado: **575.682 bytes**. `.gitattributes` fija LF
para CSV, JSON, Markdown, JavaScript y Python, y `test_runtime_bundle_is_compact_and_hashes_match` impide
aceptar una desincronización futura.

## SYSTEM_PROMPT

Solo se añadieron guardas operativas:

- preferir exactamente una tool cuando baste;
- no pedir datasets completos si la salida compacta resuelve la consulta;
- ejecutar de nuevo al cambiar un parámetro en un seguimiento;
- responder de forma breve y orientada a decisión;
- no repetir campos JSON sin valor para el usuario.

Las reglas de trazabilidad, límites semánticos y no alucinación existentes se conservan.

## Portal

Estado: **PORTAL GO**. La versión privada `urban-challenge-rc2-195b498 · v4` pasó preparación, G-01…G-06,
una consulta real de cada una de las siete tools, red-team y la regresión final del escenario. `main.py` y
`tools.py` coinciden con el runtime probado; el `ejecucion.py` adicional es infraestructura administrada por
el portal. Memoria activa, Internet desactivado y ninguna firma o llamada expone `detalle`. No se abrió
Entrega ni se publicó. Evidencia detallada: `docs/PORTAL_EVIDENCE_RC2.md`.

## Riesgos e items pendientes

- El runner del portal sufrió dos fallos transitorios de preparación del sandbox; ambos pasaron al reintentar.
- La rama está publicada, pero todavía no existe una Pull Request de `fix/portal-runtime-rc2` a `main`.
- La decisión de abrir/fusionar PR y publicar Entrega queda fuera de esta validación y requiere autorización.
