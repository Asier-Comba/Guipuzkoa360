# Datos preparados

Snapshot real y auditado: 88 municipios de Gipuzkoa y 148 registros sanitarios públicos. No es un marcador de integración pendiente.

| Archivo | Una fila representa | Uso |
|---|---|---|
| municipios.csv | Municipio, código de cinco caracteres | Indicadores agregados y trazabilidad |
| demografia.csv | Municipio y periodo 2025-01-01 | Población y denominadores |
| runtime_municipality_points.csv | Punto representativo municipal | Cálculo geométrico |
| runtime_servicios.csv | Registro sanitario, service_id único | Proximidad y escenarios |
| metadata_sources.json | Catálogo de fuentes y derivación | Procedencia y periodos |
| data_contract.json | Contrato de datos 1.1.0 | Tipos, claves e invariantes |
| runtime_manifest.json | Siete archivos con tamaños y hashes | Integridad |
| runtime_municipios.geojson | Polígono municipal simplificado | Visualización local opcional |
| municipios.geojson, servicios.csv | Geometría maestra / servicio enriquecido | Auditoría, no paquete del portal |

El ZIP conversacional no incluye el GeoJSON opcional ni los maestros. El manifiesto abarca siete archivos de datos, mientras el paquete contiene catorce miembros y el contexto declarado tiene diez archivos: son conjuntos distintos.

[Fuentes](../FUENTES.md) · [Validación](../docs/VALIDATION.md) · [Reproducción](../README.md#reproducir).
