# Captura de traza del coordinador del portal

Work 2 ya publica su contrato real en `docs/RESULT_SCHEMA.md` y las salidas de sus tools se adaptan mediante `scripts/adapt_agent_tool_result.mjs`. Este envelope adicional define la evidencia que falta capturar **del coordinador ejecutado en el portal**. No debe fabricarse a partir de los ejemplos locales.

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

Al capturar una prueba del portal, mapear sus eventos reales a este envelope sin alterar cifras. Rechazar eventos sin salida observada o referencias de datos inexistentes. La versión fija y su conversación deben conservarse para demostrar que el coordinador eligió y usó la herramienta; los ejemplos locales por sí solos no lo prueban.
