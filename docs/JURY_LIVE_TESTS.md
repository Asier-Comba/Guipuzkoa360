# GIPUZKOA 360 · Jury live tests

Último smoke del 25-09: **PASS ACOTADO**, documentado en
[smoke ultimate](internal/PORTAL_SMOKE_ULTIMATE.md). Preparación, pregunta principal y seguimiento
produjeron resultados observables; la consulta fuera de alcance se rechazó correctamente. El intento
`INFRASTRUCTURE_BLOCKED` que se detalla más abajo es histórico.

Versión objetivo: `urban-challenge-rc2-195b498 · v4`

Runtime: `195b4980fa5998b096c308296a55e452380b0371`

Esta guía separa cálculo local de latencia completa del portal. No abrir Entrega ni publicar durante las
pruebas.

## Guion privado mínimo

| Caso | Prompt | Tool y resultado obligatorio |
|---|---|---|
| Pregunta principal | «¿Qué municipios coinciden en envejecimiento de 65 o más y mayor distancia a atención primaria, con cuantil 0,75, umbral de 2 km y periodo 2025-01-01? Incluye municipios destacados, cortes, filas usadas, unidades, fuentes y el límite principal.» | Una llamada a `analizar_coincidencia`, sin `detalle`; 88 filas, 7 destacados, 23,973 % y 2.019,2 m. |
| Variación | «Ahora repítelo para 75+, cuantil 0,80 y umbral de 3 km.» | Nueva llamada a `analizar_coincidencia`; 4 destacados, 12,9796 % y 2.138,6 m. |
| Profundización | «De esos cuatro, enumera los municipios y explica brevemente por qué cumplen ambos cortes.» | Reutilizar la salida inmediatamente anterior si no cambia ningún parámetro; no inventar causalidad ni recitar el JSON. |
| Trazabilidad | «¿De qué fuente procede la población y qué periodo representa? Dame el límite principal.» | `consultar_fuente`; identificar `EUSTAT_EMH_2025`, institución, periodo y límite. |
| Límites | «Entonces Aduna no tiene médicos, ¿no? ¿Y 3 km son 3 minutos?» | Una tool si necesita recuperar el dato; rechazar ambas inferencias. Distinguir registros, distancia geométrica y tiempo de viaje. |
| Escenario | «Simula un nuevo registro de atención primaria en el punto representativo de Aduna.» | `simular_escenario`; marcar HIPOTÉTICO; 2.756,2→0,0 m y diferencia −2.756,2 m; no prometer efecto real. |

## Estado de ejecución del intento histórico bloqueado

| Prueba | Estado | Observación |
|---|---|---|
| Identidad/configuración v4 | PASS | Versión activa visible; memoria activa y sin Internet. |
| Preparación | WARN | El runner devolvió «ocupado» en los intentos actuales; no se obtuvo diagnóstico de código nuevo. |
| Pregunta principal | WARN | Dos intentos eligieron la tool y argumentos correctos, sin `detalle`; no hubo output por runner ocupado. |
| Variación | NO EJECUTADA | Se detuvo la secuencia al no existir output principal. |
| Profundización | NO EJECUTADA | Depende del resultado anterior. |
| Trazabilidad | NO EJECUTADA | Runner ocupado. |
| Límites | NO EJECUTADA | Runner ocupado. |
| Escenario | NO EJECUTADA | Runner ocupado. |

La evidencia histórica del mismo v4 sí registra estas familias como PASS en
`docs/PORTAL_EVIDENCE_RC2.md`. Se mantiene separada porque no es una ejecución nueva del 25-09.

## Latencias

- Motor local del benchmark: peor p50/p95/p99 caliente, 35,108/39,184/45,573 ms.
- Portal histórico: respuestas normales completas, aproximadamente 26–47 s.
- G-04 histórico: output visible a 28,3 s; respuesta final antes de 74,3 s.
- Escenario histórico v4: respuesta completa antes de 30,4 s.
- Intentos actuales de la pregunta principal: bloqueo observable aproximadamente a 16,5 s y 18,8 s.
- Preparación actual: bloqueo observable aproximadamente a 12,7 s; el reintento final volvió a responder
  «runner ocupado» casi inmediatamente.

Los milisegundos locales no incluyen inferencia, coordinación, arranque del sandbox ni red; no deben
compararse directamente con los segundos del portal.

## Comprobación de resultados visuales

Ejecutar siempre primero:

```powershell
py -3.12 scripts/benchmark/verify_jury_results.py --output analisis/jury_coincidence_results.json
```

Cuando Work 1 publique un export JSON de su visualización, usar:

```powershell
py -3.12 scripts/benchmark/verify_jury_results.py --candidate ruta/al/export.json
```

Esquema mínimo del candidato:

```json
{
  "cases": [
    {
      "id": "Q75_65_PRIMARY_2KM",
      "municipalities": ["Legazpi", "Ezkio-Itsaso", "Hondarribia", "Hernialde", "Oñati", "Idiazabal", "Errenteria"],
      "age_cut_percent": 23.973,
      "distance_cut_m": 2019.2,
      "highlighted_count": 7
    }
  ]
}
```

Los tres IDs esperados son `Q75_65_PRIMARY_2KM`, `Q80_75_PRIMARY_3KM` y
`Q85_65_PRIMARY_2KM`. El verificador exige orden y lista exactos; los cortes y el recuento son opcionales
en el export, pero si aparecen deben coincidir.
