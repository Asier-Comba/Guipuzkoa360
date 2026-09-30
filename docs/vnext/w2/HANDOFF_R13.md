# GIPUZKOA 360 / DeustoAI Labs — W2 R13

W2_FINAL_CANDIDATE_FROZEN=YES. STOP. NO PATCH4.
Pruebas locales y CI verdes; candidato listo y congelado para W3_REAL_PORTAL.
No se convierte una prueba determinista en aceptación conversacional.

## Identidad y aceptación independiente

START_SHA documental: `fa679248a6239604f56368f384e708a022c09e95`.
CANDIDATE_FROZEN: true. RUNTIME_SHA:
`8c94f8c3cf9d732c4ce94af7b4bef8f6e154c243`.
ZIP_SHA: `3951b290b6ca59c336886a3f0acee77a68036d4fbcbc06c2cedfe22400c08616`,
226010 bytes. MANIFEST_SHA:
`a672bf9a2afece58c468a1f762c860f0217536a2a4fa18737ba768cab755c70a`.
El ZIP, main.py/tools.py, prompt, schemas, APIs, catálogo, capabilities y assets
no cambian. Las reconstrucciones exigidas generan exactamente los mismos bytes:
no existe otro candidato ni identidad PATCH4.

Auditorías/tests off-candidate publicados en
`f7a376b3cee79078cbc8b3f878f6eea3a53fcebb`. El sucesor de cierre contiene evidencia
y documentación; su HEAD publicado se comunica en PR17/Issue16, no se intenta
incluir un hash autorreferencial en el checkpoint.

W1_ACCEPTANCE_PIN: `7f434a469d7f94fdff8ae7d2665644426a217250`.
Se leyeron delta/handoff y patch3_intake_r12.json de ese Git inmutable: 4321325 bytes
LF, SHA `a55a237f1189c3f51bdf0dc7bc484477f28593822de8a9fb28df75a6fca33328`.
PASS: 32/32 raw (30 exactos más dos rechazos controlados), 32/32 model-view,
5/5 comparaciones, 37 escenarios, 1811 assertions, cero findings/verifier errors.
No es aceptación de herramientas territoriales, LLM o portal.
W1 runtime `cb061a9e00a6496c40488a596bd94834bc2c49b2`, ZIP c66d44af y soporte
embebido c9cb37f siguen intactos; leer aceptación nueva no implica modificar el pin.

W3 preflight: `1d60cdf81d3eb7661bc1d97c12425b9bdcf69b8d`.
Avance live leído: `111aff0d9af6fe38255425bfcc8c40eb6b1dc647`, informe
resultados/vnext/r13/offline_review.json, intake y plan de smoke completos.
PASS independiente offline sobre este ZIP: cuatro modos (flat completo,
flat declarado, foreign cwd y nested declarado/foreign cwd), 36 casos por modo,
cero findings, raíz correcta. Contraste propio de filas GTFS/geometría/fórmula
seleccionadas PASS; no optimalidad exhaustiva ni entrada física. Cero llamadas
modelo en el informe. Esto NO demuestra aún montaje/schema/conversación Studio.
Baseline R10 e históricos R12 se conservan sin reinterpretar sus resultados.

## Auditoría de interfaz potencial del modelo

TOOL_SCHEMA_AUDIT: PASS_STATIC_NOT_SERVED, nueve tools. TOOL_SCHEMA_AUDIT_R13.json
se obtiene de los main/tools generados del ZIP en clean room. Registra nombres,
docstrings, tipos, parámetros, required/optional, defaults, nested TypedDict,
schema de anotación, restricciones semánticas y errores del runtime.

El public_result real de consultar_capacidades('plan_visit') permite descubrir
Zegama, Segura, Idiazabal, Ambulatorio de Beasain, fecha 2026-09-29, defaults,
rangos, perfil y comparación 2–4, sin pedir IDs humanos ni esconder esos datos
en documentación no recibida. No se añade routing por frases.

La anotación no codifica todos los enums/rangos. El schema esperado documenta
restricciones que tools/contracts imponen, pero no demuestra que el decorador
de Studio las sirva. Memory on / Internet off / max8 son configuración esperada,
no observación del modelo ni prueba de memoria.

## Schema fuzz y contaminación de estado

SCHEMA_FUZZ_COUNT: 10000. FUZZ_SEED: 360013.
UNCAUGHT_EXCEPTIONS: 0. STATE_SEQUENCE_COUNT: 500.
STATE_LEAK_FINDINGS: 0. Las 3213 llamadas de secuencia pasan en 1448.557 s.
Fuzz: 20000 ejecuciones, cada caso dos veces, PASS en 1867.182 s, cero fallos
de invariantes/excepciones. Dieciséis referencias distintas emitidas resueltas con
consultar_fuente. Máxima vista observada 98315 bytes, bajo el límite de 120000.

El corpus tiene 10000 casos indexados, 3864 payloads de invocación diferentes y
repeticiones deliberadas; no se presenta como 10000 argumentos distintos ni
como cobertura exhaustiva. Incluye las 21 categorías solicitadas y las nueve
tools. Cada caso se ejecuta dos veces para comparar la vista determinista.
La envoltura de despacho es un objeto; wrong types/array-object fuzz afectan
los campos de herramientas. Missing/extra kwargs que Python impide despachar
son un gate de schema, no una llamada exitosa al runtime.

Invariantes: sin excepción escapada, sin claims de evidencia inválida, sin raw
en la vista, sin itinerario parcial autoritativo, payload <=120000 bytes,
status/error determinista, acción segura, sin causa de red inventada y consulta
de cada source emitido. Unknown/unsupported pueden conservar metadatos de
procedencia/scope: eso no constituye un itinerario numérico válido.

500 secuencias sembradas de 6–8 operaciones mezclan territorial/health/legacy,
comparación, valid-invalid-valid, fuentes, catálogo repetido y tres orígenes.
Cada operación se compara con la referencia; SOURCE_COMPLETENESS_R13.json prueba
que toda esa referencia coincide con 16 procesos independientes, una operación
por proceso frío. Solo se normalizan request_id y execution.request_id.
No se simula memoria del LLM. Territorial admite raíces verificadas por llamada;
W1 no cambia su primera raíz en un proceso: segunda raíz válida rechazada,
sin claims/itinerario, recuperación de la primera PASS. No se anuncia root
switch de movilidad como modo soportado.

## Paquete, fuentes y prompt

PACKAGE_HARDENING: PASS. Inventarios externos e internos cerrados, sin rutas
inseguras, duplicados, colisiones de mayúsculas o symlinks. Quince context paths,
diecisiete freeze paths, 266742 bytes de contexto; main/tools exactos.
ZIP extraído 782621 bytes, W1 temporal 1252907 bytes. Doble build byte-idéntico;
flat, nested observado en agentes/<candidate>, foreign cwd, root válido e inválido
se vuelven a probar en los seis tests generados R12, sin tests/gold montados.
No se afirma montaje real por STUDIO_CONTEXT_FILES ni autoextracción del ZIP.

SOURCE_COMPLETENESS: PASS_BOUNDED_DETERMINISTIC_VIEWS. Route/trip, stops/labels,
horarios, paseo, esperas, consulta, regreso, total/slack, destino, modelled,
entrada no verificada, conflicto de dirección, fuentes/periodos/provenance y
límites presentes. Las tasas territoriales conservan numerator/denominator/source.
Caller-supplied no se transforma en human-authored. No se exige leer raw_result_json.

SYSTEM_PROMPT_AUDIT: once ataques revisados estáticamente, prompt intacto.
Inyección documental, omitir tools, fecha no soportada, realtime, disponibilidad,
mejor cita, causalidad, centro asignado, puerta a puerta, conducta individual y
número insistido. Los contratos conservan scope/semántica y rechazan datos no
soportados; no certifican que el modelo obedezca en su prosa final.
No gold añadido, ninguna respuesta concreta -35min añadida al prompt.

CRITICAL: 0. HIGH: 0 en los gates locales terminados y revisión offline consumida;
no certificación universal ni aceptación del modelo/plataforma.
MEDIUM: 2 riesgos estáticos, no dos fallos de cálculo reproducidos:

- Schema servido puede no reflejar todos los límites de anotaciones; catálogo
  y runtime sí los exponen/imponen. Comparar schema real antes del smoke.
- No hay negativa textual específica sobre comportamiento individual/centro
  asignado en el prompt. Datos y operaciones no habilitan esas inferencias,
  pero la abstención de lenguaje requiere prueba real W3. Freeze preservado.

## RAG documental separado

RAG_AB_STATUS: OFF_CANDIDATE_OFFLINE_RETRIEVAL_ONLY.
RAG_RESULT: RAG_NO_GO. RAG_IN_CANDIDATE=false.
Mismos cuatro documentos hash-pinned y mismas 18 preguntas: 15 con soporte,
tres no soportadas; mismo criterio y secciones/anchors fijados antes de evaluar.
A base navegable selecciona documento completo por lookup léxico genérico;
B reutiliza retrieval léxico de secciones existente, k3/excerpt500, sin modelo,
embeddings, vector DB, Internet, credenciales o nueva infraestructura.

A: hit14/15, support completo14/15, cita-identidad18/18, abstención3/3,
wrong-source1/15; media5267.17 bytes, mediana local1.583 ms.
B: hit15/15, support completo11/15, cita-identidad18/18, abstención3/3,
wrong-source0/15; media1626.44 bytes, mediana local6.475 ms.
B ahorra contexto y mejora hit, pero pierde contenido necesario. No cumple
mejora clara sin regresión: NO_GO permanece, sin integrar en el ZIP.
Literal completeness y citas existentes no son fidelidad de respuestas generadas;
set pequeño del autor, no holdout ni LLM benchmark. No cálculos de GTFS/rutas/tasas.

## Verificación, soporte y corte

PYTHON: suite completa una vez, 376 PASS / 277.04 s. Focused 15 PASS / 163.29 s
(nueve R13 más seis tests del artefacto generado). NODE: 17 PASS.
CI nueva sobre f7a376b, comprobada en GitHub:
[vNext 36752411375](https://github.com/Asier-Comba/Guipuzkoa360/actions/runs/36752411375)
y [fast 36752411504](https://github.com/Asier-Comba/Guipuzkoa360/actions/runs/36752411504)
SUCCESS. Los stress locales no se ejecutan automáticamente en CI; no se transfieren
checks a otro SHA ni se infiere CI de la suite local.

Comandos reproducibles:

```text
py -3.12 -m scripts.vnext_agent.audit_r13 static
py -3.12 -m scripts.vnext_agent.audit_r13 cold
py -3.12 -m scripts.vnext_agent.audit_r13 rag
py -3.12 -m scripts.vnext_agent.harden_r13 --mode fuzz --count 10000 --shards 4
py -3.12 -m scripts.vnext_agent.harden_r13 --mode sequences --count 500
py -3.12 -m pytest tests/vnext_agent/test_r13_hardening.py tests/vnext_agent/test_r12_generated.py -q -o addopts=
py -3.12 -m pytest -q -o addopts=
node --test tests/e2e/contract_flow.test.mjs
py -3.12 scripts/ops/verify_runtime_identity.py
git diff --check
```

PORTAL_SUPPORT_READY: true. Un único PORTAL_SUPPORT_R13.json y
STUDIO_DIAGNOSTIC_PLAYBOOK_R13.md publican identidades, paths/hashes, dependencias,
orden, raíz esperada, parámetros/defaults y unknowns reales de plataforma.
Owner/evidencia/no inferencias para ocho observaciones definidos en el playbook.
Prueba real de import/schema/montaje/conversación sigue NOT_RUN por W2.
LOCAL_LLM: 0. PORTAL_LLM: 0. Portal writes W2: 0. No se gasta modelo local.

V4_PRESERVED: PASS, runtime 195b4980fa5998b096c308296a55e452380b0371,
catorce archivos antes/después. Sin edits W1/W3/v4 ni runtime de candidato.
Los pilotos de auditoría errónea están reconciliados en RESUME_R13.json; ningún
fallo del harness fue usado para romper freeze. Evidencia privada no se vuelca
en respuesta al usuario ni se inventan trazas/turnos del modelo.

NEXT_EXACT_ACTION: W3_REAL_PORTAL. Consumir patch3 exacto, verificar binario/root/
imports/schema servido y realizar el lote privado acotado ya autorizado. No
volver a pedir adjuntos privados ni afirmar lectura propia del holdout.
Si todo lo local permanece verde: W2_FINAL_CANDIDATE_FROZEN=YES y STOP, sin
seguir mejorando salvo High/Critical/incompatibilidad real Studio reproducidos.
MERGED_OR_PUBLISHED_RELEASE: NO. No promesa de actividad tras esta sesión.
