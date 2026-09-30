# W2 R13 — diagnóstico de Studio sin inferencias

Único candidato: runtime `8c94f8c3cf9d732c4ce94af7b4bef8f6e154c243`,
ZIP `3951b290b6ca59c336886a3f0acee77a68036d4fbcbc06c2cedfe22400c08616`,
manifest `a672bf9a2afece58c468a1f762c860f0217536a2a4fa18737ba768cab755c70a`.
No reconstruir ni sustituir bytes en el portal. PORTAL_SUPPORT_R13.json es el
único índice R13 de identidad, dos módulos, quince assets, configuración y schemas
esperados. Es soporte de preparación, no prueba de montaje ni schema servido.

Solo W3 opera Studio. Conservar el borrador baseline por separado. Verificar el
pin, los hashes descargados, inclusión binaria del ZIP W1, rutas y schema real
antes del lote privado ya autorizado. No cambiar modelo ni recursos, publicar
Entrega, crear otra autorización implícita o consumir mensajes extra.

## Evidencia mínima por observación

| Observación | Recoger antes de atribuir causa | No inferir | Owner / siguiente paso |
|---|---|---|---|
| Import error | Error exacto y etapa; módulos y versiones realmente instaladas; main/tools `__file__`, directorio de imports y raíz de datos; versión/draft y hashes; captura de preparación. | Que un módulo local ausente también falta en Studio, que cambiar el modelo lo resuelve o que existe fallo de red. | W3 documenta entorno/plataforma; W2 reproduce con el layout exacto. W1 solo si el import del ZIP fijado falla independientemente. |
| Missing asset | Ruta relativa solicitada, inventario realmente congelado, bytes/hash descargados, cwd y raíz observados; presencia/acceso del ZIP binario. | Que subir un archivo lo congela, que context-files monta datos, que subir un ZIP lo extrae o que cabe usar otro checkout. | W3 identifica montaje; W2 contrasta contra los 17 freeze paths. |
| Stale validation | `status/error.code/message`, hashes de capabilities y tools.py, índice embebido, archivo de prueba si existe, raíz efectiva y ensamblaje mínimo exacto. | Que gold/tests deban entregarse al modelo, que el hash acredite verdad, o que el error del baseline se transfiera a patch3. | W2 reproduce cierre/índice. W3 conserva assembly; no parche del evaluador para ocultarlo. |
| Schema mismatch | Schema servido completo de las nueve tools; descripciones, union objeto/lista, required/NotRequired, tipos/defaults y nested schema; comparación literal con soporte, versiones de decorador/framework. | Que la anotación Python garantiza el schema servido; minItems/maxItems documentales no prueban imposición en Studio. | W3 recoge schema y owner plataforma; W2 revisa compatibilidad reproducida. No PATCH4 sin incompatibilidad real o High/Critical. |
| Tool exception | Tool y argumentos exactos, respuesta/error o excepción por etapa, trace privada íntegra, root/imports, hashes, intento y ejecución fría equivalente. | Causa HTTP/timeout/red no observada; fallo del motor W1 cuando la excepción viene del despacho/schema/proyección. | W2 determina etapa; W1 recibe solo un raw/provider fallo aislado sobre su ZIP. W3 no expone stack al usuario. |
| Model ignores tool | Mensaje literal, instrucciones y schema realmente enviados, modelo/config visibles, historial/tool calls auténticos, límites de iteración y estado de memoria. | Que un fake-model test demuestra routing/autonomía, que un tool determinista falló sin ejecutarse o que la respuesta es aceptada por parecer correcta. | W3 gate de modelo; W2 revisión estática solo tras fallo real. |
| Wrong result | Pregunta/parámetros, tool view y raw privados relacionados, schema/status, fuentes/periodos, escenarios/comparación y cálculo independiente del dato congelado. | Que CI verde acredita la cifra, que un raw correcto acredita la respuesta final, o que caller-supplied demuestra autoría humana. | W3 distingue lenguaje de dato; W2 verifica binding/proyección; W1 verifica cálculo solo si el raw difiere. |
| Memory loss | Secuencia real completa de mensajes y tool calls, conversación/versión, configuración de memoria, parámetros anteriores/nuevos, contexto visible y límites. | Que 500 secuencias de tools prueban memoria del LLM, que conservar caché es conservar intención o que el seguimiento debe reutilizar cifras viejas. | W3 reproduce memoria/lenguaje con el lote permitido; W2 solo contaminación de estado runtime. |

## Raíces y recuperación

Flat: imports y datos en la raíz del workspace. Nested: imports en
`agentes/<candidate>/`, datos en la raíz del workspace. Nunca priorizar cwd ni
buscar ancestros. Variable GIPUZKOA360_VNEXT_ROOT presente pero inválida debe
fallar sin fallback. W1 queda ligado a la primera raíz verificada del proceso:
cambiar esa raíz no es un modo de movilidad soportado; usar proceso nuevo.
Las herramientas territoriales sí se ligan a la raíz explícita de cada ejecución.

Un error permite describir exclusivamente el estado observado y la acción segura.
No publicar cifras parciales. Preservar escenarios no viables/unknown y sus límites;
no convertirlos en viajes válidos ni inventar citas, entrada, acceso real o causalidad.

## Corte

High/Critical o incompatibilidad Studio reproducida: guardar evidencia y detener
smoke. W2 solo entonces puede hacer parche mínimo con nuevo pin/ZIP y reaceptación
W1 obligatoria. Sin ese hallazgo: W2_FINAL_CANDIDATE_FROZEN=YES, sin PATCH4.
Prueba real, feedback y decisión de entrega siguen perteneciendo a W3/coordinación;
este documento no autoriza merge/release/publicación ni trabajo en segundo plano.
