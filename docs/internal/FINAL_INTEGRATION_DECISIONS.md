# Decisiones de integración final

BASE_SHA: `70c0e06e9858a64043088ed6510c68e857869f46`.
BRANCH: `final/gipuzkoa360-integration`.
Runtime/contexto congelados: `195b4980fa5998b096c308296a55e452380b0371`.

## Rescate selectivo

Se inspeccionaron individualmente `d72d757`, `378a333`, `59092b9`, `02451d5` y `1b0f619` de
`rescue/oier-final` (HEAD `1b0f61942403403354a317da99c88fb726bba723`).

- `59092b9`: incorporado `docs/TEAM.md`; su limpieza masiva no se adopta porque incluye navegación
  incompleta y cambia un documento empaquetado. Se conserva la evidencia histórica existente.
- `02451d5`: integrada semánticamente la organización pública de README/VALIDATION, fuentes, límites,
  autorías y advertencia sobre versiones de portal. Documentos actualizados con evidencia final propia.
- `1b0f619`: incorporado `docs/internal/OIER_FINAL_HANDOFF.md` como procedencia del rescate.
- `d72d757` y `378a333`: revisados, no incorporados íntegros. Sus herramientas de reproducción no
  resuelven por sí solas la discrepancia de bytes y no son necesarias para la prueba canónica específica.

No se cherry-pickeó ningún commit completo: los cambios útiles se integraron por archivo y semántica,
con referencias de autoría. OIER_RESCUE_FOUND=YES; OIER_COMMITS_INTEGRATED=selective material only.

## Defectos intentados y encontrados

- High visual demostrado: el explorador anterior usaba `pct >= 25` sobre tres municipios, distinto de
  la coincidencia provincial. Resuelto reutilizando diseño/mapa y mostrando salidas del core para 88 filas.
  Las vistas secundarias ya no llaman coincidencia al criterio local de distancia.
- ZIP de un byte: causa exacta `requirements.txt`, LF frente a CRLF, reproducida por SHA y CRC de cada
  miembro. Builder canónico; no se reescribe código ni contexto del portal.
- Las pruebas de generación de bundle reescribían comillas mediante `ast.unparse` local. Sus fixtures
  ahora restauran los bytes originales al terminar cada prueba; no modifica el runtime congelado.
- Se atacó la evidencia visual con nueve corrupciones y se comparó el HTML completo con el cálculo.

## Alcance del Medium

La conservación de 66 filas afectadas entre 88 analizadas es una decisión de diseño aceptada. La explicación
histórica que decía 88 afectadas era incorrecta: `analisis/payload_decision.json` la refuta. La incertidumbre del payload
extremo en el portal sigue siendo Medium, porque un escenario pequeño ejecutado no valida el extremo.
No se reduce la severidad solo para obtener un marcador cero.
