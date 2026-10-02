# R18 — general reasoning and typed evidence boundary

Base exact R17: `8f3ee977cea3295f8f5a92b776e44a598d897016`.
Branch `hotfix/r18-general-agent-final`, separate worktree; dirty R17 audit
files preserved, not reset or silently committed into the old branch.
New package generated solely from the pinned R17 Git blob.
Only main.py/tools.py change; all other 23 members, 15 context assets,
embedded W1 ZIP and frozen territorial v4 remain identical.

## Findings and narrow scope

M01: discovery advertised percentage of elderly residents living within a
radius. Neither municipal representative-point geometry nor aggregate
population supplies residential distribution. This is an unsupported subject
change, not a formula defect. Original eight-message R17 audit remains FAIL;
its earlier four-message PASS does not override that later finding.

Baseline `_claim_unit` reproduces `within_threshold_count` and
`outside_threshold_count` as `registros`. Their semantics are municipalities.
They are produced by the compact territorial response, **not currently emitted
by the detailed public agent execution path**; this is a latent metadata defect,
not an observed wrong number in the R17 real conversation. Public semantic
projection now explicitly types either as municipalities if emitted. Actual
registered_service_count remains registros. No global text substitution.

Observed baseline `difference_relative_pct` is wrongly labelled conteo.
Projection changes that unit to %, keeping the exact value/evidence path/raw.
`total_result_rows` was emitted as a claim: move it and similar counters to
operational_metadata. joined_rows records processing coverage, not population.
Raw envelopes, claim validation, provenance and historical schemas are intact.

## Nine-tool audit: what / subject / units / coverage / periods / inference

| Operation | Subject and measures | Units | Coverage/period and derivation | Allowed / forbidden |
|---|---|---|---|---|
| obtener_resumen_territorial | Named municipality; population, registered resources, representative-point distances | personas, %, registros, registros/10000personas, m | One municipality from 88; Eustat2025-01-01, services2026-09-20, geography2025-05-07 separately; count/total and birth-year method explicit | Compatible exact arithmetic; no individual residence, capacity, assigned centre or homogeneous snapshot |
| comparar_municipios | Explicit municipality list and chosen age, optionally geometry | %, personas, m |2–20 distinct municipalities; demographic selector plus distinct service/geography dates | Field-by-field compatible comparison; not travel comparison, causal claim or resident radius coverage |
| analizar_envejecimiento | Municipal age count or proportion, not individual need | personas or % |88 demographic municipalities,65+/75+,2025-01-01; ordering observed indicator | Ranking and exact compatible differences; not arbitrary age, prediction or need inference |
| analizar_acceso_servicios | Municipal representative point to nearest category record; boolean class | m; boolean municipal class; municipal counts when present |88 or requested set; EPSG25830 euclidean geometry; service2026-09-20/geography2025-05-07 | Geometric comparison/threshold classification; no residents/households/%covered, network time or effective accessibility |
| analizar_coincidencia | Municipal age proportion AND representative-point distance | %, m, municipios |88 joined municipalities; requested quantile/age/category; dates remain different | Describe cuts and qualifying municipalities; not association→cause or population→spatial distribution |
| simular_escenario | Hypothetical municipal geometry before/after | m, %, municipios; WGS84 input coordinates |Same geometry/sources; add/remove record or threshold change; exact conditional recomputation | Compare corresponding geometry; not observed impact, beneficiary count, usage prediction or siting advice |
| consultar_fuente | Source itself: publisher, URL, method, date, limitation | Metadata; source-declared units |Observed exact source IDs or full catalog; keep official/open/model/user roles distinct | Trace lineage; metadata itself isn't observed capacity/availability or proof of truth |
| consultar_capacidades | Operation catalog; inputs, enums, coverage, enabled/disabled limits | Operational counts/bounds, not analytical claims |Catalog verified against current handlers and files; public signatures preserved | Discover/check scope; not invent capabilities or treat catalog constraints as measured outcomes |
| plan_visit | Scheduled/modelled stop-to-stop health visit, full interval and components | s, verified h/min/s, m; input/default minutes and coordinates |3 catalog origins, validated date2026-09-29, modelled official destination; GTFS2026-09-28/12-27, OSMacquired29sep, healthsource dates separately | One visit per call; same-origin compatible conditional comparison; cross-origin side-by-side only. No home/realtime/bestappointment/capacity/verifiedentrance |

## Numeric surface inventory and firewall

`r18_semantics.py` is a closed metric registry, not a user-prompt router.
Population, percentages, registered counts/rates, distances, municipal counts,
relative distance percent and journey seconds/metres each receive a subject,
unit and analytical role. Entity, source IDs/roles, period, numerator,
denominator, pointer and assumptions are preserved. Future unclassified metric
fails projection closed. Errors have zero claims and no partial mobility view.
Original raw evidence remains internally verifiable and unchanged.

All other model-facing numbers are classified by container:

- `normalized_input`, `effective_request`, requested/default attribution:
  **inputs**, not observations. km thresholds, unitless quantile, top_n,
  minute durations/margins, WGS84 coordinates retain input semantics.
- `operational_metadata` and `outcomes.index`:
  counters/indices/execution/selection, **not analytical claims**. Processing
  coverage can be explained as municipalities processed, never residents served.
- `capabilities.coverage.entities`, input bounds and `mobility_catalog.ranges`:
  **catalog constraints**, no measured population/capacity.
- `claims[].value/numerator/denominator`: **analytical**, respective declared
  units and real source/period/data lineage; a municipal population count does
  not describe location of those residents.
- `municipal_classifications`: **analytical boolean**, exact raw row value,
  identified municipality and representative-point subject.
- `mobility.scenarios[].index`: **operational**. itinerary/component/time_summary
  numeric fields are **scheduled/modelled seconds**; scope_start/end_s are clock
  positions, not durations. total_hms is copied verified formatting. Walking
  total_metres/seconds are **modelled metres/seconds**. centre_anchor coordinates
  are **WGS84 location**, not entrance/accessibility evidence. Effective request
  numbers are inputs; source dates are reference metadata.

This constrains evidence given to the LLM, **not its final free text**. Prompt
instructions are not a mathematical guarantee of compliance. Real conversation
and context generalization must be measured separately; no fake offline LLM PASS.

## Reasoning and evaluation

SYSTEM_PROMPT uses ten principles-based sections, no gold municipality/number,
no test phrase or keyword routing. Nine public signatures unchanged. Capability
discovery uses omitted/null or real search text; blank remains invalid, never
coerced into a default. Reexecute meaningful follow-up changes. Compatible
derivation only; useful abstention when subject/input/source is missing.
At most one logical recovery per cause, never identical invalid retries.

Properties P1–P12 and deterministic metamorphic tool tests are permanent.
156 generated prompts, seed1802026, corpus SHA in outputs/r18/generated-corpus.json;
13 stratified real cases chosen by seed1802027 **before responses**, plus two
context mutations. Separate maximum3 clean-public messages; total budget18.
Corpus/protocol/generator are not runtime assets or hidden holdout. Structured
offline expected tool args are test declarations, never parsed from prose.
Unsupported/causal/subject/capacity cases require honest limits, not a numeric
answer. Development corpus does not prove all LLM answers safe.

Initial verifier incorrectly compared removed invalid partial model projection
as if it were raw/provider drift. Preserved outputs/r18/attempts/initial-verifier.json:
489/489 raw parity and7/7oracle; findings were totals/provenance **projection**
on nonvalid cases. Corrected verifier compares raw unconditionally and valid
projection facts only, separately requiring invalid partial projection absent.
No engine or runtime patch for this verifier defect.

## Regenerate and verify exact candidate

Canonical local CPython3.12.14 (CI3.12.10), requirements.txt, Node.

```text
python -m scripts.vnext_agent.build_r18
python -m scripts.vnext_agent.eval_r18
python -m pytest -q tests/vnext_agent/test_r18_semantic_invariants.py -o addopts= -p no:cacheprovider
python -m scripts.vnext_agent.verify_r18 --output work/r18-audit.json
python scripts/ops/verify_runtime_identity.py
python -m pytest -q -o addopts= -p no:cacheprovider --junitxml=work/r18-pytest.xml
node --test tests/e2e/contract_flow.test.mjs
python scripts/benchmark/verify_jury_results.py --output work/r18-jury.json
python scripts/release/verify_final_artifacts.py
python -m scripts.vnext_agent.build_r18
git diff --check
```

One local complete suite; exact-SHA Ubuntu/Windows CI before any private version.
No provider20k repeat, holdout, merge, main/default-branch change or publication.
Real traces/evaluation retained without retries or retrospective rubric changes.
Critical/High/Medium block readiness; Low-only style doesn't open another round.
Track, acknowledgement and publication remain HUMAN ONLY.

Prompt/tool-description review also used official [function-calling guidance](https://developers.openai.com/api/docs/guides/function-calling)
and [evaluation guidance](https://developers.openai.com/api/docs/guides/evaluation-best-practices):
clearly state purpose/output semantics and separate deterministic software
checks from variable model behavior. No API credentials or model migration.
