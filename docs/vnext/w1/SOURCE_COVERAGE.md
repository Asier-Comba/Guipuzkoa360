# Cobertura y trazabilidad de fuentes W1

## Demostrado

- Fuente **OFFICIAL**: Gobierno Vasco / Moveuskadi, feed Lurraldebus Goierrialdea.
- Adquisición **VERIFIED_LIVE** el 2026-09-29 desde el índice oficial: el ZIP canónico y la copia previamente obtenida son idénticos por tamaño y SHA-256.
- Ruta seleccionada: GO01 (`route_id=1`).
- Volumen derivado: 162 viajes y sus filas de paradas GO01; el feed completo tenía 10 rutas y 203 paradas.
- Calendarios presentes: `S`, `D`, `LJ`, `V`. `calendar_dates.txt` no existe en el ZIP; esto se registra como ausencia, no como corrupción.
- Todos los tiempos GO01 examinados declaran `timepoint=0`; por ello son horarios programados aproximados/interpolados, no puntualidad observada.
- Paradas de origen: Zegama `8305/8309`, Segura `7801/7813`, Idiazabal `7903/7906`.
- Destino piloto: llegada `7214` y regreso `7218`, centro de Beasain.
- Diez consultas se contrastan contra un oráculo independiente en `tests/mobility/test_provider.py` y se materializan en `REAL_CASES.json`.

## No demostrado

- `ORIGINAL_POC_REPRODUCTION=BLOCKED`: no se localizaron el ZIP original ni los conectores GTFS/OSM de la PoC.
- El destino no es el Ambulatorio de Beasain. No se modela ni se inventa el paseo entre parada y centro sanitario.
- No se demuestra cobertura desde domicilios, accesibilidad universal, puntualidad, disponibilidad, ahorro sanitario ni comportamiento en festivos.
- El feed nominalmente cubre más fechas, pero R2 solo valida el 2026-09-29.
- No se han reproducido los 135 escenarios ni los 14 tests históricos.
- No se cargaron variables Eustat en este proveedor. 50+/70+, edad cumplida, vivienda y demografía están **NO DISPONIBLES** aquí y deben permanecer en los proveedores propietarios.

## Clasificación documental

- **OFFICIAL**: catálogo, índices y feeds Moveuskadi.
- **VERIFIED_LIVE**: hashes y timestamps obtenidos el 2026-09-29.
- **HISTORICAL**: afirmaciones de la PoC sobre GO01, ambulatorio, 135 escenarios y 14 tests; no cuentan como ejecución actual.
- **EXTERNAL_FEEDBACK**: recomendaciones CityScope/correos, sin autoridad sobre los datos.
- **PROPOSAL**: realtime, transbordos u otras fechas/destinos hasta que tengan evidencia y contrato propios.
