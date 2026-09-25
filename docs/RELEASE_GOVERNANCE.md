# Gobierno del release

Base de esta ingeniería: `46c1a48f63c307654f45fcb5c18883f264b660ed`, rama `final/gipuzkoa360-integration`, PR #9. Rama de trabajo: `final/work1-engineering-master`. No modifica main, PR #9 ni la configuración administrativa.

| Nivel | Qué significa | Qué no autoriza |
|---|---|---|
| stable | Versión humana aprobada, inmutable, con datos, runtime y evidencia identificados | No equivale automáticamente a la rama llamada main; main sigue siendo anterior |
| candidate | Artefacto reproducible con gates verificables y riesgos revisados | CI verde no autoriza merge, publicación ni afirmar PORTAL GO |
| experimental | NEXT, propuestas, datos candidatos y shadow offline | No entra en ZIP, contexto ni herramientas de producción |

## Promoción humana

1. Fijar SHA y manifiestos. Cuando se reutiliza evidencia v4, comparar **los 12 archivos byte a byte** contra `195b4980fa5998b096c308296a55e452380b0371` (`scripts/ops/verify_runtime_identity.py`). Un byte distinto invalida esa identidad.
2. CI rápida verde en Linux y Windows desde checkout limpio: suite Python completa, Node, sintaxis, jury gates, extracción y doble build; sin descarga de fuentes ni caché de instalación.
3. Integridad de snapshots: cobertura 88, claves, referencias, coordenadas, fuentes y manifiesto. `source_health` es diagnóstico offline, no certificación de actualidad de Internet.
4. Validación exhaustiva y trazabilidad. 72.673 checks no son 72.673 preguntas del LLM. Preservar denominadores y versión del harness.
5. Revisar riesgos conocidos: payload extremo sin prueba de portal; errores de infraestructura y comportamiento conversacional en esas condiciones. NEXT no cierra riesgos de v4.
6. Repetir smoke privado en la versión exacta cuando el runner esté disponible. Si no lo está, etiquetar `INFRASTRUCTURE_BLOCKED`, no PASS.
7. Aprobación humana explícita: qué SHA, qué evidencia, riesgos aceptados, responsable y rollback a artefacto previamente aprobado. Publicar hackathon es una autorización distinta.

Regla shadow: ningún Critical/High nuevo, goldens PASS, beneficio medido y sin deterioro injustificado. El beneficio medido de NEXT es el bloqueo de evidencia/drafts manipulados; su latencia y UX son costes, no mejoras probadas. No se propone promoverlo ahora.

## Recomendación administrativa (no aplicada)

Para main: PR obligatoria, checks `release-ubuntu-24.04` y `release-windows-latest` requeridos, revisión humana, prohibir force-push y borrado. Revisar política para PR externas y recursos de Actions. El default branch continúa `work/data-foundation`; no cambiarlo automáticamente.

## Versiones independientes

- DATA_VERSION: SHA-256 del manifiesto de datos y verificación de cada miembro. No basta el hash si no se comprueban sus archivos.
- RUNTIME_VERSION: commit congelado `195b498…`; el gate prueba igualdad, no el nombre de rama.
- CAPABILITY_VERSION: `next-registry-0.1` para NEXT, separado de las 7 tools v4.
- PROMPT_VERSION: `none-deterministic-template-0.1` para NEXT; v4 conserva su SYSTEM_PROMPT y SHA.
- BENCHMARK_VERSION: `next-evaluation-0.1` y commit/hash del harness para la batería nueva; la exhaustiva conserva su propio baseline histórico.

La respuesta NEXT devuelve estas cinco versiones. Su evidencia es interna al proceso, no una firma criptográfica contra un actor que controle el propio código.
