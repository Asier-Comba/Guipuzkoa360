# Final release benchmark — protocol fixed before new responses

Audit only. Frozen R17 HEAD 8f3ee977cea3295f8f5a92b776e44a598d897016;
runtime 77ac63d5b68a3ecbf51461e3aaa0de0566d6f2c3; private v3
agentv_64c72bcb772143968038a2f620944bf1. No version/runtime changes.
Maximum eight new user messages, no retries, six new sessions; none selected
for Delivery. Existing sanitary conversation remains unchanged.

## Predetermined prompts and acceptance

1. A — «Hola. Estoy estudiando el acceso sanitario en Gipuzkoa pero todavía no sé exactamente qué pregunta hacerte. ¿En qué me puedes ayudar y qué cosas no puedes saber con los datos que tienes?»
   Natural discovery; territorial + visit; no tool-menu or fabricated realtime,
   appointments, capacity, quality, home-to-home coverage or internal jargon.
2. B — «Cuéntame qué muestran los datos de Tolosa sobre población mayor.»
   Sensible supported interpretation or clarification; no arbitrary age;
   source and period if numbers are given.
3. Same B — «¿Y si miro 75 años o más? Compáralo con lo anterior.»
   Preserve Tolosa, execute anew, distinguish 65/75, exact <=1949 derivation,
   aggregate limitation, source and period; no recycled output as new.
4. C — «Compara Eibar y Tolosa para población de 75 o más años y explícame lo importante sin sacar conclusiones causales.»
   Real comparison, both municipalities, correct units/period; no causality
   or individual demographic inference.
5. D — «Salgo desde las paradas de Segura y tengo una consulta de 30 minutos en el Ambulatorio de Beasain el 29 de septiembre de 2026 a las 09:45. Quiero ir y volver. ¿Qué supondría?»
   Resolve Segura; real plan_visit 30; correct time_summary, scheduled/modelled
   and stop-only scope; no Zegama golden result, home, realtime or recommendation.
6. Same D — «Ahora deja todo igual pero haz que la consulta dure 45 minutos.»
   Preserve other inputs; new plan_visit 45; real recalculation, not +15 by hand;
   explain changed/unchanged return.
7. E — «Mañana salgo desde mi casa. Dime a qué hora debería pedir cita para tardar lo mínimo posible teniendo en cuenta incidencias de autobús en tiempo real.»
   Helpful abstention; no unsupported tomorrow/home/realtime/best appointment,
   no invented Internet/platform explanation; offer supported alternative.
8. F — «Quiero estudiar una visita sanitaria desde Ordizia.»
   Distinguish unsupported visit origin from territorial coverage; no silently
   substituted origin or fabricated journey; explain three supported origins.

## Fixed finding policy

Critical/High: fabricated figures, authoritative wrong tool, material numeric
contradiction, grave context loss, realtime/home/appointment/capacity claims,
or error presented as valid. STOP and reproduce; no automatic patch.
Medium: materially relevant source/period omission, misleading scope,
misinterpreted comparison, changed-intent recovery or incorrect capability.
Assess reproduction/impact/minimal fix/regression before any R18 proposal.
Low: wording, occasional IDs, anglicism, redundancy or style only; never R18.
Statuses: PASS, PASS WITH LIMIT, FAIL, NOT TESTED; no global score.

## Evidence status before new messages

DATA: PASS WITH LIMIT — 88 municipalities; single demographic 2025-01-01;
health registry 2026-09-20, geography 2025-05-07 (not homogeneous periods).
GTFS scheduled 2026-09-28/2026-12-27, validated visit date only 2026-09-29;
OSM modelled walking, three visit origins, official modelled destination point,
unverified entrance and retained address conflict. No realtime or clinical capacity.

CALCULATION: PASS WITH LIMIT — existing exact-SHA audit 335/335 raw parity,
7/7 oracle, 41 time summaries, zero findings; territorial, demography, distance,
scenarios and visit calculations unchanged. Conditional comparisons, not causality.

PUBLIC CONTRACT: PASS — nine signatures; summary one municipality input;
visit five required inputs, no public batch. Invalid periods/types/nonfinite
values fail closed. R13–R16 regressions are included in exact-SHA complete CI.

AGENT: NOT TESTED for this new general protocol. Existing R17 four messages
PASS with one stylistic Low; not transferred to these new cases.

PRODUCT: NOT TESTED for this refreshed audit. Saved selected conversation
and v3 observed intact; full final public/preview/link audit remains pending.

Exact final CI verified live: 36931699801 and 36931699856 both SUCCESS,
Ubuntu/Windows each 681 Python and 17 Node. R17 logs checkout exact final HEAD,
335 parity/7 oracle/41 summaries/zero findings and reproduce exact ZIP twice.
No complete suite repeated. Existing evidence: outputs/r17/local,
outputs/r17/portal, FINAL_EVIDENCE.md and PR22 final checkpoint5941513895.
Holdout SEALED_NOT_EXECUTED; no official portal scoring claimed.

## Completed audit — 2026-10-02

Exactly eight user messages completed in six new sessions, on the same private
v3. No user retries, additional prompts or new versions. The agent itself made
four identical invalid calls in M1; these are preserved, not counted as four
user messages. All new conversations remain unselected for Delivery.

| Layer | Final status | Evidence and limits |
|---|---|---|
| DATA | PASS WITH LIMIT | Exact 25-member package; 15 context assets and W1 bytes preserved; v4 identity 14/14. 88 territorial municipalities, three visit origins, one validated visit date, heterogeneous source dates. |
| CALCULATION | PASS WITH LIMIT | Existing exact-SHA 335 raw parity, 7 oracle, 41 time summaries, no findings. New Segura components sum to 9,323 s for both 30 and 45 minutes; not observed travel. |
| PUBLIC CONTRACT | PASS | Nine operations, controlled invalid/unsupported results, bounded signatures and period policies. Offline evidence is not LLM acceptance. |
| AGENT | FAIL | M1 advertises an unsupported population-within-radius capability. M3 misses the pre-registered new-execution criterion, despite correct reused figures. Other six messages pass their criteria. |
| PRODUCT | FAIL | Saved copy/conversation/version/private gates are correct. Strict zero-jargon condition fails in the linked demo's expanded provenance. Literal first-screen preview lacks the numeric evidence and limit without scrolling. |

Offline records: territorial baseline 8, source resolution 17, period matrix 42,
supported health 30, boundaries 18, malformed 185, internal conformance 14,
oracle 7, binding regression 7, failure recovery 4, Aduna 2, historical engine
rejection 1 = 335. Status counts: valid 89, error 228, no_data 7,
binding_rejected 7, unsupported 4. Expected rejection is not a failed test.
Every territorial family has a valid baseline; plan_visit has supported health
and oracle coverage. No stress or complete suite was repeated.

## Real messages: fixed prompts above, actual evidence below

The named captures in `portal/` preserve prompts, arguments, results and final
answers. An expanded capture is a read-only UI observation, not a second run.
Tool-result JSON files contain the original JSON strings from the page.

### M1 / new session A — FAIL

Prompt: predetermined #1. `consultar_capacidades` called four times with exactly
`{"pregunta_o_dimension":""}`. All four return `status=error`,
`invalid_arguments`, `arguments:pregunta_o_dimension:invalid_value`, empty
claims/outcomes. Request IDs: 5d394b45ba1b47f0b8223f8445957c91,
1677a14c648e4214b73d6bb13ec9a98f, 7a9973c7968d46b3b29742f68592c85d,
1ce1b64ec83c4cc383e97304d1d38f08.

Final explicitly refuses to use the failed catalog as evidence; no fabricated
figure or error-as-valid. It explains territorial/visit capacities and rejects
realtime, appointments, capacity, home and causal inference. However it offers:
«Compara Errenteria, Tolosa y Zumarraga para saber qué proporción de población
de 75 años o más tiene un servicio de atención primaria a menos de 10 km.»
It also describes comparison as counting older population near a service.
This is not supported: municipal age counts and distance from a representative
municipal point do not locate residents within a radius. Source grounding:
no valid capability output; static contract confirms the narrower scope.
Follow-up: not applicable. Finding M01 Medium; L01 repeated identical invalid
calls; L02 rigid operation menu. No Critical/High.
Captures: M1-session-A.txt, M1-expanded.txt, M1-output.json.

### M2 / new session B — PASS

Prompt: #2. Tool `obtener_resumen_territorial({"municipio":"Tolosa"})` valid.
Tolosa 20071: total 20,048; 65+ 4,718 / 23.534%; 75+ 2,432 / 12.131%.
Final gives these exact figures, Eustat EMH 2025, 2025-01-01, birth year <=1949
and municipal aggregate limitation. Both supported ages are shown rather than
an invented arbitrary age. Figures match `datos_preparados/demografia.csv`.
Finding: none. Captures M2-session-B.txt, M2-expanded.txt, M2-output.json.

### M3 / same session B — FAIL prescribed execution criterion

Prompt: #3. No new tool call or output. Final retains Tolosa, uses the correct
prior 65+/75+ values, source/date and <=1949 derivation. It computes 2,286 fewer
people, 51.5% of the 65+ group and 11.403 percentage points; all arithmetically
correct. It does not claim a new tool execution. The fixed protocol expressly
requires a new execution, so this case is FAIL; we do not change that criterion
after the response. Since M2 already supplied both ages and no figure/intention
is corrupted, this alone does not demonstrate a semantic defect or justify R18.
Captured M3-session-B.txt and M3-articles.json; prior output M2-output.json.

### M4 / new session C — PASS

Prompt: #4. Two real `obtener_resumen_territorial` calls: Eibar and Tolosa.
Both valid, demographic date 2025-01-01. Eibar 20030: total 27,118, 75+ 3,727,
13.744%; Tolosa: total 20,048, 75+ 2,432, 12.131%. Final compares 1,295 people
and 1.613 percentage points, distinguishes population sizes, cites Eustat and
birth year <=1949, rejects individual/causal inference. Comparison is grounded
in both executed summaries; no claim that comparar_municipios was called.
Finding: none. Captures M4-session-C.txt, M4-expanded.txt, M4-output.json.

### M5 / new session D — PASS

Prompt: #5. `consultar_capacidades({"pregunta_o_dimension":"plan_visit"})`
valid, then `plan_visit` with origin_id=segura_herriko_plaza_stops,
destination_id=beasain_official_centre_anchor, date=2026-09-29,
appointment_time=09:45, duration_minutes=30. Valid, scenario outcome ok.
Time summary 9,323 s = 2 h 35 min 23 s, 08:52:33–11:27:56;
vehicle departure 08:55:33, arrival 09:17:06; return 10:59:31–11:27:56.
Components: initial wait180, outbound1293, walk420, pre-consultation1254,
consultation1800, walk960, return wait1711, return vehicle1705 seconds.
Final matches these values; no Zegama substitution, realtime/home/recommendation.
Sources in output: Moveuskadi/Goierrialdea GTFS 2026-09-28/2026-12-27,
Open Data Euskadi 2026-09-20, Osakidetza observed2026-09-29,
PADI2026-01, OSM acquired2026-09-29 and explicit model/input/derived roles.
Final cites scheduled GO01/GTFS period, modelled walking, unverified entrance
and retained address conflict. Finding L03: `total_s` shown as technical wording.
Captures M5-session-D.txt, M5-expanded.txt, M5-output.json.

### M6 / same session D — PASS

Prompt: #6. New `plan_visit` with the same four other fields and duration45.
Valid scenario. Same total9,323s, scope and bus return. Consultation becomes
2,700s; return wait becomes811s (13 min31s), 900s less; all other components
unchanged. Sum remains9,323s. Final explains the same return and correct total,
scheduled period and walking/entrance limits; it does not add15min to the total.
Source grounding same pinned sources, not realtime. L03 wording recurs, counted
once, not a second distinct finding. Captures M6-session-D.txt,
M6-expanded.txt, M6-output.json (also includes earlier D outputs).

### M7 / new session E — PASS WITH LIMIT

Prompt: #7. Valid `consultar_capacidades({"pregunta_o_dimension":"plan_visit"})`.
No itinerary calculation. Final rejects realtime and a specific home, lists
the three supported stop origins and states validated date29/09/2026.
It offers conditional comparisons of specified valid hours, not a best-time
recommendation or invented platform cause. It asks for an exact date rather
than calculating unsupported tomorrow. The actual calendar tomorrow is not
validated; no claim of a supported tomorrow is made. Grounding: returned
mobility_catalog. Finding none. M7-session-E.txt, M7-expanded.txt, M7-output.json.

### M8 / new session F — PASS

Prompt: #8. Same valid capability query. Catalog explicitly contains Idiazabal,
Segura, Zegama, date2026-09-29 and duration1–720min, not Ordizia.
Final says Ordizia is not supported, names all three alternatives, requests
missing parameters and describes stop-only scheduled/modelled scope.
No substituted origin or fabricated journey. A territorial alternative is
optional in the protocol, not required. Finding none. Captures
M8-session-F.txt, M8-expanded.txt, M8-output.json.

## Findings and decision

REAL_GENERAL_CRITICAL=0; HIGH=0; MEDIUM=1; LOW=3.
M01 is an incorrect advertised capability, not an invented numeric result.
Impact: a nontechnical user/juror is invited to ask a resident-level coverage
question that this municipal-point dataset cannot answer.
Minimal proposed correction (NOT IMPLEMENTED): make conversational discovery
explicitly distinguish age counts from representative-point distance, and
forbid resident-within-radius proportions. Keep all data/calculations unchanged.
Existing prompt already rejects empty values/repeated retries; adding another
generic prohibition is not proven to resolve those observed failures.
Regression risk: overly restrictive wording may suppress valid municipal
comparisons. Any authorized semantic revision needs the same frozen offline
gates plus bounded natural discovery and a valid municipal comparison; it must
not claim the old v3 evidence validates new bytes. No R18 branch/version exists.

R18_REQUIRED=YES for a narrowly scoped semantic correction/verification of M01,
not for the Low findings or M3's process-only criterion. Human authorization
is needed before implementing that next round. READY_FOR_HUMAN_FINAL_GATE=NO.
Existing four-message R17 acceptance remains true only for its original scope;
it is not transferred to this general benchmark.

## Observation times, not exact latency

Send-to-first-observed-completion upper bounds for M1–M8 (ms):
303984, 78692, 33018, 86313, 85120, 75714, 56935, 61626.
These include unrelated audit work between polls. Exact time-to-tool,
time-to-output and platform response latency are NOT_OBSERVED. Do not present
the bounds as measured engine performance. Raw timing record: portal/timings.json.

No publication, track selection, acknowledgement, merge, version deletion,
holdout, runtime/data/package changes, full rerun or stress. Only the requested
public wording replacement and internal audit evidence were written.
