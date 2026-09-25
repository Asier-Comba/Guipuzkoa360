# Evidencia de ingeniería: problemas reales, decisiones comprobables

No se infieren horas a partir del historial; el esfuerzo se acredita mediante artefactos, cambios y pruebas verificables.

Fechas de autor obtenidas con `git log --all --date=iso-strict`. Un commit acredita un cambio; el resultado solo se atribuye a un test o registro conservado. Las cifras finales no se retroatribuyen a etapas anteriores. Rama base `46c1a48…`; runtime `195b498…` congelado; [gobierno](RELEASE_GOVERNANCE.md).

| Fecha | Problema | Decisión / cambio | Test / evidencia y resultado | Commit / PR |
|---|---|---|---|---|
| 24-09-2026 | Fuentes dispersas, unidades no unidas | Ingesta oficial con originales conservados y claves municipales | `tests/data`, FUENTES y manifests; cobertura final contrastada 88 | `e3043ae`, PR #1 histórico, sustituido por #4 |
| 24-09-2026 | Coordenadas no comparables directamente | Pipeline geoespacial y distancia desde punto municipal EPSG:25830 | Integridad/coordenadas y controles manuales; distancia geométrica, no accesibilidad real | `140f8a3`, `b317491` |
| 24-09-2026 | Contratos de consumidor y ausencia de registros | Datos QA, invariantes, goldens, manifiesto runtime | `tests/data/test_quality_contract.py`, `tests/golden_cases.json` | `022a3cc`, `ba60d16`, PR #4 merge `1379b1c` |
| 24-09-2026 | Hacían falta operaciones verificables | Core determinista y agente con schema; integrar datos reales | `test_analysis`, `test_public_tools`, `test_real_data_integration` | `419a427`, `017555e`, PR #3 origen; recuperación `9295887`/`45cb122` |
| 24-09-2026 | Visuales sin vínculo suficiente al output | Adaptador real y artifacts reproducibles | `test_work3_agent_adapter`, Node contrato; no confundir local con conversación | `464f96f`, `fe5b100`, `c7819d9` |
| 24-09-2026 | Registro de tools no operativo en portal | Siete wrappers físicos visibles para Studio | `test_studio_registry`; historial de fallos conservado | `67e385e`, `dd595ac`, `93226cb` |
| 24-09-2026 | Payload, no finitos, instrucciones incompatibles | Compactar, JSON estricto, validar números; consolidar auditoría | `test_compact_outputs`, `test_adversarial_core`, `test_portal_runtime_rc2` | `961bd3d`, `c13b848`; aportes `5c8841e`/`c97032a` |
| 24-09-2026 | «65 o más» y «porcentaje» no reconocidos | Normalización de aliases con regresiones | `test_parameter_normalization`; evidencia histórica G-04/seguimiento | `d8ec018`, `ae62080` |
| 24-09-2026 | Contador de escenario ambiguo | Aclarar que service_count cuenta todos los registros sanitarios | Aduna v4 148→149 y distancia 2.756,2→0 m; alcance de versiones corregido después | `195b498`, `488f46d` |
| 25-09-2026 | Casos puntuales insuficientes | Benchmark exhaustivo y trazabilidad, pares/umbrales/escenarios/soak | 72.673/72.673, 31.545 outputs trazables; 20 inyecciones y 1.000 soak en informe | `bf5c6cc`, `a1b0ecb` |
| 25-09-2026 | ZIP discrepaba en un byte según checkout | Identificar LF/CRLF de requirements, canonizar contenido y metadatos ZIP | `analisis/zip_root_cause.json`, `cross_worktree_reproducibility.json`; alcance de toolchain acotado | `5e7210c` |
| 25-09-2026 | Hero usaba pct≥25 sobre tres municipios | Mostrar salida provincial real y cortes por cuantiles | Hero 7/4/2 y 88 filas; no recalcular métricas en JS | `d0e1a05` |
| 25-09-2026 | Pantalla podría divergir silenciosamente | Gate del output completo y ataques a artifacts | 9 corrupciones visuales rechazadas, `test_final_artifacts` | `5b0c228` |
| 25-09-2026 | Integración necesitaba estado y scope claro | Base canónica, documentación y PR abierta | PR #9, base `46c1a48`; smoke anterior bloqueado, no convertirlo en PASS | `84e9516`, `91d1a26`, `46c1a48` |
| 25-09-2026 | No existían checks remotos de release | CI separada rápida Linux/Windows y manual exhaustiva | Primeras dos ejecuciones Linux FAIL por ruta de manifiesto; parche completo y ambos PASS | `6217ecd`, `7228bbf`, `47362d3`; [runs](operations/CI_AND_REPRODUCTION.md) |
| 25-09-2026 | Evolucionar podía contaminar el runtime | NEXT aislado, DataOps solo propuestas, medición con denominadores | Suite `tests/next`; 16/16 ataques bloqueados, 8 goldens, core sin duplicar | `171b6cb` y endurecimiento posterior de esta rama |
| 25-09-2026 | Smoke reciente seguía incierto | Ejecutar P1 sobre v4 sin editar nada | Runner ocupado; fallback confunde threshold/cuántiles: Medium nuevo, no PASS | [registro del intento](operations/PORTAL_SMOKE_ENGINEERING.md) |

## Qué se midió ahora

[Benchmark repetido](../analisis/ops/full-validation/full_validation.json): 72.673 PASS, cero fallos, 31.545/31.545 trazabilidad bajo definición del harness; 20 rechazos controlados, 1.000 llamadas sin drift/excepciones. Su baseline histórico interno no es el BASE_SHA de esta ingeniería; no se reescribe ese historial.

[Salud de fuentes](../analisis/ops/source_health.json): 88/88, 148 registros, 412/412 referencias de fila y 7/7 hashes. [NEXT](../analisis/next/evaluation.json): 9 casos soportados incluyendo seguimiento, 6 fuera de alcance, 16 corrupciones/afirmaciones bloqueadas. La cifra 16/16 no mide lenguaje natural ni sustituye los 20 faults del benchmark estable.

Se conservan pruebas negativas: manifiesto vacío, bytes alterados, claves/campos/coords corruptos, fuentes falsas, no finitos, JSON duplicado, draft libre y contaminación de memoria entre sesiones. No se contabilizan líneas de código como pruebas.

## Riesgos, no marketing

M-01 payload extremo sin validar en portal; M-02 fallback con umbral confundido al fallar el runner. Infraestructura actual bloqueada. Sin aprobación para modificar la versión congelada, se documenta y no se parchea. NEXT sigue experimental; no hay autopromoción, previsión sanitaria ni capacidad/citas inferidas de registros. Cero Critical/High encontrados en los gates ejecutados no significa riesgo cero.
