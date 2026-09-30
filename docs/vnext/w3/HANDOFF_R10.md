# W3 R10 — handoff de aceptación independiente

**RELEASE_GO_NO_GO: NO_GO. MERGED_OR_PUBLISHED_RELEASE: NO.**
Producto sanitario offline aceptado; agente sanitario integrado y conversaciones reales pendientes.

## Identidad y checkpoint

- Rama: `work/vnext-w3-product-redteam`; [PR #14](https://github.com/Asier-Comba/Guipuzkoa360/pull/14).
- START_SHA: `e821341ba1ffd8ed7947cdb97802348919ef502a`.
- HEAD de código validado: `a91b6808b8da4c4fde9fa8db831747eee78ae14b`.
  HEAD final del handoff/remote y todos los commits se registran en el comentario
  final del PR, evitando incluir un SHA autorreferente dentro de su propio commit.
- Commits de código: `9ec4063` producto/retest; `1de0dfd` smoke/captura/tests;
  `a91b680` hashes portables/LF. El siguiente commit cierra solo documentación.
- Base/main ancestral: `e213eaa9b73b0f8a4d1893e0269fe92fe6756955`;
  v4 runtime congelado `195b4980fa5998b096c308296a55e452380b0371`.
- W2 publicado y retestado: `8272988566f5bca2d65d3119732bf831d11382dc`;
  ZIP `366cdc7d160ee6743cb125c6709f57e48f6ddfb91ead812a92eb881570233357`,
  movilidad stop-only 0.2.0. **No es el ZIP sanitario integrado.**
- W1 runtime: `cb061a97e78d6b5c967104fef6b935132fdc450f`,
  `prototypes.ir_y_volver.provider_r6`, 0.3.1;
  ZIP `c66d44af702eb3410fcea05ae8711f537214f675e83a7fda38c39c3b39a1b910`.
- Evidencia de productor extraída del soporte `6ebf41e2f1fe24f1c3678c4be13c6c44cf8cb62b`;
  errata/support R10 auditado desde `6e284aff347cfcf5fbb3d7eb9cb89a227b83e0d5`.
  Último fetch antes de cierre: estos dos HEADs publicados seguían fijados.
- UI: `health.html`, SHA `50638aa11c98e7bdecf48180c5a7d77ceb1c8c3a095ffea6eb553f29e4ed86d8`.
- Contrato de importación: `W3-HEALTH-QUERY-1`; trazas/scorer `W3_TRACE_2.1.0`/2.1.0.
- Modelo/configuración: **no disponibles**, sin recursos nuevos autorizados.

[RELEASE_READINESS_R10.json](RELEASE_READINESS_R10.json) contiene estados, SHA de
cada evidencia, corpus e identidades separadas. [RESUME_R10.json](RESUME_R10.json)
permite reanudar sin reinterpretar resultados históricos.

## Resultado ejecutado

| Gate | Estado y alcance |
|---|---|
|PRODUCER_READY|PASS: punto oficial modelado sanitario, no puerta verificada|
|CONTRACTS_RETESTED|PASS: cinco probes conocidos verifican tres raíces corregidas|
|ASSEMBLY_READY|BLOCKED: falta paquete conjunto W2 0.3.1; imports portal no ejecutados|
|MODEL_INTERFACE_READY|BLOCKED: modelo no recibe aún interfaz sanitaria W2 aceptada|
|LOCAL_LLM_STATUS|BLOCKED: modelo/dependencias/permiso/presupuesto ausentes; contador 0|
|PORTAL_STATUS|NOT_RUN; formato leído PARTIAL_READ_ONLY; mutaciones 0|
|HUMAN_REVIEW_STATUS|NOT_RUN; revisión W3 no sustituye evaluación humana|
|V4_COMPARISON_STATUS|NOT_RUN; cero pares comparables, sin superioridad declarada|
|RELEASE_GO_NO_GO|FAIL / NO_GO|

W2: C-R3-01 sustitución municipal rechazado; C-R3-02/04/09 tasas sin fuente del
numerador eliminadas también de `public_result`; C-R3-03 unidad «municipios».
Positivos Aduna/Tolosa/coincidencia preservados; ocho tasas atribuidas de Tolosa.
Tres defectos raíz, no cinco. OFFLINE_TOOL desde ZIP exacto/extracción limpia,
no routing, LLM ni conversación. Históricos R2/R4 no se borraron.

W1: 26 miembros del ZIP revisados y ocho solicitudes / cinco estados. Contraste
propio con filas GTFS originales por trip/stop/sequence, pickup/dropoff/timepoint,
longitudes sobre geometría fijada y fórmula publicada. No oracle de W1 para decidir
aceptación. Resultado 09:30: 10.691 s; 09:45: 8.591 s; **−2.100 s / −35 min**,
escenario condicionado, no ahorro real observado/garantizado. No optimalidad global,
puerta física, cita disponible, puntualidad o accesibilidad universal verificadas.
Schemas validados con jsonschema en entorno aislado CPython 3.12; no deps globales.

Support R10: referencias por hash/bytes; 9/25 entradas disponibles, 11 UNAVAILABLE,
5 OUT_OF_SCOPE. No contar preguntas de answerability como tools. Mapping externo
unknown por `status+error.code` aceptado; UI conserva error observado. Medio inline
legacy todavía date-specific: notificado en PR15 y mitigado por mapping externo.

## Tests, reproducibilidad y límites de sus cifras

- Full suite: **303 Python passed**, 0 failed, 19,87 s, CPython 3.14.7.
- Node: **32 passed**, 0 failed, Node 24.19.0: 17 contrato end-to-end v4,
  7 importador histórico y 8 importador sanitario 0.3.1.
- Jurado `verify_jury_results.py`: PASS; artefactos `verify_final_artifacts.py`:
  PASS, incluida identidad v4, HTML/datos contra recálculo y nueve mutaciones.
- HTML sanitario reconstruido byte a byte, evidencia embedded igual al JSON fijado.
- Después del fix de finales de línea: seis tests dirigidos de integridad/captura
  y retest W2/support pasan. No se suman como 309 tests distintos.
- Un fallo inicial de test W3 leyó raw_rows como dict en vez de lista; se corrigió
  el lector del test, sin modificar resultados ni expected de los corpus.
- No full benchmark nuevo; ningún resultado de tests se denomina fiabilidad universal.

Comandos exactos y detalles en `resultados/vnext/r10/test_results.json` y
[ACCEPTANCE_R10.md](ACCEPTANCE_R10.md). Para revisar el pin:

```powershell
python -m pytest -o addopts='' -q
node --test tests/e2e/contract_flow.test.mjs tests/vnext_redteam/import_contract.test.mjs tests/vnext_redteam/health_contract.test.mjs
python scripts/benchmark/verify_jury_results.py
python scripts/release/verify_final_artifacts.py
python -m scripts.vnext_product.build_health_visual
python -m scripts.vnext_product.local_smoke_r10
```

Corpus sin cambio de expected: desarrollo 48, conversaciones 20, holdout 12.
Hashes 40ec6a2e… / ca1dcb32… / 4dda5972… completos en readiness. Holdout:
solo comprobación de hash, sin abrir casos ni ejecutar para ajuste. Gold documental
R4 30 preguntas intacto, hash 41bc6823…; B1 W2 tiene cuatro docs del repositorio,
no S1/S2/S3. Sin corpus idéntico: RAG_NO_GO, no evaluación comparable/generación.

## Producto y navegador

[health.html](../../../resultados/vnext/health.html) autocontenido y offline;
no recalcula rutas en JS. Conserva UI histórica 0.1/0.2. Importación separada
0.3.1, fuentes/defaults/binding/IDs comprobados, null no se convierte en cero;
compatibilidad no autentica procedencia. Comparación guardada se oculta al importar
u otro escenario fuera del par 09:30/09:45. Timeline, paradas, fuentes/periodos,
límites y supuestos visibles; no HTML/PADI completos republicados.

[BROWSER_REVIEW_R10.md](BROWSER_REVIEW_R10.md): cinco tamaños solicitados y sus
CSS efectivos, móvil 355px efectivos, cero overflow de página; tabla scroll interno.
Tab/Shift+Tab/Enter/Space, foco, detalles, estados de fallo, fuentes e importación
válida/rechazo atómico comprobados. Cero console error/warn observados. Sin WCAG,
reader audit, disponibilidad remota de todos los enlaces ni certificación 125%/150%.

[Ficha/guion de 3 min](JURY_FICHE_R10.md): pregunta, variación, profundización,
límite, cifra contrastada y fuentes. Hasta tener traza real, presenta ejecución del
productor offline; no chat inventado ni agente funcional en portal por inferencia.

## Intentos reales, permisos y bloqueos

LOCAL_LLM=0, PORTAL_LLM=0, conversaciones ejecutadas=0, casos individuales
puntuados=0. `score_runs` devuelve NOT_RUN: no porcentaje de victoria.
[SMOKE_PLAN_R10.json](SMOKE_PLAN_R10.json) fija 12 conversaciones / 36 turnos
con cuatro probes auxiliares separados de los denominadores. Runner por turno
captura agente real y todos los fallos/reintentos con autorización/modelo/assembly
fijados, caps por turno y lote. No tiene validación real de captura→W3_TRACE todavía;
la transformación y revisión requieren argumentos/IDs/bindings observados, no
rellenar un assistant final ni duplicar request_id desde el output para simular input.

[Solicitud portal](PORTAL_TEST_REQUEST_R10.md) redactada y **bloqueada hasta SHA
conjunto fijo**. No se pidió autorización prematura; no ejecutar escritura/pruebas
sin gate humano específico y presupuesto. Formato leído: 100 MB/archivo, 24 MB
paquete ejecución, 10 tools, nombre 2–80, instrucciones 10–8.000; unidad/base del
límite, extracción ZIP/import closure/memoria/fingerprint de versión no probados.
No asumir causa HTTP/red si preparación falla. No tocar Entrega/track/v4 ni reset.

Critical/High **observados** pendientes en los pins/probes retestados: ninguno.
No extiende esa conclusión al candidato conjunto o modelo que no se ejecutaron.
Medium: W1 DERIVED explanatory DAG externo; W1 inline unknown heredado;
formato portal necesita smoke autorizado; captura real y comparación pendientes
como blockers, no incidentes fabricados.

## Siguiente acción exacta / archivos para W1 y W2

1. W2 publica un **ZIP conjunto sanitario** con main/tools/módulos/contextos,
   health capabilities/model schema, manifest y SHA exactos. No HEAD móvil mezclado.
2. W3 valida miembros/hashes, sin secretos/holdout/páginas completas; extracción
   limpia, tools generadas, contract/public_result, catálogo/labels/defaults y límites.
3. Con esa identidad aceptada, completar solicitud única de versión privada y smoke
   con permiso humano/modelo/presupuesto. Ejecutar un turno por revisión; Critical/High
   detiene lote afectado, reproduce, asigna propietario y exige nuevo candidato.
4. Capturar trazas 2.1.0 observadas, comparar capacidades comunes con v4 en condiciones
   equivalentes y tareas sanitarias nuevas como utilidad adicional; revisión humana.
   No mezclar fuentes nuevas bajo una afirmación de razonamiento idéntico superior.

Para W1/W2: ACCEPTANCE_R10.md, support_review.json, health_review.json,
health_evidence.json, w2_retest_report.json, PORTAL_DEPLOYMENT_CONTRACT_R10.md,
RELEASE_READINESS_R10.json, SMOKE_PLAN_R10.json y PORTAL_TEST_REQUEST_R10.md.
Comentarios hitos en PR17/PR15; publicación final en PR14 e Issue16.
Todos los cambios están dentro de rutas W3. Runtime W1/W2/v4 y dependencias globales
sin cambios. Commit/push propio; no merge ni release publicado.
