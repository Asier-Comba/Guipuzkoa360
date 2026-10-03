# R22 real acceptance — FAIL, frozen and stopped

Runtime: `202352adc10e90a4b98125387af8e0ff7a438073`.
Base R21 runtime: `b0096e9aeda533ed0a43f56bf98975becf4022d8`.
Private Studio version: `agentv_f43156f686694933951b3340d53996b4`.
Agent folder: `agentes/gipuzkoa_360_4`; R21 and v4 were not overwritten.

ZIP: `6f7912c17f06c81f637dea26ea8bb49287f56c7c41099c20cb11b4ef98373c47`.
Manifest: `29a4d17b0e39962210b7847e83595485ac14f4878dd97717345a66e8c66adc8a`.
Package: 241,884 bytes / 25 members. Only main.py and tools.py differ from R21.

## Exact-SHA offline and CI evidence

Complete Python 822/822, Node 17/17, raw parity 901/901, oracle 7/7,
14/14 semantic/metamorphic properties, 195 negatives, 5,000 malformed
cases, 10,399 attributed public claims examined, no offline findings.
Identity before/after, jury, artifacts, diff and byte-identical double build PASS.

R22 validation: https://github.com/Asier-Comba/Guipuzkoa360/actions/runs/37078936319
Fast CI: https://github.com/Asier-Comba/Guipuzkoa360/actions/runs/37078936316
Ubuntu and Windows passed on the runtime SHA above, before creating the version.
See `outputs/r22/ci-exact-sha.json`; do not transfer these results to different runtime bytes.

## Studio preparation and provenance

Main and tools were read back in full from the editor and matched the exact
local generated sources. `source-readback.json` records both SHA-256 values.
The version creation preparation validated the exact ten expected tools,
memory on, Internet off and the fifteen declared context paths.
The UI included one unused platform-created ejecucion.py scaffold; it is not
an extra registered tool or an import of the candidate. The Studio package
display was 0.5 MB / 18 files, distinct from the reproducible repository ZIP.
This is not a claim that a portal ZIP was downloaded and hashed.

A generic Connection Error banner and no-output standalone file executions
were observed before version preparation. The standalone file execution is
not the version definition check. The actual version preparation subsequently
passed. No team environment reset or runtime workaround was performed.
An optional evidence-download control did not produce a browser download
event within ten seconds; complete visible transcripts and outputs were
captured independently. This is not a model finding.

## Prefrozen protocol and real results

Protocol SHA-256: `6d3aebd834c06798da2143f27241bd381334400689cac58fff739ca2d089cfb2`.
Corpus SHA-256: `f5142de15f9311be15b35eb3015f971dba248377709155038392c45b195353c2`.
Planned: 16 targeted + 24 general user messages. Actual: 7 user messages,
4 fresh sessions for the first six turns plus a fresh access-general session.
The remaining 9 targeted and all 24 general messages were NOT SENT.
Holdout remains sealed. No public demonstration was created.

| Gate | Actual outcome |
| --- | --- |
| 01 Getaria mental health / 1 km | PASS: one valid call, 2,913.3 m, outside 1 km, municipal point, not route/time; no unasked dates |
| 02 Explicit Getaria sources | PASS: Department of Health / 2026-09-20; geoEuskadi / 2025-05-07; no technical IDs |
| 03 Tolosa hospital / 2 km | PASS: one valid call, 18,670.9 m, outside 2 km; municipal geometric distance |
| 04 Explicit Tolosa sources | PASS: same correct atomic role/source/date pairs; observed institutions |
| 05 Discovery | PASS; one LOW for extensive wording and a grammatical slip; no code change |
| 06 Five highest 65+ percentages | PASS after observed recovery, retained below; all five percentages, numerators, denominators and 65+ method supported |
| 07 General primary care / 2 km | FAIL: material unsupported classification rule; HIGH 1; STOP |

Gate 06 initially called obtener_resumen_territorial with municipio=Gipuzkoa.
The result was an unverified_result error with zero claims. The agent made
one unambiguous correction to analizar_envejecimiento(65, percentage, 5),
did not repeat the rejected call, did not use values from the error and
answered from the valid ranking output. This is an actual observed recovery,
not an offline fault injection. The initial selection error is not erased.

The source/date repair generalizes in the four observed attribution turns.
That limited PASS does NOT establish complete agent acceptance.

## First real HIGH — exact reproduction

Frozen prompt:

> Analiza para todos los municipios de Gipuzkoa la distancia geométrica a atención primaria con un límite de 2 km. ¿Qué significa y qué no mide?

Actual call: analizar_acceso_general with categoria_servicio=primary_care,
umbral_km=2. Output status valid. The answer says:

> se considera dentro solo si la distancia geométrica al registro de atención primaria más cercano es mayor que 0 y menor o igual que 2 km.

This is false. The frozen engine at portal_r22/tools.py:566 calculates:

`bool(distance is not None and distance <= threshold_km * 1000)`

Zero distance is included. The positive-only condition at line 989 validates
the threshold input, not the calculated distance. The answer transfers an
argument constraint to the analytical classification rule. It is a material
unsupported method claim, not a stylistic LOW.

Finding: R22-REAL-H01, HIGH. Unsupported material claims: 1.
No displayed municipality value was altered: all ten distances and their
false classifications are supported by the observed output. The error is
the general rule stated to the user, including its zero-distance edge case.

The public view contains ten detailed rows and explicitly records 78 omitted
entities / 88 total. The answer accurately warns that it cannot establish
the classification of all 88 from those ten returned classifications. No
global count was invented. The incomplete global answer is retained as
observed scope, not falsely attributed to source/date inversion.

Raw output, arguments, final text, snapshots and manual assessment are in
`outputs/r22/portal/gate-07.json` and `gate-07-raw.txt`.
First-observed latencies are upper bounds, not precise server timings;
folded outputs were captured when expanded. See individual observations.

## Closure

R22_REAL_ACCEPTANCE=FAIL
REAL_MESSAGES=7
REAL_CRITICAL=0
REAL_HIGH=1
REAL_MEDIUM=0
REAL_LOW=1
UNSUPPORTED_MATERIAL_CLAIMS=1
SOURCE_PERIOD_ATTRIBUTION=PASS_TESTED_SCOPE
AGENT_ENGINEERING_COMPLETE=NO
READY_FOR_HUMAN_FINAL_GATE=NO
MAIN_UNCHANGED=YES
V4_PRESERVED=YES
FINAL_CONFIRMATION=PENDING_HUMAN
PUBLICATION=PENDING_HUMAN

Per the explicit first-C/H/M stop rule, no further model questions, public
conversation, Delivery selection/copy changes or preview were performed.
No R23, automatic patch, data/formula change, merge or publication.
Next action requires human direction on this recorded HIGH, not publication.

The computer-use skill governed observed UI actions/readback and retention
of screenshots. The OpenAI guidance skill informed structural pairing in
code rather than relying only on prompt wording. Neither offline testing
nor a successful preparation is claimed as real conversational acceptance.
