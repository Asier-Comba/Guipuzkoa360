# Handoff — Work 2 Agent

## Arquitectura

Un coordinador LangChain creado por `build_agent(model)` y siete herramientas deterministas. `data_access.py`
normaliza aliases, valida esquema/tipos/claves y resuelve municipios. `metrics.py` contiene Haversine, cuantiles
y rangos percentiles. `tools.py` compone salidas homogéneas y errores controlados. No hay Internet ni secretos.

## Herramientas

- `obtener_resumen_territorial(municipio, periodo)`
- `comparar_municipios(municipios, grupo_edad, categoria_servicio, umbral_km, periodo)`
- `analizar_envejecimiento(grupo_edad, medida, periodo, top_n)`
- `analizar_acceso_servicios(categoria_servicio, umbral_km, periodo, municipios)`
- `analizar_coincidencia(categoria_servicio, grupo_edad, umbral_km, periodo, cuantil)`
- `simular_escenario(accion, categoria_servicio, ..., latitud, longitud, service_id, nuevo_umbral_km)`
- `consultar_fuente(source_id)`

Todas devuelven el contrato de `docs/RESULT_SCHEMA.md`. Acciones de escenario válidas: `add_service`,
`remove_service`, `change_threshold`.

## Datos esperados

`municipios.csv`, `demografia.csv`, `servicios.csv`, `metadata_sources.json` y opcionalmente
`municipios.geojson`. Los aliases aceptados están declarados en `data_access.py`. Son obligatorios códigos,
nombres, periodo y `source_id`; los porcentajes pueden derivarse de recuento/población total cuando existan.

## Pruebas

Desde la raíz:

```text
python -m pytest
```

Las pruebas cubren archivos/columnas ausentes, códigos de texto, NA, duplicados, edades 65/75, categorías,
municipios sin servicio, comparaciones, escenarios, trazabilidad y no invención. Los diez golden cases están
en `tests/golden_cases.json`; la conversación real debe ejecutarse después contra una versión del portal.

## Compatibilidad con el portal

Implementado: `main.py`, función síncrona `build_agent(model)`, `create_agent`, 7 tools, Internet desactivado,
8 iteraciones, rutas relativas y contexto explícito. Pendiente hasta disponer de datos reales/subida: ejecutar
“Comprobar preparación”, crear versión y ejecutar golden tests en el banco de Pruebas. Nunca asumir que editar
el borrador actualiza una versión existente.

## Datos sintéticos

Solo `tests/fixtures/`; municipios `TEST_*`, fuentes `SRC_TEST_*`. No incluirlos en la versión final ni describir
sus resultados como Gipuzkoa.

## Integración con Work 1

Seguir `docs/REAL_DATA_INTEGRATION.md`, corregir todos los errores de contrato, contrastar una cifra y actualizar
`FUENTES.md`. No sobrescribir originales.

## Contrato para Work 3

Usar `docs/RESULT_SCHEMA.md`. La visualización consume `data`, `sources`, `method`, `limitations` y el bloque
opcional `scenario`; no recalcula métricas ni interpreta ausencias como cero.

## Limitaciones

La métrica base es distancia geodésica centroide-punto. No modela red, tiempos, horarios, capacidad, calidad,
accesibilidad universal, demanda ni conducta. Coincidencia no implica causalidad. Escenario no implica impacto.

## Git y portal

Rama prevista: `work/agent-engine`. Secuencia: editar → tests → comprobar preparación → crear versión → probar
esa versión → seleccionarla para entrega. Publicación final y selección de entrega quedan fuera de este handoff.
