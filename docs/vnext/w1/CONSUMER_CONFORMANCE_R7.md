# Consumer conformance W1 R7

Contrato productor: `0.3.1` (R6 congelado).
Los valores `PRODUCER_FIXTURE` son observaciones del productor, no oráculos independientes. Las selecciones temporales marcadas `independent_gtfs_expected` proceden del CSV GTFS bruto.

| Caso | Estado | Evidencia |
|---|---|---|
| `health_defaults_omitted` | `ok` | `PRODUCER_FIXTURE` |
| `health_defaults_explicit` | `ok` | `PRODUCER_FIXTURE` |
| `health_nondefault_margins` | `ok` | `PRODUCER_FIXTURE` |
| `health_duration_changes_return` | `ok` | `PRODUCER_FIXTURE` |
| `health_no_feasible` | `no_feasible_journey` | `PRODUCER_FIXTURE` |
| `health_date_not_validated` | `unknown` | `PRODUCER_FIXTURE` |
| `health_destination_unsupported` | `unsupported` | `PRODUCER_FIXTURE` |
| `health_profile_unsupported` | `error` | `PRODUCER_FIXTURE` |
| `compare_same_origin_two_hours` | `ok` | `PRODUCER_FIXTURE` |
| `compare_duration` | `ok` | `PRODUCER_FIXTURE` |
| `compare_cross_origin` | `ok` | `PRODUCER_FIXTURE` |
| `legacy_r4_explicit` | `ok` | `PRODUCER_FIXTURE_WITH_R4_INDEPENDENT_FIXTURE` |
| `mixed_r4_r6` | `ok` | `PRODUCER_FIXTURE` |
| `invalid_structural` | `error` | `CONTRACT_SEMANTICS` |

W2 debe ejecutar sus resultados contra este pack sin copiar la lógica de selección. W3 puede mutar cada campo y contrastar status, identidades, componentes, procedencia y límites.
