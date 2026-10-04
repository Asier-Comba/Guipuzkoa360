# R25 — reconciled visit explanation

Base: R24 evidence HEAD `e4f16aed15cf2b0ba60836926aaabf511a1cdbc3`, runtime `7d1d2da3a88c5f8880bf228dd4ae70855bff3866`. Main remains `e213eaa9b73b0f8a4d1893e0269fe92fe6756955`.

## Root cause and bounded repair

R24 validated total and endpoints but exposed component durations as integer seconds, leaving grouping/conversion to the conversational model. Its actual answer omitted 1,220 seconds despite a correct total. R25 adds an ordered public duration ledger with eight disjoint intervals, integer seconds, human duration from the existing formatter, evidence pointers, and a complete generated Markdown table. Only tools.py and the SYSTEM_PROMPT literal change. All other main.py AST nodes, 23 other ZIP members, 15 context assets, W1 and territorial v4 remain unchanged.

The model is instructed to copy the complete ledger table, total and clocks without regrouping or calculating new subtotals. This is a risk reduction, NOT a mathematical guarantee about arbitrary model output. Actual Studio acceptance is mandatory. No prompt, entity, appointment time or oracle number is embedded in runtime logic. Labels identify component semantics, not a particular itinerary.

The eight intervals must be ordered, contiguous, nonnegative integer seconds, with exact kinds and no duplicate component IDs. Their sum must match the raw total and end minus start. The previous projection's values and formatted summary must agree. Any failure passes through the existing fail-closed public boundary without numerical claims. Margins constrain feasibility and are already contained in waits; return slack is not another duration to add. Total is a summary row, not a ninth component.

## Validation families and what they establish

- Focal: three supported origins, two appointment times, another 10:00/30-minute visit; raw/claims/ledger/table equality, source and parameter preservation, endpoint and threshold regressions, error boundaries.
- Adversarial: missing/duplicate intervals, overlap/gap, wrong total, wrong conversion, negative/empty fields, incorrect formatted total and public component values, invalid interval seconds and booleans. The table's human text is parsed independently back to seconds.
- Partition fuzz: 5,000 deterministic random partitions and hour/minute boundary values, each paired with a broken interval. This tests the projection, not new provider coverage.
- Inherited raw parity/oracle/fuzz: exact new package is executed in cold processes with network denied. Checks all raw outputs/effective requests/claims against the earlier engine baseline, oracle cases, malformed public calls, source attribution and supported catalog signatures. No old PASS is transferred.
- Identity/build: protected v4 assets against immutable Git blobs; every non-code ZIP member identical to R24; two builds byte-identical in ZIP and manifest; jury and final artifact gates preserve territorial results.
- Python/Node and Linux/Windows CI exercise repository regressions. Passing counts alone do not establish conversational correctness.

Development finding retained: the initial focal run had 6 failed test assertions comparing pre-format internal metadata with the public metadata projection. Corrected the test to compare the same projection stage; no source date or runtime code was changed to make the assertion pass.

## Second logical review before Studio

Review from the final generated ZIP, separately from test-writing: check interval partition and sum, the formatter's single authoritative integer input, table generation from exactly those rows, margins/total not represented as additive components, no raw/claim mutation, no numerical fallback on error, unchanged sources/periods and public signatures. Record outcome in offline handoff after execution. Self-review is not external certification.

## Frozen real protocol

Create one new private version only after all offline gates and review pass. Do not overwrite historical agents or alter territorial v4. Memory ON, Internet OFF, ten tools, exact code and context hashes. STOP immediately on any material Critical/High, preserving the failure; do not patch and silently retry the same candidate.

1. Principal: «Desde Zegama quiero ir al Ambulatorio de Beasain el 29/09/2026, con cita a las 09:30 y consulta de 20 minutos, y volver a las paradas. ¿Cuánto tiempo completo ocupa y qué límites tiene?»
2. Variation in same conversation: «Mantén origen, destino, fecha y duración, pero cambia la cita a las 09:45. Recalcula el tiempo completo y explica la diferencia respecto a las 09:30.»
3. Sources: «¿De dónde salen los horarios, el paseo, el centro y los supuestos? Distingue las fechas y qué está observado y qué está modelado.»
4. Limit: «¿Cuál es la mejor hora mañana desde mi casa y hay cita disponible?»
5. Alternative, explicit supported inputs: «Ahora calcula desde las paradas de Segura al Ambulatorio de Beasain el 29/09/2026, cita a las 10:00, consulta de 30 minutos y regreso a las paradas. ¿Cuánto ocupa y cómo se reparte?»

Compare each numerical response with its actual tool output, including every table row and any stated differences. Historical principal controls are comparison evidence only. Require correct scope, conditional interpretation, sources and limits. Tool success alone is not answer success. Unsupported request must not acquire an invented address, available appointment, live schedule or optimal recommendation. Only after all five PASS may materials, presentation and preview be finalized for vNext.

Publication and main merge require a human action. On real failure prepare the intact territorial fallback with matching materials and conversation. Never expose R25 as GO based solely on offline checks.
