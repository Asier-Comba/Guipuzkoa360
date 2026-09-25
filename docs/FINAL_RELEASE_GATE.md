# GIPUZKOA 360 · Final release gate

Fecha de auditoría: 2026-09-25

Rama de cierre: `final/work2-release-gate`

Base documental: `488f46db7047d9393d4d4a489a869ab246c215b9`

Runtime congelado: `195b4980fa5998b096c308296a55e452380b0371`

## Decisión

**GO WITH WARNINGS para integrar el cierre técnico; NO publicar todavía.**

El runtime y sus cifras pasan las puertas locales y la versión privada correcta continúa activa. La
publicación sigue bloqueada hasta que (1) el runner permita repetir al menos preparación y un smoke
privado sobre v4 y (2) Work 1 termine y contraste la experiencia visual. Ninguna de esas dos puertas se
declara PASS en esta auditoría.

## Puertas

| Componente | Estado | Evidencia |
|---|---|---|
| Relación del benchmark con la base | PASS | `488f46d` es ancestro de `bf5c6cc` y `a1b0ecb`; ambos commits están en esta rama. |
| Alcance de los dos commits de Asier | PASS | Solo añaden README, harness, informes JSON y `docs/BENCHMARKS.md`; diferencia de runtime frente a `488f46d`: cero. |
| Runtime congelado | PASS | `main.py`, `tools.py`, datos y builder no difieren de la base. Siete tools públicas; ninguna firma expone `detalle`. |
| Suite Python | PASS | 148/148, incluidos dos controles nuevos del gate de resultados del jurado. |
| Integración JavaScript | PASS | 17/17. |
| Benchmark exhaustivo | PASS | 72.673/72.673 checks; 0 Critical, 0 High; trazabilidad 31.545/31.545; 20/20 fallos controlados. |
| Payload extremo | WARN | `simular_escenario` llega a 20.155 caracteres al cambiar 1→10 km; se conservan las 88 filas y no se trunca. |
| Coincidencias 7/4/2 | PASS | Recalculadas desde los datos reales; listas y cortes exactos en `analisis/jury_coincidence_results.json`. |
| Dependencia del cuantil | PASS | q0,75 y q0,85 producen cortes y conjuntos distintos; no se usa un corte fijo del 25 %. |
| Versión privada | PASS | El selector del portal muestra activa `urban-challenge-rc2-195b498 · v4`, con memoria activa y sin Internet. |
| Preparación actual del portal | WARN | Tres intentos de esta auditoría terminaron con «El runner está ocupado», incluido el reintento final del 25-09. |
| Live tests privados actuales | WARN | La pregunta principal eligió `analizar_coincidencia` dos veces, con argumentos correctos y sin `detalle`, pero el runner no produjo output. El resto no se ejecutó para evitar ruido concurrente. |
| Evidencia histórica de v4 | PASS histórico | `docs/PORTAL_EVIDENCE_RC2.md` registra preparación, G-01…G-06, siete tools, red-team y escenario sobre el mismo runtime. No sustituye el smoke actual pendiente. |
| Experiencia visual de Work 1 | WARN | `origin/final/hugo-jury-experience` no existía tras `fetch --prune`; no se revisó ni se modificó trabajo visual. |

## Hashes y paquete

Hashes del runtime limpio auditado:

| Archivo | SHA-256 |
|---|---|
| `agentes/gipuzkoa360/portal/main.py` | `c2f4770f234522ac6ccb535d627c1252e19bc8f992e73194dab6e9f6672c585e` |
| `agentes/gipuzkoa360/portal/tools.py` | `0a5ab214ecf89cef04c85b5055c8ac42047c151c0411b4aa6c470a8de397edd5` |
| `datos_preparados/runtime_manifest.json` | `866be215720e3b58fbfc502ffceaa51ac6635266b609d112eb9460712a95642a` |

La evidencia original de Asier conserva 10/10 builds idénticas, 48.339 bytes y SHA-256
`aea14519f838dda82f3ba317c556a2ffed5e2b2cd44c5cf085c216c8897a418b`. Una reconstrucción desde este
checkout limpio produjo 48.338 bytes y SHA-256
`e642ca6b2848eb01a9e79bd260ac6d18d501fc097e8b8fd0ddf6bbba8e7cd00f`. El runtime Git no cambia: la
diferencia demuestra que el test 10/10 asegura repetibilidad dentro de una misma representación del
worktree, no portabilidad del ZIP entre representaciones/EOL. Se mantiene como WARN y no se reescribe la
evidencia de Asier. El paquete históricamente probado en v4 quedó registrado con 48.355 bytes y SHA-256
`b5b35245aaa08015b2955281b0edb9cc3254fa7fae77966d63d9fa6651b48227`.

## Resultados canónicos para el jurado

- 65+, q0,75, atención primaria, 2 km: Legazpi, Ezkio-Itsaso, Hondarribia, Hernialde,
  Oñati, Idiazabal y Errenteria; cortes 23,973 % y 2.019,2 m; 88 filas.
- 75+, q0,80, atención primaria, 3 km: Legazpi, Errenteria, Hondarribia e Idiazabal;
  cortes 12,9796 % y 2.138,6 m; 88 filas.
- 65+, q0,85, atención primaria, 2 km: Legazpi y Hondarribia; cortes 25,3557 % y
  2.308,7 m; 88 filas.

El verificador reproducible es `scripts/benchmark/verify_jury_results.py`. También puede recibir un JSON
exportado por la experiencia visual con `--candidate` y comparar orden, recuentos y cortes sin tocar sus
archivos.

## Qué impediría publicar

Son bloqueos de publicación: cualquier diferencia de runtime respecto a `195b498`; una lista visual que
no coincida con el verificador; una firma pública con `detalle`; una preparación fallida por código o
archivos; un smoke privado que no complete la cadena usuario → coordinador → tool → output → respuesta;
o una experiencia visual todavía no contrastada. El WARN de 20.155 caracteres no bloquea por sí solo:
es evidencia municipal deliberadamente conservada.
