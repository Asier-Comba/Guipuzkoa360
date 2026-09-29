# R4 · reproducciones y resolución

Antes: START_SHA c68eb5c55dec72a267b7435b4c364049f6eab408.
Después: proveedor 0.2.0; pin final en comentario de PR #15.

| Propiedad | Antes observado | Después comprobado |
|---|---|---|
| Permisos 2/3 inyectados en OUT_WD_1 | ok | no pareja ordinaria; no reserva asumida |
| Fixture synthetic-contract-v1 por API productiva | ok, 8400 s | unknown; solo inyección explícita en tests |
| Margen inicial 3 min | ausente del total | presencia 08:57, salida 09:00; total 8580 s |
| Payload anidado corrupto | validación incompleta por inspección | unknown sin itinerario; matriz de adversarios |
| JSON ajeno corrupto | escaneo global por inspección | solo lectura del ID allowlisted |
| Perfil alternativo | riesgo de perfil aceptado sin cambiar cálculo | perfil distinto de stop_only rechazado |
| Multidía | 25:xx parseado como itinerario | unsupported explícito en corredor multidía |
| Comparación | delta sin enumerar cambios | changes/held_constant y comparability por pareja |

No se presentan como incidentes de producción los probes sintéticos. Detalle
ejecutable: tests/mobility/test_r4_hardening.py. La fuente GTFS original se
enumera separadamente en scripts/mobility/raw_oracle_r4.py; no importa _legs,
plan_visit ni snapshot derivado para producir expected.

Impacto real: 6309 filas GO01, 162 viajes; pickup 0=6147/1=162;
dropoff 0=6147/1=162; timepoint 0=6309. Cero valores 2/3 en GO01 y en todo el
feed. Los diez ejemplos R2 mantienen ida/vuelta y suman exactamente 180 s por
la semántica nueva. REAL_CASES.json y PERFORMANCE.json originales no se
reescriben; verify_w1 rechaza regenerarlos con proveedor de otra versión.

R4 aporta 135 escenarios nuevos de tres orígenes × cinco horas × tres
duraciones × tres pares de márgenes. No heredan los 135 de la PoC. Todos
contrastados contra CSV bruto; once casos detallados incluyen una ausencia de
pareja viable. Timepoint aproximado limita la precisión del horario: diferencias
en segundos no se presentan como mejoras observadas ni probabilidades.

W3 C-R3-05/06/07/08 se cubren a nivel de proveedor por permisos, límites de
stop_only, atribución de duración a parámetro y recalculación de márgenes.
No se afirma que hayan pasado conversaciones, corpus del agente ni holdout W3.
