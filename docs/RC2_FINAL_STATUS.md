# GIPUZKOA 360 · Estado final local de RC2

Fecha: 2026-09-24  
Versión: `urban-challenge-rc2`  
Rama: `fix/portal-runtime-rc2`  
Commit de runtime auditado: `b8a541c097bfabd515fff248a0e7be40ce713994`

Este documento registra la congelación local. Los commits posteriores que solo actualicen evidencia o este
documento no cambian `main.py`, `tools.py`, los datos ni el contenido del paquete. Work 3 debe validar en el
portal el último SHA de la rama y confirmar que su árbol de runtime coincide con el commit anterior.

## Paquete reproducible

- Archivo: `dist/gipuzkoa360-urban-challenge-rc2.zip`.
- Tamaño: **48.095 bytes** de un máximo de 25.165.824.
- SHA-256: `de80d2c13a097cd2b2040bbe0cdddd0b3e6e7f38cfbdd55b38ae270284b2b532`.
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
| Suite Python completa | 131/131 PASS | 10,462 s incluyendo build y A–H |
| Tests de datos | 18/18 PASS | 7,727 s |
| Golden contract/fuente fija | 3/3 PASS | 2,531 s |
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

Ambas operaciones quedan muy por debajo de 100 ms localmente; coincidencia queda por debajo de 12.000
caracteres. No se aplicaron optimizaciones adicionales.

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

Estado: **PENDIENTE DE VALIDACIÓN POR WORK 3**. No se ha entrado al portal durante esta misión. La evidencia
anterior corresponde a `e13c3e5`, no a este runtime, y por tanto no autoriza un PASS de RC2. No se debe abrir
el PR a `main`, fusionar ni publicar Entrega hasta que Work 3 complete G-01…G-06 sobre el último SHA exacto.

## Riesgos e items pendientes

- El tiempo del runner del portal no es equivalente al benchmark local y debe medirse de nuevo.
- La memoria de seguimiento, selección de tool y no solicitud de detalle requieren evidencia conversacional.
- Work 3 debe publicar preguntas, tools, argumentos, salidas, tiempos y PASS/FAIL para G-01…G-06.
- Tras PASS completo: incorporar solo su evidencia final y abrir PR limpio a `main`; no publicar Entrega.
