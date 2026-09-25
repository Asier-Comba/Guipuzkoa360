# Smoke de ingeniería — 2026-09-25

**INFRASTRUCTURE_BLOCKED. No PORTAL GO nuevo.** Versión seleccionada por etiqueta de conversación: `urban-challenge-rc2-195b498 · v4`, memoria activa, sin Internet. Un intento nuevo en esta misión (máximo autorizado tres); se detiene tras error explícito de infraestructura. No se crea versión ni se edita runtime/contexto. No se abre Entrega.

Inicio del envío: **2026-09-25T14:30:13.472Z**. Pregunta:

> ¿Qué municipios coinciden en envejecimiento de 65 o más y mayor distancia a atención primaria, con cuantil 0,75, umbral de 2 km y periodo 2025-01-01? Incluye municipios destacados, cortes, filas usadas, unidades, fuentes y el límite principal.

A los 1.244 ms observados, «El agente está trabajando…». A los 14.767 ms seguía trabajando. A los 51.790 ms se observan el turno terminado, dos tool entries y respuesta. Estos son **tiempos de observación**, no latencia exacta de tool ni cálculo. No hubo output analítico exitoso.

| Entrada visible | Args | Resultado |
|---|---|---|
| obtener_resumen_territorial (innecesaria para P1) | municipio="San Sebastián", periodo="2025-01-01" | UI Error en obtener_resumen_territorial; no output analítico |
| analizar_coincidencia | categoria_servicio="atención primaria", grupo_edad="65 o más", umbral_km=2, periodo="2025-01-01", cuantil=0.75 | «ERROR al ejecutar analizar_coincidencia: El runner está ocupado. Espera a que termine una tarea e inténtalo de nuevo.» |

No se envía `detalle`. UI resumen indica 3 llamadas y 3.754 tokens; hay dos entradas tool visibles. No se equiparan contadores de modelo con llamadas de tool, ni se infiere una tercera ejecución oculta.

Respuesta visible (extractos propios del agente): «No puedo identificar los municipios coincidentes porque el cálculo solicitado no se ha ejecutado: el runner está ocupado». Reconoce falta de municipios, filas y fuentes y no inventa valores. Pero enumera «Distancia a atención primaria: más de 2 km» y «Coincidencia: ambos criterios simultáneamente», formulación que confunde el umbral con la selección por cuantiles.

Esperado P1: 88 filas, cortes 23,973 % / 2.019,2 m, 7 destacados. **No observado en este intento.** P2 seguimiento 75+/q0,80/3 km: NOT_RUN por bloqueo de P1. P3 fuera de alcance: NOT_RUN en este smoke. Los controles offline de ambos no sustituyen una ejecución de plataforma.

## Riesgo nuevo y acción segura

MEDIUM M-02: fallback conversacional bajo fallo de tool puede confundir threshold/cuántiles y hacer una llamada irrelevante. No se altera runtime por la congelación. Mitigación para demo: no presentar una respuesta de error como análisis; mostrar el control guardado claramente rotulado; explicar [la distinción](../architecture/THRESHOLD_VS_QUANTILE.md). Después, con autorización para una nueva versión, probar primero recuperación de errores y selección de tool. No se presume que NEXT parchea este comportamiento de v4.

M-01 existente: payload extremo no verificado en portal. El bloqueo es además una dependencia operativa, no un FAIL numérico del core. Evidencia histórica de versiones v2/v3/v4 queda en [PORTAL_EVIDENCE_RC2](../PORTAL_EVIDENCE_RC2.md), con su corrección de alcance; no se relabela todo como v4.
