# R13 — final deterministic oracle

Scope: W1 support scripts/tests and public evidence only. No product, source data,
contract, walking, GTFS, reconciliation, R6 ZIP, v4, W2/W3, main or integration edits.
No model, portal, merge or release publication.

## Exact identities and reconfirmation

- START_HEAD: `7f434a469d7f94fdff8ae7d2665644426a217250`.
- Runtime Git: `cb061a9e00a6496c40488a596bd94834bc2c49b2`, R6 `0.3.1`,
  `prototypes.ir_y_volver.provider_r6`.
- R6 ZIP: `c66d44af702eb3410fcea05ae8711f537214f675e83a7fda38c39c3b39a1b910`, 129365 bytes.
- W2 runtime: `8c94f8c3cf9d732c4ce94af7b4bef8f6e154c243`;
  documentation-only successor `fa679248a6239604f56368f384e708a022c09e95`.
- W2 ZIP: `3951b290b6ca59c336886a3f0acee77a68036d4fbcbc06c2cedfe22400c08616`,
  226010 bytes; manifest `a672bf9a2afece58c468a1f762c860f0217536a2a4fa18737ba768cab755c70a`.
- W3 consumed: `1d60cdf81d3eb7661bc1d97c12425b9bdcf69b8d`; its baseline/patch1
  NO_GO is historical and not acceptance of the new candidate.
- PR15/17/14 inspected live; all OPEN/DRAFT and mergeable. W1 clean at preflight;
  main/integration unchanged at `e213eaa9b73b0f8a4d1893e0269fe92fe6756955`.
  The current W2 Git blob was downloaded and its ZIP hash reconfirmed, not rebuilt.

Reconfirmation **PASS**: raw 32/32 (30 exact objects + two explicitly justified
safe rejections without numeric evidence), model-view 32/32, comparisons 5/5,
37 scenarios, 1811 assertions, verifier errors/findings 0. Exactly declared flat
freeze 14/14 raw and view, six valid/foreign/invalid-root probes.

The first unchanged R12 full traced worker hit its 300-second protocol timeout:
VERIFIER_ERROR, not candidate drift or a product Critical. Its exact report is
retained locally (`work/r13-exact-parity.json`, SHA-256
`3ea0bb1a875394c993b858d82730c5a5999f24f94b9830646abdda0df76ee58d`);
declared freeze still passed in that failed attempt. R13 then used the **same** R12
worker and assertions in bounded four-case cold batches: all counts reconfirmed
in 184.159 seconds. No timeout or acceptance rule was relaxed. Batch boundaries
reset state; the expanded metamorphic campaign separately tests A-B-A inside each
triple. Original R11/R12 history remains unchanged.

## Generated/property stress and expanded acceptance

STATUS: PASS. 20000 generated requests (17222 distinct request byte strings), seed `360013`; four disjoint
global-index-modulo-four shards, two actual producer calls for every input.
Hard campaign bound 2685 seconds. These are generated/property stress inputs,
not thousands of independent tests, real users, observed journeys or LLM calls.
Actual campaign: 40000 executions, 1121.863 seconds, crashes 0, counterexamples 0.
Statuses: ok 6465, no_feasible_journey 3635, error 7618, unknown 1382,
unsupported 900. Eighteen input families, all three origins and all 24 hours.

Every complete 40-input block covers duration 1/720/typical and 0/721, arrival
0/10/1/45/240 and -1/241, boarding 0/3/1/15/120 and -1/121; null and Zegama
09:45 return-deadline 11:07:49 ±1; explicit health/legacy/absent/malformed snapshots,
wrong types, empty/missing/extra fields, lists/dicts, unvalidated/invalid dates.
Origins cycle through all three; generated hours cover the entire civil day.
NaN/Inf input rejections are separate targeted tests, not nonstandard JSON inputs.

Checks: closed result schemas, finite strict JSON, allowed statuses, repeated
semantic bytes, component non-negativity/continuity/sums, appointment seconds,
raw scheduled stop rows and route binding, snapshot walking identity/geometry,
approximate-time caveats, retained entrance NOT_VERIFIED, no date/snapshot fallback,
health-vs-legacy separation. No producer caching or output monkeypatch is used.

The expanded campaign uses separate cold producer/candidate workers and unchanged
candidate bytes. It changes one parameter in each comparison triple, checks
effective held/changed fields, exact scoped views, within-triple A-B-A and lawful
delta/comparability. Explicit-vs-omitted defaults have equal arithmetic but distinct
provenance. No timetable monotonicity is assumed. Mutations use synthetic copies
only; spot expected values come from CSV selection and pinned geometry/formulas,
never producer output.

Expanded acceptance PASS: 23 metamorphic cases / 64 scenarios, 4583 assertions,
30 raw/view bindings: 27 exact producer objects and three documented controlled
rejections without numeric evidence. Verifier errors/findings 0. Thirty-four
distinct synthetic mutation categories caught 34/34, gaps 0. Twenty successful
raw-source spot checks, stratified across three origins, times, durations and
default/non-default margins. Source reconstruction retains pinned health/walking
derivatives; it does not assert verified entrances or observed walking times.

An initial expanded expectation incorrectly demanded partial projected results
for a comparison containing a string duration. The consumer correctly rejects
the whole call with `contract_violation` / `health:invalid_duration`, no outcomes,
claims, raw numeric result or delta. The narrow acceptance rule applies only to
that exact malformed case; eight positive/negative regressions guard it.
`r13/r13-invalid-comparison-diagnostic.json` preserves the independent cold
producer/consumer reproduction. This was a verifier expectation correction,
not a candidate change or a waived product finding.

## Truth pack and limits

FINAL_ORACLE_R13.json contains seven public intents/structured requests,
expected producer and consumer-envelope statuses (distinct layers), critical
facts, numeric claims with units/period, source facts, limits and forbidden claims.
No final natural-language answer, mandatory exact prompt, tool sequence, wording
gold or holdout. The 10691 s vs 8591 s / -2100 s contrast is a conditional
scheduled/modelled scenario difference, not observed saving, best time,
recommendation, causality or prediction.
Truth-pack SHA-256: `2f57634fcab245a63c95b2a4e833895f664b8a43b52592214470b913b6b1ba53`.
Detailed acceptance, stress shards, mutations and raw-source calculations are
retained under `r13/`; they are QA evidence, not runtime context or delivery data.

Retained historical Mediums: W1-R7-F01 explanatory DERIVED circularity (arithmetic
intact, external R8 DAG explains it); W1-R9-F01 raw + pinned health derivative,
not fully raw reproduction; W1-R9-F02 specific HTML/PADI reuse terms unverified
(exclude raw documents from delivery absent human review). R13 does not remove
these observations by changing runtime or purport to perform new legal review.

## Reproduce / closing gate

```text
python -m scripts.mobility.verify_r13 --package <exact.zip> --manifest <exact.manifest.json> --output <parity.json>
python -m pytest tests/mobility/test_r13.py -q -o addopts=
python -m scripts.mobility.run_stress_r13 --output <stress-dir> --count 20000 --shards 4 --budget 2640
python -m scripts.mobility.evidence_r13 --package <exact.zip> --manifest <exact.manifest.json> --output <evidence-dir> --stress-summary <stress-dir>/stress_summary.json
python -m pytest -q -o addopts=
node --test tests/e2e/contract_flow.test.mjs
python scripts/ops/verify_runtime_identity.py
python scripts/benchmark/verify_jury_results.py --output <jury.json>
python scripts/release/verify_final_artifacts.py
git diff --check
```

PORTAL/LLM: NOT_CLAIMED. NEXT after green closure:
WAIT_FOR_W3_OBSERVED_FAILURE_ONLY. No R14, feature, runtime repin or further support
change absent a concrete observed failure pointing to producer truth.
Local closing gates: 565/565 Python (one historical workbook-style warning),
17/17 Node, v4 runtime identity PASS before/after, jury PASS, artifact PASS and
diff check PASS. New Critical/High/Medium: 0/0/0; three historical Mediums retained.
Exact published SHA and remote CI are recorded in PR15 after the commit (no
self-referential commit hash). Read that live record before transferring readiness.
W1_FINAL_ORACLE_READY=YES and W1_FROZEN=YES only once that same-SHA remote CI is green.
