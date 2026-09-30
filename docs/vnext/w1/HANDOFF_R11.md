# GIPUZKOA 360 — W1 R11 final consumer gate

**R11_READY: YES. W1_CANDIDATE_GATE_READY: YES. W1_PARITY_PASS: NOT_RUN.**

No runtime, snapshot, walking, productive schema, fixed data or R6 package changed. No merge, portal mutation or release publication occurred.

## Identity

- START_SHA: `6e284aff347cfcf5fbb3d7eb9cb89a227b83e0d5`
- TESTED_HEAD: `99ad907ff1515174ac9823bf4cef2b4c928495b9`
- PUBLISHED_HEAD: recorded in the final PR #15 / Issue #16 milestone after this documentation-only commit, avoiding a self-referential SHA.
- W2_HEAD_FIRST_SEEN: `8272988566f5bca2d65d3119732bf831d11382dc`
- W2_HEAD_FINAL_SEEN: `8272988566f5bca2d65d3119732bf831d11382dc`
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

- CANDIDATE_PACKAGE: `scripts/vnext_agent/dist/gipuzkoa360-vnext-w2.zip`, exact remote bytes, 153,456 bytes, SHA-256 `366cdc7d160ee6743cb125c6709f57e48f6ddfb91ead812a92eb881570233357`.
- CANDIDATE_MANIFEST: `scripts/vnext_agent/dist/gipuzkoa360-vnext-w2-manifest.json` from W2 HEAD above.
- CANDIDATE_W1_PIN: `725a7b73ae0381092cd80edc41b8a25432d75fcd`, contract `0.2.0`.
- PACKAGE_INTEGRITY: **PASS**, 30 members.
- DISTRIBUTION_GATE: **PASS**; no unauthorized bundled HTML/PDF detected. Source references/hashes remain metadata, and OSM/GTFS attribution stays outside any false redistribution claim.
- RAW_PARITY: **NOT_RUN** because the exact package does not pin R6 0.3.1.
- MODEL_VIEW_PARITY: **NOT_RUN** for the same compatibility precondition.
- W1_PARITY_PASS: **NOT_RUN**, not PASS and not a parity failure.
- DIAGNOSTIC execution: exit 0 / `FINAL_STATUS=NOT_RUN`.
- STRICT execution: nonzero / `FINAL_STATUS=NOT_RUN`.

W3 advanced during R11 to `281f92a…` and independently reported `NO_GO`: producer/product offline acceptance passed, but assembly/model interface remain blocked because there is no exact combined W2 health 0.3.1 package. This independently agrees with the W1 intake result; it is not substituted for W1 parity.

## Deterministic gold and verification

- DETERMINISTIC_GOLD: 6 public deterministic cases, no expected final answer, literal wording or holdout; SHA-256 `cb41c25b836deaecd0d3ab4de12160c7c5ec20cf80f10824f82912b68b9b16fb`.
- R11 targeted: **9/9 PASS**.
- PYTHON: **517/517 PASS**, one openpyxl no-default-style warning, no failure.
- NODE: **17/17 PASS**.
- Runtime identity: **PASS**, frozen v4 identity `195b4980fa5998b096c308296a55e452380b0371`.
- Jury gate: **PASS**.
- Artifact gate: **PASS**.
- `git diff --check`: **PASS**.
- CI: Release fast CI run [36715583373](https://github.com/Asier-Comba/Guipuzkoa360/actions/runs/36715583373) on TESTED_HEAD; Ubuntu **PASS**, Windows **PASS**.
- V4_PRESERVATION: **PASS**.

## Findings and remaining actions

- CRITICAL_HIGH: none in W1 producer/support. `INCOMPATIBLE_W1_PIN` is a **HIGH compatibility precondition owned by W2**, not a failure observed in an R6 candidate.
- MEDIUM_LOW: no new R11 runtime finding. Historical W1 DERIVED explanatory-DAG limitation remains external; W3's R10 inline-unknown observation is resolved by this versioned R11 support handshake.
- NOT_RUN: compatible producer→adapter→evidence→public-result parity; LLM/routing/language evaluation; portal; human release review; private holdout.
- W2_ACTION_REQUIRED: publish one immutable `DEPLOYABLE_PACKAGE_READY` ZIP+manifest pinned to W1 `0.3.1` / `cb061a…`, exposing the required facts through its actual `public_result`.
- W3_ACTION_REQUIRED: after W1 strict PASS on that exact package, perform independent model/routing/language and bounded portal acceptance; use `DETERMINISTIC_GOLD_R11.json` only as public deterministic truth, never as answer wording or holdout.
- NEXT_EXACT_ACTION: run the single R11 intake command against the exact compatible W2 package; publish `W1_W2_PARITY_PASS` or structured failures without modifying W2.

PORTAL_MUTATIONS: **0**  
MERGED_OR_PUBLISHED_RELEASE: **NO**
