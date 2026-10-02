# R21 — aceptación real: FAIL / STOP

## Identidad congelada

- Runtime probado: `b0096e9aeda533ed0a43f56bf98975becf4022d8`.
- ZIP: `a714bac1fa91caebe3e8ef6fb65259c4f11447120479ecf51dce4813cfba5dc2`; 240430 bytes, 25 miembros.
- Manifiesto: `6d425d3e194e6fea016ae4a4b685ae2e50af978897278539d17b7bb03fad31b9`.
- Únicos miembros distintos de R20: `main.py`, `tools.py`; los otros 23, los 15 assets y v4 se conservan.
- Versión privada real: `agentv_488851cc28d143be972ced32584fc582`, nombre `GIPUZKOA 360`, Internet desactivado.
- Protocolo prefijado: `outputs/r21/real-protocol.json`, SHA-256 `9166debb4d54458e54413f3da875543ddc55ab79a9a9348369dfb2ec57ab1928`.

## Preparación y validación determinista

Studio validó exactamente las diez herramientas y sus firmas. La copia de `main.py` y `tools.py` se verificó mediante lectura posterior del editor. La creación mostró un aviso genérico `Connection Error:`; no se repitió el clic. Una pestaña nueva confirmó la versión persistida por su identificador y pudo ejecutar tres mensajes reales. No se atribuye una causa al aviso.

El scaffold del portal contiene un `ejecucion.py` generado por la plataforma, no utilizado por los imports del candidato. No se afirma que una exportación del portal sea idéntica al ZIP de distribución de 25 miembros; este incluye material de verificación no cargado como contexto.

- Python completo: 780/780; Node: 17/17.
- Paridad raw: 901/901; oracle histórico: 7/7; 26 comparaciones compuestas.
- Metamorphic: 14/14; negativos: 195; fuzz malformed: 5000; findings offline: 0.
- Identidad v4, jury, artifacts, diff y dos builds idénticos: PASS.
- CI R21: [37073444619](https://github.com/Asier-Comba/Guipuzkoa360/actions/runs/37073444619), Ubuntu y Windows PASS sobre el runtime exacto.
- Fast CI: [37073444574](https://github.com/Asier-Comba/Guipuzkoa360/actions/runs/37073444574), ambos sistemas PASS.
- Metadatos y asociación exacta: `outputs/r21/ci-exact-sha.json`.

Los primeros fallos del verificador se conservan en `local-gates.json`: orden de diccionarios serializados, URLs nulas de provenance no web y spelling de un origen de prueba. Se corrigió el verificador; no se transfirió PASS de intentos previos.

## Tres mensajes reales, sin transferencia de evidencia histórica

1. Discovery: PASS, un LOW estilístico por extensión; catálogo válido, diez herramientas, fuentes y límites fieles.
2. Ranking 65+: PASS; una primera llamada válida, cinco porcentajes y numeradores/denominadores iguales a los claims, Eustat 2025-01-01; sin explicación 75+.
3. Getaria: FAIL HIGH por atribución errónea de fechas a fuentes.

Los transcripts, argumentos, outputs completos, scorecards y mediciones observadas están en `outputs/r21/portal/gate-01.json` a `gate-03.json`. Las latencias son cotas superiores de observación, no tiempos exactos del modelo. El registro de la segunda prueba utiliza una cota conservadora anterior al envío; la observación final de discovery fue tardía por revisión de evidencia. No se deduce un problema de rendimiento de esas cotas.

## R21-H01 — reproducción del fallo real

Prompt exacto prefijado:

> Explícamelo para una persona no técnica: En Getaria, ¿qué distancia geométrica hay al registro de salud mental más cercano y queda dentro de 1 km?

Primera y única llamada: `analizar_acceso_municipios`, argumentos `{"categoria_servicio":"mental_health","umbral_km":1,"municipios":["Getaria"]}`. Output `status=valid`, distancia 2913.3 m, clasificación fuera del umbral. No hubo error ni retry.

`claims[0].reference_periods` atribuye inequívocamente:

- `ODE_HEALTH_CENTRES_2026`: `2026-09-20`, registro sanitario.
- `GEOEUSKADI_MUNICIPIOS_2025`: `2025-05-07`, punto municipal/cartografía.

La distancia, conversión a aproximadamente 2.9 km, clasificación y límites de la respuesta son correctos. Sin embargo, su última frase dice:

> La referencia del registro sanitario es del 7 de mayo de 2025 y la del punto municipal, del 20 de septiembre de 2026.

Intercambia ambas atribuciones fuente/fecha. Son dos claims materiales no soportados, agrupados en un hallazgo HIGH de trazabilidad. La cifra aislada de fecha existente no respalda su atribución a otro sujeto. Evidencia: `gate-03.json`, `gate-03-live.txt`, `gate-03-dom.txt`, `gate-03-failure.png`.

## STOP obligatorio, no entrega verde

`REAL_MESSAGES=3`, `REAL_CRITICAL=0`, `REAL_HIGH=1`, `REAL_MEDIUM=0`, `REAL_LOW=1`, `UNSUPPORTED_MATERIAL_CLAIMS=2`.

Se aplicó literalmente la condición de parada R21: no se ejecutaron gates 4–11, muestra general, conversación pública ni presentación. No se creó R22, no se parcheó el runtime, no se seleccionó este candidato en Entrega, no se marcó confirmación ni se publicó. Los PASS offline no convierten esta aceptación real en PASS.

`AGENT_ENGINEERING_COMPLETE=NO`; `READY_FOR_HUMAN_FINAL_GATE=NO`; holdout sellado/no ejecutado. La Entrega permanece privada y sin cambios de esta ronda. El siguiente paso requiere una decisión humana explícita sobre el hallazgo; la autorización actual prohíbe arreglarlo automáticamente.
