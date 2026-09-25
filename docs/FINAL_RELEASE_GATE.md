# Gate de integración final

Fecha: 2026-09-25. **FINAL_RELEASE_GO=YES, con advertencias; NO publicación**.

BASE_SHA: `70c0e06e9858a64043088ed6510c68e857869f46`.
Rama: `final/gipuzkoa360-integration`.
Candidato ejecutado: `84e95167bfb9718ebb5f26b533f12cd885901e20`.
Runtime congelado: `195b4980fa5998b096c308296a55e452380b0371`.
Los commits posteriores registran evidencia/documentación y corrigen el texto del diagnóstico del
benchmark; no alteran runtime ni cálculos. El benchmark exhaustivo se ejecutó una vez.

## Matriz de decisión

| Componente | Estado | Evidencia y ataque realizado |
|---|---|---|
| Runtime y contexto | PASS | 12 archivos byte a byte contra el runtime congelado; 7 tools, ninguna con parámetro público detalle. |
| Manifiesto | PASS | 7 entradas contrastadas con bytes y SHA físicos; STUDIO_CONTEXT_FILES completo. |
| Python | PASS | 152/152; incluye 18 de datos y 3 del módulo golden contractual. Cuatro tests nuevos: 3 de ZIP y 1 del gate adversarial. |
| Node | PASS | 17/17 y comprobación sintáctica de jury_view.js. |
| Contrastes y flujo | PASS | 4/4 contrastes fijos; A–H 8/8; QA de datos 41/41 en worktree limpio. No son conversaciones. |
| Benchmark | PASS | 72.673/72.673; trazabilidad 31.545/31.545; 20/20 corrupciones controladas; soak 1.000 sin deriva/excepciones. |
| Hero numérica | PASS | Todas las filas, geometrías, fuentes y escenario comparados con recálculo. Nueve mutaciones rechazadas; listas 7/4/2 exactas. |
| Hero en navegador | PASS acotado | Clicks, retorno sin contaminación, teclado, 88 contornos y escenario inspeccionados en escritorio. No se afirma QA móvil exhaustiva. |
| ZIP cross-worktree | PASS acotado | 3 checkouts limpios autocrlf false/true/input, mismo SHA. Misma versión Python/zlib. |
| Payload extremo | WARN | 20.155 caracteres, 66 filas afectadas de 88 analizadas; sin truncar. Extremo no ejecutado en portal. 1 Medium abierto. |
| Portal actual | WARN | INFRASTRUCTURE_BLOCKED: dos preparaciones con runner ocupado y un envío con Connection Error. Principal sin output; seguimiento no ejecutado. |
| Historia de portal | Evidencia acotada | Consultas observadas en v2/v3 y escenario en v4, mismo core. No toda la batería ocurrió en v4. |
| Docs y demo | PASS | Seis documentos canónicos; guiones 10 s/30 s/3 min/6 min; 24 respuestas de defensa; pack mínimo y autorías. |
| Integración | READY | main es ancestro de la rama final; nueva PR sin merge. main y default sin modificar. |

Critical=0 y High=0 conocidos abiertos. El High visual del corte fijo del 25 % fue reproducido y
corregido fuera del runtime. La política autorizada admite el smoke bloqueado con historia válida y
delimitada; no se convierte ese bloqueo en un PASS conversacional.

## Identidad

| Artefacto | SHA-256 |
|---|---|
| portal/main.py | `c2f4770f234522ac6ccb535d627c1252e19bc8f992e73194dab6e9f6672c585e` |
| portal/tools.py | `0a5ab214ecf89cef04c85b5055c8ac42047c151c0411b4aa6c470a8de397edd5` |
| runtime_manifest.json | `866be215720e3b58fbfc502ffceaa51ac6635266b609d112eb9460712a95642a` |
| ZIP canónico, 48.338 bytes | `2808110d14e0bc30a53018cab1ec39b926e1e6ca1f1be19f0b2c9cf21106680a` |

La diferencia histórica de un byte procede exclusivamente de requirements.txt LF (66 bytes) frente a
CRLF (67). Se reconstruyeron exactamente ambos SHA históricos, con metadatos y CRC por miembro.
El builder fija plataforma Unix, permisos, orden y fecha; canoniza CRLF solo en el ZIP. No escribe
runtime/contexto. El nuevo ZIP no se atribuye al portal histórico: son controles distintos.

## Resultados municipales

| Consulta | Municipios destacados, en orden | Cortes |
|---|---|---|
| 65+, q0,75, 2 km | Legazpi; Ezkio-Itsaso; Hondarribia; Hernialde; Oñati; Idiazabal; Errenteria | 23,973 %; 2.019,2 m |
| 75+, q0,80, 3 km | Legazpi; Errenteria; Hondarribia; Idiazabal | 12,9796 %; 2.138,6 m |
| 65+, q0,85, 2 km | Legazpi; Hondarribia | 25,3557 %; 2.308,7 m |

Siempre 88 filas analizadas. El umbral no sustituye al cuantil. Aduna: 2.756,2→0,0 m, diferencia
−2.756,2 m, escenario hipotético. El HTML muestra cálculos guardados, no conversación en vivo.

## Evidencia

- [Benchmark final](../analisis/final/BENCHMARKS.md) y [nota de ejecución/errata](../analisis/final/README.md).
- [ZIP raíz](../analisis/zip_root_cause.json), [tres worktrees](../analisis/cross_worktree_reproducibility.json).
- [Gate adversarial](../analisis/final_artifact_audit.json), [payload](../analisis/payload_decision.json).
- [Inspección visual](internal/HERO_BROWSER_REVIEW.md), [smoke actual](internal/PORTAL_SMOKE_FINAL.md).
- [Rescate y commits](internal/FINAL_INTEGRATION_DECISIONS.md).

## Bloqueos y acciones humanas

FAIL de identidad, corrupción numérica, fuente inventada, manifiesto incompleto o lista visual errónea
revocarían este GO. No se conoce ninguno tras los ataques. El Medium sigue abierto: conservar evidencia
es una decisión aceptada, no prueba de capacidad del portal.

Publicar sigue fuera de autorización: aprobar el merge técnico, verificar main resultante, cambiar
entonces la rama por defecto, revisar/seleccionar los seis materiales y versión privada, autorizar entrega.
La PR #8 es cierre parcial histórico. La PR final usa esta rama. Nada se fusiona ni publica aquí.
