# Integración de datos reales

1. Conservar los originales sin cambios en `datos_originales/`.
2. Preparar los cinco archivos contractuales en `datos_preparados/` y registrar transformaciones en
   `FUENTES.md` y `metadata_sources.json`.
3. Mantener códigos territoriales como texto. Comprobar tipos, periodos, unidades, ausencias y duplicados.
4. Instanciar `DataRepository("datos_preparados")` y cargar `municipalities()`, `demography()`, `services()` y
   `metadata()`; cualquier error debe corregirse en la preparación, no ocultarse.
5. Ejecutar `python -m pytest` desde la raíz `gipuzkoa360/`.
6. Ejecutar los diez casos de `tests/golden_cases.json` en una versión fija del portal.
7. Verificar manualmente al menos una cifra: dato original → archivo preparado → filtro → operación → salida.
8. Confirmar compatibilidad temporal entre demografía y servicios. Documentar cualquier desfase.
9. Sustituir o complementar los fixtures solo en pruebas; nunca renombrarlos como datos reales.
10. Crear una versión nueva en el portal y probar esa versión. Editar archivos no actualiza versiones previas.

Los escenarios consumen `runtime_municipality_points.csv` y `runtime_servicios.csv` con coordenadas EPSG:25830.
Si faltan, la herramienta debe informar la ausencia; no debe sustituir silenciosamente la métrica por otra.
Antes de utilizar distancias de red o tiempos de viaje debe añadirse una fuente y un cálculo validado.
