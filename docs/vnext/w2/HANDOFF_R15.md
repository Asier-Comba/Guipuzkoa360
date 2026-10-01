# W2 R15 — candidato offline; aceptación real pendiente

Rama `work/vnext-w2-r15-final-agent`. BASE_SHA=`094745b26bc57aee5cc1a5e003401743d96a914f`.
HEAD final y CI del mismo SHA se publican en el handoff del PR R15, sin autorreferencia dentro del commit.
No Studio, Entrega, track, holdout, merge ni cambio de v4. No se transfiere ningún PASS R14 a R15.

## Identidad canónica

| Elemento | Valor |
| --- | --- |
| ZIP | `scripts/vnext_agent/dist/r15/gipuzkoa360-r15-final-agent.zip` |
| ZIP SHA-256 | `f937ed8124ba1107c78d2a516c5404626a97b9efe38b576a03b6cd98f781efd0` |
| Tamaño | 228025 bytes; 789207 expandidos |
| Manifest | `scripts/vnext_agent/dist/r15/gipuzkoa360-r15-final-agent-manifest.json` |
| Manifest SHA-256 | `95c78e2a26ae8a55e0e6ec772905e04a74620d2c18b282a605522ff0154eed76` |
| main.py SHA-256 | `5d08e34bfefc9a5cca43f6ea9af09d4e71f0b0f64cad0b38449bbfb19640fb34` |
| tools.py SHA-256 | `49b0fb3f0e09c7d10132ba803a0e8274f9188ffcff7b466f6f6775f577cce3de` |
| W1 ZIP sin cambios | `c66d44af702eb3410fcea05ae8711f537214f675e83a7fda38c39c3b39a1b910` |
| v4 protegido | `195b4980fa5998b096c308296a55e452380b0371` |

El manifest enumera los 25 miembros exactos y su diff SHA a SHA: solo cambian main.py/tools.py.
Los 15 assets declarados (266742 bytes) son byte-idénticos a R14; sus hashes están también en FINAL_MANIFEST de entrega.
`build_r15.py` lee R14 por Git/hash, conserva inventario y solo trasplanta cuatro funciones W2: `_validate_arguments`, `_effective_request`, `_mobility_catalog_view`, `_public_result`.
R14 no se pisa; motor territorial/W1, GTFS, routing, walking, fórmulas y datos no cambian. Tests/conformance históricos del ZIP son audit-only, no contexto del modelo; regresiones R15 van fuera del paquete.

## Contrato y correcciones

PUBLIC_AGENT_CONTRACT: `plan_visit(origin_id: str, destination_id: str, date: str, appointment_time: str, duration_minutes: int) -> str`.
Cinco obligatorios, sin request anidado, batch, `**kwargs` u opcionales. El wrapper conserva los valores exactos; no repara ni convierte basura.
ENGINE_CONTRACT conserva deadline, snapshot, perfil, márgenes, legacy explícito 0.2.0 y batch interno 2–4. Defaults siguen en el productor/MODEL_DEFAULTS; un argumento del agente no demuestra elección humana.
Comparación pública: llamadas individuales, observar outputs, comparar solo resultados válidos compatibles. Entre orígenes: lado a lado sin delta. Diferencias del mismo origen son condicionales, nunca ahorro observado ni recomendación.
Nueve tools con escalares/listas de strings; catálogo público coincide con firmas. La auditoría infiere esquema local, no schema completo servido en Studio.

Reproducción publicada antes de parchear: [Issue16](https://github.com/Asier-Comba/Guipuzkoa360/issues/16#issuecomment-5927721280).
`R15_PERIOD_REPRODUCTION.md`: exact-empty ya fallaba cerrado; whitespace/fechas no soportadas daban cifras en acceso/simulación.
`R15_ADVERSARIAL_REPRODUCTION.md`: service_id whitespace, argumentos de otra acción ignorados y umbral 0/None sin categoría. Se valida frontera/nullabilidad/coherencia con límites existentes, sin alterar cálculo.
Inputs inválidos producen error sin claims autoritativos, outcomes parciales engañosos ni raw válido. Campos públicos inexistentes fallan en binding antes del motor; esto no se presenta como envelope de dominio.
El replay interno de M05 mantiene `mobility:invalid_clock`; quitar el opcional del contrato público no equivale a tolerarlo en el motor.

Periodos: resumen/comparación/envejecimiento/coincidencia seleccionan demografía (`2025-01-01`); omitido/None usa el único periodo, y si hubiera varios exige elección, nunca “latest”.
Acceso/simulación admiten referencias `2026-09-20`/`2025-05-07`, no filtrado histórico; omitido/None conserva periodos distintos. `period_policy`/allowed_values/nullabilidad reflejan esa diferencia.
`consultar_fuente` proyecta el method existente junto a periodo/limitaciones. Derivación 75+ accesible, sin cambiar números/raw/fuentes; véase `R15_SOURCE_PERIOD_VIEW_REVIEW.md`.
Prompt limpio: intención, tools reales, observar outputs, recalcular follow-up, fuente/periodo/derivación breve, abstención y recuperación acotada sin repetir llamada inválida idéntica. Conserva límites y frontera de documentos no confiables; ningún gold.

## Evidencia final y denominadores

| Gate | Estado |
| --- | --- |
| Focal source final | 183 PASS /16.60 s: 127 periodo +45 R15 +11 R14 histórico |
| Artifact final | 2 PASS /4.36 s; doble build ZIP/manifest idénticos, generado y regresiones |
| Auditoría final dirigida | PASS: 333 casos, 101 paridad raw/vista, 7 oracle, 231 inválidos, 42 periodos, 17 fuentes |
| Ejecuciones de auditoría | 331 R14 +326 R15, dos procesos fríos, sockets denegados, 0 modelo, 0 findings /86.969 s |
| Python completo local | 552 PASS /169.25 s; una única suite completa local, 0 failures/errors/skips |
| Node | 17/17 PASS; tres comprobaciones de sintaxis PASS; Node local 22.20.0 |
| v4 antes/después; jury/artifact; diff | 14/14 archivos protegidos byte-idénticos antes/después; jury PASS, artifact 7/7 PASS, diff check PASS |
| CI Ubuntu / Windows | REQUIRES_EXACT_HEAD_CI_IN_FINAL_HANDOFF |

`R15_AUDIT.json` SHA-256 `3a5bde7c5bbcc49920214f540f446e87eb728a7902d3bb37a19b567ded076578`; script `7f4a8bcfa44680e25a8a0ebe053cd2848eb3b7582785153df21321ca33e91324`.
Paridad raw exacta; vista normaliza solo hash de código y nuevo source_metadata.method (contrastado aparte con raw). Oráculo `2f57634fcab245a63c95b2a4e833895f664b8a43b52592214470b913b6b1ba53`: MAIN10691 s, VARIATION8591 s, segundo−primero −2100 s/−35 min.
56 focales iniciales y 12 generated/157.32 s sobre build intermedio no se suman ni transfieren al ZIP final. Errores de entorno/autoría de tests, intentos y rerun final están en `ATTEMPTS_R15.md`.

## Reproducir doce gates en orden

Checkout del HEAD exacto con historial Git completo, CPython3.12 y requirements existentes; CI usa 3.12.10/Node24.12.0, local 3.12.14.
Usar un intérprete CPython 3.12 real con pytest/dependencias disponibles; en Windows comprobar la ruta resuelta, no asumir que el launcher Store es ejecutable. No hacen falta rutas del perfil del autor.
Los comandos siguientes usan `python` para ese intérprete (PowerShell: `& $r15Python`). Usar directorios basetemp nuevos, vacíos y dentro de work; nunca carpetas con archivos propios.

1. Focal: `python -m pytest tests/vnext_agent/test_r15_period.py -q -o addopts= -p no:cacheprovider --basetemp=work/r15-reproduction-01`.
2. R13/R14: `python -m pytest tests/vnext_agent/test_r14_binding.py tests/vnext_agent/test_r15_public_contract.py -q -o addopts= -p no:cacheprovider --basetemp=work/r15-reproduction-02`.
3. Contrato: `python -m scripts.vnext_agent.verify_r15 --package scripts/vnext_agent/dist/r15/gipuzkoa360-r15-final-agent.zip --output work/r15-reproduction-audit.json`; revisar public_contract.status PASS y firmas/catálogo.
4. Parity/oracle: revisar las filas de paridad y oráculo del mismo reporte; raw exacto y valores anteriores. El audit de pasos3–5 se ejecuta una vez, no tres.
5. Adversarial: mismo reporte, cero findings, errores seguros/binding/límites/failure recovery; no benchmark gigante ni LLM/holdout.
6. Package: `python -m pytest tests/vnext_agent/test_r15_artifact.py -q -o addopts= -p no:cacheprovider --basetemp=work/r15-reproduction-06`; exige doble build idéntico. Builder manual: `python -m scripts.vnext_agent.build_r15`.
7. Python completo una vez local: `python -m pytest -q -o addopts= -p no:cacheprovider --basetemp=work/r15-reproduction-full --junitxml=work/r15-pytest.xml`.
8. `node --test tests/e2e/contract_flow.test.mjs`; `node --check scripts/jury_view.js`, `scripts/build_jury.mjs` y `scripts/build_results.mjs`.
9. `python scripts/ops/verify_runtime_identity.py`, además del control previo al ciclo.
10. `python scripts/benchmark/verify_jury_results.py --output work/r15-jury-gate.json`; `python scripts/release/verify_final_artifacts.py`.
11. `git diff --check`; comprobar hashes/ausencia de cambios de regeneración, sin descartar cambios ajenos.
12. CI del HEAD exacto: Ubuntu/Windows Release fast CI y vNext candidate validation. Publicar SHA, runs y estado del mismo SHA; nunca un PASS histórico ni pending.

## Handoff humano

Final_delivery importa solo los cuatro documentos PR19 `3a8e2b0948bb06df87af7a0f5769a369da568eff`: coherencia técnica corregida, copy/cifras/fuentes/licencias preservados; Hugo revisa producto. Los reportes W1 R14 quedan en historical_r14, no como auditoría R15.
W3 `f4fd0a3c79ff2827c19a1200c0c76f7c5815eab7`/M05 sigue como última evidencia real: Critical0/High1/Medium3 OPEN, schema completo NOT_OBSERVED. No se atribuye causa a Studio/Luna sin evidencia.
Portal5/12 usado,7 restante. HOLDOUT=SEALED; PORTAL_REAL_AGENT=NOT_RETESTED; RELEASE_GO=NO. Sin Studio, Entrega, track, merge ni v4.
NEXT_EXACT_ACTION=W1 accepts exact R15 bytes independently; then Hugo/W3 performs the bounded real Studio retest.
