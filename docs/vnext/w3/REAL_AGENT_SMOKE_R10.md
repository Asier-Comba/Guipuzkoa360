# Smoke real R10 — preparado, BLOCKED

No se llamó a un LLM. QA local no tiene langchain/langchain_core, modelo/factory
configurado ni credenciales/presupuesto autorizado. Una suscripción no es permiso
para abrir una API. No se instalaron dependencias globales ni eligió proveedor nuevo.
El ZIP actual W2 0.2.0 tampoco es el candidato sanitario. Contador real: **0**.

[SMOKE_PLAN_R10.json](SMOKE_PLAN_R10.json) congela 12 conversaciones de desarrollo
ya existentes: cuatro territoriales, cuatro sanitarias y cuatro límites/adversarios.
36 turnos para el scorer, no 12 aciertos de casos individuales. Cuatro probes extra
cubren puerta, fuente falsa, error de evidencia/HTTP y comparación 09:30→09:45;
son evidencia auxiliar, fuera de los denominadores congelados. Holdout sin abrir.

## Runner

`python -m scripts.vnext_product.local_smoke_r10` solo comprueba entorno y plan;
no carga modelos, código candidato ni red. `--run` ejecuta **un turno** del agente
real `main.build_agent(model)`, desde ZIP revisado y extracción limpia. El usuario
formula la pregunta; W3 no inyecta herramienta/ID correctos ni llama a tools para
hacer pasar routing. Conserva callbacks de modelo/tools y mensajes originales,
fallos antes de respuesta y reintentos. Nunca fabrica un assistant final.

No está probado contra un modelo real. La captura es RAW, no una traza puntuable
por cambiar bandera. Se revisa y convierte a W3_TRACE_2.1.0 con los timestamps,
argumentos, IDs, public_result y bindings **observados**; si falta alguno queda
capture_incomplete o raw, no se inventa. Reutilizar `score_runs.py` 2.1.0;
no se cambió su esquema, corpus, expected ni scorer. El binding interno request_id
requiere evidencia de execute además del envelope público; no duplicarlo desde
el output para simular que se observó el input. Los semantic_checks requieren
JSON Pointer real y revisión del significado, no coincidencia literal.

Config autorizada (sin secretos) necesita:

- `existing_resources_authorized=true`, referencia a permiso humano específico.
- `max_model_calls_per_turn` 1–8 y `max_model_calls_total` 1–288; ambos caps se
  cuentan por callback real y el total incluye intentos fallidos/reintentos.
- `assembly_manifest_file`/SHA: W3_ASSEMBLY_1 con ZIP, datos, miembros/source_shas,
  imports, comando de generación, modelo/config y contexto fijados.
- `health_review_file`/SHA con `combined_health_acceptance=PASS` y el mismo SHA
  del ZIP W2; el review del ZIP W1 separado **no** satisface este requisito.
- `model_factory_file`/SHA: recurso existente, humanamente autorizado,
  `build_model(model_id, model_config)`; nunca claves en archivos de evidencia.

```powershell
python -m scripts.vnext_product.local_smoke_r10 --run --config <config-autorizada.json> --evidence-root <evidencia-fijada> --scenario VN-CONV-11 --turn 1 --output-dir <capturas-del-candidato>
python -m scripts.vnext_product.score_runs --runs <trazas-revisadas-2.1.0.jsonl> --evidence-root <evidencia-fijada> --output <scores.json>
```

Un turno por paso permite revisar antes de continuar. Critical/High: guardar
STOP_CRITICAL_HIGH.json en el directorio, parar lote afectado, reproducción mínima,
propietario y nuevo candidato. No ampliar a holdout hasta freeze y revisión humana.
No compartir out entre modelos/configs o usar historia de otro candidato.
Captura no certifica aislamiento del runtime portal. No modelo real = no generación,
latencia LLM, routing ni comparación v4. Su transformación con un candidato/modelo
real sigue pendiente de validación; no se afirma que el pipeline conversacional
end-to-end pasó por los unit tests del capturador.
