# R19 real acceptance — FAIL / STOP, not release approval

Tested runtime commit: `e501b45745fd7cc283ca0fa559d9965ca6fda9ee`.
Private Studio version: `agentv_cafd8f750b5741959fb29c4045743da1`
(`GIPUZKOA 360 · v1`, model `openai:gpt-5.6-luna`, memory on, Internet off).
R18 and legacy v4 are untouched. Delivery and presentation were not started.

ZIP `f65032611cc5d4e71609432cdc54f0d080aedc9289387e54c3804e24db192c9f`
(236543 bytes); manifest
`233ef41a6650409fd209405c8d57a15854bec64c01c2dcd3bec137b41ebdf786`.
Only main.py and tools.py differ from the pinned R18 package. Full editor
clipboard readback matched both generated files before version creation.
Studio preparation recognized all nine simplified signatures and the fifteen
context assets. Studio adds an unused ejecucion.py template, not imported by
either tested file; the local 25-member ZIP is not represented as an export of
the portal folder.

Exact runtime CI: R19 [37028594182](https://github.com/Asier-Comba/Guipuzkoa360/actions/runs/37028594182),
Ubuntu and Windows PASS; fast [37028594313](https://github.com/Asier-Comba/Guipuzkoa360/actions/runs/37028594313),
Ubuntu and Windows PASS. Python736/736, Node17/17, raw parity549/549,
oracle7/7, identity/jury/artifacts/diff PASS. These are not LLM acceptance.

## Mandatory new-session gates

All prompts were fixed in outputs/r19/real-protocol.json before Studio.
Each gate used a separate empty conversation of the private version.
DOM, expanded raw output, full log, screenshot and timing observations are in
outputs/r19/portal/gate-{A,B,C}-*.

| Gate | Actual first tool and arguments | Outcome |
|---|---|---|
| A discovery | consultar_capacidades, {} | PASS; valid first call, understandable capabilities and limits |
| B ranking65 | analizar_envejecimiento, grupo_edad65/percentage/top_n5 | PASS; correct five results and isolated65 metadata, no75/1949 |
| C historical Getaria | analizar_acceso_servicios, mental_health/1km/[Getaria] | PASS; valid first call, no periodo, no retry,2913.3m and outside1km |

Claim scorecard:

- A: all capability statements,2–20 comparison bound, age groups, fixed source
  dates and geographic/causal/service/visit limits are SUPPORTED_BY_TOOL by the
  observed catalogue, semantic contracts and mobility catalogue.
- B: Zerain81/290/27.931%, Ibarra1127/4076/27.650%, Deba1473/5364/27.461%,
  Legazpi2276/8377/27.170%, Donostia48832/183388/26.628% are SUPPORTED_BY_TOOL
  by claims1–5 with their numerator/denominator. Eustat,2025-01-01, both-sex
  prepared65 group, ratio formula and three-decimal rounding are
  SUPPORTED_BY_TOOL. No inferred birth cutoff.
- C: Getaria2913.3m, false within_threshold, municipal reference subject,
  service2026-09-20 and geography2025-05-07 are SUPPORTED_BY_TOOL. Approximate
  2.9km is EXACT_DERIVATION (2913.3/1000 rounded to one decimal). No resident
  coverage, individual access or travel-time claim.

Observed completion upper bounds after submit: A51.381s, B49.774s,C44.293s.
Polling did not measure exact first-tool or intermediate-output latency; these
values are not falsely presented as exact provider timings. Header 'llamadas'
counts model calls, not the number of deterministic tools. Each gate has one
observed deterministic call and zero errors or identical invalid retries.

Mandatory-gate sample: Critical0/High0/Medium0/Low0, unsupported material
claims0. These three successes do not override the subsequent general failure.

## Frozen general sample and claim scorecard

Seven general cases passed before the eighth failed. Ten other families and
both defined follow-ups were NOT_RUN under the mandatory stop rule. Eleven
user messages total (three gates plus eight general prompts); no prompt was
adapted or resubmitted. Each case's expanded output, args and final text are
stored with its claim assessment in outputs/r19/portal/{family}-{index}.json.

| Case | Claims / exact derivations | Result |
|---|---|---|
| discovery07 | Available operations,2025 date, three origins, destination, limitations SUPPORTED_BY_TOOL;5/10km are clearly illustrative inputs, not results | PASS |
| lookup00 Deba | Population5364;65:1473/27.461%;75:687/12.808%;primary2,13.578/29.112 per10000;other three categories0: SUPPORTED_BY_TOOL claims1–17. Different source dates preserved, zeros not absence of care | PASS |
| ranking65-07 | All five percentages/counts/totals match gateB, SUPPORTED_BY_TOOL, isolated65 metadata | PASS |
| ranking75-06 | Donostia24884,Irun7604,Errenteria5372,Eibar3727,Arrasate2982 persons SUPPORTED_BY_TOOL;2025 Eustat | PASS |
| comparison03 | Mutiloa26/10.442%,Albiztur34/10.828% SUPPORTED_BY_TOOL;8 persons and0.386pp EXACT_DERIVATION;75 cutoff1949 supported | PASS |
| access02 | Azkoitia5027.6m,Beizama8034.9m, outside1km SUPPORTED_BY_TOOL;3007.3m difference and rounded km EXACT_DERIVATION;municipal subjects and source dates retained | PASS |
| coincidence07 | Ibarra27.650%/18114.7m,Hernialde25.387%/18562.2m,cuts23.973%/15813.7m,highlighted2 SUPPORTED_BY_TOOL;88 scope from observed selection;rounded18.1/18.6/15.8km EXACT_DERIVATION | PASS |
| scenario04 | No final answer; incorrect placeholder arguments and repeated invalid recovery; see below | FAIL / STOP |

All material claims in completed responses are grounded; zero unsupported
material claims observed. This does NOT certify the unexecuted remainder.
Multi-tool use was observed in lookup00, but general multi-tool, multi-turn,
ambiguity, unsupported handling and natural-language acceptance are not fully
accredited. Recovery is specifically FAIL.

## Exact failed case, observed trace, no adaptive fix

Frozen prompt:
“Estoy preparando un estudio. Simula cambiar el umbral de distancia municipal
a salud mental de 1 a 6 km. ¿Qué cambia y qué no demuestra?”

1. simular_escenario arguments:
   accion=change_threshold,categoria_servicio=mental_health,umbral_km=1,
   latitud=0,longitud=0,service_id="",nuevo_umbral_km=6.
   Portal reports `ERROR al ejecutar simular_escenario: No se pudo completar
   la operación (503)`. Its infrastructure/runtime cause is **unproven**;
   do not attribute503 to those arguments without further evidence.
2. consultar_capacidades({}) succeeds.
3. analizar_acceso_servicios uses municipios=[] at thresholds1 and6.
   Both controlled results reject municipios, contain zero claims and
   explicitly retry_same_call=false and invalid_fields=[municipios].
4. The exact1km request appears three times and the exact6km request twice:
   **three additional identical-invalid retries**. The last two calls lack
   displayed outputs. No final answer; saved conversation is Fallida.

R19-M01 Medium: action-specific scenario inputs are incorrectly filled with
irrelevant coordinate zeros and an empty service identity, despite a correct
documented omission/null convention. This classification is about observed
model arguments, not a claimed cause of503.

R19-M02 Medium: repeated controlled invalid access requests despite explicit
error recovery guidance; a supported question remains unanswered.

Initial live view restored the composer and displayed Failed to fetch with no
trace. It was provisionally classified infrastructure-only, preserved in
scenario-04-transport-attempt.json/dom/screenshot. One page reload and reading
the saved failed conversation recovered the actual trace above. This corrected
the preliminary diagnosis. **No second prompt was sent.** Do not describe the
initial connection view as proof that no tools executed.

Timing: other general cases' recorded completion-observation bounds are about
41–72s; coincidence109.283s. Scenario last observation jumped to2864.918s
across an extended tool-call interruption; this is an observation bound, not
continuous sampled latency or exact model time. No first-tool/output latency
claim is made where the page did not expose it live.

Final observed real findings: Critical0/High0/Medium2/Low0.
R19_AGENT_FINAL=FAIL
PORTAL_REAL_AGENT=FAIL
AGENT_ENGINEERING_COMPLETE=NO
IDENTICAL_INVALID_RETRY=FAIL
R20_REQUIRED=YES (future remediation needs a new explicit round; none started).
No new model calls, runtime edits, adaptive prompt changes or producer changes
after discovery of the real failure. All R19 bytes remain frozen, R18/v4 remain
untouched, no merge, no Delivery or presentation work, no publication.

Next exact action: coordinator authorizes a narrowly scoped scenario-interface
and repeated-invalid-recovery remediation, then freezes new bytes and repeats
the same frozen real protocol. Do not claim R19 acceptance or select it publicly.
