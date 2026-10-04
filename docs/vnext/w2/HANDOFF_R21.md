# R21 · ten-tool final acceptance

Candidate base: `81c42da2e8ab7074074d9f114d4ac7990e715da4`, the tested R20 runtime, not its later evidence HEAD. Branch: `hotfix/r21-final-10-tool-agent`. R20 preparation was blocked by the observed platform maximum of ten uniquely named tools; no R20 real messages or version were created. Its evidence is preserved under `outputs/r20/portal` and `R20_PORTAL_GATE.md`.

## Deliberate, bounded delta

Only `main.py` and `tools.py` differ in the 25-member package. The complete R20 `tools.py` is an unchanged prefix. The other 23 members, all 15 context assets, W1 provider package, data, contracts and legacy v4 are unchanged. No formula, producer, historical oracle or source fact is rewritten.

Exactly ten public tools, in order:

1. obtener_resumen_territorial
2. analizar_envejecimiento
3. analizar_acceso_general
4. analizar_acceso_municipios
5. analizar_coincidencia
6. simular_anadir_servicio
7. simular_retirar_servicio
8. simular_cambiar_umbral
9. consultar_capacidades
10. plan_visit

Municipal comparison composes fresh summaries. Source explanation uses observed analytic provenance, with the full locally validated source cards and age derivations exposed by the catalog when detail is needed. Neither capability is an additional callable tool. The previously abbreviated catalog lacked methods and limitations; projecting the existing complete cards closes that specific evidence gap.

## Reproduction

Use Python 3.12 with `PYTHONUTF8=1`, requirements.txt, and Node 24. No network or model is used by the offline observer.

```text
python -m scripts.vnext_agent.build_r21
python -m scripts.vnext_agent.eval_r21
python -m pytest -q -o addopts= -p no:cacheprovider
python -m scripts.vnext_agent.verify_r21
node --test tests/e2e/contract_flow.test.mjs
python scripts/ops/verify_runtime_identity.py
python scripts/benchmark/verify_jury_results.py
python scripts/release/verify_final_artifacts.py
python -m scripts.vnext_agent.build_r21
git diff --check
```

The second build must reproduce the first ZIP and manifest bytes. Build asserts ten unique names before Studio. Offline verification compares raw outputs, claims and effective requests against cold R20 execution; historical direct source/comparison handlers are internal references only. All 88 municipalities are checked by code and name. Composed comparison checks reuse no model answers. The historical seven-case oracle, boundaries and 5,000 malformed input attacks are separate from model acceptance.

Verifier corrections before the final pass: the first focal attempt yielded 15 PASS / 2 FAIL because the observer serializes mapping keys in canonical alphabetical order (not tool registration order), and because model/user/derived provenance is not an official web source and correctly has a null URL. Registration order is now checked in the generated AST and catalog, while null URLs are accepted only for the enumerated non-web provenance roles. No candidate code changed for these two verifier errors. The initial audit also used an unsupported test-only origin spelling; it was corrected to the frozen catalog identity before final acceptance. These initial attempts are not transferred as candidate PASS or presented as defects in the candidate.

## Real acceptance and publication boundary

`outputs/r21/real-protocol.json` and its corpus are selected before any response. Eleven targeted messages precede the stratified 24-message general acceptance. First real Critical/High/Medium stops the round; no automatic R22 or patch is authorized. An offline PASS never implies Studio or conversational PASS.

Studio must prepare and show these exact ten names. Create a new private human-named version only after exact-runtime-SHA Ubuntu and Windows CI are green. Internet remains OFF. Do not overwrite historical versions or select this version for delivery before its real acceptance is complete.

Only after real acceptance is entirely green may the public conversation, copy, presentation and preview be completed. Delivery stays private; track remains the human-selected Equipos de servicios. Final acknowledgement, publication, merge, main changes and holdout execution are not authorized.

Final evidence and exact version/SHA associations will be recorded in `R21_REAL_ACCEPTANCE.md`; unrun checks must remain explicitly NOT_RUN rather than inheriting R19/R20 results.

## Local final pass

780/780 Python, 17/17 Node, 901/901 raw parity, 7/7 historical oracle, 26 composed comparisons, 14/14 metamorphic properties, 195 negative cases and 5,000 malformed inputs: PASS with no findings. v4 identity, jury and artifact gates and diff check: PASS. Package: 240,430 bytes; ZIP SHA-256 `a714bac1fa91caebe3e8ef6fb65259c4f11447120479ecf51dce4813cfba5dc2`; manifest SHA-256 `6d425d3e194e6fea016ae4a4b685ae2e50af978897278539d17b7bb03fad31b9`. These are offline results only. Exact SHA CI and Studio remain separate gates.
