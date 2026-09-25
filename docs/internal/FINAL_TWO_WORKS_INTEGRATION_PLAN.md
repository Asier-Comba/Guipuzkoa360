# FINAL TWO WORKS INTEGRATION PLAN

- **BASE_SHA:** `46c1a48f63c307654f45fcb5c18883f264b660ed`.
- **WORK1_HEAD:** `fddcf05217959ddc347f5d1a1ee9f35245ea9806` (snapshot y documentación cerrados; el handoff posterior solo registra evidencia).
- **WORK3_HEAD_REVIEWED:** `36d18429d8a598820aa35d379d50937f93b47fe8`.
- **RUNTIME:** `195b4980fa5998b096c308296a55e452380b0371`, identidad sin cambios.

## WORK3_COMMITS

| Commit | Estado | Razón |
|---|---|---|
| `6e8a7ae7514dcc5acf76949b329526d45dbb1352` | **ACCEPT** | Superficies de producto y evidencia guardada; conserva cálculo canónico y no cambia runtime/datos. |
| `9639e8ba69f34cecbe6e099a2654c67270d33ba0` | **ACCEPT** | Añade 30 tests de producto y conserva método/límites del escenario. Debe viajar con el commit anterior. |
| `09478c8d7334ed4778ef85850809df515d8f99b0` | **ACCEPT** | README, demo, 44 Q&A, one-pager y guía; la referencia ausente a HUGO_JURY_HANDOFF quedó eliminada en el commit siguiente. |
| `36d18429d8a598820aa35d379d50937f93b47fe8` | **NEEDS_CHANGE** para la evidencia NEXT; **ACCEPT** para etiquetas/narrow-screen | Publica correctamente el prototipo como offline, pero fija el snapshot viejo `171b6cb`. Debe reconciliarse con `analisis/next/product_snapshot.json` de Work 1, commit `fddcf05`. |

Ningún commit queda **REJECT** íntegro. Sí se rechaza presentar HTML como diálogo live, reutilizar cifras sin su denominador o conservar el snapshot NEXT antiguo después de integrar Work 1.

## Revisión ejecutada una sola vez

Worktree detached al HEAD Work 3: **183/183 Python PASS**, incluidos tests de producto; **17/17 Node PASS**; `verify_final_artifacts` PASS con nueve mutaciones; sintaxis de `jury_view.js`/`build_jury.mjs` PASS. El snapshot NEXT de `36d1842` coincide byte/hash con `171b6cb:analisis/next/quality_kpis.json`, precisamente el desajuste que debe actualizarse. No se integró nada.

## FILE CONFLICTS

No hay solapamiento directo en archivos de ownership: Work 3 modifica README, docs de producto, resultados y builders; Work 1 modifica CI, arquitectura/operaciones, scripts ops/evaluation, NEXT y análisis. Conflicto semántico: `resultados/evidencia/next_prototype.json` referencia la evidencia antigua. Riesgo M-02 debe incorporarse a la Q&A/demo: cuando el runner falla, el umbral no se convierte en corte del cuantil.

## PRODUCT_SNAPSHOT_RECONCILIATION

- Fuente canónica nueva: `analisis/next/product_snapshot.json`.
- **PRODUCT_SNAPSHOT_COMMIT:** `fddcf05217959ddc347f5d1a1ee9f35245ea9806`.
- Work 3 debe copiar/transformar desde ese JSON, conservar `source_commit=eae3b70…`, scope acotado, denominadores y política proposal-only.
- Regenerar `product_evidence.json` y cuatro HTML; actualizar fingerprints y tests. No editar números a mano.

## CHERRY_PICK_ORDER

Sobre una rama nueva desde `46c1a48…`, aplicar Work 1 en orden:
`6217ecd`, `7228bbf`, `47362d3`, `171b6cb`, `d6a60b7`, `eae3b70`, `448009b`, `fddcf05`, y el commit final de handoff.

Después aplicar Work 3:
`6e8a7ae` → `9639e8b` → `09478c8` → `36d1842`, resolviendo únicamente la reconciliación de snapshot descrita. No merge/cherry-pick ciego y no tocar main/PR #9 sin aprobación.

## POST_INTEGRATION_COMMANDS

```sh
python scripts/ops/verify_runtime_identity.py
python -m pytest -o addopts= -q
node --test tests/e2e/contract_flow.test.mjs
node --check scripts/jury_view.js
node --check scripts/build_jury.mjs
python scripts/benchmark/verify_jury_results.py --output work/jury-gate.json
python scripts/release/verify_final_artifacts.py
python scripts/ops/verify_package.py
python scripts/ops/compute_source_health.py --output work/source-health.json
python scripts/evaluation/evaluate_next.py --output-dir work/next
python scripts/benchmark/full_validation.py --output-dir work/full-validation
python scripts/ops/verify_runtime_identity.py
```

Además: regeneración byte-reproducible de producto, inspección visual de las cuatro superficies, CI Linux/Windows sobre el SHA integrado y smoke privado P1/P2/P3 solo si el runner está operativo.

## RUNTIME_IDENTITY_CHECK

Debe ser PASS antes y después. El gate compara 12 archivos byte a byte con `195b498…`; cualquier cambio invalida la evidencia histórica y exige nueva versión/pruebas. NEXT/producto no entra en STUDIO_CONTEXT_FILES ni ZIP.

## FINAL_RELEASE_GATE

0 Critical, 0 High, ambos Medium revisados, contratos/datos/trazabilidad/goldens/regresión/artefactos PASS, CI Linux+Windows PASS y aprobación humana. Si el portal sigue ocupado: `INFRASTRUCTURE_BLOCKED`, no PORTAL GO. Publicar Entrega es una acción humana separada. Este documento no autoriza merge ni publicación.
