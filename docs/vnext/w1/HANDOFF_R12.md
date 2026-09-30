# R12 — isolated consumer gate and R11 reconciliation

Scope: acceptance scripts/tests only. R6 0.3.1, its snapshots/contracts/ZIP, legacy 0.2.0, v4, W2/W3, main and integration are unchanged. R11 evidence is retained as history, not silently replaced.

START_SHA `c9cb37f6c65e77149e18cd883eeaff40d1c1bb8e`; TESTED_HEAD (gate/tests/evidence) `1edb66a6146a506dc25cc2c7dc366b886c045918`. PUBLISHED_HEAD and exact remote CI are recorded externally in PR15 after this documentation-only closure, avoiding an impossible self-referential commit SHA.

## Exact candidate and environment

Baseline W2 Git `2321e03e3d994b488db9723560383d9defedcac7`; ZIP `scripts/vnext_agent/dist/gipuzkoa360-vnext-w2.zip`, **219354 bytes**, SHA-256 `b4feb978b625b34f9d7331ce8d376a34a29e84e4783868f83ce48a0c0d1011be`. Adjacent manifest SHA-256 `00e1de56e93bf47ddb951cef2f8276f4ae86c034b4c7a0b46c662468e2968cbb`.

The real W1 runtime Git is `cb061a9e00a6496c40488a596bd94834bc2c49b2`; the historical `cb061a97e78d6b5c967104fef6b935132fdc450f` is an erratum, not a compatibility credential. Contract `0.3.1`; entrypoint `prototypes.ir_y_volver.provider_r6`. Actual nested R6 ZIP is checked against `c66d44af702eb3410fcea05ae8711f537214f675e83a7fda38c39c3b39a1b910` / 129365 bytes. Outer and nested manifest inventories must be nonempty, closed, and match every member's hash/size; duplicate, unsafe and case-colliding entries fail. A manifest's own raw-evidence authorization flag does not establish human permission.

`intake_candidate_r12` launches the oracle and extracted candidate in **different cold `python -I` subprocesses**. Candidate cwd/root is the extraction, with only that root explicitly added to its import path. No inherited `PYTHONPATH`, prior product-root variables, model keys or loaded producer modules. Environment allowlist: SYSTEMROOT, WINDIR, PATH, TEMP, TMP, TMPDIR, COMSPEC, PATHEXT, LANG, LC_ALL; UTF-8 I/O is explicit. The valid/invalid-root probes set only `GIPUZKOA360_VNEXT_ROOT`. Socket connect/DNS are blocked by the worker's audit hook; candidate source/output is not patched. Runtime module imports and generated tools bytes are hash-checked. Actual roots are observed at calculation/validation/projection, not inferred from arguments.

Evidence records Python, cwd/configured and observed roots, import paths/hashes, exact invocations, raw envelopes, public tool strings, parsed views, stage and traceback. No environment dump or secrets. These are deterministic tool executions, **not LLM conversations or portal evidence**.

## R11_FINDINGS_RECONCILED

Published early in [Issue 16](https://github.com/Asier-Comba/Guipuzkoa360/issues/16#issuecomment-5914599913). The old R11 reports/comments remain available.

- R11's Critical legacy raw failure does **not** reproduce package-local: legacy raw equals the separate frozen producer and `public_result` succeeds. The R11 evaluator mixed an observer checkout into candidate execution/projection: HARNESS_DEFECT, owner W1.
- The sixteen missing **health** labels do **not** reproduce cold/package-local or with an explicitly valid root. Effective stop IDs map correctly, including other origins. The original unconditional canonical-label requirements were invalid.
- `KeyError('transformation')` is reproduced in W1 `intake_candidate_r11.validate_model_view -> expected_value -> pointer`, applying `/sources/0/transformation` to legacy. It is a W1 assertions/VERIFIER_ERROR, not an exception from W2 `public_result`. R12 records its actual traceback separately from acceptance.
- Legacy has no health destination/walking contract. Failed itineraries have no successful itinerary fields. Rejected normalization has no populated effective request. Every NOT_APPLICABLE records its reason and scenario index; applicable health checks are retained.
- **A real W2 alternate-root defect remains**: from an observer cwd containing data, explicit execute root is not consistently propagated into legacy calculation/public projection. This is distinct from the false claim that isolated deployment fails. W2 acknowledged product ownership in [its reproduction](https://github.com/Asier-Comba/Guipuzkoa360/issues/16#issuecomment-5914139816). An explicitly configured valid root works; an invalid root stays invalid and produces `data_unavailable` with zero claims, not silent fallback.

## Baseline result and remaining product defect

Strict baseline acceptance: **FAIL (exit 1)**. Full evidence: [candidate_r12/baseline_intake_r12.json](candidate_r12/baseline_intake_r12.json).

- 32 invocations: 27 plans, 5 comparisons, 37 scenarios; 1811 scoped assertions; current verifier errors 0.
- Raw binding PASS 32/32: **30 exact raw objects plus two explicit safe rejections**, not 32 fabricated raw objects. Structural invalid input maps `invalid_request` to consumer invalid-input error. An unverified snapshot maps producer `unknown/snapshot_not_found` to consumer `error/contract_violation/health:unverified_requested_snapshot`; safe next action and zero claims required. Both mappings are visible, have no computed numeric evidence and have explicit applicability reasons.
- Model-view: 29/32 PASS. Comparison parity: 4/5 PASS. Original 14-case subset: raw 14/14, model-view 12/14; this is not a release PASS.
- One cold-package High root cause: stop **7214** is displayed as `"7214"`, expected **Beasain - Zaldizurreta 7**, at `mobility.scenarios[index].itinerary.outbound.to_stop_label`. Occurrences: `legacy_r4_explicit` index 0, `mixed_r4_r6` index 1, `sequence_legacy_after_health` index 0. Same label failure also appears in the explicit-valid-root probe. No cold Critical defect reproduced. Alternate-root propagation is a second High root cause in its separate environment probe. Exact declared freeze is a third High root cause: **0/14 raw bindings pass**, with `contract_violation/capability:stale_validation_evidence`; it independently reproduces W3's assembly blocker.

Comparison checks bind every scenario index/status/error/normalized request, changed/held parameters, pair identities, offered deltas, required source facts/assumptions/limitations and numeric claims to **exact** raw pointers. Empty inventories never pass. Eight scoped mutation regressions cover swapping identities, altered statuses/parameters/deltas, empty/dropped scenarios, duplicated truth elsewhere and contradictory claims. Human-authored input is never inferred from caller-supplied provenance. Sources preserve required facts, order and cardinality while allowing readable enrichment; absent legacy health fields are not fabricated. Negative tests reject altered/dropped required facts.

Three origins and legacy/health sequences are included. Thirteen existing immutable-input boundary cases are reused; the corruption case that requires altering the runtime ZIP is not run against the real candidate. Separate synthetic integrity mutations test rejection, not modified production-package acceptance. Intermediate W1 verifier errors are reconciled in [ATTEMPTS_RECONCILED.md](candidate_r12/ATTEMPTS_RECONCILED.md), with original verbose reports retained locally by hash. Final workers use a bounded 300-second timeout. This is not an agent-latency benchmark.

## W3 closure and exact W2 patches

W3's final R12 publication is `1d60cdf81d3eb7661bc1d97c12425b9bdcf69b8d` (tested support `0601367e11ce0e869d3042e55623409d20aac203`). Its independent baseline review and NO_GO are preserved: [Issue16 checkpoint](https://github.com/Asier-Comba/Guipuzkoa360/issues/16#issuecomment-5915038316). It created no version and used 0/12 smoke messages. No holdout was read by W1.

W2 first patch: Git `6693cbce605484dc48eca9ed7de867e32c5f3aa7`, ZIP `9dbb2d7421e2468e44949f94ad1ef5b9011430601d34dd76057fb1720e0bfb1b` / 224576 bytes. Root/label corrections pass interim deterministic parity, but its thirteen-file declaration still fails W3's declared-freeze reproduction; this is not release acceptance.

W2 second patch: Git `7dc4d807d4ac159b508ef383b9ec950b4dce3e41`, ZIP `c5bedc0c2fbc028258135d3f8b2a94d5fc37aa3a9808417fee3165a9915e98d4` / **225894 bytes**; manifest `059ad32664aacaccdb7302e9f50ca519f21b5103a27df3bd409f45fa8caee1a9`. Fifteen declared data assets now include the W1 ZIP and mobility source catalog. W1 downloads exact immutable Git bytes; it does not rebuild this candidate. The gate reads the literal `STUDIO_CONTEXT_FILES` from packaged main.py, extracts **only** main.py/tools.py plus those paths into another fresh directory, then repeats the original fourteen public cases. Full tests, gold and filesystem proof/pin artifacts are absent there. Final result is recorded in `candidate_r12/final_patch_intake_r12.json`, including its separate `declared_freeze` verdict. This local closure simulation does **not** prove that Studio mounts a binary ZIP or preserves the expected folder layout; W3 must verify real inclusion/schema before using its bounded smoke authorization.

**PATCHED_PACKAGE_RESULT=PASS (exit 0)**: raw binding 32/32 (30 exact, two controlled rejections), model-view 32/32, comparisons 5/5; 1811 primary assertions and 37 scenarios. Declared freeze raw/model **14/14** each; six separate environment-probe invocations. Alternate cwd/valid configured root both pass; invalid configured root yields controlled errors, no numeric claims and no fallback. Current verifier errors **0**, findings **0**, Critical/High **0** in this bounded deterministic gate. Baseline/parity histories remain FAIL; release/LLM/portal are not approved. No support/runtime change is needed after this PASS.

Evidence JSON is losslessly compacted to avoid a 196,000-line review diff; all raw/public values remain. Repository LF-byte identities (not Windows working-copy newline identities): baseline **3102841 bytes**, SHA-256 `b8602c026e7141360e0070009d185c704371da8b71d675ae226525fbeb2ff84b`; final patch **4321325 bytes**, SHA-256 `802ce0d06b4d8830ec7326c4e2dd0d306d7b766ead010c806824ce56005bc50d`. Each records its start-time gate/worker/requirement hashes.

## Reproduce and next action

Download the ZIP and adjacent manifest from the **exact W2 Git SHA**, without rebuilding or changing them. From the W1 checkout:

```text
python -m scripts.mobility.intake_candidate_r12 --package <exact-W2.zip> --manifest <exact-W2-manifest.json> --output <report.json>
python -m pytest tests/mobility/test_r12.py -q -o addopts=
python -m pytest -q -o addopts=
node --test tests/e2e/contract_flow.test.mjs
python scripts/ops/verify_runtime_identity.py
python scripts/benchmark/verify_jury_results.py --output work/jury-gate-r12.json
python scripts/release/verify_final_artifacts.py
git diff --check
```

PASS exits 0; FAIL, strict NOT_RUN and VERIFIER_ERROR exit nonzero. Diagnostic NOT_RUN is informational only and cannot approve a release. Local complete suite: **541 Python PASS**, **23 R12 tests included**, **17 Node PASS**, v4 identity before/after PASS, jury/artifact/diff gates PASS. One non-failing openpyxl style warning. Remote CI on the published W1 SHA is recorded in PR15, not inferred from local tests. Green W1 CI proves verifier regressions; exact-package parity proves only the tested deterministic package; neither proves LLM/portal behavior.

W2: preserve the accepted second-patch Git/ZIP identity while consumers review it. W3: independently consume that exact package/report, verify real Studio binary/layout/schema, and only then resume its bounded authorized private smoke. No other tool/territorial behavior or LLM conversation is certified by this W1 mobility gate; retain scheduled-vs-observed and modelled-vs-verified-entrance limits. W1 needs no new feature, runtime or support changes absent a concrete failing observation. Checkpoint: [RESUME_R12.json](RESUME_R12.json). No merge, portal or release publication.
