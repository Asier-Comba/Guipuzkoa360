# GIPUZKOA 360 · Work 3

Experiencia de visualización e integración para explorar población mayor e indicadores territoriales de servicios. **Los HTML de esta rama contienen solo datos sintéticos de desarrollo.** No ofrecen resultados sobre Gipuzkoa ni acreditan un agente operativo. La base real está en `work/data-foundation` (PR #1) y se integrará sin copiarla a esta rama.

Abrir `resultados/demo.html` para revisar el prototipo sin servidor ni conexión. Cambiar edad, umbral y capa actualiza el fixture local; la demo final necesita una nueva ejecución del agente con datos reales.

```powershell
node scripts/build_results.mjs
node --test tests/e2e/contract_flow.test.mjs
```

Cuando la rama de datos y el agente estén integrados, añadir contornos municipales al JSON del agente con `scripts/enrich_work1_result.mjs` y generar de nuevo los HTML. El mapa usará GeoJSON real de las unidades comparadas; los resultados y la traza deberán seguir viniendo de una ejecución del agente.

Leer `docs/HANDOFF_WORK_3_INTEGRATION.md` para integrar las entregas de datos y agente y `docs/SUBMISSION_CHECKLIST.md` antes de preparar la entrega en el portal.
