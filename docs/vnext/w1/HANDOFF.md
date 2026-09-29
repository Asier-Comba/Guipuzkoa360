WORK_ID: W1

ROUND: G360-R2

STATUS: READY_FOR_REVIEW

BASE_SHA: e213eaa9b73b0f8a4d1893e0269fe92fe6756955

MAIN_OBSERVED_SHA: e213eaa9b73b0f8a4d1893e0269fe92fe6756955 (verificado en remoto antes de publicar)

BRANCH: work/vnext-w1-mobility

TESTED_HEAD: d7793ffa8bfb5d1f9044a7e317515e32f5b31f1d

PUBLISHED_HEAD: registrar después de este commit en la PR y en la respuesta; no se autorreferencia este archivo

CONSUMED_WORK_HEADS: ninguno; rama creada directamente desde BASE_SHA literal

CONTRACT_VERSIONS_AND_HASHES: `ir_y_volver` 0.1.0; capabilities `ecbb5f012818528ebf4efd51fb7b95720a37fa91ff8da1d105905f22fd50b9d9`; request `60e9c0f6bbc1a8ee7e254a36dc6ffd1e4d1c7b22d78178b4b85890b328e41c44`; result `2b2034999e887e89ed9252b02d1fdbb5efeb8763789add3fb65e9ffff9f6ff1d`

SOURCE_COVERAGE_AND_GAPS: GO para GTFS estático oficial Goierrialdea, GO01 y fecha validada 2026-09-29 entre paradas catalogadas de Zegama/Segura/Idiazabal y centro de Beasain. Fuente ZIP 811.289 bytes, SHA-256 `3276fcae7bfa5002a39a2a094fef6637603de2e50648a46a436b314db27832a4`. `ORIGINAL_POC_REPRODUCTION=BLOCKED`: no están los bytes del ZIP/OSM original, no se reproduce el Ambulatorio, 135 escenarios ni 14 tests históricos. Otras fechas, realtime, puerta a puerta, accesibilidad, transbordos y demografía quedan fuera o pendientes. Detalle en `DATA_GO_NO_GO.md`, `SOURCE_COVERAGE.md` y `REALTIME_RESEARCH.md`.

FILES_CHANGED: `docs/vnext/coordination/LAUNCH_R2.md`; `docs/vnext/w1/**`; `prototypes/ir_y_volver/**`; `scripts/mobility/**`; `tests/mobility/**`. Ninguna ruta de agente, runtime v4, datos v4, UI, workflow o dependencia global.

IMPLEMENTED: contrato 0.1.0; `get_capabilities`, `plan_visit`, `compare_visits`; defaults catalogados; validación estricta; cinco estados; calendarios/excepciones; permisos pickup/dropoff; orden de paradas; HH>24; búsqueda directa completa; componentes disjuntos; trazabilidad de trip/service/stop/sequence/timepoint; no confusión entre fallo de datos y ausencia de viaje; comparación 2–32; snapshot oficial compacto y regenerable; 10 casos reales; descriptor para W2; investigación realtime sin habilitarla.

TESTS_EXECUTED: Windows, Python 3.12.4, Node 24.12.0. `python -m pytest tests/mobility -q -o addopts=` → PASS 48/48. `python scripts/mobility/verify_w1.py --iterations 200` → PASS 10/10 casos; 200 ejecuciones, mediana 41,679 ms, p95 53,386 ms, máximo 65,113 ms; payload 2.548–2.559 bytes. `python -m pytest -o addopts= -q` → PASS 312/312 en 46,82 s. `node --test tests/e2e/contract_flow.test.mjs` → PASS 17/17. `verify_runtime_identity.py` antes y después → PASS. `verify_jury_results.py` → PASS. `verify_final_artifacts.py` → PASS. JSON de contratos/snapshot/evidencia → parse PASS. `git diff --check` → PASS.

TESTS_NOT_RUN_AND_REASON: los 14 tests y 135 escenarios históricos no pueden ejecutarse sin el paquete original; no hay prueba OSM del paseo al Ambulatorio; no se prueba realtime ni portal porque no forman parte del runtime 0.1.0; no se extrapolan otras fechas nominalmente cubiertas. El benchmark masivo v4 no se repitió porque W1 no cambia ningún byte de su runtime y la identidad antes/después pasó.

FINDINGS: W1-F01 MEDIUM, falta paquete original; reproducción: buscar `poc_DeustoAILabs_horarios.zip`; evidencia: búsqueda en repo/adjuntos sin resultado; propietario: humano/fuente PoC. W1-F02 MEDIUM, ficha oficial sin SPDX específico; evidencia: enlaza a Información legal y términos generales de reutilización; propietario: humano/legal. W1-F03 MEDIUM, `timepoint=0` en GO01 y sin `calendar_dates.txt`; evidencia: filas fuente y snapshot; propietario: W1/datos, mitigado con scheduled+limitaciones. W1-F04 MEDIUM, realtime publicado pero no integrado/validado; propietario: futura ronda. W1-F05 LOW, destino piloto es centro de Beasain y no Ambulatorio; propietario: producto/W2 para comunicar el alcance. Critical=0; High=0.

DATA_RUNTIME_PACKAGE_IDENTITIES: manifiesto `docs/vnext/w1/RUNTIME_MANIFEST.json`; 8 archivos, 825.670 bytes; snapshot 804.348 bytes SHA-256 `30fc9d638f3576ae0e1084ee1e0c7b0268469bffc8af1dd15fd12430019d968b`; ejecución offline, sin ZIP bruto ni HTTP.

V4_PRESERVATION_EVIDENCE: `verify_runtime_identity.py` PASS antes y después; identidad congelada `195b4980fa5998b096c308296a55e452380b0371`; suite completa 312/312, Node 17/17, jury gate PASS y artifact gate PASS. El diff desde BASE_SHA está limitado a rutas W1 autorizadas y `LAUNCH_R2.md`.

DEPENDENCIES_AND_CONTRACT_REQUESTS: W2 debe importar las tres entradas de `prototypes.ir_y_volver`, leer `CAPABILITY_DESCRIPTOR.json`, conservar `sources/assumptions/limitations`, y no tratar `unknown` como ausencia de autobús. W3 debe usar `REAL_CASES.json` y añadir casos no viables. Cualquier cambio de nombres/semántica requiere contrato versionado nuevo. No hay nueva dependencia Python ni red en runtime. Acción humana opcional: aportar el ZIP original y revisar el matiz legal antes de redistribución externa.

PR_AND_CI: draft PR hacia `integration/vnext-2026-10-04` pendiente de apertura tras publicar PUBLISHED_HEAD; la integración apunta a BASE_SHA y no ha recibido commits. CI remoto pendiente del evento PR; pruebas locales completas verdes.

REMOTE_MUTATIONS: creadas `integration/vnext-2026-10-04` en BASE_SHA y `work/vnext-w1-mobility`; primer commit contractual `c06903c94a6c87f19bdf7feaa8172ce5ad6091f2` publicado. No force-push, merge, cambio de default branch ni edición de ramas ajenas.

PORTAL_MUTATIONS: ninguna

NEXT_EXACT_STEP: publicar el commit de handoff, abrir draft PR `work/vnext-w1-mobility` → `integration/vnext-2026-10-04`, esperar CI y entregar a W2/W3 el descriptor, manifiesto y casos reales sin integrar todavía.

HUMAN_ACTION_REQUIRED: revisar el draft PR; decidir si se acepta el riesgo de licencia sin SPDX; facilitar el paquete original solo si se exige reproducir literalmente la PoC histórica.

MERGED_OR_PUBLISHED_RELEASE: NO
