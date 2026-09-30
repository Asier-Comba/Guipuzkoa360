# W2 R12 — carga y aceptación por W3

Estado: candidato determinista disponible, **no aceptación Studio ni release**.
Consumir el commit de runtime fijado en `RESUME_R12.json`, no HEAD mutable.
El primer patch `6693cbce605484dc48eca9ed7de867e32c5f3aa7` se conserva histórico;
este segundo patch añade el cierre de archivos declarados tras el hallazgo W3.

## Identidad y cierre de archivos

Paquete: `scripts/vnext_agent/dist/gipuzkoa360-vnext-w2.zip`.
SHA-256: `c5bedc0c2fbc028258135d3f8b2a94d5fc37aa3a9808417fee3165a9915e98d4`.
Manifest: `scripts/vnext_agent/dist/gipuzkoa360-vnext-w2-manifest.json`.
SHA-256 del manifest: `059ad32664aacaccdb7302e9f50ca519f21b5103a27df3bd409f45fa8caee1a9`.

La lista **exacta**, las rutas relativas, bytes y hashes de cada miembro están en
`members` del manifest. El cierre ejecutable mínimo está en `freeze_paths` y
`runtime_static_closure` de `STUDIO_DEPLOYMENT_R12.json`; el resto es auditoría.
No usar las capacidades del checkout fuente como las del paquete: el builder habilita
plan_visit solo en el registro combinado verificado dentro del ZIP.

Tamaños: 225894 bytes comprimidos; 782144 bytes extraídos en el workspace;
1252907 bytes adicionales del ZIP W1 extraído temporalmente. Total de ambas
extracciones: 2035051 bytes. La ayuda observada por W3 dice 24 MB total y 100 MB
por archivo, sin precisar unidades o base comprimida/expandida. Todas estas
medidas son inferiores a 24 millones de bytes; la comprobación real corresponde a W3.

## Procedimiento de carga

1. Verificar commit, ZIP, manifest y cada miembro antes de cargar. Extraer el ZIP
   explícitamente fuera del portal para obtener sus miembros. Subir el ZIP no
   demuestra que Studio lo extraiga.
2. Verificar los hashes de los assets comunes contra v4 antes de reutilizarlos.
   No reemplazar archivos compartidos por contenido diferente. Los assets nuevos
   están bajo `datos_preparados/vnext`, `contracts/vnext`, `tests/vnext_agent` y
   `scripts/vnext_agent` según el inventario. Una discrepancia se comunica, no se oculta.
3. W3 debe comprobar que cada asset de freeze_paths está realmente accesible mediante filesystem,
   con su ruta relativa exacta, **junto al directorio que contiene tools.py generado**.
   Los quince `STUDIO_CONTEXT_FILES` declaran los datos que se deben fijar, incluido
   el ZIP W1 y mobility_sources. El binario ZIP debe quedar legible por filesystem;
   no se debe interpretar su contenido como texto de prompt. La declaración no
   prueba por sí sola el montaje ni que Studio acepte este tipo de asset.
4. Cargar `tools.py` generado en el editor de herramientas y después `main.py`
   generado en el editor principal. Ambos proceden del ZIP, no de los módulos fuente.
   Las pruebas y w1_pin.json son auditoría del ZIP, no dependencias de lectura en
   ejecución. tools.py incorpora solo el índice de hashes exactos de las pruebas
   y nombres de función derivados de su AST. No se incorpora su lógica de aceptación,
   contenido gold o resultados esperados. Si una prueba existe pero está alterada,
   el runtime la rechaza; el índice no oculta archivos corruptos.
   El gold `w1_conformance_r7.json` tampoco se introduce en el prompt ni en contexto.
5. Usar el nombre, SYSTEM_PROMPT y configuración de main.py: nueve tools, ocho
   iteraciones máximas, memoria activada, Internet desactivado, modelo proporcionado
   por Studio. Nombre: 38 caracteres; instrucciones: 2968; contexto: quince archivos,
   266742 bytes (incluido el ZIP comprimido). No crear modelo, credenciales o servicios adicionales.
6. Antes de una conversación, W3 captura directorio del módulo/raíz y legibilidad
   de assets, comprueba tempfile escribible y guarda el schema que Studio realmente
   sirve. Si el montaje o imports no están disponibles, registrar ENVIRONMENT_NOT_READY;
   no modificar v4 ni inferir un montaje alternativo.

## Raíz, imports y dependencias

Python 3.12 y biblioteca estándar; `studio.tool` y
`langchain.agents.create_agent` proporcionados por Studio. La versión efectiva
de esas dos dependencias es pendiente de captura por W3; no se promete una versión.
Localmente no están instaladas. La prueba offline usa el fallback de decorador
sin LLM: no demuestra integración de Studio ni LangChain.

Orden de raíz: argumento explícito, variable `GIPUZKOA360_VNEXT_ROOT` si existe,
directorio del tools.py generado. Una variable vacía o raíz incompleta falla;
no se busca otro checkout. cwd y `GIPUZKOA360_DATA_DIR` no eligen los datos W2.
main.py resuelve una raíz por llamada y la pasa al cálculo y a la proyección.
Los cálculos territoriales usan el mismo repositorio explícito, sin modificar v4.

tools.py verifica el SHA del ZIP W1, limita tamaño y rutas, lo extrae en tempfile
e importa provider_r6 desde allí. Los dos adapters W2 se encuentran incorporados
en tools.py. No hay Git/red en runtime. El runtime cacheado no cambia de raíz;
un `prototypes` preimportado ajeno se rechaza, no se usa como proveedor de confianza.
W3 debe comprobar ese cierre en el proceso real de Studio.

## Schema esperado y schema servido

`STUDIO_DEPLOYMENT_R12.json` contiene `expected_tool_schemas` para las nueve tools,
derivados de las anotaciones reales mediante `get_type_hints(include_extras=True)`.
TypedDict/NotRequired se resuelven en el Python local declarado en ese archivo.
La forma esperada de plan_visit es un objeto con `request`, que puede ser un objeto
VisitRequest o una lista de dos a cuatro VisitRequest.

Campos obligatorios: origin_id, destination_id, date, appointment_time,
duration_minutes. Opcionales: arrival_margin_minutes, boarding_margin_minutes,
walking_profile_id, snapshot_id, return_deadline. La variante legacy exige
snapshot_id explícito y conserva su contrato 0.2.0; no se convierte en sanitario.
Las restricciones semánticas y rangos se verifican en runtime además del schema.

**SERVED_SCHEMA_STATUS: NOT_RUN.** Este JSON es una especificación esperada, no
un schema capturado de Studio/LangChain. W3 compara campos obligatorios/opcionales,
unión objeto/lista y tipos con las versiones del portal y conserva la captura.

## Prueba local del mismo modo y prueba real pendiente

`py -3.12 -m pytest tests/vnext_agent/test_r12_generated.py -q -o addopts= -s`
extrae el ZIP, importa main.py/tools.py generados, bloquea red, deja el entorno
vNext limpio y usa tanto cwd de la extracción como un observador con datos ajenos.
Pasa catorce casos con raw idéntico a W1, secuencias health/legacy, legacy frío,
comparaciones, tres orígenes, nueve etiquetas sanitarias, procedencia, cinco
regresiones territoriales y errores/payload. La parada legacy fuera de las nueve
etiquetas sanitarias se resuelve desde el snapshot completo GTFS dentro del ZIP W1,
con SHA verificado, sin añadir nombres literales. Un cuarto modo extrae solo main.py,
tools.py y los quince archivos declarados: no hay tests/gold/w1_pin en esa raíz y
el mismo circuito determinista pasa. Esto reproduce la política observada por W3,
no certifica el filesystem real de Studio. Máxima vista de cuatro escenarios
ensayada: 98137 bytes; límite local: 120000. Doble build idéntico.

La única colisión de definiciones/globales entre core y W2 es consultar_fuente:
reemplazo intencionado tras guardar el handler core y _safe en territorial.
No se ha reescrito el empaquetador por preferencia estética.

La prueba local no acredita routing, memoria ni calidad de respuesta. W3 debe
capturar con modelo real: pregunta principal, variación, límite, cifra contrastada,
seguimiento con recálculo y error recuperable. Guardar tools e historial efectivos,
no respuestas precalculadas ni mensajes finales inventados. No resolver el conflicto
de dirección/entrada por conjetura: entrada NOT_VERIFIED, paseo modelado y horario
programado en 2026-09-29; no citas reales, realtime o puerta a puerta.

W3 es el único operador autorizado del portal. W2 no ha escrito allí ni ejecutado
un LLM local o de portal. No publicar Entrega, track, release ni merge.
