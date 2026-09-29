# W1 R6 · delta de procedencia 0.3.1

Estado: **PUBLICADO ANTES DE IMPLEMENTAR**. Este documento fija el cambio localizado que W2/W3 pueden revisar sin bloquear su consumo estable de R4/R5.

## Hallazgo reproducido

En `provider_r5.plan_visit`, una petición sin `boarding_margin_minutes`, otra con el valor explícito `3` y otra con `5` producen `initial_wait` con `basis=user_input` y `source_refs=[USER]`. La primera afirmación es incorrecta: `3` fue aplicado por el modelo como default. Además, los componentes de paseo y espera citan un conjunto amplio de fuentes aunque no todas participen en cada cálculo.

## Corrección compatible

- R4 0.2.0, R5 0.3.0, sus snapshots, bytes, resultados y entrypoints quedan intactos.
- Se añade el entrypoint opt-in `prototypes.ir_y_volver.provider_r6`, contrato cerrado 0.3.1.
- 0.3.1 añade procedencia por parámetro: `human_explicit` o `model_default`.
- `USER` contiene y hashea solo los campos explícitos; `MODEL_DEFAULTS` identifica los valores aplicados por el proveedor.
- Cada componente cita solo sus entradas efectivas: horario GTFS, red OSM, punto sanitario, fórmula, parámetros explícitos/defaults y/o derivación según corresponda.
- No cambia selección, tiempos, geometría, snapshot ni semántica de acceso modelado.

Compatibilidad: W2 puede seguir fijado a R4 0.2.0 o R5 0.3.0. Adoptar 0.3.1 es voluntario y exige importar explícitamente `provider_r6` y validar los schemas 0.3.1.

Clasificación de los hallazgos W2 anteriormente reportados: `FIXED_BY_AUTHOR_PENDING_W3_RETEST`; no se presentan como defectos abiertos confirmados ni como aceptados independientemente.
