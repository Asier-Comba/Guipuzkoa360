# Consumo sanitario R5 · contrato 0.3.0

Leer primero CURRENT.json. No inferir latest de archivos sin sufijo; CAPABILITY_DESCRIPTOR.json y RUNTIME_MANIFEST.json son históricos. R4 sigue disponible en su pin 725a7b7 y su entrada habitual, sin cambios.

## Entrada opt-in

```python
from prototypes.ir_y_volver.provider_r5 import get_capabilities, plan_visit, compare_visits
request = {
    "snapshot_id": "official-goierrialdea-go01-health-r5-20260929",
    "origin_id": "zegama_center_stops",
    "destination_id": "beasain_official_centre_anchor",
    "date": "2026-09-29",
    "appointment_time": "09:45",
    "duration_minutes": 20,
    "arrival_margin_minutes": 10,
    "boarding_margin_minutes": 3,
    "walking_profile_id": "poc_reference_50m_min_plus_120s"
}
result = plan_visit(request)
```

El dispatcher R5 usa salud por defecto. **Enviar snapshot_id explícito**. R4 explícito devuelve el mismo JSON 0.2.0 que provider.py, byte-equivalente al serializar del mismo modo. El export original del paquete no cambia: `from prototypes.ir_y_volver import plan_visit` continúa siendo R4. No cambiar imports W2 silenciosamente. Las capabilities R5 indican contrato, escenario y semántica por snapshot. Una comparación íntegramente R4 mantiene 0.2.0; una mixta devuelve 0.3.0 con resultados versionados y delta nulo.

## Qué copiar

Los 19 archivos exactos del RUNTIME_MANIFEST_R5.json, respetando directorios. Biblioteca estándar Python; sin conexión de red en ejecución. El ZIP incluye ambos contratos/snapshots y solo código necesario para ejecutarlos. No incluye tests, fuentes brutas, pack privado, matriz ni documentación de desarrollo.

## Contratos y unidades

`contracts/v0.3.0/*.schema.json` son JSON Schema draft 2020-12. NormalizedRequest, Leg, Itinerary, TimelineComponent, SourceReference, ErrorEnvelope, WalkingLinkEvidence, HealthDestinationEvidence, SnapshotCapability y ComparisonPair tienen propiedades explícitas cerradas. La rama LegacyR4Result conserva deliberadamente el contrato antiguo, no se anuncia como endurecimiento retroactivo de 0.2.0. El evaluador estándar independiente se usó en QA; el runtime incorpora un evaluador limitado al subconjunto de schema emitido, sin dependencia externa.

Tiempos: segundos desde medianoche Europe/Madrid de la fecha validada; duraciones enteras en segundos; entradas duration/margins en minutos enteros; coordenadas `[lat,lon]` EPSG:4326; distancias en metros crudos. No redondear distancias antes de `ceil(m/50)*60+120`. El buffer 120 s pertenece una sola vez a cada enlace completo parada→anchor o anchor→parada, no a cada conector.

Itinerary guarda las filas identificables por trip_id y stop_sequence, horas originales y timepoint. Los ocho componentes son contiguos; total=end-start=suma. return_slack=salida de vuelta-fin de consulta-paseo de vuelta-margen de embarque, siempre >=0 en resultados ok. La espera de regreso incluye el margen, no se añade nuevamente. No es probabilidad ni garantía contra retrasos.

## Procedencia y comunicación obligatoria

SourceReference separa GTFS, registro, ficha sanitaria, PADI conflictivo, OSM, parámetros, usuario y cálculo. Cada timeline component tiene source_refs. `walking` contiene nodos/vías por tramo, geometría con ambos conectores y tags relevantes; no dibujar una ruta distinta. Geometry[1:-1] es la red, los extremos restantes son conectores modelados.

**El paseo termina en un punto de referencia modelado del centro; no representa una puerta física verificada.** Mostrar entrada no verificada, modelo 50 m/min, márgenes y horarios aproximados. No domicilio, asignación sanitaria, capacidad/citas, realtime, accesibilidad universal ni velocidad deducida de edad. El conflicto Bernedo Enea 1/PADI Zaldizurreta 2 permanece visible y requiere revisión humana; no se infiere traslado. Cruces/pendientes/condiciones temporales no se convierten en tiempos medidos.

Solo tres orígenes R4, tres paradas destino admitidas, GO01 directa y 29/09/2026. Los estados unknown/unsupported/no_feasible_journey no equivalen a inexistencia de transporte. Fuera del bbox no significa desconexión real. La comparación conserva ambos resultados; delta solo para misma fecha/origen/destino/snapshot/perfil, ambos ok. Parámetros cambiados y constantes quedan enumerados.

## Reconstrucción y verificación

Desde el pin, sin refrescar fuentes:

```text
python -m scripts.mobility.build_contract_r5
python -m scripts.mobility.build_health_r5
python -m pytest tests/mobility -o addopts= -q
python -m scripts.mobility.verify_health_r5
python -m scripts.mobility.package_r5 --output <directorio-temporal>/w1-r5.zip
```

Se leen GTFS bruto conservado, snapshot R4, registro sanitario conservado, derivado OSM público y capturas oficiales R5. No hace falta el OSM privado original ni el pack privado para reconstruir. Si se recupera el OSM R4 completo, su hash debe coincidir. No volver a descargar sobre archivos fijados: una adquisición nueva requiere nuevo snapshot/evaluación. La captura HTML se preserva en binario para evitar que Git cambie los bytes con saltos de línea. Para la identidad OSM R5 se usa el XML público normalizado a LF, no el hash dependiente del checkout CRLF; esta transformación se declara en sources y no modifica la adquisición histórica.

Para W2: adaptar de forma explícita validación/pins/import y provenance del sobre; no activar movilidad en portal aún. Corregir previamente los hallazgos CRITICAL/HIGH de PR17. Para W3: REAL_CASES_R5.json aporta fixtures públicos offline; validar independientemente el pin antes de afirmar aceptación del producto. No se han leído ni enviado preguntas holdout. Este paquete no contiene un agente LLM ni acredita pruebas del portal.
