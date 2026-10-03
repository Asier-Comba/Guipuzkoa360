# R26 — deterministic comparison of appointment times

## Scope and provenance

This branch starts at the exact R25 runtime `f955669adb2920718b5b888b916681fc00dc3593`, not its later evidence head. PR30 and its evidence are unchanged. The selected territorial fallback is not changed by this work. No merge or publication is authorized.

R25's public conversation contained two false model-generated comparisons despite correct tool totals: 45 minutes instead of 35 minutes less, and 15 minutes instead of a 35-minute later start. R26 moves this responsibility into the existing deterministic provider comparison path; it does not change the provider or observations.

## Public contract

Exactly ten tools remain. Only `plan_visit` changes its public five-field signature:

```python
plan_visit(origin_id: str, destination_id: str, date: str,
           appointment_times: list[str], duration_minutes: int) -> str
```

One HH:MM value executes the unchanged single scenario. Two distinct HH:MM values are ordered `[confirmed baseline, new scenario]` and use the existing `health_adapter.consume_compare` / provider comparison. Empty arrays, more than two values, duplicates and malformed clocks are rejected before execution. Other fields stay identical across the pair. This interface does not compare different origins.

The public comparison ledger validates both complete eight-component duration ledgers, effective request identity, equal non-time parameters, provider comparability and signed total delta. It derives signed start/end deltas from verified endpoints. It emits an authoritative table and Spanish sentence, including direction and unchanged endpoints. Invalid comparison data exposes no partial mobility result or numeric claims.

The coordinator must use one comparative tool call and copy this verified presentation. It must not subtract, convert units or infer shifted clocks itself. An ambiguous baseline requires clarification.

## Frozen package

- ZIP SHA-256: `9716389b7094096195062e8bda9b9ddd4c0f21cedce09cee8496b6ae45f570c7`
- Manifest SHA-256: `dae1dfee59ebbd8839b3ab7468be9c04b4e0d9abd621e933a751824575b40a3e`
- ZIP size: 247,818 bytes; 25 members.
- Changed members relative to R25: `main.py`, `tools.py` only.
- All 15 context assets, including the W1 runtime ZIP, are byte-identical.
- Two clean builds produced identical ZIP and manifest hashes.
- No benchmark gold values or case-specific hints occur in generated runtime code.

## Offline evidence

- 81 focused tests: singleton preservation, 36 ordered time pairs across three origins, invalid schemas, fail-closed mutations, deterministic repeat/order reversal, both signs and synthetic equal-duration case.
- 5,000 seeded formatting properties (separate from the inherited boundary fuzz).
- 901/901 raw parity cases; 7/7 oracle cases; 26 composed comparisons; 195 negative cases; 5,000 boundary fuzz cases; zero findings.
- 10,399 claims checked for atomic source attribution; all inherited metamorphic checks passed.
- Node: 17/17; territorial runtime identity, jury checks and artifact gate passed.
- Full Python suite: 992/992 passed in 374.65 seconds. The additional explicit deterministic/sign/zero property was added after that run was collected; the final focused suite including it passed 81/81. Exact-commit CI will collect 993 tests.
- Raw audit: `outputs/r26/offline-audit.json`; observed catalog: `outputs/r26/catalog-observed.json`.

This is author-side offline evidence, not a claim of real model or portal acceptance. Exact-commit Linux/Windows CI results must be recorded separately before Studio acceptance.

## Reproduce

```text
python -m scripts.vnext_agent.build_r26
python -m pytest -q -o addopts= -p no:cacheprovider
python -m scripts.vnext_agent.verify_r26 --output work/r26-audit.json
node --test tests/e2e/contract_flow.test.mjs
python scripts/ops/verify_runtime_identity.py
python scripts/benchmark/verify_jury_results.py --output work/r26-jury.json
python scripts/release/verify_final_artifacts.py
python -m scripts.vnext_agent.build_r26
git diff --check
```

The inherited parity harness keeps its historical baseline identity. Only the intentional public singleton field rename is adapted for the candidate; raw results, effective requests and claims must stay equal. New paired requests have dedicated provider parity assertions.

## Real acceptance still required

One private version, official Studio model unchanged, memory on, Internet off. Verify code/context identity and the five-field list schema before prompting. Execute two clean main+variation sessions on that same version, then sources, unsupported home/realtime/availability, Segura and its comparison. Stop on any Critical, High or material Medium; do not retry or create another version. Until every gate passes, the territorial fallback remains selected. No R27 and no publication.
