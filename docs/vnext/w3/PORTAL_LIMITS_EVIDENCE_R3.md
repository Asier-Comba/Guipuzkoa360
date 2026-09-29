# Portal · evidencia de lectura R3 (29/09/2026)

**Clasificación: VERIFIED_LIVE, solo lectura.** Cuenta de participante Hugo,
workspace GIPUZKOA 360, secciones **Agentes → Python** y **Entrega**. Se
abrió la ayuda y se leyó el selector existente; no se creó, probó,
seleccionó ni publicó ninguna versión. No se reinició el entorno.

| Superficie y fragmento visible | Demuestra | No demuestra |
|---|---|---|
| Ayuda «Construir y probar un agente Python»: `build_agent(model)` síncrono; la plataforma proporciona el modelo. | Contrato de entrada descrito hoy por la ayuda. | Modelo exacto, presupuesto, latencia o éxito de un paquete concreto. |
| Ayuda «Comprobaciones de publicación»: `AGENT_NAME` 2–80 caracteres, instrucciones 10–8.000 caracteres, hasta 10 herramientas. | Límites actuales publicados en esa ayuda. | Límite de tamaño del ZIP, contexto efectivo o coste de ejecución. |
| Entrega: «Hasta 100 MB por archivo» en **Archivos · opcionales**. | Límite por material visual opcional de entrega. | Límite comprimido/descomprimido del agente, memoria o contexto. |
| Entrega: «BORRADOR PRIVADO», versión seleccionada `urban-challenge-rc2-195b498 · v4`. | La selección de entrega sigue en v4; vista muestra 19 ejecuciones terminadas de esa versión, sin evaluación W3. | Que esas 19 sean correctas, ni que una vNext se haya probado. |
| Agentes: editor activo `Agente principal · borrador`, plantilla genérica con 8 iteraciones, memoria activada e Internet desactivado. | Estado visible de ese **borrador genérico**. | Configuración de v4, de «Versión final · v6» o de W2 vNext. |

Inventario de opciones ya presentes en el selector de Entrega (lectura del
valor DOM de opciones sin cambiar el selector):

| Nombre visible | `version_id` | Fecha de creación | Fingerprint del paquete | Acceso |
|---|---|---|---|---|
| `urban-challenge-rc2-195b498 · v4` | `agentv_58e6ab81efc04f07b2be0cacead6a492` | No expuesta en esta vista | No expuesto; el sufijo del nombre no prueba identidad de bytes | Seleccionada en borrador privado |
| `GIPUZKOA 360 · Versión final · v6` | `agentv_48f0db6526684d1bb0d9e6d8726448d8` | No expuesta en esta vista | No expuesto | Listada, no seleccionada ni atribuida a W2 |

El constructor W2 R2 contiene `LIMIT = 24 * 1024 * 1024` en su código y su
ZIP mide 55.455 bytes según su manifiesto. Ese número es un **límite local
impuesto por W2**, no una confirmación de plataforma. No se observó aquí un
límite oficial de 24 MB para el paquete del agente. Tampoco se infiere el
presupuesto runtime, número de tokens, máximo de contexto o tamaño
descomprimido. La opción «v6» no revela su código ni una huella verificable.

**Estado del gate:** `PORTAL_GATE_PENDING`. Antes de una nueva versión o prueba
se necesitan candidato y paquete fijados, autorización humana separada,
preflight y presupuesto/alcance de ejecución. La [solicitud preparada](PORTAL_TEST_REQUEST_R3.md)
no autoriza esas acciones por sí sola.
