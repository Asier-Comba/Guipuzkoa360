# GIPUZKOA 360 · Urban Challenge release candidate

Versión candidata actual: `urban-challenge-rc2`.

RC1 queda preservado como histórico mediante el tag `urban-challenge-rc1` sobre `main`; no debe utilizarse para
las pruebas nuevas del portal. RC2 se construye desde `fix/portal-runtime-rc2`. El SHA exacto validado localmente,
el tamaño y el SHA-256 del paquete se registran en `docs/RC2_FINAL_STATUS.md`. El manifiesto reproducible es
`dist/gipuzkoa360-urban-challenge-rc2-manifest.json`; el ZIP no se versiona en Git.

## Contenido y datos

- Agente Python síncrono con siete tools deterministas y sin Internet.
- Bundle de dos archivos Python compatible con el editor del portal.
- Siete wrappers `@tool` declarados físicamente en `main.py`; sus firmas públicas fuerzan salidas compactas.
- El modo detallado se conserva solo en el core para auditoría offline y no se expone al coordinador de Studio.
- Datos preparados bajo contrato `1.1.0`: 88 municipios, demografía 2025-01-01 y 148 registros sanitarios públicos con corte 2026-09-20.
- Geografía geoEuskadi con corte 2025-05-07 y cálculos métricos en EPSG:25830.
- Casos A–H y cinco golden cases fijos.
- Adaptador de salida real de tool a los tres HTML de Work 3.

## Reproducibilidad

Ejecutar la secuencia de `docs/PORTAL_DEPLOYMENT.md`. El paquete usa orden de archivos y timestamp ZIP fijos, por lo que dos builds del mismo commit deben producir el mismo SHA-256.

La validación local no equivale a validación del portal. RC2 solo pasa a candidato de integración cuando Work 3
publique evidencia privada completa para el SHA exacto; hasta entonces no se fusiona a `main` ni se publica la entrega.
