# Evidencia para comprender el resultado

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
