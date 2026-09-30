# R4 · acceso, lectura y procedencia

Fecha: 2026-09-29. No se publican formación privada, correos ni cuentas de
contribuidores OSM. Se publican conclusiones técnicas y fuentes públicas.

## Acceso comprobado

- Lectura/escritura local: checkout W1 separado, limpio al iniciar; nuevo contrato
  escrito y ejecutado. Origin Asier-Comba/Guipuzkoa360 verificado; fetch realizado.
- GitHub: lectura live de PR #15/#17/#14 y comentarios de #16; push de contrato
  y comentario de coordinación realizados. Ningún merge.
- Ejecución: Python y Node disponibles. `jsonschema` no estaba instalado; se usó
  un directorio temporal aislado para validar schemas sin cambiar dependencias.
- Descarga: OSM map API devolvió XML real; bytes y hash en HEALTH_DESTINATION_R4.
  GTFS es copia exacta conservada de R2, no descarga nueva fingida.

## Lecturas realizadas y brechas

Lectura completa: misión R4 y misiones locales W1 previas; provider.py,
builder GO01, contratos 0.1.0 y ejemplo, test_provider.py, verify_w1.py,
descriptor, manifiesto, handoff y decisión de datos R2. REAL_CASES se leyó y se
reconcilió fila a fila en verify_r4. Lectura W2 mobility_adapter y sus tests
en f4615b36d0af93966e6ca0f2044288841e6574b8. Lectura W3 query_w1_offline,
PRODUCT_CONTRACT_R3, test_custom_query y los nueve casos C-R3 en
cf9cd0afadc97b255c021a4ff867dab7ae6dabbc. Sus esperados no se modifican.

Existe un volcado local oficial 2026-09-29. Se leyeron su manifiesto, gaps y
literal Urban Challenge; se buscó Beasain/ambulatorio/7214 en el ejemplo
resuelto, que no contiene la PoC de este corredor. Este volcado no es el
paquete privado 00–12 requerido. No se afirma haber leído sus 73 lecciones
en R4. Búsqueda acotada en el workspace y adjuntos: no se localizaron
START_HERE, master, estado técnico completo, feedback CityScope, orquestación,
PoC textual específica ni ZIP original de la PoC. Sus nombres pueden referir
secciones de un paquete no montado. La misión R4 permite continuar reparación
independiente; no se inventan esos contenidos.

`ORIGINAL_ARCHIVE=NOT_AVAILABLE`. GTFS conservado rehasheado y leído como CSV:
811289 bytes; SHA-256
3276fcae7bfa5002a39a2a094fef6637603de2e50648a46a436b314db27832a4.
`GTFS_COMPONENT_IDENTIFIED`: coincide con el hash que el coordinador atribuye
al componente histórico; no se dispone del manifiesto histórico original para
una segunda comprobación independiente. No identifica el ZIP completo ni OSM.

## Fuentes primarias

- Semántica GTFS consultada live:
  https://gtfs.org/documentation/schedule/reference/#stop_timestxt
  Permisos 0/vacío ordinarios; 1 prohibido; 2/3 sujetos a coordinación. Los
  últimos no se promueven como ordinarios. Timepoint 0 aproximado, 1 exacto;
  ausencia se trata como exacto según la especificación, no como aproximación.
- GTFS original: URL y metadata de adquisición preservadas en
  R4_SOURCE_METADATA.json. Raw ZIP en datos_originales/movilidad. El builder
  recibe metadata, exige el hash indicado y rechaza sobrescribir snapshots.
- Centro: XLSX oficial ya conservado (hash en HEALTH_DESTINATION_R4) y fila
  entityBC631DA5; nombre/dirección contrastados live con Osakidetza:
  https://www.osakidetza.euskadi.eus/ambulatorio-de-beasain/centro-salud/webosk00-cercon/es/
  Fuente sanitaria 2026-09-20, no fecha de una cita. Las filas entity24E39531 y
  entity38D83782 comparten coordenadas; no son entradas peatonales alternativas.
- OSM nuevo: bounding box explícito, consulta única; 6400 nodos y 867 ways.
  Way 42927929, ref:osakidetza=ambulat_beasain. No entrada etiquetada en el
  edificio. Se conserva respuesta original local, excluida de Git por metadatos
  de cuentas de contribuidores; derivado público elimina user/uid/changeset.
  No se construye un tramo recto ni se unen componentes desconectados.

## Reutilización y límites

Open Data Euskadi: https://opendata.euskadi.eus/como-reutilizar/-/reutilizar-datos-abiertos/
Los términos generales permiten reutilización con atribución y respeto a las
condiciones particulares. Se conserva Gobierno Vasco/Moveuskadi, URL, fecha y
hash, y se distingue el derivado del original. La ficha concreta no aporta un
SPDX específico: no se inventa uno ni se trata su ausencia como prohibición.
El matiz de condiciones particulares permanece como riesgo de revisión humana.

OSM: OpenStreetMap contributors, ODbL 1.0;
https://www.openstreetmap.org/copyright. El derivado de red conserva atribución,
identificadores, geometría y tags técnicos; no se incluye en runtime. No implica
precisión empírica, ruta peatonal validada ni accesibilidad universal.
