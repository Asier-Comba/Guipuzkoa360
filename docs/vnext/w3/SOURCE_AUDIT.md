# W3 R2 · cobertura de fuentes y clasificación

Fecha de lectura: 29/09/2026. Esta matriz no implica completar prácticas
formativas ni validar con usuarios.

| Fuente | Estado | Uso y límite |
|---|---|---|
| Repositorio público y `main` `e213eaa` | VERIFIED_LIVE | GitHub y fetch confirmados. Base W3 literal. |
| `docs/RUBRIC_TRACEABILITY.md` | HISTORICAL | Resumen versionado de la rúbrica; el literal `contexto-principal.md` no está en esta base y queda pendiente. Los gates 57/60 son propuesta de proyecto. |
| `docs/RESULT_SCHEMA.md`, `docs/PORTAL_DEPLOYMENT.md` | HISTORICAL | Contratos y guía v4; no sustituyen la configuración observada del portal. |
| `docs/PORTAL_EVIDENCE_RC2.md`, `docs/internal/PORTAL_SMOKE_ULTIMATE.md`, `docs/FINAL_RELEASE_GATE.md` | HISTORICAL | Evidencia v4; no acredita ejecución vNext. |
| Generalized `7e864f4` | HISTORICAL | 36 casos de desarrollo preservados sin cambiar prompts ni criterios. |
| W1 `c68eb5c` | VERIFIED_LOCAL | Contrato 0.1.0, fuente oficial fijada, 10 casos reales y cinco outputs calculados offline por W3. No es agente W2. |
| CityScope MIT | OFFICIAL | Capacidades declaradas en [fuentes primarias](CITYSCOPE_SCOPE.md); sin prueba pareada. |
| Paquete plano privado 00–12 | BLOCKED | No aparece en adjuntos montados ni workspace. No se leyó feedback literal, correos, PoC completa ni manifiesto. |
| Formación 73/73 páginas | BLOCKED | No localizada en el paquete disponible; 73 extraídas no significaría prácticas completadas. Progreso histórico 55/73 sin modificación. |
| Conversación 50+/504 | REPORTED_NOT_REPRODUCED | Sin versión, tool, argumentos, output, respuesta y tiempos observados; no se atribuye causa raíz ni HTTP real. |
| Portal, ayuda «Construir y probar un agente Python» | VERIFIED_LIVE | Leída sin escritura el 29/09/2026: `build_agent(model)` síncrono, modelo provisto por la plataforma, hasta 10 herramientas, `AGENT_NAME` de 2–80 caracteres e instrucciones de 10–8.000 caracteres. No confirma un límite de 24 MB del paquete del agente. |
| Portal, Agentes/Pruebas/Entrega | VERIFIED_LIVE | Entrega sigue como **borrador privado**, con `urban-challenge-rc2-195b498 · v4` seleccionada; la vista de Entrega indica 17 ejecuciones terminadas de esa versión sin evaluar. El editor activo es un borrador genérico (`STUDIO_MAX_ITERATIONS=8`, memoria activada, Internet desactivado) y **no** identifica la configuración de v4 ni del futuro vNext. La lista contiene una «Versión final · v6», que no se toma como candidato vNext sin paquete y huella. |
| Portal candidato W2 y A/B | NOT_RUN | No hay rama/paquete/version fijada ni autorización de escritura; no se abrió conversación ni se lanzó una prueba nueva. `PORTAL_GATE_PENDING`. |

El documento `docs/vnext/coordination/LAUNCH_R2.md` en la rama W1 reemplaza el
bootstrap G0 anterior: fija base, rama de integración y propiedad. El paquete
privado faltante es una limitación de cobertura, no motivo para inventar
conclusiones. Si aparece, W3 lo leerá antes de aceptar candidato o revisar
criterios de producto; cualquier cambio posterior se versionará.

La vista de Entrega observada exige ficha completa, versión fija, track y
equipo confirmado; explicación, mapas, informes, enlaces y conversaciones
revisadas son opcionales. Indica hasta 100 MB **por material opcional de la
entrega**; esto no demuestra el límite de tamaño del agente o su contexto.
No se seleccionó track, versión o archivo ni se guardó/publicó la entrega.
