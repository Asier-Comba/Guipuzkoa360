# R15 source and period view review

Read-only inspection first used the actual generated R15 `portal/tools.py`
with the declared repository data root. The inspected operations were
`obtener_resumen_territorial(municipio="Aduna")`,
`consultar_fuente(source_id="EUSTAT_EMH_2025")`, and
`consultar_capacidades(pregunta_o_dimension="obtener_resumen_territorial")`.
No LLM, Studio, portal budget, holdout or engine modification was involved.

## Source and derivation

The numeric summary already provided source IDs, periods, numerator and
denominator for the 75+ percentage, plus the assumption that 75+ is derived
from birth years. The prepared 75+ count was tagged as a direct cell read;
this is not proof that the original statistical source directly observed an
age bucket. Its source lookup already exposed the exact birth-year cutoff
(`<=1949` at `2025-01-01`) in the existing catalog limitations.

Therefore the derivation was reachable, not missing evidence. No numeric
claim, formula, count, source or raw evidence was changed. The only source
projection improvement exposes the catalog's existing general `method`
alongside its existing limitations in `consultar_fuente`. The prompt can be
followed with a short source/period/derivation explanation without duplicating
whole metadata records into every numeric response.

## Period metadata

Before the metadata adjustment, summary capability coverage correctly listed
the three source reference dates, while its public `periodo.allowed_values`
was empty. Those source dates are not interchangeable selector values:
summary/comparison/aging/coincidence select demography; access/scenario retain
distinct current source dates and do not implement historical filtering.

The public projection now derives demographic selector values from the
unchanged repository's `available_periods()` and access/scenario values from
their unchanged capability coverage. Coverage itself is preserved. The
projected period field declares nullability and its allowed values, with an
explicit `period_policy` stating selection meaning, omission/`None` behavior
and fail-closed handling of explicit invalid values.

The demographic omission rule is **one available period, otherwise request a
period**, not "latest available". Source-only omission preserves each source's
own period; it does not create a homogeneous snapshot. Public docstrings were
aligned with that existing behavior.

Permanent focused regressions in `test_r15_period.py` compare source method
and limitations with the actual catalog, prove every advertised period is
accepted by its operation, preserve original coverage/raw evidence, and check
the nullable/omission policy. This is an offline view contract review, not an
independent acceptance or real-model retest.
