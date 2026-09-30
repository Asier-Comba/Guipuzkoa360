# R5: propuesta de contrato 0.3.0

Estado: PROPOSAL, no pin sanitario listo. R4 0.2.0 y su paquete permanecen congelados en `725a7b73ae0381092cd80edc41b8a25432d75fcd`.

## Niveles de evidencia

| Campo | Valores |
|---|---|
| CENTRE_IDENTITY | CONFIRMED / CONFLICTED / UNKNOWN |
| CENTRE_ANCHOR | CONFIRMED_OFFICIAL_POINT / DERIVED_BUILDING_POINT / UNKNOWN |
| MODELLED_NETWORK_ACCESS | PASS / FAIL / UNKNOWN |
| ENTRANCE_VERIFICATION | VERIFIED / NOT_VERIFIED / CONFLICTED |
| DOOR_TO_DOOR | UNAVAILABLE |
| HEALTH_MODELLED_ACCESS_GO | YES / NO |
| HEALTH_VERIFIED_ENTRANCE_GO | YES / NO |
| PRODUCT_HEALTH_JOURNEY_GO | YES_WITH_MODELLED_ACCESS_LIMIT / NO |

Texto obligatorio para consumidores: «El paseo termina en un punto de referencia modelado del centro; no representa una puerta física verificada». No certifica accesibilidad, adscripción, citas ni condiciones reales del recorrido.

## Decisión contractual

0.3.0 incorpora `health_visit`, evidencia de conectores y red, procedencia por componente y objetos anidados cerrados. No es un parche compatible 0.2.1. Los schemas 0.2.0 NO se reescriben. Se implementará un punto de entrada separado `provider_r5`, con delegación intacta al proveedor 0.2.0 para el snapshot R4; los consumidores deben validar según `schema_version`, nunca reinterpretar stop-only como salud.

Objetos nuevos cerrados: NormalizedRequest, Leg, Itinerary, TimelineComponent, SourceReference, ErrorEnvelope, WalkingLinkEvidence, HealthDestinationEvidence, SnapshotCapability y ComparisonPair. Cada referencia distinguirá horario oficial, registro sanitario, ficha sanitaria, red abierta, parámetro del modelo, input humano y cálculo derivado. Duración de consulta es input, no dato sanitario.

## Política del modelo

Punto oficial `entityBC631DA5`, EPSG:4326, no entrada. Nodo admisible más cercano, desempate por ID, conector geodésico <=100 m en ambos extremos, sin resnap para salvar componentes desconectados. Dijkstra dirigido sobre vías admitidas; geometría y cálculo comparten nodos/vías. Duración de cada enlace completo y sentido: `ceil(metros_crudos/50)*60+120`. No velocidad inferida por edad.

Selección: mínimo intervalo presencia en parada origen → llegada a parada retorno; empate por metros caminados, horarios e IDs. Se conservan ocho componentes y slack tras descontar paseo y margen de embarque. Solo GO01 directa, fecha validada 2026-09-29.

## Conflicto oficial de dirección

Consulta live 2026-09-29: [ficha específica](https://www.osakidetza.euskadi.eus/ambulatorio-de-beasain/webosk00-cercon/es/) publica Bernedo Enea 1, teléfono 943027700. [PADI enero 2026, página 4](https://www.osakidetza.euskadi.eus/contenidos/informacion/salud_padi/es_def/adjuntos/padi-kontsultak-gipuzkoa.pdf) publica Zaldizurreta 2 y el mismo teléfono en un listado de consultas dentales. No demuestra traslado ni que sean edificios distintos, ni prueba que la dirección sea exclusivamente de un servicio separado.

Clasificación: `conflicting_current_sources`, revisión humana pendiente. Precedencia explícita: ficha específica actual + registro sanitario versionado para el punto; publicación PADI se conserva como conflicto, no se elige por orden de lectura. No se declara resuelto por coincidencia de teléfono.

## Coordinación

Preflight: W1 limpio en 725a7b7; W2 f4615b36d0af93966e6ca0f2044288841e6574b8 y W3 cf9cd0afadc97b255c021a4ff867dab7ae6dabbc siguen vigentes. Leídos PR15/17/14 e Issue16 y comentarios. W3 comunica fallos W2 de binding municipal (CRITICAL) y procedencia de numerador sanitario (HIGH): propietarios W2, no corregidos por esta propuesta. W1_HEALTH_PIN_READY=NO hasta pruebas, paquete y handoff. No portal, merge ni integración.
