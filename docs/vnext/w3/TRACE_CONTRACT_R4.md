# Revisión de traza W3 `W3_TRACE_2.1.0`

El contrato [R3 2.0.0](TRACE_CONTRACT_R3.md) queda histórico. **2.1.0 es
incompatible**: el scorer rechaza 2.0.0 de forma explícita. Se preservó el
fixture original como `NO_LLM_single_case_v2_0.jsonl`; el fixture activo es
2.1.0. No se migran trazas reales automáticamente: un ejecutor debe aportar
los campos y la evidencia nuevos observados, nunca rellenarlos por conjetura.

## Campos nuevos y semántica

- `execution_mode`: `SYNTHETIC_TEST`, `OFFLINE_TOOL`, `LOCAL_LLM` o
  `PORTAL_LLM`. Los dos primeros no pueden afirmar invocación de modelo.
- `invocation_state`: `not_started`, `started`, `completed`, `failed`,
  `interrupted` o `capture_incomplete`. `llm_executed` conserva el significado
  de invocación **iniciada**, no de respuesta recibida; debe concordar con el
  estado. Solo `completed` admite veredicto de corrección y respuesta final.
  Intentos fallidos o interrumpidos permanecen en el denominador, con clase
  y observación de error. No se inventa un mensaje `assistant` ausente.
- `identity.assembly_manifest_file` y `.assembly_manifest_sha256` son
  obligatorios para una invocación de LLM. El manifiesto `W3_ASSEMBLY_1`
  captura HEAD declarado, ZIP y datos por SHA, miembros por hash, archivos
  fuente capturados, configuración, imports externos declarados y comando de
  generación. El scorer comprueba bytes, relaciones y seguridad ZIP sin
  exigir `.git`. Esto demuestra **consistencia del paquete de evidencia**,
  no autoría o autenticidad absoluta de un portal.
- `semantic_checks[].evidence_path` es un JSON Pointer. Un `parameter` o
  `recalculation` que pasa debe referir una llamada real y un valor extraído
  de `/arguments/...` o `/output/...`; `observed` autoescrito no basta.
  Aclaraciones y negativas justificadas usan `limit` o revisión humana sin
  forzar una llamada inexistente.

El lector JSONL rechaza claves duplicadas antes de convertir a diccionario.
Cuando el output de una tool contiene `request_id`, este se compara con el
binding de la traza. En conversaciones, cada mensaje `tool` añadido debe
corresponder al output JSON canónico de una llamada observada. Si la
plataforma no expone un ID se registra `null`; no se fabrica.

## Denominadores

`single_cases.target_per_system` es 48 o 60; `scored_by_system`,
`correct_by_system` e `incorrect_by_system` tienen claves `v4` y/o
`candidate`. `conversations.planned_per_system` es 20;
`executed_by_system`, `complete_by_system` y `turns_scored_by_system` son
mapas por sistema. No se muestra 120/60 ni 40/20 como un porcentaje.
`systems[...].families[SINGLE_CASE|CONVERSATION]` conserva identidad,
primeras tentativas, repeticiones y p50/p95 por familia. Fallos y estados
de invocación tienen recuentos propios. Los pares comparables requieren
misma configuración, datos y protocolo; las fuentes nuevas se informan como
utilidad adicional. Sin llamadas LLM, el estado continúa `NOT_RUN`.

**Modo de prueba:** los registros `LOCAL_LLM` que construyen los unit tests
son hipotéticos y viven solo en `tmp_path`; no se publican como runs. El
fixture público `SYNTHETIC_TEST` no puede puntuarse ni convertirse en una
ejecución real cambiando solo `llm_executed`.
