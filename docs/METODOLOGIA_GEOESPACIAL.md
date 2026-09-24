# Metodología geoespacial

## Unidad de análisis

Municipio (88 unidades). Se eligió por disponer de demografía y geometría con código común estable. No se adopta sección censal ni malla porque en esta entrega no se ha verificado una distribución espacial de población 65+/75+ compatible y actualizada.

## Escalera de accesibilidad alcanzada

1. **Disponibilidad municipal**: número de centros por categoría y centros de atención primaria por 10.000 residentes de 65+.
2. **Proximidad geométrica aproximada**: distancia euclídea en metros desde un punto interior representativo del polígono municipal hasta el centro más cercano de la categoría, calculada en EPSG:25830.

No se calcula cobertura de población, distancia por red, tiempo de viaje, frecuencia de transporte ni disponibilidad real. El punto representativo no está ponderado por población; en municipios extensos puede quedar lejos del núcleo habitado. Por ello el campo debe describirse literalmente como **distancia geométrica aproximada desde el punto representativo municipal**.

## CRS

- Fuente geométrica y cálculos métricos: ETRS89 / UTM zona 30N, EPSG:25830.
- Intercambio GeoJSON y coordenadas de servicios: WGS84, EPSG:4326.

EPSG:25830 es adecuado para distancias locales en Gipuzkoa y coincide con la proyección de la fuente administrativa.

## Escenarios soportados

Los archivos permiten cambiar umbral demográfico (65+/75+), categoría de servicio, comparar municipios y añadir/retirar en memoria puntos hipotéticos. Para nuevos umbrales de distancia debe recalcularse sobre las geometrías/puntos; no se debe interpretar el indicador actual como tiempo real.

## Periodos

Demografía 2025-01-01; geometría 2025-05-07; servicios 2026-09-20. La separación máxima es 627 días. Se acepta para una demo exploratoria, se muestra explícitamente y no se afirma simultaneidad perfecta.

