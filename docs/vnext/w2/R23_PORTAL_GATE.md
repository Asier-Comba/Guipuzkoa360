# R23: umbral corregido; aceptación final detenida por HIGH nuevo

## Identidad exacta

- Runtime: `6e960e873972b06fbd9e5125e7a498eef61c6d3a`.
- ZIP: `b88f44aaabeac6cf50ee7a0e3aaea7295737f0b00bfb47cc2e34c1240e63b2e0`, 242.911 bytes.
- Manifest: `ceaed687082f4ab165e79ae828cd8f0b17ca51cd888669f9c21f0e3ab6ef9f62`.
- Versión privada real: `agentv_0604ea1aa5e141269381e41f9f463c97`, carpeta `agentes/gipuzkoa_360_5`.
- main.py/tools.py leídos de vuelta y contrastados byte a byte; preparación real Studio: 10 tools, 15 context assets, memoria ON, Internet OFF. El scaffold de plataforma ejecucion.py no se importa ni registra. Su presencia no se confunde con los 25 miembros del ZIP de referencia.

## Validación local y CI, no evidencia del modelo

836/836 Python, 17/17 Node, 14 focales, 901/901 paridad raw, 7/7 oracle, 26 comparaciones compuestas, 14 propiedades metamórficas, 195 negativos, fuzz 5.000, 10.399 atribuciones verificadas. Identity/v4, jury, artifacts, double-build y diff PASS. Offline C0/H0/M0.

CI exacto antes de Studio: [R23 37113709603](https://github.com/Asier-Comba/Guipuzkoa360/actions/runs/37113709603), Ubuntu y Windows PASS; [fast 37113709628](https://github.com/Asier-Comba/Guipuzkoa360/actions/runs/37113709628) PASS. Los logs de ambos jobs acreditan checkout del runtime indicado, 836 Python, 17 Node y hashes de dos builds idénticos. El registro `outputs/r23/ci-exact-sha.json` distingue ese runtime de cualquier commit posterior de evidencia.

## Doce mensajes reales; STOP al primer fallo material nuevo

| Caso | Resultado |
|---|---|
| Pregunta exacta R22-H01, atención primaria/2 km | PASS, regla ≤2 km; 10/88 explícito |
| Distancia hipotética 0 m/2 km | PASS, cero incluido; no accesibilidad efectiva inferida |
| Getaria salud mental/1 km | PASS, 2.913,3 m, fuera |
| Fuentes Getaria | PASS, Salud20/09/2026 frente a geo07/05/2025 |
| Tolosa hospital/2 km | PASS, 18.670,9 m, fuera |
| Fuentes Tolosa | PASS, asociación fuente/fecha correcta |
| Ranking 65 años o más | PASS, cinco valores y método Eustat2025-01-01 correctos |
| Legorreta/Alegia, dos resúmenes nuevos | PASS, 309/378 personas, 20,614/20,410%, diferencia69 y0,204pp |
| Umbral salud mental1→6 km | PASS, criterio cambia; no distancias ni mejora real |
| Alta hipotética43,-2 WGS84/2km | PASS, consulta real; no apertura/capacidad/citas inferidas |
| Retirada mediante identidad observada Aduna | PASS, entityF0E8348B; 2.756,2→3.137,2m; +381m |
| Visita Zegama09:30/20min | **FAIL R23-H01: alcance final contradictorio**, cálculo correcto10.691s |

La primera consulta general mostró recuperación REAL: `obtener_resumen_territorial({municipio:Gipuzkoa})` devolvió error controlado sin cifras y se corrigió una sola vez con `analizar_acceso_general(primary_care,2)`. No se repitió la llamada fallida ni se cambió la intención. Los dos prompts adicionales de recuperación se omitieron por redundancia, no se contabilizan como ejecutados.

## R23-H01 literal: fallo del relato, no del productor

Prompt congelado:

> Desde Zegama quiero ir al Ambulatorio de Beasain el 29/09/2026, con cita a las 09:30 y consulta de 20 minutos, y volver a las paradas. ¿Cuánto tiempo completo ocupa y qué límites tiene?

Tool real: catálogo y después plan_visit, origin_id=zegama_center_stops, destination_id=beasain_official_centre_anchor, date=2026-09-29, appointment_time=09:30, duration_minutes=20. Salida válida: scope=origin_stop_presence_to_return_stop_arrival; inicio08:09:37, final11:07:48, total10.691s=2h58m11s. La espera inicial de180s está incluida; el autobús no sale a08:09:37.

La respuesta comienza correctamente describiendo el regreso a Zegama, pero contradice después el extremo final:

> Parte de las paradas, no del domicilio, y termina en un punto de referencia del ambulatorio, cuya puerta y accesibilidad no están verificadas.

El punto sanitario es un destino intermedio; el cálculo completo termina en las paradas de regreso de Zegama. **HIGH1 / unsupported material claim1** por la contradicción de alcance en la presentación del resultado. Las cifras y componentes de la herramienta son correctos; no se cambia ni culpa al productor. El rótulo “Salida modelada:08:09:37” tampoco distingue por sí solo presencia inicial y salida del vehículo; se conserva la respuesta literal sin ocultar esa ambigüedad.

Evidencia completa: `outputs/r23/portal/health.json`, `health-scope-proof.json`, `health.txt` y `final-stop-proof.png`. Cada caso contiene prompt, argumentos observados, salida, respuesta, versión/runtime y latencias. Las latencias son cotas superiores de primera observación en UI; abrir el output colapsado añade tiempo de revisión y no acredita latencia del servidor.

## Estado final acotado

REAL C0/H1/M0/LOW2; unsupported material claims1. LOW: verbosidad de límites y formato redundante de longitud firmada+cardinal; coordenadas reales correctas. Ninguno se usa para añadir código.

THRESHOLD_SEMANTICS=PASS; ZERO_DISTANCE_INCLUDED=PASS; R22_HIGH_REGRESSION=PASS. Acceso general/seleccionado, fuentes, multi-tool, multi-turn, recuperación real y las tres simulaciones PASS. Recalculation PASS únicamente para el escenario de umbral; el seguimiento sanitario09:45 no se ha ejecutado y no se acredita con el oracle offline.

Health09:45, honestidad en tiempo real, ambigüedad y conversación pública de tres turnos **NOT_RUN por STOP**. No se traslada ningún PASS real de R22 ni de generaciones anteriores. No se repite el caso ni se provoca una respuesta correctora para borrar el fallo.

AGENT_ENGINEERING_COMPLETE=NO; READY_FOR_HUMAN_FINAL_GATE=NO; FINAL_PROJECT_STATE=NO_GO. Se conserva el candidato exacto para decisión humana R23/fallback, sin R24 automático, parche, merge ni publicación.

Entrega sin cambios: no se seleccionó R23; permaneció la selección previa “GIPUZKOA360 · Visita sanitaria · v3”, copy existente, dos enlaces, presentación existente y track Equipos de servicios. Equipo de tres personas confirmado y casilla final sin marcar se observaron antes de probar. No se revalidó presentación ni preview tras el STOP; no se afirma su PASS para R23. El borrador seguía privado y no se pulsó publicación ni confirmación.
