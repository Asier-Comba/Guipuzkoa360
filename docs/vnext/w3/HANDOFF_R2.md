# GIPUZKOA 360 · W3 R2 · handoff verificable

WORK_ID: W3

ROUND: G360-R2

STATUS: PARTIAL — producto y corpus revisables; comparación v4↔vNext aún `NOT_RUN`.

BASE_SHA: `e213eaa9b73b0f8a4d1893e0269fe92fe6756955`

MAIN_OBSERVED_SHA: `e213eaa9b73b0f8a4d1893e0269fe92fe6756955`, `origin/main` consultado el 29/09/2026.

BRANCH: `work/vnext-w3-product-redteam`

TESTED_HEAD: `2aa0794d12d4711a71fe7e886e809d1433bc275e` (tests locales sobre exactamente este contenido de código y artefactos; este handoff es posterior y solo documental).

PUBLISHED_HEAD: SHA del commit de este handoff registrado después de publicarlo en un comentario de [PR #14](https://github.com/Asier-Comba/Guipuzkoa360/pull/14); se evita la autorreferencia.

CONSUMED_WORK_HEADS: W1 `c68eb5c55dec72a267b7435b4c364049f6eab408` en checkout aislado y de solo lectura; generalized `7e864f4da3a529b5648444700e7148f3ae2304b5` solo para 36 prompts. W2: ninguno disponible. No se integraron commits ajenos.

CONTRACT_VERSIONS_AND_HASHES: W1 `ir_y_volver` 0.1.0; capabilities `ecbb5f012818528ebf4efd51fb7b95720a37fa91ff8da1d105905f22fd50b9d9`; request `60e9c0f6bbc1a8ee7e254a36dc6ffd1e4d1c7b22d78178b4b85890b328e41c44`; result `2b2034999e887e89ed9252b02d1fdbb5efeb8763789add3fb65e9ffff9f6ff1d`. W3 evidencia `W3-PROVIDER-EVIDENCE-1`; contrato agente W2 pendiente.

SOURCE_COVERAGE_AND_GAPS: [matriz de fuentes](SOURCE_AUDIT.md). Feed oficial GTFS GO01, fecha validada 29/09/2026, paradas de Zegama/Segura/Idiazabal ↔ centro de Beasain; no Ambulatorio, domicilio, realtime, capacidad ni citas. Portal leído sin escritura; Entrega privada conserva v4. Paquete privado 00–12, correos/feedback literal y ZIP PoC original no montados; el progreso formativo histórico 55/73 no se cambia. Incidente 50+/504 reportado pero no reproducido ni atribuido a HTTP.

FILES_CHANGED: únicamente `resultados/vnext/**`, `scripts/vnext_product/**`, `tests/vnext_redteam/**`, `docs/vnext/w3/**`; diff desde BASE_SHA auditado.

IMPLEMENTED: corpus de 48 casos de desarrollo y 20 conversaciones de tres turnos congelados antes de salida W2; holdout de 12 preguntas en archivo privado con hash público; export reproducible de cinco resultados **reales del proveedor determinista offline W1**; HTML autocontenido con pregunta, ida/vuelta, total y componentes con unidad, fuente, huellas, supuestos y estados `ok`/`no_feasible_journey`/`unknown`; scorer de trazas observadas con primeras tentativas, errores, comparabilidad y `NOT_RUN` sin LLM; [guion](PRODUCT_REVIEW.md), [CityScope](CITYSCOPE_SCOPE.md) y [QA visual](BROWSER_REVIEW.md). No se ejecutó un agente vNext.

TESTS_EXECUTED: Windows; Python 3.14 del entorno local `product-jury-qa-env`: `python -m pytest -q -o addopts=` → PASS **269/269** en 18,14 s. Node 24: `node --test tests/e2e/contract_flow.test.mjs` → PASS **17/17**. Python 3.12: `scripts/ops/verify_runtime_identity.py` → PASS 14/14 archivos congelados; `scripts/benchmark/verify_jury_results.py` → PASS; `scripts/release/verify_final_artifacts.py` → PASS. `export_w1_evidence.py --w1-root <checkout W1 c68eb5c>` → PASS, cinco outputs `ok` ×3, `no_feasible_journey`, `unknown`; `build_visual.py` → PASS y hash HTML estable. `score_runs.py` con y sin holdout → `NOT_RUN`, 0 intentos LLM, targets 48/60. Navegador y teclado: [matriz observada](BROWSER_REVIEW.md). `git diff --cached --check` → PASS antes del commit de producto.

TESTS_NOT_RUN_AND_REASON: corpus A/B 60/60, 20 conversaciones, p50/p95 de tool/LLM y revisión humana de respuestas: `BLOCKED`, sin candidato W2 fijado ni autorización de escritura en portal. No prueba de versión vNext, paquete integrado ni CityScope pareado. Zoom 125/150 %, lectores de pantalla y navegadores alternativos no probados. `python -m pytest` del Python 3.12 aislado no arrancó por ausencia de pytest; se usó el entorno QA con pytest para la suite completa.

FINDINGS: W3-F01 **HIGH/bloqueo de aceptación**: no existe rama/PR/paquete W2 fijado. Reproducción: listar ramas remotas; solo W1 y W3 vNext, sin W2. Evidencia: `git ls-remote origin` 29/09/2026; propietario W2/coordinación. W3-F02 **MEDIUM/cobertura**: paquete privado 00–12 ausente; búsqueda de adjuntos y workspace sin los archivos; propietario humano/fuentes. W3-F03 **MEDIUM/atribución**: 50+/504 sin traza reproducible; no se acepta una causa técnica ni se cambia expected; propietario coordinación/portal al proporcionar versión, tool, argumentos, salida y tiempos. W3-F04 **MEDIUM/alcance**: paseo `stop_only` de 0 s y destino centro de Beasain pueden leerse como puerta a puerta; mitigado por copy visible y [revisión adversaria](PRODUCT_REVIEW.md); propietario W3/W2 para conservar matiz en respuestas. Hallazgos Critical confirmados: 0; un HIGH de dependencia sin resolver.

DATA_RUNTIME_PACKAGE_IDENTITIES: v4 congelado `195b4980fa5998b096c308296a55e452380b0371` verificado byte a byte. W1 provider HEAD `c68eb5c55dec72a267b7435b4c364049f6eab408`; snapshot SHA-256 `30fc9d638f3576ae0e1084ee1e0c7b0268469bffc8af1dd15fd12430019d968b`; GTFS ZIP fuente SHA-256 `3276fcae7bfa5002a39a2a094fef6637603de2e50648a46a436b314db27832a4`; `provider_evidence.json` SHA-256 `57738bd27f6bbd78cc399d862235df13c1d8d9d2f3f46eaf6e367230e853b0db`; HTML SHA-256 `7775612cfb7debc6cd17d33b92cba18b24df4022e9f39aa52affe170b8a665fc`. Paquete W2/portal vNext: inexistente o no identificado.

V4_PRESERVATION_EVIDENCE: diff desde BASE_SHA solo rutas W3; `verify_runtime_identity.py` PASS 14/14; verificadores de cifras/artefactos v4 PASS; `main` y `gh-pages` sin push W3. En Entrega se observó `urban-challenge-rc2-195b498 · v4` seleccionada, borrador privado; W3 no la cambió.

DEPENDENCIES_AND_CONTRACT_REQUESTS: W2 debe publicar HEAD, paquete/huella, descriptor de herramientas y output real con `status`, `itinerary`, `components_s`, `sources`, `assumptions`, `limitations`; consumir contrato 0.1.0 sin convertir `unknown` en «no hay servicio». Cambios semánticos requieren versión nueva. Coordinación debe fijar candidato integrado y autorizar por separado las pruebas de portal. El paquete privado 00–12 se pide para cerrar cobertura de fuentes.

PR_AND_CI: [draft PR #14](https://github.com/Asier-Comba/Guipuzkoa360/pull/14), base `integration/vnext-2026-10-04`; al crear este handoff CI «Release fast CI» Linux/Windows estaba en curso. Estado final y PUBLISHED_HEAD se registran en comentario del PR tras el push; no hay merge autorizado.

REMOTE_MUTATIONS: creada/publicada rama W3; commits `59bb7c3` (congelación P0) y `2aa0794` (producto/harness), draft PR #14; más el commit documental de este handoff registrado en el PR. Sin force-push, merge ni edición de ramas ajenas.

PORTAL_MUTATIONS: ninguna. Se leyeron Agentes, Pruebas, ayuda y Entrega.

NEXT_EXACT_STEP: W2 publica candidato con HEAD/paquete/contrato; W3 revisa diff y contrato, fija identidad, solicita autorización específica para versión/pruebas del portal y ejecuta corpus pareado (incluido holdout privado después de congelar candidato), conserva intentos y revisa manualmente; después prueba SHA integrado.

HUMAN_ACTION_REQUIRED: facilitar o localizar paquete plano privado 00–12 para auditoría completa; revisar PR #14; autorizar expresamente la creación de versión y las pruebas del portal **solo** cuando exista paquete W2 fijado. La ausencia de esa autorización no impide revisar este PR offline.

MERGED_OR_PUBLISHED_RELEASE: NO


CORPUS_HASH_AND_COUNTS: desarrollo 48 `40ec6a2e25331a2e040b7fedfd3ad75ff7245b508ef30c605d9cc6fdeb5e046a`; conversaciones 20 × 3 turnos `ca1dcb321bc92d2efa42c871e9730926421a375bfeab77edfee696e5ed09f413`; holdout 12 `4dda59721932f620cba53e5686df288f7cf0e0e968ec30540216ffb1f52ec5c0`. Los 60 turnos conversacionales no se suman a los 60 casos individuales.

HOLDOUT_STATUS: guardado en artefacto local privado recuperable por W3 fuera de GitHub; hash revalidado. No se entregó a W1/W2. La ocultación respecto de ellos depende de mantener esa separación hasta congelar el candidato; no se afirma garantía criptográfica de secreto.

V4_VS_VNEXT: `NOT_RUN`; ningún dato de superioridad o regresión. La comparación CityScope tampoco es un benchmark.

LLM_EXECUTED: 0; scorer devuelve `NOT_RUN`, nunca `PASS`.

PORTAL_VERSION_AND_PACKAGE: `urban-challenge-rc2-195b498 · v4` seleccionado en Entrega, 17 ejecuciones terminadas indicadas por la UI y sin evaluar por W3. La ayuda vigente confirma hasta 10 herramientas y 8.000 caracteres de instrucciones; no confirma 24 MB para agente. El editor activo genérico no se atribuye a v4. Versión/paquete W2: `PORTAL_GATE_PENDING`.

LATENCY_AND_FAILURE_COUNTS: ninguna latencia LLM/tool de A/B ni tasa de fallo medida (`n=0`). Cinco ejecuciones deterministas offline W1 reproducidas; tres `ok`, una `no_feasible_journey`, una `unknown` son **estados de caso**, no fallos de plataforma. No se infiere causa de 504 ni fiabilidad general.


**Demostrado:** cinco resultados offline trazables, cambio de hora de −19 s
calculado por proveedor, pérdida de viaje completo al ampliar duración, estado
desconocido honesto, corpus congelado y suite local verde. **Pendiente:**
candidato W2, fuentes privadas, A/B y autorización/evidencia del portal. La
acción inmediata es revisar este PR sin integrarlo como mejora demostrada.
