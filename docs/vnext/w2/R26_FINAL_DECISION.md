# R26 final decision — retain territorial fallback

`FINAL_DECISION=FALLBACK_TERRITORIAL`

`VNEXT_FINAL_GO=NO`

## Candidate, not a real-agent acceptance

- Draft PR: https://github.com/Asier-Comba/Guipuzkoa360/pull/31
- Runtime commit: `d5c02a2f9a1d8b67b5a74c3569c7e98094b0eacd`.
- ZIP: `9716389b7094096195062e8bda9b9ddd4c0f21cedce09cee8496b6ae45f570c7`, 247,818 bytes.
- Manifest: `dae1dfee59ebbd8839b3ab7468be9c04b4e0d9abd621e933a751824575b40a3e`.
- Exact-commit CI: https://github.com/Asier-Comba/Guipuzkoa360/actions/runs/37164267299 — Linux and Windows PASS. Both collected 993 Python tests, passed 17 Node tests, 901 raw parity cases, 7 oracle cases, 5,000 boundary fuzz cases, identity before/after, jury and artifacts. Both builds reproduced the package and manifest hashes.
- Full job logs are retained in `outputs/r26/ci-exact-runtime.json`.

## Observed portal sequence

1. Created one isolated draft, **GIPUZKOA 360 · Visitas comparadas**, at `agentes/gipuzkoa_360_visitas_comparadas`.
2. Filled `main.py` and `tools.py` with the exact generated candidate bytes. Downloaded both and verified SHA-256 equality:
   - main: `3f6dd27f397bc3cbe771516ea1d4c19ff2ff3da02b39c219d57ffebe9247bc9f`.
   - tools: `040c33490091e1f298b0e10f23122541e344e0585928dcf5f0445075d399dafa`.
3. Downloaded all 15 declared context assets from the portal and matched every hash to the manifest. No asset was uploaded or changed.
4. Studio preparation reported **DEFINICIÓN VALIDADA**, `openai:gpt-5.6-luna`, 10 tools, memory on, Internet off. It showed the five exact `plan_visit` fields, including `appointment_times`, and accepted the code's `list[str]` annotation. The normal UI enumerates parameter names, not the complete JSON schema.
5. Studio also included its automatically created, unused `ejecucion.py` template in the prospective snapshot. It is not imported by the candidate and not one of its ten registered tools. This extra template is disclosed; the prospective Studio archive is not claimed byte-identical to the 25-member engineering ZIP.
6. Clicked **Crear versión y probar** exactly once. Controls became disabled and the UI subsequently navigated to Pruebas, displaying the previous R25 conversation. No new R26 version appeared in the selector. After one read-only refresh, the new agent still appeared as **borrador** and the testing selector still had no corresponding version.
7. No second creation was attempted. No prompts were sent. No R25 answer was attributed to R26. The page also displayed a generic `Connection Error:` indicator; its cause and relation to version creation are **not established**. There is no verified new version ID.

Evidence: `outputs/r26/portal/preparation.txt`, `context-identity.json`, `version-not-registered.txt`, and `draft-after-create.png`.

## Acceptance status

Preparation and draft code/context identity passed. Immutable-version identity and real-agent acceptance remain **NOT VERIFIED**. Sessions A/B, M3, M4, M5 and generalization are **NOT RUN**. Real Critical/High/Medium/Low counts and unsupported-claim rates are **NOT ASSESSED**, not zero-case proof of reliability. No candidate mathematical defect was found offline; this decision is due to missing real acceptance, not an invented runtime failure.

The required GO conjunction is therefore false. No retry, new version, code change, R27, merge or publication follows this decision.

## Preserved delivery

- Selected fallback: `agentv_58e6ab81efc04f07b2be0cacead6a492`, **urban-challenge-rc2-195b498 · v4**.
- Delivery: **Borrador privado**; final confirmation unchecked; Publicar disabled.
- Existing territorial presentation and literal territorial proof remain selected. No R26 material replaces them.
- Presentation: `entrega/exec_664856e502534fc0a6a508cbfbf0e243/GIPUZKOA 360.pptx`.
- Proof: `entrega/exec_07940b39e69e4918ba08ba6c1c038c25/Prueba territorial.txt`.
- Existing territorial conversation remains in the preview; Pages and repository links unchanged.
- Track: Equipos de servicios; 3 confirmed team members; checklist 4/4.
- Main remains `e213eaa9b73b0f8a4d1893e0269fe92fe6756955`; R25 remains `34f8d571b56c6ca7f7dd2d0a545769d0b2417366`.

Human action: review the already prepared territorial preview and decide whether to publish it. R26 must not be selected as validated. Investigating/resuming the unconfirmed portal creation would require a new explicit human decision; this round is stopped.
