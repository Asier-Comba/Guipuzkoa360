# Metodología geoespacial

## Unidad de análisis

Municipio (88 unidades). Se eligió por disponer de demografía y geometría con código común estable. No se adopta sección censal ni malla porque en esta entrega no se ha verificado una distribución espacial de población 65+/75+ compatible y actualizada.

## Escalera de accesibilidad alcanzada

1. **Registros municipales**: número de registros por cada categoría (`primary_care`, `hospital`, `mental_health`, `other_health`) y tasa por 10.000 residentes de 65+ o 75+. No mide disponibilidad.
2. **Proximidad geométrica aproximada**: distancia euclídea en metros desde un punto interior representativo del polígono municipal hasta el centro más cercano de cada categoría, calculada en EPSG:25830.

No se calcula cobertura de población, distancia por red, tiempo de viaje, frecuencia de transporte ni disponibilidad real. El punto representativo no está ponderado por población; en municipios extensos puede quedar lejos del núcleo habitado. Por ello el campo debe describirse literalmente como **distancia geométrica aproximada desde el punto representativo municipal**.

## CRS

- Fuente geométrica y cálculos métricos: ETRS89 / UTM zona 30N, EPSG:25830.
- Intercambio GeoJSON y coordenadas de servicios: WGS84, EPSG:4326.

EPSG:25830 es adecuado para distancias locales en Gipuzkoa y coincide con la proyección de la fuente administrativa.

## Escenarios soportados

Los archivos permiten cambiar grupo demográfico (65+/75+), categoría de servicio, comparar municipios y añadir/retirar en memoria puntos hipotéticos. `representative_point_longitude/latitude` y `runtime_servicios.csv` permiten recalcular un escenario en EPSG:25830. El resultado es `min(distancia_base, distancia_al_punto_hipotético)` para una adición; una retirada exige eliminar por `service_id` y recalcular contra el resto. Nunca se modifica el dato observado ni se presenta la hipótesis como servicio existente.

Para nuevos umbrales de distancia se compara el valor en metros tras una conversión explícita a kilómetros (`/1000`); no se debe interpretar el indicador como tiempo real. Las tasas se calculan por separado para cada denominador y no deben mezclarse entre 65+ y 75+.

## Periodos

Demografía 2025-01-01; geometría 2025-05-07; servicios 2026-09-20. La separación máxima es 627 días. Se acepta para una demo exploratoria, se muestra explícitamente y no se afirma simultaneidad perfecta.

## Errores de interpretación que bloquean una respuesta

- Llamar “accesibilidad” a una distancia euclídea o convertirla en minutos.
- Interpretar `services_* = 0` como imposibilidad de acceso.
- Sumar porcentajes municipales o comparar conteos sin sus denominadores.
- Ocultar que los periodos difieren.
- Tratar dos registros con la misma coordenada como duplicados si sus `service_id` o categorías son distintos.
- Reemplazar un nulo por cero. El snapshot auditado no contiene nulos; un nulo futuro debe provocar fallo.
