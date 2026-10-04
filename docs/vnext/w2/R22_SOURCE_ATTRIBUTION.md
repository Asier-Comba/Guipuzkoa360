# R22 — atomic source attribution

Scope: the explicit human authorization after the reproduced R21 HIGH.
R21 remains historical and immutable, including its failed real acceptance.
The branch starts at R21 runtime `b0096e9aeda533ed0a43f56bf98975becf4022d8`.

Only `main.py` and `tools.py` differ inside the package. The 23 other
members, all 15 context assets, datasets, formulas, services, walking model,
producer ZIP, v4 and ten public tool signatures are unchanged.

## Deterministic boundary

Each public analytical claim has additive `source_attributions`.
Every object keeps source ID, technical role, closed human role label,
reference period and catalog institution together.

The join indexes `source_refs` and `reference_periods` independently by
source ID. It requires exactly the same unique IDs as `source_ids`,
verifies roles and periods against the existing engine/catalog, and sorts
the resulting objects by ID. It never parses the legacy concatenated
`period` string. All claims are built before returning any projection.
An incomplete, duplicate or unverified join returns an error with no claims;
it cannot leak a partially attributed result.

Existing public transformations still distinguish model versions from
observed dates. Institutions come from the catalog, with the unchanged
existing human-label presentation transform; no new institution is invented.

The prompt adds one general atomic-attribution principle and replaces the
routine date/source enumeration instruction: exact dates are given when
asked or materially needed, not as an unnecessary addition to every answer.
There are no example municipalities or golden dates in the runtime prompt.

## Verification and provenance

The new focal suite covers one/two/three sources, all independent array
permutations, missing/duplicate/extra IDs, swapped periods/roles, catalog
failures, atomic fail-closed output, 16 municipality/category combinations,
the health model roles, all existing role labels and prompt non-conflict.

The complete inherited R21 offline harness still compares the unchanged raw
calculation, effective request and every original claim against the pinned
baseline. Only the new additive `source_attributions` field is excluded
from original-claim equality; exact new public outputs remain observed.
Offline tests are not evidence of conversational or Studio acceptance.

An initial author test exposed an incorrect call to the existing error-view
helper. It was corrected before freezing the package; regression assertions
now check request identity, capability identity, error code/class, empty
claims and forbidden retry. This was a pre-freeze implementation defect,
not a portal result. An initial inherited-harness extension also incorrectly
required the new public-only field on historical internal-engine calls.
Raw parity remained 901/901 and all 14 semantic properties passed; those
false positives are a verifier-scope defect, not a candidate defect.
The verifier now distinguishes actual public calls by their explicit route.
The initial report is retained separately; acceptance is rerun on frozen bytes.
No historical verifier or candidate finding is deleted.

Build: `python -m scripts.vnext_agent.build_r22`.
Freeze protocol before responses: `python -m scripts.vnext_agent.eval_r22`.
Offline acceptance: `python -m scripts.vnext_agent.verify_r22`.
Full suites and gates are specified in `.github/workflows/r22-validation.yml`.

The private Studio version can only be created after exact-SHA Ubuntu and
Windows CI pass. The prefrozen protocol contains the 14 equivalent targeted messages and
the unchanged 24-message stratified general sample, plus a prefrozen
two-turn unknown-municipality/clarification case (16 targeted turns total).
First any real
Critical/High/Medium stops the run; no automatic R23. Actual error recovery
is not claimed if no real error occurs. Holdout remains sealed.

Delivery changes are forbidden before complete real acceptance.
Final human confirmation, merging and publication remain forbidden.

## Final local acceptance (not model acceptance)

- Python complete suite: 822/822; focal suite: 42/42.
- Node: 17/17.
- Raw parity: 901/901; oracle: 7/7; composed comparisons: 26.
- Semantic/metamorphic properties: 14/14; malformed fuzz: 5,000;
  negative boundary cases: 195; public attributed claims checked: 10,399.
- Final findings: zero. Identity, jury, artifacts and diff checks PASS.
- Independent double build: identical ZIP and manifest.
- ZIP: `6f7912c17f06c81f637dea26ea8bb49287f56c7c41099c20cb11b4ef98373c47`,
  241,884 bytes, 25 members.
- Manifest: `29a4d17b0e39962210b7847e83595485ac14f4878dd97717345a66e8c66adc8a`.

Actual report: `outputs/r22/offline-audit.json`; full Python report:
`outputs/r22/local-pytest.xml`. These are local evidence, not CI or Studio
evidence. CI and real acceptance must refer to this exact new package.
