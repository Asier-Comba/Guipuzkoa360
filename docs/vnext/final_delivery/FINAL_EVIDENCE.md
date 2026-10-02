# Evidencia vigente R18 — offline cerrado; CI y conversación real pendientes

R18 parte del SHA exacto8f3ee977cea3295f8f5a92b776e44a598d897016, no del
checkout R17 con auditoría sin commit. [Handoff](../w2/HANDOFF_R18.md).
ZIP57fe8ccab8ab3613c0729aa9a4b25702dbaead5d74bfb6216e8bbe117c421256,
235611bytes; manifiesto d2eee50d906be5056c227102c8c2005b9cb93c3916d8fbf6a3df35571ec4af74.
Solo main/tools cambian;23otrosmiembros/15assets/W1/v4 conservados.
28focales;709Python completos una vez local675,06s;17Node; identidad14/14
antes/después;jury y artifacts7/7 PASS. Builds byte-idénticos.
Matriz inicial489/489raw,7oracle,53time summaries,0findings tras corregir el
verificador de proyección no válida; primer fallo conservado, no drift raw.
Corpus ampliado156/156structural independiente,12time summaries,0findings,
SHAc98ab497aed72b2b18c63f7c652d4c220a156e9846cb9b7aa9393f807ffd81e4.
No sumar ambas matrices como645casos únicos ni afirmar que el segundo informe
tiene oráculos (0; los7 pertenecen al primero). CI exacto ejecutará matriz
combinada489 con el corpus ampliado; ambos reports actuales conservados.
La ampliación fue adversarial de corpus/harness, no cambio de paquete ni de
pruebas del motor. Modelo llamado0;real R18 NOT_RUN;holdout cerrado.
No declarar generalización LLM por estas pruebas deterministas.

R17 general audit posterior:Critical0/High0/Medium1/Low3,FAIL. Nunca transferir
su anterior aceptación de4mensajes aR18 ni borrar el hallazgo de población
dentro de radio. Capturas originales en outputs/final_release.
El nuevo semantic firewall tipa evidencia, no verifica matemáticamente prosa
final del LLM: queda aceptación real sobre versión privada exacta.
READY_FOR_HUMAN_FINAL_GATE=NO;track/confirmación/publicación HUMAN ONLY.

## Histórico R17 — no estado ni aceptación de R18

# Evidencia histórica R17 — cierre privado del agente y de Entrega

Runtime probado: 77ac63d5b68a3ecbf51461e3aaa0de0566d6f2c3. Base R16 exacta:
c859a26396838d59a52b8d91f1eda5ef6b69e4cd. [PR22](https://github.com/Asier-Comba/Guipuzkoa360/pull/22), draft contra R16; main no modificado.
ZIP: 1b263724110c68efab69c14e479f50ed2d101f935c6c83102bb0e5d4c699dc79,
231.758 bytes; manifiesto: 246f703e1e1881fe984598fe7b428b1b18380c43e7555c03fca2b53dd1982fee.
Solo cambian main.py y tools.py: otros 23 miembros, quince assets y ZIP W1 byte-idénticos.
Datos, fuentes, GTFS, paseo, fórmulas, productor y v4 preservados. Dos builds locales idénticos.
El manifiesto del build conserva NOT_RUN histórico: el estado real posterior está aquí y en las trazas, sin cambiar el paquete después de Studio.

## Qué se cerró y alcance de la limpieza

Resumen territorial público: un único campo obligatorio municipio: str, sin periodo.
Las 88 filas demográficas solo contienen 2025-01-01; el motor interno conserva selección de periodo y el catálogo público informa de esa referencia sin anunciarla como input.
Tres intentos de periodo extra se rechazan antes de ejecutar. Las otras cinco tools de periodo no cambian.
75+: selección de año de nacimiento <=1949 en scripts/data/01_download_sources.py, suma por municipio y sexo total en 03_prepare_demography.py, porcentaje a tres decimales. Datos agregados por año, no cumpleaños individuales; no identifica nacidos el propio 01/01/1950.

Metadata interpretativa humanizada sin alterar claims/resultados. Source IDs históricos W1_*/W2_* se conservan como claves de trazabilidad, no como títulos, instituciones ni nombres públicos. El auditor excluye únicamente esas claves de identificador, no frases libres ni instituciones. No se afirma ausencia de las claves técnicas necesarias para consumir JSON.

## Cuatro mensajes reales, nueva versión privada

agentv_64c72bcb772143968038a2f620944bf1, GIPUZKOA 360 · Visita sanitaria · v3.
Modelo observado openai:gpt-5.6-luna, memoria ON, Internet OFF, nueve tools.
Preparación y firma pública comprobadas antes de crear versión; v2 R16 intacta.
[Identidad por descargas UI](../../../outputs/r17/portal/workspace-file-identity.json):
main/tools y quince assets 17/17 coinciden con el manifiesto tras crear la versión.
La definición congela esos paths. No es una exportación ZIP de la versión congelada ni identidad de la carpeta completa; scaffold del portal adicional no consumido.

| Caso y sesión | Llamadas reales nuevas | Resultado / criterio | PASS/FAIL | Envío → final observado |
|---|---|---|---|---:|
| M1 Aduna, A vacía | obtener_resumen_territorial, municipio=Aduna, ningún otro argumento | valid a la primera, sin invalid_arguments/recovery: 36/507, 7,101 %, Eustat, 01/01/2025; explica nacidos hasta 1949 y recuentos agregados | PASS | <=37,809 s |
| M2 sanitaria, B vacía | consultar_capacidades(plan_visit); plan_visit(Zegama, punto Beasain, 2026-09-29, 09:30, 20) | 10691 s, 2 h 58 min 11 s; 08:09:37–11:07:48; bus 08:12:37 diferenciado; componentes suman 10691 | PASS | <=104,501 s |
| M3 seguimiento, misma B | nuevo plan_visit, solo cambia appointment_time=09:45 | 8591 s, 2 h 23 min 11 s; 08:44:37–11:07:48; 35 min menos, comparación condicional, no recomendación | PASS | <=61,762 s |
| M4 límites, C vacía | consultar_capacidades(plan_visit) | Zegama/Segura/Idiazabal; rechaza domicilio, realtime, mejor hora y disponibilidad de cita; fecha validada 29/09/2026 | PASS | <=56,332 s |

Trazas literales: [M1](../../../outputs/r17/portal/M1-session-A.txt),
[M2](../../../outputs/r17/portal/M2-session-B.txt),
[M3](../../../outputs/r17/portal/M3-session-B.txt),
[M4](../../../outputs/r17/portal/M4-session-C.txt).
Outputs originales desplegados en archivos M*-tool-outputs.json adyacentes.
M3 incluye acumulados de B: son capacidades y dos visitas, no nuevas repeticiones.
La respuesta M3 verbaliza 35 minutos; -2100 s se contrasta por 8591-10691, no se finge una cita literal del final.
[Cotas de latencia](../../../outputs/r17/portal/real-latencies.json): observación UI, no tiempo exacto de servidor, p95 ni medición separada de tool/output (NOT_OBSERVED). Ningún quinto mensaje ni evaluador LLM ejecutado.

## Findings actuales y observaciones no ocultadas

REAL_CRITICAL=0, REAL_HIGH=0, REAL_MEDIUM=0, REAL_LOW=1.
Low estilístico M4: enumera IDs internos de origen y usa el término inglés realtime; sus límites son correctos.
No se cambia runtime ni se abre R18 por estilo. Se selecciona únicamente B sanitaria limpia; M4 no se comparte.
M1 cierra el primer periodo vacío R16 con nueva evidencia, no modifica retrospectivamente aquel FAIL.
El corte 1949 aparece ahora explícitamente; la explicación no atribuye edades individuales exactas.

Persisten aviso genérico Connection Error y renderer de preview que deja etiquetas Respuesta vacías en eventos de tools y muestra Markdown literal. Las ejecuciones y el guardado sí concluyen; no se editan respuestas ni se afirma que esas limitaciones de UI se hayan corregido.
Un selector de status fue ambiguo después del guardado (dos notificaciones); leído luego confirmó Borrador guardado. No fue fallo del agente ni se reenvió prompt.

## Validación exacta, sin transferencia de CI

Una sola suite local completa: 681/681, 304,04 s (XML 303,874 s), cero fallos/errores/skips.
Focal corregido 13/13; autoauditoría del autor 335/335 raw parity, siete oracle y 41 resúmenes temporales, cero findings; no aceptación independiente.
Primera auditoría de lenguaje fallida y focal inicial 12/13 conservados en attempts; cifras raw ya coincidían, se corrigieron solo etiquetas antes del checkpoint y Studio.
Node 17/17, identity 14/14 antes/después, jury y artifacts PASS, diff-check PASS.
[CI R17 del runtime](https://github.com/Asier-Comba/Guipuzkoa360/actions/runs/36928182340): Ubuntu job110590589306, 681 en 99,09 s; Windows job110590589440, 681 en 120,94 s; ambos Node17/audit335/oracle7/identity/gates/rebuild PASS y artefactos generados.
[Fast CI del runtime](https://github.com/Asier-Comba/Guipuzkoa360/actions/runs/36928182347): SUCCESS.
El cierre posterior es documental; su SHA y CI exactos se fijan en el checkpoint PR22 tras el push, sin atribuirle los runs anteriores.
No se repite la suite completa local, estrés20k ni holdout.

## Entrega guardada y dos revisiones del jurado

DELIVERY_CONTENT_COMPLETE=YES, copy público en voz del equipo; [DELIVERY_COPY](DELIVERY_COPY.md) coincide literalmente con la explicación guardada.
Ficha: Gipuzkoa.; destinatarios breves; utilidad en dos niveles (88 municipios / visita completa).
Versión seleccionada v3 exacta; una conversación B de dos turnos revisada, sin retries.
Solo demo territorial y repositorio; archivos seleccionados 0. Demo leída sin cambios, identificada como visualización del screening territorial, no agente sanitario en vivo.
Equipo 3/3 confirmado por el gate del portal; nombres oficiales completos conservados en la explicación.
[Preview completo](../../../outputs/r17/portal/delivery-preview.txt) leído literalmente incluyendo ambas respuestas; segunda revisión activa de números, fechas, alcance, atribución, supuestos, realtime/domicilio/citas/mejor hora, enlaces y jerga interna: sin contradicción material.
No nombres Works/Rxx/hashes/CI/debug en el contenido público seleccionado. Dropdown privado conserva versiones históricas, no se borran.
Estado observado Borrador privado / Borrador guardado; versión sin evaluar no equivale a evaluación oficial. Track sin seleccionar, acknowledgement sin marcar/deshabilitado, Publicar entrega deshabilitado.
HOLDOUT=SEALED_NOT_EXECUTED, RELEASE_GO=NO. Siguiente paso exclusivamente humano: track, preview final, confirmación y publicación.

## Histórico superseded R16 — conservar resultado original

El texto siguiente describe R16 y no es el estado vigente. Su Medium recuperado y sus Low no se borran ni se convierten retrospectivamente en PASS.

# Histórico R16: cálculo, agente real y borrador

Runtime probado d4dd2e65434c6c7f9f33c74ef1041b0f136cde69; ZIP 374af43fa6ce58b513a10477fc216215c7472f54bd28eada4fc0908da6f3dd6c (229.844 bytes); manifiesto a46415845f86c5c22ad648965b45e5bd109c839e9cb6cc14daee0ef37d7f788e. Base R15 exacta 69bcc6ead9ce444a884aa2b15469bd3b519775f5. Solo cambian main.py y tools.py del paquete; otros 23 miembros, quince assets, productor/W1, fuentes/datos y v4 idénticos. Dos builds locales y CI reproducen hashes. [Handoff R16](../w2/HANDOFF_R16.md).

El manifiesto del paquete es inmutable y registra NOT_RUN en el momento del build; el estado posterior real está en FINAL_MANIFEST.json y las trazas, no se reescribe el manifiesto para cambiar su hash después de Studio.

## Prueba real privada, sin transferir resultados históricos

Versión agentv_f4ca979c0c5b415da187711e96ba2c4d, GIPUZKOA 360 · Visita sanitaria · v2; modelo visible openai:gpt-5.6-luna; memoria activa, Internet desactivado. Tramo R16 5/5 mensajes. Sesiones A/B/C verificadas vacías antes de la primera pregunta. Capturas DOM visible y JSON de resultados desplegados, no reconstrucciones ni simulación de LLM. [Inventario descargado 17/17](../../../outputs/r16/portal/file-identity.json). Studio contiene un scaffold de ejecución adicional no importado por main/tools; no se equipara su carpeta completa al ZIP.

| Caso | Tools nuevas en el turno | Resultado observado | Gate estricto | Cota superior envío→final observado |
|---|---|---|---|---:|
| M1, A principal | capacidades; plan_visit, Zegama/Beasain/2026-09-29/09:30/20 | valid, 10691 s; 2 h 58 min 11 s; 08:09:37–11:07:48; salida del vehículo 08:12:37 diferenciada | PASS | ≤85,890 s |
| M2, A variación | plan_visit, mismos inputs salvo 09:45 | valid, 8591 s; 2 h 23 min 11 s; 08:44:37–11:07:48; final 35 min menor, condicional | PASS | ≤36,992 s |
| M3, A fuentes/límites/cobertura | capacidades | fuentes/periodos, paseo modelado, entrada no verificada; Zegama, Segura e Idiazabal; rechaza realtime/domicilio/mejor hora | PASS | ≤76,004 s |
| M4, B principal limpio | capacidades; plan_visit, exactamente M1 | valid, 10691 s; 2 h 58 min 11 s; 08:09:37–11:07:48, sin contradicción | PASS | ≤81,352 s |
| M5, C Aduna 75+ | resumen con periodo vacío (invalid); capacidades; resumen con 2025-01-01 (valid) | 36/507; 7,101 %; EUSTAT_EMH_2025, 2025-01-01; recupera error sin repetir args | FAIL, Medium recuperado | ≤114,682 s |

Cotas desde envío hasta observación del final: no latencias exactas ni p95. Time-to-tool y time-to-output separados: NOT_OBSERVED; no se infieren de capturas sin marcas de streaming. PREs de M2/M3 son acumulativos de A, no llamadas nuevas repetidas. M2 expresa −35 min correctamente; −2100 s consta en totals y contraste determinista, no se atribuye falsamente como cita literal del final.

Trazas con prompts/args/outputs/final: [M1](../../../outputs/r16/portal/M1-session-A.txt), [M2](../../../outputs/r16/portal/M2-session-A.txt), [M3](../../../outputs/r16/portal/M3-session-A.txt), [M4](../../../outputs/r16/portal/M4-session-B.txt), [M5](../../../outputs/r16/portal/M5-session-C.txt); cada una tiene su M*-tool-outputs.json adyacente. Version ID y sesiones vacías en el mismo directorio.

## Hallazgos actuales, no falsa totalidad verde

- Critical 0, High 0: H-01 no reaparece en dos sesiones limpias; scope, duración y componentes concordantes. No se atribuye causa psicológica al modelo.
- Medium 1: M5 aún envía periodo vacío inicialmente. Backend fail-closed intacto; consulta capacidades una vez y corrige una vez, sin llamada idéntica repetida; cifra final correcta. Cierra la repetición inválida R15, no satisface «no periodo vacío». REAL_ADUNA=FAIL y PORTAL_REAL_AGENT=FAIL según protocolo estricto, aunque su respuesta numérica pasa. No más prompts ni nuevo candidato tras 5/5.
- Low 1: catálogo principal humanizado y finales observados sin Rxx/defaults del proveedor; persiste jerga interna en algunos campos de linaje de fuente (transformation, institución/título de MODEL_DEFAULTS). L01_PUBLIC_JARGON=LOW, no limpieza completa de toda metadata. No se modifica runtime después de estas pruebas.
- Low 2: explica 75+ por año de nacimiento sin mostrar el corte exacto ≤1949 en el final; no llama consultar_fuente para completarlo. Source metadata conserva el método. La explicación sanitaria es compacta; copy adjunto completa atribución OSM y referencia PADI sin afirmar que el agente las verbalizó todas.

Problemas operacionales separados: preparación inicial Failed to fetch, recuperada con recarga y nueva preparación antes de crear versión. Descarga opcional de evidencia desde UI agotó tiempo; se conservaron DOM y outputs visibles. No se presenta como fallo matemático ni se oculta. Portal muestra aviso genérico Connection Error pero confirmó borrador guardado; estado guardado y vista previa acreditan las ediciones.

## Validación offline y CI exactos

Focal 116/116. Autoauditoría del autor 333/333 raw parity, siete oracle, 231 inválidos y 41 resúmenes temporales, cero findings; no aceptación independiente. Sin Internet/modelo; sin estrés20k ni holdout.

Suite Python local completa una vez: 667 PASS, 1 timeout histórico de test_generated_r12_end_to_end[declared_nested], con timeout restante negativo −1296,203 s; causa no demostrada. Solo ese test se repitió: 1 PASS en 85,85 s. Reportes originales conservados; no se reescribe el resultado fallido. CI del SHA probado: [36892707817](https://github.com/Asier-Comba/Guipuzkoa360/actions/runs/36892707817), Ubuntu 668/668 en 74,61 s y Windows 668/668 en 79,68 s; Node 17/17, identity 14/14, jury/artifacts PASS, doble build idéntico ambos. Fast CI [36892707797](https://github.com/Asier-Comba/Guipuzkoa360/actions/runs/36892707797) SUCCESS. SHA documental final y su CI en PR21; bytes probados realmente no cambian.

[Auditoría offline](../../../outputs/r16/local/r16-audit.json), [suite local original, comprimida sin editar](../../../outputs/r16/local/r16-pytest.xml.zip), [recheck único](../../../outputs/r16/local/r16-timeout-recheck.xml). La compresión conserva incluso el whitespace del traceback; no se modifica el informe para pasar diff-check.

## Entrega y límites de aceptación

Borrador v2 con conversación A revisada (tres turnos), demo territorial y repositorio. Ficha sanitaria actualizada, contenido listo para pegar y revisión literal de vista previa; sin archivos originales HTML/PADI ni capturas antiguas seleccionadas. Track vacío, confirmación sin marcar, no publicación. DELIVERY_CONTENT_COMPLETE=YES no implica RELEASE_GO. «Sin evaluar» de plataforma no se sustituye por evaluación oficial inventada.

HOLDOUT=SEALED_NOT_EXECUTED: no disponible con custodia verificable, no leído/reconstruido, no requisito oficial. TECHNICAL_RELEASE_READY=NO por M5 y revisión coordinadora pendiente. Siguiente acción: decisión humana sobre Medium recuperado y delta, no más desarrollo automático.

## Histórico superseded: evidencia documental R14/R15

Lo siguiente es procedencia; «último agente», gates y casos no conversacionales corresponden a ese momento. No transfiere PASS/FAIL al candidato actual.

# Histórico: Evidencia para comprender el resultado

Pregunta principal: ¿Cómo cambia la carga temporal de una visita sanitaria para personas que dependen del transporte público cuando cambia el municipio de origen, la hora de la cita o su duración?

Caso contrastado **offline**, no respuesta sanitaria del agente real: Zegama → punto oficial modelado del Ambulatorio de Beasain, 29/09/2026.

| Escenario | Duración consulta | Carga temporal programada/modelada |
|---|---:|---:|
| Cita 09:30 | 20 min | 10.691 s |
| Cita 09:45 | 20 min | 8.591 s |
| Segundo menos primero | sin cambio | −2.100 s / −35 min |

Los tres valores proceden del [oráculo público R13 fijado](https://github.com/Asier-Comba/Guipuzkoa360/blob/4bf975511ecea46c25662becfccb65713d381aa0/docs/vnext/w1/FINAL_ORACLE_R13.json), contrastado con filas GTFS y geometría/fórmula. R14 conserva productor y datos; el benchmark final de W1 publicado en `3a8e2b0948bb06df87af7a0f5769a369da568eff` contrasta ese candidato R14 con el oráculo. Sus resultados son evidencia histórica, no aceptación ni benchmark del nuevo candidato R15. No se ha abierto el holdout.

La carga abarca presencia en parada de origen → llegada a parada de regreso, no domicilio → domicilio. Se suman ocho componentes: espera inicial, vehículo de ida, paseo de ida, espera previa, consulta, paseo de vuelta, espera de regreso y vehículo de vuelta. La consulta usa minutos × 60; el paseo usa ceil(metros/50) × 60 + 120 por enlace completo y sentido. Las unidades se conservan, no se deduce tiempo de una distancia geométrica.

## Fuente → transformación → cifra

- **GTFS**, Moveuskadi/Goierrialdea: horarios estáticos del periodo 28/09–27/12/2026; fecha de cálculo validada **solo 29/09/2026**. Filas GO01 normalizadas, tiempos aproximados con timepoint=0. [Fuente oficial](https://opendata.euskadi.eus/transport/moveuskadi/lurraldebus/goierrialdea/gtfs_goierrialdea.zip).
- **HEALTH_REGISTRY**, Open Data Euskadi, referencia 20/09/2026: punto oficial entityBC631DA5 en EPSG:4326, no puerta ni asignación. [Registro](https://opendata.euskadi.eus/catalogo/-/centros-de-salud-publicos-en-euskadi/).
- **OSM**, adquirido 29/09/2026: derivación de red peatonal acotada. © OpenStreetMap contributors, [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/); geometría → longitud → fórmula, no paseo medido.
- **MODEL**, R5.1: 50 m/min + 120 s por enlace; **USER/MODEL_DEFAULTS**: hora, duración y márgenes. Un argumento enviado por el agente no demuestra elección humana.
- **HEALTH_PAGE/PADI_2026**, Osakidetza: referencias de identidad/dirección con conflicto conservado, observación 29/09/2026 / documento enero 2026. Reutilización específica NOT_VERIFIED: solo referencia/hash; no distribuir HTML/PDF originales. La reconciliación usa un derivado sanitario fijado, no es reproducción íntegramente raw.
- Capa municipal: Eustat/Gobierno Vasco y geoEuskadi/Open Data Euskadi según source ID y periodo de cada claim. No atribuir un resultado GTFS a Eustat, homogeneizar periodos ni interpretar proximidad como acceso real.

Hashes, columnas consumidas, fuentes por componente, licencias y transformaciones exactas: [ledger R8](https://github.com/Asier-Comba/Guipuzkoa360/blob/4bf975511ecea46c25662becfccb65713d381aa0/docs/vnext/w1/SOURCE_LEDGER_R8.json), [licencias R9](https://github.com/Asier-Comba/Guipuzkoa360/blob/4bf975511ecea46c25662becfccb65713d381aa0/docs/vnext/w1/SOURCE_LICENSE_R9.json) y `sources` de FINAL_MANIFEST.json adyacente; los informes R14 que allí se enumeran pertenecen al commit de auditoría PR19, no se presentan como resultados R15. Cada cifra sanitaria remite a los source_facts y numeric_claims del oráculo; total_s en segundos y resta segundo−primero /60 en minutos.

## Qué está y qué no está probado

El cálculo, variaciones de duración, tres orígenes, márgenes, legacy, opcionales y errores se prueban sin modelo. La comparación pareada v4/vNext solo cubre herramientas territoriales comunes sobre idénticos archivos e inputs; no mide conversación ni establece un ganador. Las visitas sanitarias y el registro de capacidades son añadidos vNext. La comparación sanitaria interna 2–4 permanece en ENGINE_CONTRACT, sin tool pública que acepte una lista de visitas. PUBLIC_AGENT_CONTRACT permite comparar ejecutando visitas individuales, observando sus resultados y comparando únicamente salidas válidas; **no anuncia batch público ni una comparación conversacional ya demostrada**.

La [evidencia real M05](https://github.com/Asier-Comba/Guipuzkoa360/blob/f4fd0a3c79ff2827c19a1200c0c76f7c5815eab7/resultados/vnext/r14/M05_normalized.json) prevalece: el agente añadió deadline vacío, recibió dos errores mobility:invalid_clock y no produjo cifra. Un tercer intento no pudo crear sandbox. Su respuesta honesta no equivale a completar el caso. No se atribuye causa a Studio, Luna ni al productor sin evidencia. RELEASE_GO=NO.

## Contrato público R15 frente al motor interno

`plan_visit` expone exactamente cinco argumentos obligatorios: `origin_id: str`, `destination_id: str`, `date: str`, `appointment_time: str` y `duration_minutes: int`. Los IDs se consultan en capacidades; fecha y hora usan `YYYY-MM-DD` y `HH:MM`, y la duración se expresa en minutos. No admite `request`, listas de visitas ni los opcionales internos como argumentos públicos.

`return_deadline`, `snapshot_id`, `walking_profile_id`, `arrival_margin_minutes` y `boarding_margin_minutes` no son decisiones que el LLM deba rellenar. Su riqueza se conserva en ENGINE_CONTRACT; la llamada pública omite esos campos y el productor conserva sus defaults documentados y su atribución MODEL_DEFAULTS. Legacy y sus opciones explícitas siguen siendo alcance del motor interno, no una selección pública que esta firma de cinco campos pueda prometer. No se convierten cadenas vacías en valores por defecto.

La capa territorial conserva sus herramientas. La reproducción R15 sobre R14 encontró que `periodo=""` ya se rechazaba, mientras espacios y fechas no soportadas producían cifras en acceso/simulación. La ausencia legítima de `periodo` no equivale a esos valores explícitos inválidos. La reproducción previa al parche está en `docs/vnext/w2/R15_PERIOD_REPRODUCTION.md`; cobertura y validación posterior se registran en `docs/vnext/w2/HANDOFF_R15.md`, sin atribuirlas al benchmark histórico R14.

En resumen, comparación municipal, envejecimiento y coincidencia, `periodo` selecciona demografía (`2025-01-01`); omitirlo o usar `None` solo aplica el único periodo disponible, y si hubiera varios debe pedirse selección, no elegir el más reciente. En acceso/simulación, los valores admitidos (`2026-09-20`, `2025-05-07`) son referencias de las fuentes actuales, no filtros históricos; omisión/`None` conserva sus periodos distintos. El catálogo público expone esta `period_policy`, su nullabilidad y valores permitidos. Cada cifra conserva el periodo de su propia fuente, sin homogeneizarlos.

`consultar_fuente` proyecta el `method` ya existente en el catálogo, junto a periodo y limitaciones. La derivación de 75+ por año de nacimiento sigue accesible; no se altera ninguna cifra, fórmula ni fuente para facilitar su explicación. Entre orígenes distintos la comparación es solo lado a lado, sin delta numérico; las diferencias condicionales numéricas requieren resultados válidos de alcance compatible y el mismo origen.

La identidad R15 está fijada por los hashes de FINAL_MANIFEST.json y su validación offline se registra en `docs/vnext/w2/HANDOFF_R15.md`. HEAD final y CI de ese mismo SHA se publican en el handoff del PR; no heredan el PASS de R14. El High real y los Medium históricos siguen abiertos hasta nueva evidencia del agente.

## Reproducir la evidencia histórica R14

En el checkout exacto `3a8e2b0948bb06df87af7a0f5769a369da568eff` de PR19, con CPython 3.12 y dependencias del repositorio:

```text
python -m scripts.mobility.final_public_release --package <ZIP_R14_EXACTO> --manifest <MANIFEST_R14_EXACTO> --output <temporal>
python -m scripts.mobility.build_final_delivery --benchmark <temporal> --output <temporal_entrega>
```

Descargar ZIP y manifiesto desde `historical_r14` de FINAL_MANIFEST.json; verificar sus hashes antes de ejecutar. Para el candidato R15 usar exclusivamente su identidad canónica y el procedimiento de su handoff, no reutilizar este PASS histórico. El benchmark no llama a Internet/modelo, no modifica runtime y no recibe holdout. Latencias son llamadas offline únicas, no tiempos del agente ni p95 fiable.
