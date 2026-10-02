# R19 — public interface and grounded evidence

Agent-only candidate based on immutable R18 `574d3d2dca5f84433f39c425b7ecce1c4cd01944`.
This is internal engineering evidence, not Delivery or jury presentation copy.
No main merge, publication, Delivery selection, product, source, data, provider,
formula, oracle or historical package changes are authorized by this round.

## Reproduced baseline before any functional edit

`outputs/r19/baseline-reproduction.json` records nine calls against the pinned
R18 ZIP `57fe8ccab8ab3613c0729aa9a4b25702dbaead5d74bfb6216e8bbe117c421256`:
empty discovery, ranking, comparison and access reject; valid age65 ranking
receives age75/year1949 metadata; three identical empty-period access calls and
one dot-period call fail. The same access query without that field succeeds.
This reproduces the arguments and metadata, **not a new LLM replay**. The real
retry loop and incomplete answer remain in the six preserved R18 conversations,
private version `agentv_d6b999e5c0c046f28e8eeabba0381039`, and the
[original failure checkpoint](https://github.com/Asier-Comba/Guipuzkoa360/pull/23#issuecomment-5955160942).
R18 observed sample: Critical0/High0/Medium3/Low2, not general release acceptance.

## Complete nine-tool field audit

Closed enums are `Literal` annotations in the actual public signatures, not
merely suggestions in the prompt. Mandatory text values still undergo the
unchanged deterministic validator. Blank, whitespace and dot are not defaults.

| Tool | Required public fields | Optional public fields | Real user decision / text risk | Engine-only, removed from public interface | Recommendation applied |
|---|---|---|---|---|---|
| obtener_resumen_territorial | municipio:string | none | Municipality name/code, required; invalid text rejects | periodo | One fixed demographic reference; distinct service dates in output |
| comparar_municipios | municipios:list[string] | grupo_edad:enum65/75=65 | Entity set and age; no optional free text | categoria_servicio, umbral_km, periodo | Demographic comparison only |
| analizar_envejecimiento | none | grupo_edad:enum65/75=65, medida:enumpercentage/count=percentage, top_n:integer=10 | Age, ranking measure and size; no optional free text | periodo | Fixed demographic snapshot, output provenance retained |
| analizar_acceso_servicios | categoria_servicio:enum | umbral_km:number=1, municipios:list[string]/null=all | Category, threshold, municipal subset; nullable array has a real all-entities meaning | periodo | Compare geometric distances using multiple municipalities |
| analizar_coincidencia | categoria_servicio:enum | grupo_edad:enum65/75=65, umbral_km:number=1, cuantil:number=.75 | Real age/threshold/selection choices; no optional free text | periodo | Descriptive cross-dimension result, not spatial population coverage |
| simular_escenario | accion:enum, categoria_servicio:enum | umbral_km:number=1, latitud:number/null, longitud:number/null, service_id:string/null, nuevo_umbral_km:number/null | Action-dependent inputs. **One real optional free-text field**: record identity for removal or user-chosen hypothetical record name for addition; no placeholder. Observed existing identity required for removal | periodo | Preserve all three actions; omit irrelevant fields, reject invalid/unused ones |
| consultar_fuente | source_id:string | none | Exact identity from observed catalogue/provenance, not user prose; mandatory | optional/list-all mode | General list is now the observed sources_catalog in capabilities |
| consultar_capacidades | none | none | No choice needed for nine operations; impossible to send an empty search placeholder | pregunta_o_dimension | Complete zero-argument catalogue within public payload bound |
| plan_visit | origin_id:string, destination_id:string, date:string, appointment_time:string, duration_minutes:integer | none | Explicit visit inputs; IDs and validated date from catalogue. Single currently validated service date is a coverage constraint, not a historical demographic selector | request object, batch, defaults, snapshot, margins, deadline | Preserve the existing required five-field flat health interface |

`PUBLIC_OPTIONAL_FREE_TEXT_FIELDS=1`, all representing a real scenario identity
decision; `OPTIONAL_FREE_TEXT_WITHOUT_REAL_DECISION=0`. Removing service_id would
lose the supported removal action or require a second scenario tool. Neither is
needed. Conditional requirements remain enforced without coercing an empty ID.

Removed comparison service functionality is preserved by access with the same
municipality list. Combined demographic/service questions use those two results
or coincidence. General source lookup is preserved in the capabilities source
catalogue and the required-ID source tool. No supported analysis is deleted.

## Snapshot proof and dates

The frozen demography contains only `2025-01-01`; available_periods checks it.
Access's old `periodo` only recorded `period_requested`, and scenario's only
recorded a filter; neither selected historical service/geometry snapshots.
Service reference `2026-09-20` and geography `2025-05-07` remain separately
attributed in the output. Ranking, comparison and coincidence use the one fixed
demographic reference. A different requested year must be refused, not silently
replaced or injected through a hidden selector. Provider visit date is unchanged.

## Age derivation / claims / recovery

Age is determined by structured metric, numerator data_ref or validated result
age_group, never by a user-question parser. Age65 uses the prepared Eustat
65+ group/pivot, without inventing a birth-year threshold. Age75 retains the
source-validated <=1949 transformation at 2025-01-01. Mixed summaries expose
both separately in age_group_derivations; each age claim points to its own entry.
Single-age analytical results never include the other age's derivation.
Source cards may describe both prepared indicators, because that is their scope.

Every projected numerical claim retains its validated raw pointer, entity,
value, unit, period, sources and derivation; subject and forbidden_inferences
remain explicit. No raw value or formula is changed. Original raw claim and
envelope validation still run before the strengthened public projection.

Every nonvalid public result has zero claims, retry_same_call=false,
invalid_fields, observed allowed values/coverage where verifiable and a clear
next step. There is no partial numerical result or error-message prose parser
that guesses a new tool request. The field extraction reads validated exception
field tokens, not a conversation. An unverified workspace supplies no invented
catalogue. A repeated invalid call is discouraged, not falsely claimed impossible.

Safe duplicate suppression was evaluated: these decorated functions receive no
verified conversation/run context. No shared global error cache, invented session
ID or cross-user state was introduced. Prevention is minimal schemas + controlled
errors + general prompt. Real Studio traces must prove the absence of retry loops.

## Evaluation and reproducibility

`build_r19.py` reads the exact committed R18 ZIP and manifest and checks both
hashes. The only package members that may differ are main.py and tools.py.
The other 23 members, all 15 context assets, embedded provider ZIP and frozen
legacy v4 are byte-identical. A third changed member is a hard failure.

`r19_bindings.py`, `r19_interface.py` and `r19_prompt.txt` are build inputs,
not extra runtime members. The short principles prompt contains no gold
municipality, benchmark phrase, cutoff or expected number. Schema design was
cross-checked with the official [function-calling guide](https://developers.openai.com/api/docs/guides/function-calling).

New tests preserve all historical R13–R18 suites, reject removed public kwargs,
check age isolation, mixed summaries, catalogue signatures, controlled errors,
finite values, entity/category/default substitution and byte-identical builds.
Offline phrase variation proves only identical structured-request behavior;
it is explicitly **not evidence of LLM language understanding**.

216 generated development requests across 18 families use seed1902026.
The real sample uses seed1902027 and is frozen before any Studio response in
`outputs/r19/real-protocol.json`; three fresh-session gates precede the sample.
Maximum23 user messages, including two defined follow-ups. Runtime does not
contain the corpus. Unsupported questions require honest limitations, not figures.
Every real material numerical/factual claim must be scored SUPPORTED_BY_TOOL or
EXACT_DERIVATION; unsupported material numbers are High. Any real Medium/High/
Critical stops execution. A Low-only cosmetic issue does not start another round.

Initial local attempts are not hidden: the new test harness first tried to send
NaN through a strict JSON transport (verifier defect), and its age65-count
expectation used an unverified value (test defect; replaced by the prepared CSV's
48832). The initial R19 projection also failed on a legitimate null numerator
data_ref; this new boundary defect was fixed before freezing any candidate or
entering Studio. No producer change was needed. Final tests must run on the
corrected exact bytes; failed attempts are never converted to PASS evidence.
The first parity attempt began before the null-data_ref correction and reported
549/549 raw parity and7/7oracle but15 projection findings. Its report read the
manifest after a concurrent rebuild, so that initial manifest reference is not
an identity proof. Preserved as `outputs/r19/attempts/initial-parity.json`; the
verifier now captures and validates ZIP+manifest together before executing.

```text
python -m scripts.vnext_agent.probe_r19
python -m scripts.vnext_agent.build_r19
python -m scripts.vnext_agent.eval_r19
python -m pytest tests/vnext_agent/test_r19_interface.py -q -o addopts= -p no:cacheprovider
python -m scripts.vnext_agent.verify_r19
python -m scripts.vnext_agent.build_r19
python -m pytest -q -o addopts= -p no:cacheprovider --junitxml=work/r19-pytest.xml
node --test tests/e2e/contract_flow.test.mjs
python scripts/ops/verify_runtime_identity.py
python scripts/benchmark/verify_jury_results.py --output work/r19-jury.json
python scripts/release/verify_final_artifacts.py
git diff --check
```

Canonical CPython3.12; complete local suite once after focal corrections. Exact
commit Ubuntu+Windows CI must be green before creating a **new private** Studio
version. R18 is never edited. Validate served schemas/bytes, then gates A/B/C,
then the frozen general sample and claim scorecard. CI/offline tests alone do
not claim PORTAL_REAL_AGENT=PASS or AGENT_ENGINEERING_COMPLETE=YES.

Local full suite: **736/736** in332.12s on CPython3.12.4, including27 new R19
tests and all historical regressions. Node **17/17**. Legacy identity14/14,
jury gate and artifact gate PASS. Canonical builds used the bundled
CPython3.12.14; both R19 ZIP and manifest were identical to the3.12.4 build.
Historical R15 regeneration under3.12.4 temporarily changed only AST f-string
quote serialization; canonical3.12.14 regeneration restored its exact committed
bytes. No historical generated-file diff remains. This is recorded separately
from R19 raw-engine parity and never passed off as an R19 functional change.

Frozen ZIP `f65032611cc5d4e71609432cdc54f0d080aedc9289387e54c3804e24db192c9f`,
236543bytes. Manifest `233ef41a6650409fd209405c8d57a15854bec64c01c2dcd3bec137b41ebdf786`.
Corpus `e4a37bb1a28154fd118d471838847f2fb09258116dcf0506df14ced0c1559c1e`;
real protocol `a58c4d755a0abf99f79e072247c71dbaff6fcac2d6ca28e7e6416d14089c922c`.
CI and Studio success remain unclaimed until measured on this exact candidate.
Final offline audit: **549/549 raw parity**, including333 historical engine
requests and216 generated requests; **7/7oracle**, zero findings, offline
Critical0/High0/Medium0. The original28 R18 semantic tests are preserved in
the736-test full suite. This is structural acceptance, not LLM acceptance.

DELIVERY_WORK=NOT_STARTED
PRESENTATION_WORK=NOT_STARTED
