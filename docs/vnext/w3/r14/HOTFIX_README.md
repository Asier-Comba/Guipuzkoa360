# R14 binding compatibility candidate

Base exact runtime 8c94f8c3cf9d732c4ce94af7b4bef8f6e154c243. Temporary W3 ownership covers only the portal tool boundary. Nine tools; no new feature, data, provider or maths.

Use CPython 3.12:

    python -m scripts.vnext_agent.build_r14_binding
    python -m scripts.vnext_agent.verify_r14_binding --oracle docs/vnext/w3/r14/FINAL_ORACLE_R13.json --output resultados/vnext/r14
    python -m scripts.vnext_agent.reconcile_r14_reports
    python -m pytest -q -o addopts=
    node --test tests/e2e/contract_flow.test.mjs

New ZIP/manifest: scripts/vnext_agent/dist/r14. Historical patch3 ZIP/manifest stay intact. Only main.py differs as an expanded ZIP member. main.py source and generated editor changed; tools.py and all fifteen assets are unchanged. Original patch3 audit tests remain byte-identical inside ZIP; revised flat-interface tests are off-package. Internal nested comparison tests use main._run, while single visits use flat main.plan_visit.

Double build is for CPython 3.12; a 3.14 trial produced a different compressed ZIP identity with identical expanded members. It is NOT this candidate and was not deployed. Constructor now rejects non-3.12 builds. W1 must review the published exact ZIP, not substitute a local recompression.

Full hotfix suite: 378 PASS with clean 3.12.14 environment. Node17 PASS. Focused76 PASS; recorder1 PASS after its import switched to R14 builder. V4 identity PASS. Generated 5000 distinct kwargs /10000 calls, seed360014, no crashes/mapping errors/authoritative claims on errors. All random combinations were errors; valid requests are covered by the separate explicit 18-case parity report. This is invalid-input stress, not 5000 successful journeys. Seven final W1 truth-pack cases, all three origins, defaults/None, nondefault margins, duration, legacy and limits checked by complete public_result equality.

Early verifier/environment failures were corrected: error outcomes can retain explanatory evidence, CPython3.14 cannot reproduce pinned W1 ZIP, foreign numpy3.14 cannot load in3.12, legacy tests used old request signature, error scenario may omit health_destination. No business logic changed. Legacy recorder also regenerated old local outputs; its builder now selects R14 and those generated files were restored exactly from base. Preserved actual R13 M04 replay is unchanged; exact two prose calls are replayed against frozen tools and equal original error responses.

W1_R14_FRONTDOOR_ACCEPTANCE=PENDING. No Studio upload, no model calls, no new user messages. Historical4/12 consumed;8 remain. Schema emitted is expected local signature only, not Studio served schema. Real-agent binding High and source-copy Medium remain pending until independent acceptance and bounded portal retest. No release GO.
