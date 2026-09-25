# Plan de integración de los dos trabajos

Base: `46c1a48f63c307654f45fcb5c18883f264b660ed` (`final/gipuzkoa360-integration`, PR #9 sin alterar).
Work 1: `final/work1-engineering-master`, ingeniería/CI/operaciones/NEXT, runtime intacto.
Fetch de Work 3: 25-09-2026; rama **encontrada** `final/work3-product-jury`.
Snapshot auditado: `09478c8d7334ed4778ef85850809df515d8f99b0`.

## WORK3_COMMITS / ACCEPT

| Commit inspeccionado individualmente | Cambio | Decisión |
|---|---|---|
| `6e8a7ae7514dcc5acf76949b329526d45dbb1352` | Hero y 4 superficies guardadas, exporter adicional, fuentes/KPIs con denominadores | ACCEPT técnico condicionado a cierre de su rama; conserva build() canónico y no cambia runtime/datos |
| `9639e8ba69f34cecbe6e099a2654c67270d33ba0` | 30 tests adicionales de producto, método/límites específicos de escenario, reproducción | ACCEPT junto al anterior; no integrar visual sin sus tests |
| `09478c8d7334ed4778ef85850809df515d8f99b0` | README, pitches, 44 QA, one-pager, guía de uso | ACCEPT condicionado a resolver enlaces a HUGO_JURY_HANDOFF.md, ausente en este snapshot |

La rama se ha auditado en un worktree separado, detached al SHA exacto. **182/182 Python PASS (152 base + 30 producto), 17/17 Node PASS, verify_final_artifacts PASS incluidas nueve mutaciones, runtime identity PASS.** No acredita render visual exhaustivo ni una ejecución Linux remota de esa rama. No se han aplicado estos commits sobre Work 1 ni se ha tocado ningún archivo propiedad de Work 3.

## REJECT

Ningún commit rechazado íntegramente por defecto técnico demostrado. Sí se rechaza presentar esos HTML como diálogo nuevo, su benchmark histórico como resultado de esta nueva ingeniería o el 1 Medium histórico como inventario global actual. No copiar resultados viejos sobre analisis/ops o analisis/next.

## CONFLICTS / pendientes concretos

- No solapamiento directo con archivos Work 1. `tests/test_product_jury.py` es nuevo; CI de Work 1 lo incluirá automáticamente tras integración.
- En QA aparecen enlaces a `docs/HUGO_JURY_HANDOFF.md`; el archivo no existe en `09478c8`. Señal de documentación aún por cerrar, no motivo para inferir entrega final de Work 3.
- El producto muestra KPIs históricos, correctamente rotulados como base. El nuevo smoke Work 1 detecta M-02 (fallback umbral/cuántiles); el consolidado debe enlazar el registro actual y mantener separado el 1 Medium del benchmark histórico de los 2 Medium de ingeniería.
- El exporter extrae counts desde texto de VALIDATION.md mediante regex. No actualizar esa prosa arbitrariamente: si cambia la forma, el build puede fallar. Evolución posible: fuente estructurada de counts en otro commit autorizado; no reescribirlo aquí.
- `input_sha256` protege documentos base además de datos. Si se integra luego una modificación de VALIDATION/FINAL_RELEASE_GATE, regenerar product_evidence y las cuatro vistas, no saltarse fingerprints.
- Conserva el core y frozen files; el contexto de cada salida resumen aclara procedencia general sanitaria/geográfica además de sources declaradas, sin alterar cifras.

## INTEGRATION_ORDER

1. Obtener handoff final de Work 3 y fetch nuevo; inspeccionar cualquier commit posterior a `09478c8`. No presumir completitud por estar publicado.
2. Revisar y aceptar la rama de ingeniería contra base canónica en una rama candidata autorizada. No cambiar main/default ni PR #9 en esta misión.
3. Aplicar secuencialmente los tres commits de producto revisados (o sus equivalentes finales), en orden 6e8a7ae → 9639e8b → 09478c8. No merge/cherry-pick ciego.
4. Cerrar enlaces y consolidar scope de riesgos mediante cambio del owner de producto; solo entonces regenerar sus artifacts.
5. Congelar SHA integrado y guardar evidencia nueva. La publicación necesita decisión humana distinta.

## POST_INTEGRATION_TESTS

Identidad byte a byte antes/después; pytest completo (esperado 259 si no cambian suites: 152+77+30, **expectativa, no resultado medido**); Node17; sintaxis; verify_jury_results; verify_final_artifacts; nuevo test_product_jury; build_jury_data + build_jury reproducibles; source_health; NEXT eval; paquete doble; benchmark exhaustivo; CI Linux y Windows. Revisar mapa/tablas/selector/navegación a tamaños de pantalla de demo. Repetir P1/P2/P3 privados en v4 solo cuando esté operativo, sin editar runtime por fallos de infraestructura.

No merge realizado. No publicación. La integración final queda preparada, no fingida.
