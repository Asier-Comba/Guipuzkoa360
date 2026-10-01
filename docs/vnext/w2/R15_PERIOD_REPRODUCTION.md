# R15 period boundary: reproduction before implementation

Base inspected: `094745b26bc57aee5cc1a5e003401743d96a914f` (R14).
Reproduced locally through the actual public functions in
`agentes.gipuzkoa360_vnext.main`, before changing their validation. No Studio,
portal, holdout, dataset, calculation or W1 code was used or modified.

## Minimal numeric-acceptance reproduction

```python
import json
from agentes.gipuzkoa360_vnext import main

result = json.loads(main.analizar_acceso_servicios(
    categoria_servicio="primary_care", municipios=["Aduna"], periodo="   "))
assert result["status"] == "valid"
assert len(result["claims"]) == 1
assert result["error"] is None
```

The same call with `periodo="2099-01-01"` also returns one numeric claim.
`simular_escenario(accion="change_threshold",
categoria_servicio="primary_care", nuevo_umbral_km=2.0, periodo="   ")`
returns `valid` with 40 claims; the unsupported date also returns 40 claims.
These are explicitly supplied inputs, not omitted values or `None`.

An exactly empty string (`""`) was already rejected by all six public tools
with a period field: `domain / invalid_arguments`, zero claims. The precise
numeric-acceptance defect is therefore **whitespace and unsupported dates**,
not an exactly empty string. No claim is made that Astra's unpublished
exact-empty reproduction has been independently reproduced.

## Matrix observed before implementation

Each of six public interfaces was executed with seven period variants (42
calls): omitted, `None`, `"2025-01-01"`, `""`, `"  "`, integer `2025`, and
`"2099-01-01"`. The third value is the demographic dataset's valid period,
not a valid services/geography snapshot period.

| Public interface | Omitted / None | Demographic date | Empty / wrong type | Whitespace / unsupported date |
| --- | --- | --- | --- | --- |
| obtener_resumen_territorial | valid | valid | domain error, no claims | unknown / unverified_result, no claims |
| comparar_municipios | valid | valid | domain error, no claims | unknown / unverified_result, no claims |
| analizar_envejecimiento | valid | valid | domain error, no claims | unknown / unverified_result, no claims |
| analizar_acceso_servicios | valid | valid, despite absent period support | domain error, no claims | valid numeric claims |
| analizar_coincidencia | valid | valid | domain error, no claims | unknown / unverified_result, no claims |
| simular_escenario | valid | valid, despite absent period support | domain error, no claims | valid numeric claims |

The unchanged engine records `period_requested` in access results and does
not time-filter the services/geography calculation. The scenario passes the
same requested period to access. This does not make an unsupported requested
period evidence of a supported historical snapshot.

## Supported period sources

The actual capability registry reports:

- Demographic period: `2025-01-01` (via `DataRepository.available_periods()`).
- Access/scenario coverage periods: `2026-09-20` and `2025-05-07` (services
  and geography source reference periods, respectively).
- Summary/comparison/coincidence coverage lists all three source dates, but
  their `periodo` selects demography and must still use the unchanged
  demographic `choose_period()` contract.

Proposed narrow validation: reject strings/string-array elements whose
`strip()` is empty without stripping, coercing or repairing submitted values;
validate access/scenario explicit periods against their capability coverage;
retain the demographic selector and classify its unsupported period as a
controlled input error. Omitted/`None` keep existing documented defaults and
source-specific periods; accepting a source date does not establish a
homogeneous snapshot or introduce historical filtering.

## Additional eight-tool probes

Nineteen adversarial public calls covered scalar-versus-list serialization,
numeric age versus string age, wrong coordinate types, missing conditional
coordinates, percentile 75 versus quantile 0.75, unsupported source IDs,
prose in category fields, object instead of text query, `None`, whitespace,
unknown municipalities and duplicate municipalities. No exception escaped;
invalid calls produced zero claims. Known municipal identity errors are
classified as `unknown / unverified_result` and duplicates as
`execution / contract_violation`; these fail closed and are recorded rather
than used to expand this numeric-acceptance fix.

This file records observations **before** the validation patch; regression
tests and final package evidence record the after-state separately.
