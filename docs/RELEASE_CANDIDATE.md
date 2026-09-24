# GIPUZKOA 360 · Urban Challenge release candidate

Versión: `urban-challenge-rc1`.

Los valores finales de commit, tamaño y SHA-256 se registran tras integrar la rama de release. El manifiesto reproducible es `dist/gipuzkoa360-urban-challenge-rc1-manifest.json`; el ZIP no se versiona en Git.

## Contenido y datos

- Agente Python síncrono con siete tools deterministas y sin Internet.
- Bundle de dos archivos Python compatible con el editor del portal.
- Datos preparados bajo contrato `1.1.0`: 88 municipios, demografía 2025-01-01 y 148 registros sanitarios públicos con corte 2026-09-20.
- Geografía geoEuskadi con corte 2025-05-07 y cálculos métricos en EPSG:25830.
- Casos A–H y cinco golden cases fijos.
- Adaptador de salida real de tool a los tres HTML de Work 3.

## Reproducibilidad

Ejecutar la secuencia de `docs/PORTAL_DEPLOYMENT.md`. El paquete usa orden de archivos y timestamp ZIP fijos, por lo que dos builds del mismo commit deben producir el mismo SHA-256.
