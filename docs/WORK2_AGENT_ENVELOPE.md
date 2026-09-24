# Interfaz preparada para Work 2

Al 24/09/2026 no hay rama ni PR de Work 2 en el repositorio. Este contrato define el mínimo necesario para conectar una ejecución real sin atribuir al agente un cálculo que solo se hizo localmente. Se ajustará mediante adaptador cuando Work 2 publique su formato real; no se exige que cambie su implementación.

```json
{
  "run_id": "identificador estable de ejecución",
  "agent_version": "versión fija probada",
  "question": "pregunta textual",
  "tool_events": [
    {
      "tool": "nombre real de la herramienta",
      "arguments": {"age_group": "65+"},
      "output": {
        "comparison": [],
        "analysis": {},
        "metrics": [],
        "sources": [],
        "input_files": [{"path":"...","sha256":"...","rows":88}]
      }
    }
  ],
  "result": {"schema_version":"1.0.0", "...":"campos de EXPECTED_RESULT_SCHEMA.md"}
}
```

`scripts/adapt_work2_envelope.mjs` exige una salida **observada** de herramienta, calcula su `output_ref` y comprueba que `comparison`, `analysis`, `metrics` y `sources` del resultado coincidan exactamente con esa salida. Así una respuesta narrativa no puede introducir cifras diferentes. El JSON adaptado lleva `trace.execution_mode = "agent"`; después se añaden contornos con `scripts/enrich_work1_result.mjs` y se renderiza con `scripts/build_results.mjs`.

Si Work 2 devuelve otro JSON, crear un mapeo de su traza real a este envelope sin alterar valores. Rechazar eventos sin salida observada, identificadores de ejecución reutilizados, herramientas no permitidas o referencias de datos inexistentes. La versión fija del portal y sus pruebas siguen siendo necesarias: una traza JSON local no acredita por sí sola la ejecución en el portal.
