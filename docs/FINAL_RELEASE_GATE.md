# Gate del candidato final

Fecha: 2026-09-25. **FINAL_CANDIDATE_READY sujeto a CI final y decisión humana; entrega no publicada.**

- `CANDIDATE_BRANCH`: `final/gipuzkoa360-ultimate`
- `CANDIDATE_SHA`: el commit que contiene este documento; el hash exacto se registra en la PR final sin crear otro commit.
- `FROZEN_RUNTIME`: `195b4980fa5998b096c308296a55e452380b0371`
- `MAIN_AT_CLOSURE`: `bacc29d3b4d4d48eab11e5bf1ad00134f5b12a01`
- `DEFAULT_BRANCH_AT_CLOSURE`: `work/data-foundation`

El gate de identidad compara byte a byte los dos módulos offline, los dos módulos de portal y diez
archivos de contexto con el runtime congelado. La regeneración de evidencia no puede modificar ese
conjunto.

## Matriz de decisión

| Componente | Estado | Evidencia y alcance |
|---|---|---|
| Runtime y contexto | PASS | 14 archivos idénticos al runtime congelado; 7 tools; ningún parámetro público `detalle`. |
| Datos y manifiesto | PASS | 88/88 municipios, 148 registros sanitarios, 0 nulos obligatorios, duplicados, coordenadas inválidas o referencias huérfanas; 7/7 hashes. |
| Python integrado | PASS | 263/263 en la suite completa del candidato. No se suma al benchmark exhaustivo. |
| Node | PASS | 17/17 y sintaxis de los tres scripts críticos. |
| Fast CI | PASS del pre-cierre | Run 36194062246, Ubuntu 24.04 y Windows latest. El commit documental final requiere su propia ejecución verde. |
| Benchmark exhaustivo | PASS histórico; repetición final requerida | 72.673/72.673; trazabilidad 31.545/31.545; 20/20 corrupciones controladas; soak 1.000 sin deriva ni excepciones. |
| Hero y artefactos | PASS | Filas, geometrías, fuentes y escenario contrastados; listas 7/4/2; nueve mutaciones rechazadas. |
| Navegador | PASS acotado | Matriz Chromium 1920, 1366, 1280, 1024 y 390 px; reflow equivalente 125/150 %, teclado y foco. No es certificación WCAG ni prueba con usuarios. |
| Q&A | PASS documental | 44 preguntas y respuestas con punteros de evidencia. |
| NEXT | PASS acotado | 77/77; prototipo offline con intents estructurados. No es benchmark de routing LLM, portal ni producción. |
| Paquete | PASS | ZIP canónico reproducido dos veces: 48.338 bytes, SHA-256 `2808110d14e0bc30a53018cab1ec39b926e1e6ca1f1be19f0b2c9cf21106680a`. |
| Portal | PASS acotado | v4: preparación PASS; P1 y seguimiento P2 produjeron output real de `analizar_coincidencia`; P3 rechazó predicción/citas/capacidad. No sustituye la suite local. |
| Integración | READY | La PR final debe apuntar de `final/gipuzkoa360-ultimate` a `main`, quedar abierta, limpia y sin merge. PR #9 queda sustituida. |

## Controles municipales

| Consulta | Resultado | Cortes |
|---|---:|---|
| 65+, q0,75, atención primaria, 2 km | 7 de 88 | 23,973 %; 2.019,2 m |
| 75+, q0,80, atención primaria, 3 km | 4 de 88 | 12,9796 %; 2.138,6 m |
| 65+, q0,85, atención primaria, 2 km | 2 de 88 | 25,3557 %; 2.308,7 m |

El umbral en km solo determina `within_threshold`; no reemplaza el corte por cuantil. En Aduna, el
escenario añade hipotéticamente un servicio en el punto representativo y cambia 2.756,2 m a 0,0 m.
No es predicción ni recomendación, y cero registros no significa ausencia de atención sanitaria.

## Severidad y riesgos conocidos

**Benchmark exhaustivo:** Critical 0, High 0, Medium 1, Low 0.

- **M-01:** `simular_escenario` extremo conserva 66 filas afectadas de 88 y produce 20.155 caracteres.
  No se ha demostrado ese extremo en el portal; no se trunca porque se perdería evidencia municipal.

**Release completo:** Critical 0, High 0, Medium 2 conocidos.

- **M-01**, anterior.
- **M-02:** durante un fallo de runner, el fallback conversacional confundió el umbral de 2 km con el
  corte de distancia por cuantil. La tool no produjo output: no existe evidencia de cálculo core
  incorrecto. El smoke final posterior sí separó ambos conceptos, pero el riesgo histórico se conserva.

Estas cifras describen hallazgos conocidos y gates definidos; no afirman riesgo cero.

## Evidencia y acciones humanas

- [Validación](VALIDATION.md), [benchmark](BENCHMARKS.md), [revisión de navegador](internal/HERO_BROWSER_REVIEW_V2.md) y [smoke de portal](internal/PORTAL_SMOKE_REFRESH.md).
- [Fuentes](../FUENTES.md), [metodología](METODOLOGIA.md), [pack mínimo](SUBMISSION_PACK.md) y [checklist final](internal/FINAL_SUBMISSION_READINESS.md).

Después del commit documental final se registran en la PR, sin cambiar el SHA: fast CI del head,
`Full release validation` del mismo head y estado mergeable. Una persona debe revisar la PR, autorizar
el merge, validar `main`, decidir el cambio de rama por defecto y autorizar por separado la publicación.
