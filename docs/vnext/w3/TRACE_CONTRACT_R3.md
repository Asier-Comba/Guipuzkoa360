# W3 R3 · contrato de trazas observadas (`W3_TRACE_2.0.0`)

Este contrato pertenece al **evaluador independiente**, no sustituye el
contrato de evidencia W2 1.0.0. Una fila JSONL representa **un intento** de un
caso individual o **un turno** de una conversación. Todos los ejemplos
`NO_LLM` son sintéticos y solo prueban el validador. El corpus congelado R2 y
sus criterios permanecen byte a byte intactos.

## Identidad y evidencia común

Cada fila tiene exactamente: `schema_version`, `record_type`, `record_id`,
`system`, `identity`, `attempt`, `started_at`, `ended_at`, `llm_executed`,
`error_class`, `error_observation`, `verdict`, `reviewer`, `review_notes`,
`evidence`, `tool_calls`, `final_response`, más los campos del tipo indicados
abajo. `record_type` es `SINGLE_CASE` o `CONVERSATION`; `system` es `v4` o
`candidate`. Los timestamps son ISO 8601 con zona y los intervalos deben
ser ordenados. `error_class` es `null`, `agent`, `contract`, `data`, `platform`
o `unknown`; sin observación causal no se admite `platform`. El validador no
infiere que un error de dominio sea HTTP 504.

`identity` contiene exactamente `runtime_commit` (40 hex), `package_sha256`
(64 hex), `model_id`, `model_config` (objeto no vacío),
`data_manifest_sha256` (64 hex), `context_mode` (`portal_memory`,
`local_memory` o `isolated`), `corpus_sha256` (SHA-256 de los bytes del JSON
congelado de esta familia) y `scoring_version` (`2.0.0`). El evaluador
**rechaza más de una identidad por sistema y familia** en un lote. No agrupa
dos paquetes bajo `candidate`. Las huellas de cero están reservadas para
fixtures `NO_LLM`; nunca para una ejecución puntuable.

`evidence` contiene `path` y `sha256`. `path` apunta a un archivo de evidencia
existente dentro de la raíz de evidencia pasada al scorer; se comprueban
bytes y hash. Un vínculo no vacío, una opinión de reviewer o un `PASS`
declarado sin archivo recuperable no son evidencia. Los archivos de portal
pueden exportarse a un almacén privado local: no se suben conversaciones
sensibles al PR.

Cada entrada de `tool_calls` conserva `call_id`, `name`, `arguments`,
`arguments_sha256`, `output_or_error`, `output_sha256`, `request_id` y
`result_request_id` (los dos últimos pueden ser `null` si la plataforma no
expone esos identificadores), `started_at` y `ended_at`. Los hashes de
argumentos y salida usan JSON UTF-8 canónico (`sort_keys=True`, separadores
compactos, sin NaN). Si ambos IDs existen deben coincidir. Para W2, se
conserva además el sobre de evidencia original en `output_or_error`.

## `SINGLE_CASE`

Campos propios: `case_id`, `prompt`, `initial_context_protocol`,
`history_before`. El protocolo es `{id:"seed_user_prompts_v1",
seed_user_prompts:[...]}` y debe igualar el plan congelado. `history_before`
registra **mensajes reales** anteriores, con `role` (`user`, `assistant`,
`tool`), `content` textual y `sha256` de sus bytes UTF-8. Para cada pregunta
seed debe verse el mensaje `user` y una respuesta `assistant` posterior;
los mensajes de tool pueden intercalarse. Un seed sin respuesta real no crea
un contexto comparable. La pregunta actual sigue en `prompt`. Las
respuestas previas de v4 y candidato pueden diferir, pero se registran ambas.

## `CONVERSATION`

Campos propios: `conversation_id`, `turn_index` (1..3 en R2), `session_id`,
`prompt`, `history_before`, `history_after`, `semantic_checks`. Cada sistema
empieza cada escenario en una sesión nueva. Para un mismo escenario, el
`history_before` del turno siguiente debe ser idéntico al `history_after`
del anterior; el `session_id` no cambia. `history_after` añade la pregunta,
los mensajes de herramienta observados y la respuesta final cuando se
ejecuta. No se exige igualdad textual entre historias de v4 y candidato.

`semantic_checks` registra una o más verificaciones en cada seguimiento:
`kind` (`reference`, `parameter`, `recalculation`, `topic_return`,
`session_isolation`, `limit`), `expected`, `observed`, `passed`,
`evidence_call_id` (o `null`) y `review_note`. En un cambio de parámetro,
`expected` y `observed` son valores JSON y deben coincidir para un veredicto
`correct`. El scorer conserva el juicio humano; no sustituye la revisión
semántica con coincidencias de palabras. Un check fallido impide `correct`.

## Agregación y comparabilidad

Los intentos empiezan en 1 sin huecos por caso/turno. La métrica principal
usa la primera tentativa; todas las repeticiones y sus errores/latencias se
conservan aparte. Un registro sin LLM solo puede ser `not_scored`. Las 20
conversaciones planeadas cuentan como cero ejecutadas si no hay trazas.

Un par v4/candidato comparte `prompt` y protocolo de inicialización. Para
declarar **cálculo comparable**, además debe coincidir `model_id`,
`model_config`, `data_manifest_sha256` y `context_mode`. Una tarea sanitaria
con datos adicionales es utilidad nueva con cobertura distinta, no un
acierto adicional en igualdad de fuentes. El scorer informa pares observados
y pares comparables por separado. `EVALUATED_REVIEW_REQUIRED` nunca equivale
a `PASS` de producto o release.

## Fixture y ejecución

`tests/vnext_redteam/fixtures/NO_LLM_single_case.jsonl` y su evidencia
prueban únicamente el formato. El resultado esperado es `NOT_RUN` en
capacidad conversacional, `llm_executed=0`. Un ejecutor real deberá guardar
JSONL y evidencia privada y llamar a `score_runs.py --runs ...
--evidence-root ...`. No hay ejecución de modelo implícita en el scorer.
