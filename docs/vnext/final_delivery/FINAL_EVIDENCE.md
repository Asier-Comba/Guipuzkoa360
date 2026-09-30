# Evidencia para comprender el resultado

Pregunta principal: ¿Cómo cambia la carga temporal de una visita sanitaria para personas que dependen del transporte público cuando cambia el municipio de origen, la hora de la cita o su duración?

Caso contrastado **offline**, no respuesta sanitaria del agente real: Zegama → punto oficial modelado del Ambulatorio de Beasain, 29/09/2026.

| Escenario | Duración consulta | Carga temporal programada/modelada |
|---|---:|---:|
| Cita 09:30 | 20 min | 10.691 s |
| Cita 09:45 | 20 min | 8.591 s |
| Segundo menos primero | sin cambio | −2.100 s / −35 min |

Los tres valores proceden del [oráculo público R13 fijado](https://github.com/Asier-Comba/Guipuzkoa360/blob/4bf975511ecea46c25662becfccb65713d381aa0/docs/vnext/w1/FINAL_ORACLE_R13.json), contrastado con filas GTFS y geometría/fórmula. R14 conserva productor y datos; el benchmark final vuelve a contrastar cifras, componentes, fuentes, periodos y límites con ese oráculo. No se ha abierto el holdout.

La carga abarca presencia en parada de origen → llegada a parada de regreso, no domicilio → domicilio. Se suman ocho componentes: espera inicial, vehículo de ida, paseo de ida, espera previa, consulta, paseo de vuelta, espera de regreso y vehículo de vuelta. La consulta usa minutos × 60; el paseo usa ceil(metros/50) × 60 + 120 por enlace completo y sentido. Las unidades se conservan, no se deduce tiempo de una distancia geométrica.

## Fuente → transformación → cifra

- **GTFS**, Moveuskadi/Goierrialdea: horarios estáticos del periodo 28/09–27/12/2026; fecha de cálculo validada **solo 29/09/2026**. Filas GO01 normalizadas, tiempos aproximados con timepoint=0. [Fuente oficial](https://opendata.euskadi.eus/transport/moveuskadi/lurraldebus/goierrialdea/gtfs_goierrialdea.zip).
- **HEALTH_REGISTRY**, Open Data Euskadi, referencia 20/09/2026: punto oficial entityBC631DA5 en EPSG:4326, no puerta ni asignación. [Registro](https://opendata.euskadi.eus/catalogo/-/centros-de-salud-publicos-en-euskadi/).
- **OSM**, adquirido 29/09/2026: derivación de red peatonal acotada. © OpenStreetMap contributors, [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/); geometría → longitud → fórmula, no paseo medido.
- **MODEL**, R5.1: 50 m/min + 120 s por enlace; **USER/MODEL_DEFAULTS**: hora, duración y márgenes. Un argumento enviado por el agente no demuestra elección humana.
- **HEALTH_PAGE/PADI_2026**, Osakidetza: referencias de identidad/dirección con conflicto conservado, observación 29/09/2026 / documento enero 2026. Reutilización específica NOT_VERIFIED: solo referencia/hash; no distribuir HTML/PDF originales. La reconciliación usa un derivado sanitario fijado, no es reproducción íntegramente raw.
- Capa municipal: Eustat/Gobierno Vasco y geoEuskadi/Open Data Euskadi según source ID y periodo de cada claim. No atribuir un resultado GTFS a Eustat, homogeneizar periodos ni interpretar proximidad como acceso real.

Hashes, columnas consumidas, fuentes por componente, licencias y transformaciones exactas: [ledger R8](https://github.com/Asier-Comba/Guipuzkoa360/blob/4bf975511ecea46c25662becfccb65713d381aa0/docs/vnext/w1/SOURCE_LEDGER_R8.json), [licencias R9](https://github.com/Asier-Comba/Guipuzkoa360/blob/4bf975511ecea46c25662becfccb65713d381aa0/docs/vnext/w1/SOURCE_LICENSE_R9.json) y FINAL_MANIFEST.json adyacente. Cada cifra sanitaria remite a los source_facts y numeric_claims del oráculo; total_s en segundos y resta segundo−primero /60 en minutos.

## Qué está y qué no está probado

El cálculo, variaciones de duración, tres orígenes, márgenes, legacy, opcionales y errores se prueban sin modelo. La comparación pareada v4/vNext solo cubre herramientas territoriales comunes sobre idénticos archivos e inputs; no mide conversación ni establece un ganador. Las visitas sanitarias y el registro de capacidades son añadidos vNext. La comparación sanitaria interna 2–4 no tiene tool pública para una lista de visitas: **no se anuncia como capacidad pública demostrada**.

La [evidencia real M05](https://github.com/Asier-Comba/Guipuzkoa360/blob/f4fd0a3c79ff2827c19a1200c0c76f7c5815eab7/resultados/vnext/r14/M05_normalized.json) prevalece: el agente añadió deadline vacío, recibió dos errores mobility:invalid_clock y no produjo cifra. Un tercer intento no pudo crear sandbox. Su respuesta honesta no equivale a completar el caso. No se atribuye causa a Studio, Luna ni al productor sin evidencia. RELEASE_GO=NO.

## Reproducir

En el checkout del SHA de auditoría publicado, con CPython 3.12 y dependencias del repositorio:

```text
python -m scripts.mobility.final_public_release --package <ZIP_R14_EXACTO> --manifest <MANIFEST_R14_EXACTO> --output <temporal>
python -m scripts.mobility.build_final_delivery --benchmark <temporal> --output <temporal_entrega>
```

Descargar ZIP y manifiesto desde los enlaces exactos de FINAL_MANIFEST.json; verificar sus hashes antes de ejecutar. El benchmark no llama a Internet/modelo, no modifica runtime y no recibe holdout. Latencias son llamadas offline únicas, no tiempos del agente ni p95 fiable.
