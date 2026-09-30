# GIPUZKOA 360 / DeustoAI Labs — W2 R12

STATUS: PATCH_CANDIDATE_READY_PENDING_INDEPENDENT_ACCEPTANCE.
Objetivo W2: candidato corregido disponible, no aceptación final ni release.

## Identidades inmutables

START_SHA: `2321e03e3d994b488db9723560383d9defedcac7`.
TESTED_HEAD: `8c94f8c3cf9d732c4ce94af7b4bef8f6e154c243`.
PUBLISHED_HEAD: `8c94f8c3cf9d732c4ce94af7b4bef8f6e154c243` (candidato de runtime
usado por los gates; el sucesor de cierre contiene solo documentación/diagnóstico,
no otro runtime. Su SHA se comunica en el comentario final de PR17/Issue16).
Rama: work/vnext-w2-agent-evidence; PR17 draft; base de integración intacta.

W1_RUNTIME_GIT_SHA: `cb061a9e00a6496c40488a596bd94834bc2c49b2`.
W1_PACKAGE_SHA: `c66d44af702eb3410fcea05ae8711f537214f675e83a7fda38c39c3b39a1b910`.
W1_SUPPORT_SHA: `c9cb37f6c65e77149e18cd883eeaff40d1c1bb8e`.
W3_CONSUMED_SHA: `1d60cdf81d3eb7661bc1d97c12425b9bdcf69b8d`;
preflight W3 `281f92a25170c5082c5772c0130d2275e57edaaf`, delta de código
`0601367e11ce0e869d3042e55623409d20aac203` y cierre posterior leídos.
W1 provider_r6 0.3.1 y legacy explícita 0.2.0 permanecen byte-idénticos.

La errata histórica textual `cb061a97e78d6b5c967104fef6b935132fdc450f`
se conserva como dato histórico, no se exige como commit Git ni se inventa equivalencia.
El commit real, blobs y ZIP exacto acreditan la identidad ejecutable.

## Baseline, reproducciones y atribución

R10 se conserva en START_SHA. Lectura directa del blob Git: 219354 bytes, SHA
`b4feb978b625b34f9d7331ce8d376a34a29e84e4783868f83ce48a0c0d1011be`.
PATCH 1 se conserva en `6693cbce605484dc48eca9ed7de867e32c5f3aa7`, ZIP
`9dbb2d7421e2468e44949f94ad1ef5b9011430601d34dd76057fb1720e0bfb1b`.
PATCH 2 se conserva en `7dc4d807d4ac159b508ef383b9ec950b4dce3e41`, ZIP c5bedc0c.
PATCH 3 añade el layout anidado observado por W3. Cada patch tiene SHA/registro;
no se modifican bytes silenciosamente en revisión.

REPRODUCED_FINDINGS / ENVIRONMENT_VS_PRODUCT_FINDINGS:

- Mismo ZIP R10 en A (proceso nuevo, extracción/cwd limpio): raw de legacy válido
  y cuatro casos health con nombres correctos. En B (cwd observador con datos W1,
  execute(root=extracción), public_result sin root): labels leídos desde otra raíz
  y FileNotFoundError del contrato legacy. Es defecto W2 de propagación de raíz.
- KeyError transformation: en ambos controles nace en el evaluador W1 R11,
  validate_model_view → expected_value → pointer(/sources/0/transformation), al
  aplicar un requisito sanitario al raw 0.2.0. No nace en public_result. No se
  fabrican campos transformation ni defaults vacíos en el contrato legacy.
- Legacy en A también proyectaba la parada 7214 como ID. Es defecto real W2;
  su nombre se deriva ahora del snapshot GTFS completo verificado, no de cuatro
  nombres literales ni alterando las nueve etiquetas sanitarias de W1.
- W3 publicó STUDIO_FREEZE_OMITS_RUNTIME_ASSETS sobre el baseline: solo trece
  datos declarados más módulos no contienen el cierre de runtime. PATCH 2 declara
  ZIP/mobility_sources y elimina la dependencia filesystem de las pruebas mediante
  un índice de SHA/nombres AST incrustado, sin lógica de aceptación ni gold.

Se guardaron cwd, root, archivos reales de tools/adapters, rutas/hashes de catálogo,
labels y contrato, inputs/outputs y stacks completos en diagnósticos privados del
host temporal. Baseline: g360-w2-r12-diagnostics-31ekqd7x/baseline; PATCH 1:
g360-w2-r12-diagnostics-ip7adw3y/baseline. PATCH 2:
g360-w2-r12-diagnostics-x8q76g1k/baseline; PATCH 3 final:
g360-w2-r12-diagnostics-ji2e53rx/baseline. REPRODUCTION_R12.json publica hashes,
estados y procedencia por caso sobre el ZIP final. El informe no contiene trazas
personales ni stack en la respuesta al usuario. El script de diagnóstico permite
repetir A/B con el ZIP y manifest exactos sin modificarlos.

W1 R12 R11_FINDINGS_RECONCILED en Issue16 confirma la atribución del evaluador y
el defecto de etiqueta legacy; W3 R12 acepta offline el baseline con límite de
etiqueta y reproduce el gap de freeze. **Esos informes no aceptan nuestro nuevo ZIP.**
Se les comunicaron los tres candidatos exactos, con cada incremento publicado,
para repetir sus gates sin consumir bytes mutables.

## Parches y conservación del circuito

PATCHES: raíz ligada al módulo/configuración explícita, sin priorizar cwd ni
buscar un checkout alternativo; root propagado a adapter legacy, validación,
consulta de fuentes y proyección. main resuelve una raíz por llamada. El cálculo
territorial usa v4 sin cambios, con su repositorio ligado a esa misma raíz.
El bootstrap verifica el ZIP incluso en caché y no cambia de raíz/proveedor.

Proyección por versión explícita, conserva raw W1, scope/estado, ida/vuelta,
horarios/ruta/paradas, walking, componentes, consulta hipotética, total/slack,
fuentes legibles con ficha equivalente y límites. No devuelve raw_result_json
al modelo. Si falta etiqueta, evidencia o capacidad, devuelve error sin cifras
parciales ni stack; no inventa red/HTTP/timeout. La poda de payload elimina la
proyección numérica además de los claims. Límite público: 120000 bytes.

Appointment_s y initial_wait_s se atribuyen al parámetro concreto USER o
MODEL_DEFAULTS, no a ambos indiscriminadamente. USER significa presente en llamada,
no autoría humana acreditada. Prompt permite claims y hechos proyectados verificados;
conserva pregunta → tools → observación → seguimiento/recálculo → error recuperable.
No routing por frase, gold precalculado, nuevas features, motor W1 o RAG adicional.

## Pruebas y CI

TEST_COMMANDS_AND_RESULTS detallados en RESUME_R12.json.
PATCH 3: seis tests R12 generados PASS (344.79 s), incluyendo controles A/B,
legacy frío y cierres declarados plano/anidado sin tests/gold/w1_pin. Cada circuito de A/B/freeze
recorre catorce casos, raw W1 exacto cuando procede, secuencias health/legacy,
comparaciones sanitarias/legacy/mixtas, error entre válidos, tres orígenes, nueve
etiquetas, cinco probes territoriales, fuentes/defaults, 1–4 escenarios y exceso.
Doble ZIP idéntico. Máxima vista de cuatro escenarios ensayada: 98137 bytes.

PATCH 1: suite completa 365 Python PASS (101 W2 incluidos, no sumables), 17 Node
PASS. CI vNext run 36739418186 y fast run 36739418502 SUCCESS. Requisitos sanitarios
W1 R11 aplicables evaluados sin cambios sobre las vistas capturadas A/B: ningún
hallazgo; legacy reproduce por separado el error de requisito inapplicable.

PATCH 2: suite completa 366 Python PASS (102 W2 incluidos), Node 17 PASS.
CI 36742033336 (fast) y 36742033364 (vNext) SUCCESS.
PATCH 3 final: suite completa 367 Python PASS (442.98 s; 103 W2 incluidos,
no sumables), Node 17 PASS. CI comprobada sobre TESTED_HEAD: vNext
[36744447987](https://github.com/Asier-Comba/Guipuzkoa360/actions/runs/36744447987)
y fast
[36744447389](https://github.com/Asier-Comba/Guipuzkoa360/actions/runs/36744447389)
SUCCESS. Identidad v4 14/14 antes/después PASS; diff check PASS.
Las dos CI corresponden al candidato inmutable, no se infieren del resultado local.

## Paquete y preparación real

PACKAGE_SHA_AND_SIZE: `scripts/vnext_agent/dist/gipuzkoa360-vnext-w2.zip`, SHA
`3951b290b6ca59c336886a3f0acee77a68036d4fbcbc06c2cedfe22400c08616`,
226010 bytes comprimidos / 782621 extraídos. W1 temporal adicional: 1252907 bytes.
Manifest adyacente SHA
`a672bf9a2afece58c468a1f762c860f0217536a2a4fa18737ba768cab755c70a`.

DEPLOYMENT_MODE: dos editores generados main.py/tools.py y quince assets declarados,
ZIP W1 verificado y extraído temporalmente. STUDIO_DEPLOYMENT_R12.json enumera
freeze_paths/hashes/bytes, dependencias, orden y schemas esperados. STUDIO_LOAD_R12.md
da instrucciones y prueba local, tanto layout plano como módulos en
agentes/<candidato> y assets en raíz. La raíz se determina por posición del módulo,
no buscando ancestros/cwd; inválida falla. Tests/gold/w1_pin son auditoría, no contexto LLM.
No se presume autoextracción del ZIP ni montaje por STUDIO_CONTEXT_FILES.

SERVED_SCHEMA_STATUS: NOT_RUN. TypedDict/NotRequired resueltos con las anotaciones
y Python locales reales; Studio/langchain no instalados. El schema esperado
no es el servido. W3 debe probar el binario congelado, layout/root, tempfile,
imports, tipos/obligatorios de tool y conversaciones reales con historial/capturas.

LOCAL_LLM_COUNT: 0. PORTAL_LLM_COUNT: 0. PORTAL_WRITES_BY_W2: 0.
OPEN_CRITICAL_HIGH: sin fallo runtime W2 reproducido pendiente en nuestros gates;
root/legacy/freeze quedan FIXED_BY_AUTHOR_PENDING_INDEPENDENT_RETEST. Los gates
de aceptación W1/W3/Studio siguen pendientes, no se convierten en PASS por CI.

NOT_RUN: gate W1 R12 corregido sobre este ZIP, scorer W3/holdout sobre candidato
nuevo, servido/imports/filesystem Studio, routing/memoria/lenguaje con LLM,
resolución humana de puerta/dirección, comparación LLM v4/vNext y RAG con modelo.
RAG_NO_GO anterior se conserva; no se añaden embeddings, vector DB ni servicios.
Private 00–12 no montados: no se afirma lectura propia ni se vuelven a pedir.

V4_PRESERVATION: runtime `195b4980fa5998b096c308296a55e452380b0371`, catorce archivos
congelados PASS. Ocho assets comunes del ZIP cotejados byte-idénticos contra v4.
Sin edits W1/W3/v4, main/integration/gh-pages, merge/release/Entrega/track.

NEXT_EXACT_ACTION: W1/W3 consumen `8c94f8c` completo y hash 3951b290, repiten gates
aplicables por versión; **W3 es único operador** y verifica freeze/imports/schema
reales antes del smoke autorizado y acotado. Preservar intentos e historial, detener
ante Critical/High, no fabricar mensajes finales. W2 no promete actividad futura.

MERGED_OR_PUBLISHED_RELEASE: NO.
