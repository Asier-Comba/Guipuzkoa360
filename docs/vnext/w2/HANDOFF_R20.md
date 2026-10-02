# R20 narrow public surface — Studio preparation blocked

Current closure: [R20_PORTAL_GATE](R20_PORTAL_GATE.md). Exact-SHA Ubuntu and
Windows CI are green, but Studio rejects12 tools against a hard10-tool limit.
No R20 version or real model message exists; no real acceptance is claimed.

Base is tested R19 runtime `e501b45745fd7cc283ca0fa559d9965ca6fda9ee`,
not evidence-only `767a5ab343e5094546a556935c3002db5cd3b0c6`.
R19 FAIL remains immutable in PR24 and its captured scenario trace. The new
mission authorizes a structural correction, not retrospective acceptance.
R19 evidence-head workflows37040937879/37040937944 have also completed green;
those are historical, not CI for R20.

## Exact scope

Build from the pinned R19 ZIP; append a public adapter after the complete
byte-identical tools engine, replace public bindings/prompt only. Other23 ZIP
members,15 declared context assets, W1 R6 package and v4 stay identical. No
producer, snapshot, source, formula, oracle, main branch or holdout changes.
Public tool count12, internal operation families unchanged. `build_agent(model)`
is synchronous; standard library plus existing Studio/LangChain only, Internet
off, memory on. No added runtime dependency, regex routing or global dedup.

| Public tool | Required human/observed decisions | Optional public decisions |
|---|---|---|
| obtener_resumen_territorial | municipio | none |
| comparar_municipios | 2–20 distinct resolvable municipios | age65/75, default65 |
| analizar_envejecimiento | none | age65/75; count/percentage; top_n1–100 |
| analizar_acceso_general | category; threshold(0,100]km | none; no municipality selector |
| analizar_acceso_municipios | category; threshold;1–88 distinct resolvable municipalities | none; no null/empty all-territory shortcut |
| analizar_coincidencia | category | age; threshold; level of exigency0.5–0.95 |
| simular_anadir_servicio | category; finite WGS84 coordinates; threshold | none; technical ID internallyNone |
| simular_retirar_servicio | category; registered service identity observed in access; threshold | none; no coordinates or new threshold |
| simular_cambiar_umbral | category; current threshold; new threshold | none; no ID/coordinates |
| consultar_fuente | source identity observed in catalog/output | none |
| consultar_capacidades | none | none; zero-argument catalogue |
| plan_visit | observed origin/destination;date;appointment time;duration minutes | none; producer margins remain internal assumptions |

Enums close category/age/measure; no extra action field in public simulations.
All new-tool fields are required. List shape is plain `list[str]` for the known
Studio interface; nonempty/bounds/resolution/semantic uniqueness are enforced
atomically before engine execution and advertised in the capabilities contract.
Do not falsely claim `minItems` appeared in a served SDK schema until observed.
Required/nonnullable selection plus a separate no-selector general tool removes
the empty-list *decision ambiguity*: invalid lists never become all88.

Every executed public result still carries the validated engine input,
effective parameters, raw digest and typed analytical claims. Access adds a
bounded `observed_services` projection from exactly the same verified raw rows;
IDs match nearest_service_id pointers. This enables genuine identity-based
removal without inventing a code or adding a dataset. It is not clinical
assignment. Raw results/formulae remain unchanged.

Errors expose error_class, invalid_fields, retry_same_arguments, allowed_values,
required_next_information and corrected_call_possible. Missing/extra signature
fields are rejected at binding, not passed to the engine. Deterministic errors
have zero claims; no partial age/classification/mobility evidence is promoted.
No identical argument/contract retry. One controlled identical retry is allowed
only for explicitly observed transport failure with valid arguments/no result.
No session-global state is invented; retry limit is instruction/envelope, not
falsely claimed as stateful enforcement. No unobserved503 cause is asserted.

Public capabilities match all callable names, field order/requiredness/defaults;
the raw internal capabilities asset remains pinned and is clearly engine-only.
No new input periods: demographic2025-01-01, services2026-09-20,
geography2025-05-07, visit2026-09-29; preserve heterogeneous sources.

## Reproduction and frozen development protocol

Use CPython3.12 (canonical local3.12.14 for historical builders), dependencies
in requirements.txt. `python -m scripts.vnext_agent.build_r20` then
`python -m scripts.vnext_agent.eval_r20` freezes264 development cases,24families,
seed2002026, plus real protocol:7 targeted fresh sessions,22 stratified fresh
cases and2 follow-ups (=24 general messages). Files are outside runtime ZIP.
No offline paraphrase test claims natural-language routing or holdout evidence.

`python -m scripts.vnext_agent.verify_r20` runs cold/network-denied old/new
processes, explicit effective mapping/provenance, all three actions, raw parity,
seven unchanged public oracles, eleven metamorphic properties,200 negative
cases and5000 malformed-boundary fuzz calls. Full pytest additionally retains
all R13–R19 historical suites. Node17, v4 identity, jury/artifact/diff gates,
two identical builds and exact-SHA Ubuntu/Windows CI are mandatory before Studio.

Retained verifier attempts: [R20_ATTEMPTS](R20_ATTEMPTS.md). No silent waiver.
Current author-local evidence: raw parity660/660, unchanged oracle7/7,
eleven metamorphic properties,200 negative cases and5000 malformed-boundary
fuzz calls PASS, findings0. Latest focused suite27/27 PASS (22.09s), including
synthetic transport/contract distinction. Node17/17, identity14/14, jury and
artifact7/7 gates PASS. Two builds match ZIP
`9a271888b414168d06d92dad1b9a9ee594ee0209f78f0abee8d85925cdb6e33e`
(240004 bytes), manifest
`0362aa249756275f6377cf9b3d3e4859f1f01ad856e0e5663e5cc12150030081`.
The full local attempt was757PASS/5encodingFAIL, followed by5/5 targeted
rechecks with inherited UTF-8. This is not claimed as a clean full-suite run.
Exact-SHA fresh complete CI on both operating systems completed PASS:
R20 validation37046444655 and Release fast CI37046444701,763 Python/17 Node.
These results do not override the observed portal preparation blocker.
Local results are separate from real-agent acceptance. Real evidence must
record actual prompt/tool/args/output/final/material-claim scorecard and observed
time-to-tool/output/final (missing timestamps NOT_OBSERVED). Any new reproducible
Critical/High/Medium stops R20 acceptance; one isolated authorized R21 only under
the mission's defect-specific conditions, never R22.

Only after a completed real sample with C0/H0/M0: freeze exact version and bytes,
create clean public sanitary conversation, finish Delivery and six-slide
presentation, inspect preview, preserve services track/team, save PRIVATE draft.
No merge or publication. Historical final_delivery documents are not current
R20 approval; their verdicts, failed versions and source limits are preserved.

Interface design follows the user's structural requirement and official
[OpenAI function-calling guidance](https://developers.openai.com/api/docs/guides/function-calling):
clear responsibilities, enums/object structure and avoiding model-filled technical
values. Studio serving behavior still requires direct observation.
