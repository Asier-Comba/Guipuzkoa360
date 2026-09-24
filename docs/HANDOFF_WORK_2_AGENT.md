# Handoff — Work 2 Agent

## Estado de integración

Integrado con `work/data-foundation` de Work 1 el 24/09/2026. La rama conserva los commits originales de Work 2
`419a427` y `b197c32` y la historia completa de Work 1. No se modificó la rama remota de Work 1.

Datos reales cargados: 88 municipios, 148 centros sanitarios públicos, demografía 2025-01-01, geometría
2025-05-07 y servicios 2026-09-20. Los fixtures `TEST_*` siguen aislados bajo `tests/fixtures/`.

## Arquitectura

Un coordinador LangChain creado por `build_agent(model)` y siete herramientas deterministas. `data_access.py`
normaliza aliases, valida esquema/tipos/claves y resuelve municipios. `metrics.py` contiene distancia euclídea
EPSG:25830, conversión WGS84→UTM 30N para puntos hipotéticos, cuantiles y rangos percentiles. `tools.py`
compone salidas homogéneas y errores controlados. No hay Internet ni secretos en runtime.

## Herramientas

- `obtener_resumen_territorial(municipio, periodo)`
- `comparar_municipios(municipios, grupo_edad, categoria_servicio, umbral_km, periodo)`
- `analizar_envejecimiento(grupo_edad, medida, periodo, top_n)`
- `analizar_acceso_servicios(categoria_servicio, umbral_km, periodo, municipios)`
- `analizar_coincidencia(categoria_servicio, grupo_edad, umbral_km, periodo, cuantil)`
- `simular_escenario(accion, categoria_servicio, ..., latitud, longitud, service_id, nuevo_umbral_km)`
- `consultar_fuente(source_id)`

Acciones de escenario: `add_service`, `remove_service`, `change_threshold`. Cada salida sigue
`docs/RESULT_SCHEMA.md`.

## Métrica territorial integrada

La proximidad es **distancia geométrica aproximada desde el punto representativo municipal**: distancia
euclídea en EPSG:25830 entre `representative_point()` del polígono y el servicio más cercano. Unidad: metros.
Los cálculos del agente reproducen las columnas precomputadas de Work 1 para atención primaria y hospitales
con tolerancia de 0,1 m. No es distancia por red, tiempo de viaje ni acceso real.

`runtime_municipality_points.csv` y las coordenadas proyectadas añadidas a `runtime_servicios.csv` permiten
recalcular altas/bajas hipotéticas con la misma métrica sin GeoPandas en el runtime del portal.

## Pruebas ejecutadas

Comando:

```text
py -m pytest
```

Resultado del release candidate: **56 passed** en Python y **17 passed** en la suite Node/HTML. Incluye las pruebas originales de Work 2, las pruebas de integridad
de Work 1 y nuevas pruebas reales de carga, tipos, cobertura, reproducción de distancias, comparación municipal,
escenario, conversión de coordenadas, fuentes y trazabilidad.

Contraste manual automatizado: Donostia / San Sebastián tiene **183.388 habitantes** tanto en
`datos_originales/eustat_demografia_2025.csv` como en el registro preparado. Fuente: `EUSTAT_EMH_2025`, periodo
2025-01-01. El registro de Work 1 contiene además Eibar 27.118, Tolosa 20.048 y 148 centros, todos `PASS`.

## Datos y fuentes

- `municipios.csv`: tabla analítica y métricas precomputadas.
- `demografia.csv`: población total, 65+, 75+ y porcentajes.
- `runtime_municipality_points.csv`: puntos representativos en WGS84 y EPSG:25830.
- `runtime_servicios.csv`: servicios con coordenadas WGS84/EPSG:25830, periodo y fuente.
- `metadata_sources.json`: tres fuentes oficiales y el registro derivado.

La población 75+ se deriva de año de nacimiento <=1949. Los periodos no son idénticos (máximo 627 días).

## Contrato para Work 3

Definido en `docs/RESULT_SCHEMA.md`. Unir siempre por `municipality_code`. Para mapas usar
`runtime_municipios.geojson`; para puntos, `runtime_servicios.csv`. No recalcular métricas en la interfaz ni
convertir ausencias en cero. Ejemplos reales reproducibles en `docs/examples/`, regenerables con:

```text
py scripts/agent/generate_examples.py
```

## Preparación para el portal

`main.py` mantiene `build_agent(model)` síncrono, `create_agent`, siete tools, 8 iteraciones, memoria activa,
Internet desactivado y contexto explícito. El runtime incluye solo código, metodología, contrato y CSV/JSON
ligeros; excluye originales, tests y el GeoJSON maestro. Ejecutar `scripts/agent/build_portal_package.py` para
crear el ZIP y revisar su informe de tamaño antes de subir.

Secuencia oficial: editar → tests → comprobar preparación → crear versión → probar esa versión → seleccionarla.
Crear una versión no publica la entrega ni sustituye automáticamente una versión seleccionada.

## Limitaciones

- Punto municipal no ponderado por población.
- Sin red viaria/peatonal, tiempos, horarios, capacidad, citas, calidad, demanda o accesibilidad universal.
- Coincidencia no implica causalidad ni necesidad individual.
- Escenario no es predicción ni recomendación administrativa.
- Periodos de demografía, geometría y servicios distintos.

## Pendientes

1. Copiar el paquete en el borrador del portal siguiendo `docs/PORTAL_DEPLOYMENT.md`.
2. Crear una versión fija y ejecutar los ocho casos A–H con el modelo del portal.
3. No publicar la entrega hasta autorización expresa del equipo.
