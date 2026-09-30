# DAG de derivación R8

El DAG externo elimina `DERIVED` como fuente mágica. Las hojas son inputs humanos, GTFS, OSM, anchor sanitario y parámetros del modelo.

- `initial_wait = boarding_margin_s`.
- `pre_appointment_wait = appointment - llegada de ida - paseo de ida`.
- `return_wait = salida de vuelta - appointment - duración - paseo de vuelta`.
- `return_slack = return_wait - boarding_margin`. No son la misma magnitud.
- `total = suma de ocho componentes contiguos`.

W1-R7-F01 queda `RUNTIME_FINDING_RETAINED / EXPLANATORY_DAG_RESOLVED_EXTERNALLY`; no se afirma que el runtime haya cambiado.
