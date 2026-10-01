# Evidencia vigente R16: cálculo, agente real y borrador

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
