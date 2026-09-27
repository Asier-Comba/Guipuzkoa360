# WORK 1 TECHNICAL HANDOFF

- **BASE_SHA:** `46c1a48f63c307654f45fcb5c18883f264b660ed`.
- **HEAD_SHA:** `fddcf05217959ddc347f5d1a1ee9f35245ea9806` — technical/snapshot head covered by final CI. This handoff and the integration-plan correction are a later docs-only commit; resolve it with `git log -1 --format=%H -- docs/internal/WORK1_TECHNICAL_HANDOFF.md`.
- **BRANCH:** `final/work1-engineering-master`.
- **COMMITS:** `6217ecd`, `7228bbf`, `47362d3`, `171b6cb`, `d6a60b7`, `eae3b70`, `448009b`, `fddcf05`, plus the docs-only commit containing this handoff.
- **RUNTIME_CHANGED:** NO. Twelve frozen files match `195b4980fa5998b096c308296a55e452380b0371` byte for byte after the final local gate.

## Gates

- **CI_LINUX:** SUCCESS, Ubuntu 24.04, run `36181625120`, SHA `fddcf05`.
- **CI_WINDOWS:** SUCCESS, windows-latest, same run/SHA.
- **PYTHON_COUNT:** 229/229 PASS locally after closure; CI on the same technical SHA also PASS.
- **NODE_COUNT:** 17/17 PASS locally; syntax of critical JS and artifact checks PASS.
- **FULL_VALIDATION_SHA:** evidence committed at `171b6cb2a366f18509d3432d87f46fa21ea4aefa`; frozen runtime/data algorithms have not changed afterwards.
- **FULL_VALIDATION_CHECKS:** 72.673/72.673 PASS; traceability 31.545/31.545 under the published definition; 20/20 controlled faults; 1.000 calls, no drift/exceptions. Not rerun after Markdown/CI/snapshot-only changes.
- **JURY/ARTIFACT:** coincidence 7/4/2 PASS; full HTML/recalculation equality PASS; nine deliberate mutations rejected.
- **PACKAGE:** 48.338 bytes, SHA-256 `2808110d14e0bc30a53018cab1ec39b926e1e6ca1f1be19f0b2c9cf21106680a`; double-build reproducibility on the same toolchain.

## Data and NEXT

- **SOURCE_HEALTH:** PASS. 3 external sources / 4 catalog entries, 88/88 municipalities, 148 health records, 0 required missing cells, 0 duplicate keys, 0 invalid coordinates, 0 orphan municipality references, 412/412 row source IDs resolvable, 7/7 manifest files, temporal spread 627 days.
- **NEXT_SCOPE:** OFFLINE PROTOTYPE with structured intents. Planner, registry, executor reusing core, critic, composer, evaluator, proposal-only evolution and read-only watcher. No LLM planner benchmark, natural-language accuracy claim, portal/production use, self-editing, auto-deploy or auto-promotion.
- **NEXT_TESTS:** 77/77 PASS.
- **NEXT_KPIS:** tool selection 9/9; parameters 9/9; numeric grounding against shared core 9/9; source IDs 9/9; limitations 9/9; follow-up 1/1; out-of-scope 6/6; bounded critic attacks 16/16; composer blocks 16/16; determinism 8/8. These denominators are scoped, not general accuracy.
- **PRODUCT_SNAPSHOT:** `analisis/next/product_snapshot.json`, committed at `fddcf05217959ddc347f5d1a1ee9f35245ea9806`; `source_commit=eae3b7026a8608946d31c718fabc10111c3fa16e`.

## Portal and product

- **PORTAL_REFRESH:** `docs/internal/PORTAL_SMOKE_REFRESH.md`; v4, one attempt, `INFRASTRUCTURE_BLOCKED`. Tool call occurred; no analytical output. P2/P3 NOT_RUN. No more attempts and no runtime/version change.
- **PORTAL_THRESHOLD_QUANTILE_RISK:** Medium M-02. Model fallback after runner failure equated 2 km with coincidence criterion; no evidence of a core bug. Work 3 must keep threshold=within_threshold distinct from quantile cuts.
- **WORK3_HEAD_REVIEWED:** `36d18429d8a598820aa35d379d50937f93b47fe8`. Isolated results: 183/183 Python, 17/17 Node, jury/artifact PASS. First three commits ACCEPT; last is ACCEPT for UI labels but NEEDS_CHANGE for its stale NEXT snapshot.
- **INTEGRATION_PLAN:** `docs/internal/FINAL_TWO_WORKS_INTEGRATION_PLAN.md`. No merge performed.

## Open risk and actions

- **CRITICAL_OPEN:** 0.
- **HIGH_OPEN:** 0.
- **MEDIUM_OPEN:** 2: M-01 extreme portal payload unverified; M-02 threshold/quantile confusion in error fallback.
- **HUMAN_ACTIONS:** create an authorized integration branch; apply commits in documented order; reconcile Work 3 evidence from the new product snapshot; run post-integration commands and Linux/Windows CI; review two Mediums; retry P1/P2/P3 only when runner is operational; approve merge separately; publish Entrega only by explicit human decision. Optionally configure main protection (required PR/checks, no force-push/delete).
- **TECHNICAL_GO:** YES for Work 1 integration review. NO claim of PORTAL GO, final integrated release approval or hackathon publication.
