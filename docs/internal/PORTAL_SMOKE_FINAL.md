# Smoke actual de la integración final

Fecha: 2026-09-25. Runtime local congelado `195b4980fa5998b096c308296a55e452380b0371`.
Versión existente seleccionada: `urban-challenge-rc2-195b498 · v4`.
No se creó otro agente o versión; no se abrió Entrega.

Estado: **INFRASTRUCTURE_BLOCKED**.

| Intento separado | Acción | Punto exacto del bloqueo |
|---|---|---|
| 1 | Seleccionar v4 y «Comprobar preparación» | Consola: «El runner está ocupado. Espera a que termine una tarea e inténtalo de nuevo.» Observado al volver a la página; no se midió la latencia exacta. |
| 2 | Repetir preparación tras trabajo local independiente | Mismo error del runner; resultado observado a 36,9 s de la acción, cota de observación y no tiempo de cálculo. |
| 3 | Seleccionar v4 en Pruebas, abrir conversación privada y enviar pregunta 65+/q0,75/2 km | La interfaz mostró «Connection Error:». El mensaje permaneció en el cuadro de texto, sin turno, tool call ni output; comprobado a 22,0 s. |

La conversación mostraba «VERSIÓN PROBADA · V4», «Memoria activa» y «Sin Internet». La pregunta preparada:

> ¿Qué municipios coinciden en envejecimiento de 65 o más y mayor distancia a atención primaria, con
> cuantil 0,75, umbral de 2 km y periodo 2025-01-01? Incluye municipios destacados, cortes, filas usadas,
> unidades, fuentes y el límite principal.

La pregunta principal actual NO pasó; el seguimiento actual NO se ejecutó. No se cambia código por este
bloqueo y no se atribuyen tiempos locales al portal. Se detuvieron los intentos al alcanzar el máximo de tres.

## Alcance de la evidencia histórica

`docs/PORTAL_EVIDENCE_RC2.md` conserva el informe histórico. La lista de conversaciones observada ahora
sitúa consultas de fuente/resumen/comparación/aliases en v2, coincidencia y red-team en v3, y escenario en
v4. La etiqueta del nombre del agente se actualiza también en conversaciones antiguas: el número de
versión es la referencia. El informe no acredita que toda la batería se repitiera en v4.

El runtime final conserva el core validado; `195b498` añadió la aclaración de que el contador del escenario
incluye todos los registros sanitarios. La regresión de Aduna se verificó históricamente en v4. Mantener
esta evidencia y el bloqueo presente permite el gate condicional autorizado, sin fabricar un smoke PASS.
