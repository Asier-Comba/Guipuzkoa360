# Final submission readiness

Fecha de cierre: 2026-09-25. Este documento prepara una decisión humana; no autoriza merge ni publicación.

- **CANDIDATE:** `final/gipuzkoa360-ultimate`
- **FINAL_SHA:** commit que contiene este archivo; resolver con `git rev-parse HEAD` y registrar en la PR sin crear otro commit.
- **RUNTIME:** `195b4980fa5998b096c308296a55e452380b0371`; 14 archivos protegidos; sin cambios.
- **PR_FINAL:** `TO_BE_RECORDED_EXTERNALLY`; base `main`, no draft, no merge.
- **FAST_CI:** pre-cierre run 36194062246 PASS Linux/Windows; run del final SHA pendiente de registrar en PR.
- **FULL_VALIDATION:** `TO_BE_RECORDED_IN_PR` sobre el final SHA; esperado 72.673/72.673 según harness publicado.
- **PYTHON:** 263/263 suite integrada.
- **NODE:** 17/17 y tres comprobaciones sintácticas.
- **TOOLS:** 7 operaciones públicas deterministas.
- **DATA:** 88/88 municipios; 148 registros sanitarios; 412/412 referencias de fila; manifiesto 7/7.
- **HERO:** 7/4/2; cortes y 88 filas recalculados; Aduna 2.756,2→0,0 m como hipótesis.
- **PORTAL:** PASS acotado en v4. Preparación PASS; P1=7 y P2=4 con output real de `analizar_coincidencia`; P3 rechazó predicción/citas/capacidad. Entrega no publicada.
- **BENCHMARK_MEDIUMS:** 1 — M-01 payload extremo de 20.155 caracteres, no probado en portal.
- **RELEASE_MEDIUMS:** 2 — M-01 y M-02 fallback conversacional bajo fallo de runner; no es fallo observado del core.
- **SUBMISSION_PACK:** READY; seis piezas en `docs/SUBMISSION_PACK.md`.
- **MAIN_STATUS:** sin modificar, `bacc29d3b4d4d48eab11e5bf1ad00134f5b12a01` al inicio del cierre.
- **DEFAULT_BRANCH:** `work/data-foundation`; cambio posterior requiere decisión humana.
- **PORTAL_VERSION:** `urban-challenge-rc2-195b498 · v4`; no crear ni seleccionar otra versión automáticamente.
- **RECOMMENDED_DECISION:** revisar CI y full validation del exact final SHA; si ambos pasan y la PR está limpia, aprobar integración técnica. Publicar la Entrega es una decisión separada.

## HUMAN_ACTIONS

1. Revisar la PR final y sus run IDs; autorizar o rechazar el merge.
2. Tras un merge autorizado, validar `main` y decidir si pasa a ser la rama por defecto.
3. En el portal, completar pregunta de investigación, destinatario y utilidad; elegir track. El equipo ya muestra 3 personas confirmadas.
4. Seleccionar v4, revisar las seis piezas, la vista previa y el estado de privacidad.
5. Autorizar explícitamente la publicación; hasta entonces no pulsar el control final.
