# GIPUZKOA 360 — W1 R11 final consumer gate

**R11_READY: YES. W1_CANDIDATE_GATE_READY: YES. W1_PARITY_PASS: FAIL.**

No runtime, snapshot, walking, productive schema, fixed data or R6 package changed. No merge, portal mutation or release publication occurred.

## Identity

- START_SHA: `6e284aff347cfcf5fbb3d7eb9cb89a227b83e0d5`
- TESTED_HEAD: `99ad907ff1515174ac9823bf4cef2b4c928495b9`
- PUBLISHED_HEAD: recorded in the final PR #15 / Issue #16 milestone after this documentation-only commit, avoiding a self-referential SHA.
- W2_HEAD_FIRST_SEEN: `8272988566f5bca2d65d3119732bf831d11382dc`
- W2_HEAD_FINAL_SEEN: `2321e03e3d994b488db9723560383d9defedcac7`
- W3_HEAD_FINAL_SEEN: `281f92a25170c5082c5772c0130d2275e57edaaf`
- RUNTIME_CHANGED: **NO**
- R6_PACKAGE_PRESERVED: **YES**, 129,365 bytes, SHA-256 `c66d44af702eb3410fcea05ae8711f537214f675e83a7fda38c39c3b39a1b910`; tested runtime pin `cb061a97e78d6b5c967104fef6b935132fdc450f`.

## Final support contract

- HANDSHAKE_VERSION: `r11.0-support`
- HANDSHAKE_SHA: `7cd86bae4699c0fcc50e85841585ee74534f19da6972e10be04f1971168a7643` (12,521 bytes)
- UNKNOWN_SEMANTICS_FIXED: **YES**. Compact `unknown` now means that evidence cannot verify the result; its concrete cause is bound to `status+error.code`. R10 remains historical.
- MODEL_VIEW_GATE: **READY**. `scripts/mobility/intake_candidate_r11.py` imports the extracted candidate's actual `tools.public_result(envelope)`; it does not invent a W1 projection or read the raw as a substitute for the model view.
- MODEL_VIEW_REQUIREMENTS: 38 requirements, SHA-256 `cee2a75e3bc5f1cbe86c1e4bd4e08989373fe25df7a814364fc011a6f0bdd905`.
- STRICT_GATE: PASS=0, NOT_RUN≠0, FAIL≠0 — tested.
- DIAGNOSTIC_GATE: PASS=0, NOT_RUN=0, FAIL≠0 — tested.
- Failure classes include package, manifest, W1 pin, import, raw parity, missing/wrong model view, semantic mismatch, distribution policy and NOT_RUN, each with severity, owner, evidence and safe next action.

The model-view gate requires status/request, route/trip and stop identities plus labels, scheduled times, walking distance/time/model, appointment and waits, return details/slack, total, health-centre identity, `modelled_access`, `entrance_verified=false`, scope, readable sources, assumptions, limitations, caller/default provenance and timepoint caveat. Mutations of trip, route label, stop ID/label, scheduled departure/arrival, centre ID/label, entrance, modelled access, source and timepoint wording fail even when totals remain correct.

## Candidate intake result

- CANDIDATE_PACKAGE: `scripts/vnext_agent/dist/gipuzkoa360-vnext-w2.zip`, exact remote bytes, 219,354 bytes, SHA-256 `b4feb978b625b34f9d7331ce8d376a34a29e84e4783868f83ce48a0c0d1011be`.
- CANDIDATE_MANIFEST: `scripts/vnext_agent/dist/gipuzkoa360-vnext-w2-manifest.json` from W2 HEAD above.
- CANDIDATE_W1_PIN: contract `0.3.1`, bound by exact frozen R6 package SHA-256 `c66d44af…`; manifest records observed source commit `cb061a9e…` separately from the prompt's non-object support pin.
- PACKAGE_INTEGRITY: **PASS**, 24 members.
- DISTRIBUTION_GATE: **PASS**; no unauthorized bundled HTML/PDF detected. Source references/hashes remain metadata, and OSM/GTFS attribution stays outside any false redistribution claim.
- RAW_PARITY: **FAIL**: 13/14 cases pass; `legacy_r4_explicit` returns `unverified_result` with no raw result after the full candidate sequence although producer R6 returns the explicit legacy result.
- MODEL_VIEW_PARITY: **FAIL**: 9/14 cases pass. Four health `ok` cases expose stop IDs as their labels for all outbound/return ends (16 missing semantic facts). The legacy model projection additionally raises `KeyError: transformation`.
- Invalid structural request is an allowed controlled projection: the consumer preserves the validated `health:invalid_duration` reason and safe next action without inventing raw evidence.
- W1_PARITY_PASS: **FAIL**. Exact evidence: `docs/vnext/w1/candidate_r11/candidate_intake_r11.json`, 19,181 bytes, SHA-256 `cc1755a72bfc3c80e6b3afcc23c4f0410e0d7ac4b7865cda57e39051bab2fb37`.
- STRICT execution: nonzero / `FINAL_STATUS=FAIL`.

W3 advanced during R11 to `281f92a…` and independently reported `NO_GO`: producer/product offline acceptance passed, but assembly/model interface remain blocked because there is no exact combined W2 health 0.3.1 package. This independently agrees with the W1 intake result; it is not substituted for W1 parity.

## Deterministic gold and verification

- DETERMINISTIC_GOLD: 6 public deterministic cases, no expected final answer, literal wording or holdout; SHA-256 `cb41c25b836deaecd0d3ab4de12160c7c5ec20cf80f10824f82912b68b9b16fb`.
- R11 targeted before candidate arrival: **9/9 PASS**; after adding exact-package/bootstrap and equivalent-error coverage: **10/10 PASS**.
- PYTHON: **517/517 PASS**, one openpyxl no-default-style warning, no failure.
- NODE: **17/17 PASS**.
- Runtime identity: **PASS**, frozen v4 identity `195b4980fa5998b096c308296a55e452380b0371`.
- Jury gate: **PASS**.
- Artifact gate: **PASS**.
- `git diff --check`: **PASS**.
- CI: Release fast CI run [36715583373](https://github.com/Asier-Comba/Guipuzkoa360/actions/runs/36715583373) on TESTED_HEAD; Ubuntu **PASS**, Windows **PASS**.
- V4_PRESERVATION: **PASS**.

## Findings and remaining actions

- CRITICAL_HIGH: W1 producer/support **none**. W2 candidate: **CRITICAL** producer/adapter parity failure for the explicit legacy case; **CRITICAL** model projection exception for that case; **HIGH** loss of four stop labels in four health cases.
- MEDIUM_LOW: no new R11 runtime finding. Historical W1 DERIVED explanatory-DAG limitation remains external; W3's R10 inline-unknown observation is resolved by this versioned R11 support handshake.
- NOT_RUN: LLM/routing/language evaluation; portal; human release review; private holdout.
- W2_ACTION_REQUIRED: fix label lookup so `route_label`/stop labels are human-readable and correct; reproduce and fix the sequence-dependent explicit R4 failure plus `public_result` source projection exception; publish a new immutable ZIP+manifest.
- W3_ACTION_REQUIRED: do not start model/portal acceptance on `b4feb978…`; after W1 strict PASS on a patched exact package, independently evaluate routing/language/portal. Use the gold only as public truth, never answer wording or holdout.
- NEXT_EXACT_ACTION: W2 publishes the minimal patched candidate; W1 reruns this exact strict intake and publishes PASS or remaining structured failures.

PORTAL_MUTATIONS: **0**
MERGED_OR_PUBLISHED_RELEASE: **NO**
