# Auditoría de recuperación de PR #3

PR #3 (`work/agent-engine`) contenía tres commits: `419a427` (agente determinista), `b197c32` (tests de schema/build) y `017555e` (integración con la primera capa de datos).

## Código recuperado

- Runtime: `main.py`, `tools.py`, `data_access.py`, `metrics.py`, `schemas.py`, `__init__.py` y `requirements.txt` bajo `agentes/gipuzkoa360/`.
- Prompt y configuración: `SYSTEM_PROMPT`, memoria, ocho iteraciones, Internet desactivado y `build_agent(model)` síncrono.
- Siete tools públicas y schemas de resultado/error.
- Tests unitarios, de contrato, build, fixtures y datos reales.
- Generadores de ejemplos y paquete del portal.
- Documentación de Work 2 y ejemplos JSON.

## Decisiones de conflicto

Los conflictos en `FUENTES.md`, `README.md`, `analisis/`, `datos_originales/`, `datos_preparados/`, pipeline `scripts/data/`, métricas y tests de datos se resolvieron conservando la versión de PR #4. No se restauró ningún dataset ni manifest obsoleto de PR #3. Sobre esa base se mantuvieron únicamente los cambios del agente, sus tests, documentación y scripts de runtime.

El bundle final añade una adaptación necesaria del portal: sus únicos editores Python son `main.py` y `tools.py`, por lo que `scripts/agent/build_portal_sources.py` genera un `tools.py` autocontenido desde los módulos revisables del repositorio.

## Supersesión

PR #3 queda sustituido por la rama de release después de incorporar y endurecer su código útil. PR #4 mantiene autoridad sobre datos, contratos, fuentes, QA, manifests y metodología.
