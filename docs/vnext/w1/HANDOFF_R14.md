# R14 — independent flat portal boundary acceptance

W1 producer remains frozen. This round changes only W1 support/tests/evidence.
No W2/W3 code, data, contracts, GTFS, walking, snapshot, sources or runtime edits.
No model/portal calls, version creation, merge or publication.

## Exact target

- W1 start: `106879509a667b75baec4860e28a16b9720fdc71`.
- Hotfix: `094745b26bc57aee5cc1a5e003401743d96a914f`, PR18,
  branch `hotfix/r14-portal-binding`, readiness announced in Issue16 comment5918172714.
- Exact base: `8c94f8c3cf9d732c4ce94af7b4bef8f6e154c243`.
- ZIP: `9c6fa5c692df178afe36366c6291e7c0e7c3da06134381b09d853f55d6707252`, 226337 bytes.
- Manifest: `d6c0122b475284c468fdfc3e343b9ab0d9d175cf20513048c915281cedf4e911`.
- W1 runtime: `cb061a9e00a6496c40488a596bd94834bc2c49b2`; R6 ZIP
  `c66d44af702eb3410fcea05ae8711f537214f675e83a7fda38c39c3b39a1b910` unchanged.
- W3 evaluator successor: `9a49672672388a871874c93f23300283477d9483`.

## Audited scope

Only expanded ZIP member `main.py` changes. Exact inventory and all other bytes,
including tools, fifteen assets, historical audit tests and nested W1 ZIP,
match patch3. Safe outer/nested inventory, hashes, members and declared freeze
checked by unchanged W1 package gate. Two independent in-memory builds from old
ZIP metadata and exact new member bytes reproduce the reviewed ZIP hash.

Coordinator AST outside plan_visit and SYSTEM_PROMPT is identical. Prompt adds
only two generic rules (structured fields; source/period/derivation). No answer
gold, totals, -35, phrase routing or new capability. Business logic unchanged.

Five required fields: origin_id:str, destination_id:str, date:str,
appointment_time:str, duration_minutes:int. Five optional None defaults:
arrival_margin_minutes:int|None, boarding_margin_minutes:int|None,
walking_profile_id:str|None, snapshot_id:str|None, return_deadline:str|None.
Nine tools. No external request argument. This is a LOCAL_EXPECTED signature
under the identity decorator fallback, **not** Studio-served schema evidence.

## Independent execution

47 detailed calls PASS: seven R13 public cases, applicable R12 plan cases,
three exact supported origins, explicit malformed inputs, omission/None/defaults.
An execute-boundary spy verifies independently constructed request and exact root;
it never replaces computation. Required values preserved; None omitted;
provided optionals preserved without trimming, casts or substitutions.
Unchanged structured execute + public_result equals the entire flat public view.
Test-only correlation ID fixes UUID noise; production UUID/candidate bytes unchanged.

R12 gate on exact new ZIP: raw32/32 (30 exact objects plus two controlled safe
rejections), model-view32/32, comparisons5/5, scenarios37, assertions1811,
verifier errors/findings0; declared flat freeze14/14. Same frozen R12 worker and
assertions, cold four-case batches as documented in R13. Offline network blocked.

Default check: omission equals all None byte-semantically; explicit10/3 retains
identical components, itinerary and walking but changes provenance from
model_default to human_explicit. Caller-supplied does not prove actual human intent.
Legacy preserves stop-only semantics and labels; no fabricated health destination.

Public truth pack checked field-by-field: statuses by layer, components, critical
facts, sources, itinerary and limits. MAIN10691s versus VARIATION8591s gives
-2100s/-35min, conditional scheduled/modelled difference only. Structured M04
representation PASS; real LLM repair NOT_CLAIMED.

Generated boundary fuzz: PASS. Seed360114,5000 indexed requests /10000 executions,
four disjoint cold workers,916.077s. Mix1500 valid-domain and3500 invalid inputs;
566 distinct payloads, not5000 independent tests or users. Exceptions, mapping
mismatches, silent defaults, invalid accepted, valid rejected and semantic
mismatches all0. Public statuses: valid1054,no_data446,error3303,unsupported197.

Initial fuzz stopped because the verifier confused public valid/no_data with
producer ok/no_feasible_journey. Preserved in first-fuzz-attempt; corrected only
the layer-specific expected predicate and added four positive/negative regressions.
No candidate patch or waiver. Final acceptance must use the corrected report.

## Closure and reproduction

```text
python -m pytest tests/mobility/test_r14.py -q -o addopts=
python -m scripts.mobility.accept_frontdoor_r14 --package <exact.zip> --manifest <exact.json> --output <evidence>
python -m scripts.mobility.verify_r13 --package <exact.zip> --manifest <exact.json> --output <parity.json>
python -m scripts.mobility.accept_frontdoor_r14 --package <exact.zip> --manifest <exact.json> --output <evidence> --fuzz
python -m scripts.mobility.verify_frontdoor_evidence_r14 --targeted <evidence>/targeted.json --output <truth.json>
```

No repeat of R13 producer20k stress. Full Python once after fuzz:577 PASS (one
historical openpyxl style warning); targeted12 PASS; Node17/17 PASS. V4 identity,
jury, artifact and diff gates PASS. Own commit/push/same-SHA CI is recorded in the
explicit checkpoint on PR15, PR18 and Issue16. Hotfix CI36765784442
PASS Ubuntu/Windows is separate from W1 final evidence CI recorded on PR15.

Local R14 Critical0/High0/new Medium0. Acceptance remains conditional on own
same-SHA CI until the explicit checkpoint is published. Three W1
historical Medium observations retained from R13. Historical W3 High1/Medium1
are NOT resolved by local wrapper acceptance; require actual bounded portal retest.
Eight of twelve private message slots remain; no budget reset.

W1_RUNTIME_CHANGED=NO; V4 preserved195b4980fa5998b096c308296a55e452380b0371.
PORTAL_LLM=NOT_CLAIMED. NEXT=W3_PORTAL_RETEST after explicit same-SHA green
W1_R14_FRONTDOOR_ACCEPTANCE=PASS on PR15/Issue16. Then W1 STOP, no R15.
