# Prueba privada del coordinador en el portal · 24/09/2026

Se creó en el workspace del equipo un agente **separado** llamado `GIPUZKOA 360 · integración jurado` y se cargó `dist/gipuzkoa360-portal.zip` (43.370 bytes). No se tocó el borrador `Agente principal`, no se eligió versión para Entrega y no se publicó la entrega.

## Resultados observados

| Versión | Configuración | Preparación | Prueba conversacional |
|---|---|---|---|
| v1 | `main.py` extraía el ZIP e importaba las siete tools originales | 7 tools detectadas, versión creada | El coordinador seleccionó `analizar_coincidencia`; el runtime devolvió `KeyError: La tool analizar_coincidencia no está registrada`. |
| v2 | Siete wrappers `@tool` físicos en `tools.py` del agente privado | 7 tools detectadas, versión creada | El mismo `KeyError` de registro. |
| v3 | `@tool analizar_coincidencia` declarada directamente en `main.py`; código de prueba reproducible en `scripts/agent/portal_probe.py` | 1 tool detectada, versión creada | Se ejecutó la tool y devolvió errores controlados de parámetros. El coordinador transformó «atención primaria» en una categoría inválida; corrigió grupo y periodo, pero no la categoría técnica `primary_care`. No inventó un recuento. |

En la misma conversación v3 se envió una llamada con `categoria_servicio="primary_care"`, `grupo_edad="65"`, `periodo="2025-01-01"`, `cuantil=0.75` y `umbral_km=1`. La llamada apareció en la traza, pero permaneció **en curso más de dos minutos, sin resultado observado**. Se detuvo y la conversación quedó cancelada. Esto no valida el cálculo en el portal.

## Conclusión operativa

Las salidas locales verificadas y los HTML no deben presentarse como ejecución del coordinador en el portal. La versión privada v3 tampoco debe seleccionarse para la entrega: solo contiene una tool de diagnóstico y no completó una llamada válida.

Para resolverlo, registrar las siete tools como funciones locales del agente en Studio y colocar los CSV preparados como archivos físicos declarados para la versión, en vez de depender de extraerlos del ZIP durante la llamada. Repetir las cinco consultas del guion, comprobar al menos un `output_ref` contra el CSV y capturar la traza antes de elegir la versión definitiva. El PR de integración conserva el código y resultados locales completos para hacer esa prueba sin cambiar el contrato de producto.
