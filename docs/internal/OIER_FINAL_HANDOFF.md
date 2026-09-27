# Rescate final para Asier

BRANCH: `rescue/oier-final` (publicada; base `488f46d`).

COMMITS: `d72d757` auditoría/snapshot; `378a333` reproducción; `59092b9` checkpoint
completo; `02451d5` README/VALIDATION finales. Este documento y el informe previo
se añaden en el commit de handoff.

RECOVERED_LOCAL_WORK: dos commits locales, documentación iniciada, 14 históricos
preservados, inventario de 121 archivos/414 apariciones y herramientas de auditoría.
Nada descartado. No hubo stashes. El checkpoint NO es una propuesta de merge indiscriminado.

README: terminado, compacto, fuentes, ejemplo, capacidades, límites y equipo.

VALIDATION: terminada; enlaza evidencia de Asier en `a1b0ecb` y `70c0e06`.
72.673 checks, 31.545 outputs trazables, 20 fallos controlados, 1.000 soak, 148 Python
y 17 Node. Separa esos resultados de los 146 tests anteriores de Oier.
PORTAL GO histórico, no aprobación del smoke actual. Packaging = WARN.

TEAM: terminado; nombres y contribuciones contrastados con commits.

FILES_PARTIAL: limpieza documental del checkpoint, docs/DEMO.md y scripts/release/.
Hay enlaces a documentos aún NO creados: internal/release/INTEGRATION_PLAN.md,
AUDIT.md y SUBMISSION_PACK.md. No adoptar toda la limpieza sin revisar navegación.
`reproduction-report-pre-rescue.json` conserva el ensayo sobre `378a333`,
no acredita este HEAD ni el nuevo paquete documental.

STALE_DOCS_FOUND: docs/RUBRIC_TRACEABILITY.md:8–9 aún dice «fuentes reales pendientes»
y «agente real pendiente». Los históricos están rotulados; no borrar evidencia.
Las vistas antiguas comparan tres municipios con corte local del 25 %: no presentarlas
como el resultado provincial por cuantil.

RUNTIME_CHANGED=NO. Verificación byte a byte de dos Python + diez archivos de contexto
contra `195b4980fa5998b096c308296a55e452380b0371`: PASS; manifiesto 7/7 PASS.
No se tocó el portal durante el rescate ni se repitió el benchmark.

WHAT_ASIER_MUST_FINISH:

- Integrar semánticamente README.md, docs/VALIDATION.md y docs/TEAM.md; no hacer
  cherry-pick ciego del checkpoint sobre su gate.
- Reconciliar packaging: 48.339 frente a 48.338 bytes en su evidencia. Mi corrección
  de docs/PORTAL_DEPLOYMENT.md cambia intencionalmente otro miembro documental del ZIP:
  candidato local 47.900 bytes, SHA ef9352647001a8011dc007d70df851bc9cd7b236069ef9cc3cf26167c3a12b51.
  NO es paquete final aprobado. Código/contexto idénticos; preservar esa distinción.
- Resolver enlaces parciales y claims obsoletos solo cuando integre la limpieza.
- Cerrar smoke privado cuando el runner funcione y contrastar la visual de Hugo.
  Mi inspección previa vio pruebas en v2/v3 y escenario/comparación en v4:
  conservar versión por traza, no deducirla solo del nombre del agente.
- Completar integración a main, verificar y cambiar después la rama por defecto.
  No se hizo merge, PR nueva ni entrega desde este rescate.
