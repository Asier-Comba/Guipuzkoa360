# R16 — delta de presentación, candidato privado

Base inmutable R15: `69bcc6ead9ce444a884aa2b15469bd3b519775f5`.
ZIP base: `f937ed8124ba1107c78d2a516c5404626a97b9efe38b576a03b6cd98f781efd0`.
Manifest base: `95c78e2a26ae8a55e0e6ec772905e04a74620d2c18b282a605522ff0154eed76`.
Rama `hotfix/r16-presentation-consistency`, PR draft contra R15, nunca main.

## Delta autorizado

El builder lee el ZIP del SHA base, no archivos de una rama mutable. Solo modifica
`main.py` y `tools.py`; los otros 23 miembros, quince assets y W1 permanecen
byte-idénticos. El directorio generado `portal_r16` evita que las pruebas
históricas de R15 sobrescriban el candidato. No modifica source/builder R15.

En la frontera pública, `time_summary` copia start_s/end_s/total_s del raw
validado y verifica tipos enteros, intervalo, suma de componentes, espera inicial
y coherencia con salida del vehículo. Formatea relojes y duración con divmod
entero, sin redondeo. Un fallo de proyección bloquea toda cifra parcial.

El prompt contiene reglas generales, sin números/orígenes del oráculo: usar
resumen canónico, catálogo real para cobertura, omisión de periodo no solicitado
y recuperación acotada sin llamada inválida idéntica. Metadata de versiones,
hashes y nombres internos queda en raw/manifiesto, no en la vista del modelo.
IDs de fuentes, valores, periodos observados y linaje numérico se conservan.
La etiqueta de versión MODEL no se presenta como periodo de observación.

## Regeneración y gates

CPython 3.12 con requirements del proyecto. Desde este checkout exacto:

```text
python -m scripts.vnext_agent.build_r16
python -m pytest tests/vnext_agent/test_r16_presentation.py -q -o addopts=
python -m scripts.vnext_agent.verify_r16 --output work/r16-audit.json
python -m pytest -q -o addopts= --junitxml=work/r16-pytest.xml
node --test tests/e2e/contract_flow.test.mjs
python scripts/ops/verify_runtime_identity.py
python scripts/benchmark/verify_jury_results.py --output work/r16-jury.json
python scripts/release/verify_final_artifacts.py
git diff --check
```

El manifiesto enumera hashes/tamaños exactos. HEAD y CI se vinculan en checkpoint
del PR para evitar autorreferencia. La autoauditoría se denomina
`R16_AUTHOR_DELTA_CHECK`, NO aceptación independiente W1. La matemática aceptada
R15 y el productor no cambian; el agente real debe validarse nuevamente.

Checkpoint temprano: focal 116 PASS. Suite completa, auditoría y CI pendientes
en este checkpoint; no es autorización de Studio hasta su PASS exacto.
Primer focal: 115 PASS/1 FAIL por usar `departure` en vez del campo real
`departure_time` en la nueva presentación. Corregido antes del candidato;
no es fallo del productor, ni se borra el intento. Focal final 116 PASS.

## Histórico y presupuesto real

R15 real: Critical0/High1/Medium2/Low1; 12/12 mensajes consumidos. Evidencia
preservada en PR20/Issue16, sin cierre retrospectivo. R16 tiene autorización
separada para máximo cinco mensajes: principal y seguimiento/fuentes en sesión A,
principal en sesión B completamente limpia y Aduna75+ en sesión C limpia.
STOP-on-High. No abrir holdout ni modificar Entrega hasta C0/H0 reales.

Nueva versión privada con main/tools exactos, quince assets, nueve tools,
plan_visit con cinco campos, modelo observado, memoria ON e Internet OFF.
Guardar ID y trazas reales. No editar la versión histórica R15.
Sin merge, cambio main, track, confirmación ni publicación. RELEASE_GO=NO.
