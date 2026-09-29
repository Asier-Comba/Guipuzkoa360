# GIPUZKOA 360 vNext — W2 R2 handoff

WORK_ID: W2

ROUND: G360-R2

STATUS: PARTIAL

BASE_SHA: `e213eaa9b73b0f8a4d1893e0269fe92fe6756955`

MAIN_OBSERVED_SHA: `e213eaa9b73b0f8a4d1893e0269fe92fe6756955` (remote observation 2026-09-29)

BRANCH: `work/vnext-w2-agent-evidence`

TESTED_HEAD: `92554f313c1d9a26578e1566ece7fd456be70fc8` (code, registry, tests, generated package; handoff text excluded)

PUBLISHED_HEAD: recorded in draft PR and final response after this handoff commit; never embedded here to avoid a self-referential SHA.

CONSUMED_WORK_HEADS: W1 `c68eb5c55dec72a267b7435b4c364049f6eab408` read-only; generalized reference `7e864f4da3a529b5648444700e7148f3ae2304b5` read-only. No commits imported.

CONTRACT_VERSIONS_AND_HASHES: Evidence v1.0.0 `81f1162cb90a65394d96e8735f6403050094eea29a9c17648426282dfc3dc191`; Capability v1.0.0 `1ad14eb4a825d426958d29fde54104f6d4b45e60f2e25ccc5920af23df435d4c` (SHA-256 of files).

SOURCE_COVERAGE_AND_GAPS: VERIFIED_LIVE repository base, current remote refs, v4 data/source catalog and W1 provider/snapshot were inspected. HISTORICAL three project summaries were read as background only. The requested thirteen TXT files `00_START_HERE_UPLOAD_ALL_THESE_TXT.txt` through `12_MANIFEST_SHA256.txt` are not mounted or in the project mirror. In particular, OFFICIAL M4/M5 literal, history and emails have not been read. No claim is made that 73/73 practices were completed; historical account progress remains 55/73. The original 50+/504 trace was not located. Private content is not copied into the package.

FILES_CHANGED: `contracts/vnext/{evidence-v1,capability-v1}.schema.json`; `agentes/gipuzkoa360_vnext/**`; `scripts/vnext_agent/**`; `datos_preparados/vnext/capabilities.json`; `tests/vnext_agent/**`; `docs/vnext/w2/HANDOFF.md`; `.github/workflows/vnext-validation.yml`. No W1, W3, v4, release or existing workflow files changed.

IMPLEMENTED: Isolated `build_agent(model)` using the portal-provided model; eight real territorial/introspection tools; strict capability registry with data hashes, handler and source checks; Evidence v1 request binding, per-claim provenance and result pointers; controlled domain/data/execution/transport/unknown errors; one disclosed equivalent-category alias; per-session follow-up recalculation in offline harness; no silent raw-row truncation. A separate W1 consumer checks the published provider and snapshot SHA and preserves nonviable comparison results, but is **not** exposed in the portal candidate. Builder generates a two-file Studio bundle and deterministic independent ZIP. This is a candidate, not a claim of real conversational acceptance.

TESTS_EXECUTED: Windows, Python 3.12: `py -3.12 -m pytest tests/vnext_agent -q -o addopts=` → 47 passed; `py -3.12 -m pytest -o addopts= -q` → 311 passed; `py -3.12 scripts/ops/verify_runtime_identity.py` → PASS for all 13 frozen files; `node --test tests/e2e/contract_flow.test.mjs` → 17 passed. The W2 tests include canonical 7/4/2 recomputation, 50+/70+ unsupported inputs, registry and JSON corruption, request/source/period binding, sessions, observed simulated transport vs unknown, payload limit, double reproducible package build, extracted offline execution, and W1 provider/snapshot at the published SHA. No synthetic transport test is called an observed portal 504.

TESTS_NOT_RUN_AND_REASON: No live portal/model conversation or W3 acceptance trace: portal writes are prohibited and W3 limit evidence has not been supplied. GitHub PR merge-ref CI can run only after PR creation; main CI is not candidate CI. No RAG retrieval evaluation because the official M4/M5 text and authorized corpus are missing. No live mobility operation is enabled in the portal; W1 is not yet integrated into the target branch.

FINDINGS: W2-F01, medium, source attribution gap: `obtener_resumen_territorial("Aduna", detalle=True)` returns nested service indicators but only EUSTAT in its execution-level `sources`; W2 regression `test_result_cannot_cite_catalog_only_source` reproduces it, and W2 omits those figures from verified claims while retaining raw result and adding an explicit limit; owner W3/core source producer for a versioned fix. W2-F02, medium, original 50+/504 trace absent; no causal infrastructure conclusion is supportable; owner coordinator/W3 to supply the trace. W2-F03, high for release decision, no real novel-conversation or prompt-injection acceptance; local scripted tests do not establish routing quality; owner W2 with W3/portal coordinator after authorized test. W2-F04, documentation gate, thirteen required TXT including official M4/M5 absent; owner coordinator to provide them.

DATA_RUNTIME_PACKAGE_IDENTITIES: v4 fallback runtime `195b4980fa5998b096c308296a55e452380b0371` unchanged; vNext registry SHA-256 `aa26492b3cf01d46672dc7688a0ca7825df164616d26fda02a0242c89e0006ee`; candidate ZIP `1992cc739e8e89cd4512ad45919d1ebc102a6385628f82689a23de49de6f2661`, 55,455 bytes, 24 MiB limit; W1 official GO01 snapshot SHA-256 `30fc9d638f3576ae0e1084ee1e0c7b0268469bffc8af1dd15fd12430019d968b`; raw GTFS SHA-256 `3276fcae7bfa5002a39a2a094fef6637603de2e50648a46a436b314db27832a4`. Package contains no W1 mock or snapshot.

V4_PRESERVATION_EVIDENCE: Frozen-runtime identity PASS before handoff; branch diff is restricted to W2-owned paths. Candidate regeneration and v4 identity are separate CI gates. This is not a v4 release change.

DEPENDENCIES_AND_CONTRACT_REQUESTS: Supply exact 00–12 TXT, especially M4/M5; W3 to supply current portal limits and original 50+/504 trace; coordinator to integrate W1 by published SHA and decide whether to expose pilot after joint acceptance. Any source attribution fix in core requires a versioned request, not a W2 edit to v4. No new credentials, frameworks, services or budget.

PR_AND_CI: Draft PR to `integration/vnext-2026-10-04` and merge-ref workflow status must be recorded in the PR/final response after publication. Main CI green at base is not W2 CI.

REMOTE_MUTATIONS: Work branch push and draft PR only, if publication succeeds; see PR/final response for exact IDs. No merge, release, branch overwrite or force-push.

PORTAL_MUTATIONS: NONE.

RAG_GO_NO_GO: RAG_NO_GO. The missing official M4/M5 corpus prevents an authorized documentary-question set and measured comparison with a navigable base. Proposed (not official) acceptance gate: 30 questions with explicit denominators; recall@k ≥90%, supported citations ≥95%, abstention ≥95% when unanswered, zero invented citations. RAG does not repair missing demographics or compute routes.

MULTIAGENT_DECISION: One LLM coordinator with deterministic providers remains baseline. No additional LLM agent or runtime infrastructure; revisit only with separately scoped responsibilities and measured improvement.

MOBILITY_BINDING_STATUS: W1 published HEAD and official snapshot were consumed by an isolated read-only test; adapter binding PASS. Portal/runtime capability remains disabled pending target integration and acceptance. Scheduled, stop-to-stop with destination walk only; no realtime or door-to-door claim.

NEXT_EXACT_STEP: Obtain the thirteen TXT and W3 portal-limit/trace evidence; read M4/M5 literally; run a documented real-conversation evaluation against the candidate in an authorized, non-release portal context; review PR merge-ref CI; only then ask the coordinator to decide exposure/integration.

HUMAN_ACTION_REQUIRED: Attach or identify the thirteen TXT and provide W3's current portal limits and original 50+/504 trace. Coordinator must review the draft PR; no merge or publication is requested here.

MERGED_OR_PUBLISHED_RELEASE: NO
