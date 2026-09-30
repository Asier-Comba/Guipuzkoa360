# Semántica de claims R9

Los valores directos del GTFS son valores programados de fuente, no observaciones reales.
`timepoint=0` indica que la hora del feed es aproximada/interpolada; no acredita paso operacional exacto.
Los paseos son estimaciones del modelo, no comportamiento peatonal medido.

## Wording seguro

- **Evitar:** El autobús sale exactamente a las 08:12:37.
  **Usar:** El horario GTFS utilizado sitúa la salida programada en 08:12:37; el feed la marca como aproximada (timepoint=0).
- **Evitar:** Caminas 7 minutos.
  **Usar:** El modelo estima 420 s de paseo con el supuesto fijado.
- **Evitar:** Ahorras 35 minutos.
  **Usar:** En el escenario modelado, el total de 09:45 es 35 min menor que el de 09:30.
- **Evitar:** No hay transporte.
  **Usar:** No se encontró una combinación viable dentro del snapshot y restricciones analizados.
- **Evitar:** Esta es la entrada del ambulatorio.
  **Usar:** El paseo termina en el punto oficial modelado del centro; la entrada física no está verificada.
