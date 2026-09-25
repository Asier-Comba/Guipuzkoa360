# CI y reproducción

## Evidencia remota real

- [36146104354](https://github.com/Asier-Comba/Guipuzkoa360/actions/runs/36146104354): Windows PASS; Linux FAIL por separadores Windows en el manifiesto original.
- [36146381547](https://github.com/Asier-Comba/Guipuzkoa360/actions/runs/36146381547): misma avería; el primer parche había normalizado el manifiesto preparado, no el original. Se conserva el intento fallido, no se presenta como arreglo completo.
- [36147113831](https://github.com/Asier-Comba/Guipuzkoa360/actions/runs/36147113831), commit `47362d3`: ambos sistemas PASS tras corregir la lectura del manifiesto original. Fuentes, hashes y runtime no cambiaron.

Los runs posteriores de la rama incorporan NEXT. Consultar siempre el SHA del run, no extrapolar un resultado anterior al HEAD. Actions están fijadas por SHA y runtimes Python 3.12.10 / Node 24.12.0. Dependencias Python del proyecto siguen rangos de requirements: checkout limpio demostrado, no lock universal de todos los wheels futuros. Instalación `--no-cache-dir`, checkout completo, permisos contents:read y sin credenciales persistidas.

## Ejecución rápida desde la raíz

```sh
python -m pip install --no-cache-dir -r requirements.txt
python scripts/ops/verify_runtime_identity.py
python -m pytest -o addopts= -q
node --test tests/e2e/contract_flow.test.mjs
node --check scripts/jury_view.js
node --check scripts/build_jury.mjs
node --check scripts/build_results.mjs
python scripts/benchmark/verify_jury_results.py --output work/jury-gate.json
python scripts/release/verify_final_artifacts.py
python scripts/ops/verify_package.py
python scripts/ops/compute_source_health.py --output work/source-health.json
python scripts/evaluation/evaluate_next.py --output-dir work/next
python scripts/ops/verify_runtime_identity.py
```

Los tests existentes regeneran temporalmente el bundle y restauran sus bytes. El gate posterior detecta contaminación. NEXT importa tools con un nombre de módulo propio; no modifica los imports del agente. El gate de identidad se ataca con una copia temporal alterada por un salto de línea y luego ausente.

## Validación completa, separada

```sh
python scripts/benchmark/full_validation.py --output-dir analisis/ops/full-validation
python scripts/ops/verify_runtime_identity.py
```

`.github/workflows/full-validation.yml` tiene exclusivamente `workflow_dispatch`, timeout 90 minutos y artifact de 30 días. La rápida no ejecuta los 72k checks. El workflow manual no se ha despachado remotamente en esta rama: no estaba en el default branch y no se modifica ese branch para activarlo. **HUMAN_ACTION_REQUIRED** tras integración autorizada: Actions → Full release validation → Run workflow → seleccionar SHA/rama aprobada. La ejecución local del mismo comando es PASS (72.673/72.673); no se etiqueta como run remoto.

Paquete: `verify_package` prueba dos builds, miembros exactos y contenido canónico. La reproducibilidad está acotada a toolchain/zlib probado; no implica igualdad de compresión en cualquier biblioteca futura. Reports de Actions caducan; conservar los gates relevantes con el release aprobado.
