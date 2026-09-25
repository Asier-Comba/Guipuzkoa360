# GIPUZKOA 360 NEXT — estados reales, sin promesas implícitas

| Etiqueta | Estado |
|---|---|
| **LIVE TODAY** | Runtime congelado `195b498…`, 7 tools deterministas, datos versionados de 88 municipios/148 registros y evidencia histórica de la familia de versiones del portal. El smoke más reciente está bloqueado por infraestructura. |
| **OFFLINE PROTOTYPE** | Planner, CapabilityRegistry, Executor, EvidenceCritic, Composer, Evaluation, ImprovementProposal y source watcher. Solo intents estructurados; no está en el portal ni en producción. |
| **PROPOSED** | Evaluar patrones de uso agregados, generar propuestas, shadow/benchmark y promoción humana. No hay autoedición ni autodespliegue. |
| **REQUIRES NEW DATA** | Movilidad, capacidad, demanda, vivienda, ambiente y seguimiento longitudinal comparable. No están implementados. |

Implementación: `prototypes/gipuzkoa360_next/`. No está en STUDIO_CONTEXT_FILES, imports de producción ni ZIP. Ningún nuevo modelo, servicio de red, framework de agentes o proceso persistente. Cinco responsabilidades lógicas bastan; no hay motivo demostrado para desplegar cinco LLMs.

```text
CURRENT
Pregunta → coordinador → tool determinista → evidencia → respuesta

NEXT PROTOTYPE
Structured Intent → Planner → Capability Registry → Executor → Evidence Critic → Composer

OPERATIONS
Data / Usage Signal → Evaluate → Proposal → Tests → Human Approval
```

## Fronteras que sí aportan

| Componente | Responsabilidad | Exclusión |
|---|---|---|
| Planner | Validar intención explícita y parámetros; resolver seguimiento con estado propio de sesión | No calcula cifras; no se anuncia comprensión arbitraria de lenguaje natural |
| Resolver | Allowlist de capacidades, parámetros y estado | No genera tools ni habilita capacidades por petición del usuario |
| Executor | Llamar al TerritorialAnalysis existente mediante el contrato y JSON estricto | No replica distancias, cuantiles, tasas ni algoritmos territoriales |
| Critic | Validar sobre, fuentes declaradas, periodos/unidades/filas/método/límites, escenario y consistencia por reejecución | No es oráculo numérico independiente ni detector semántico general |
| Composer | Plantilla exacta con evidencia validada, unidades, periodo y límites | No acepta redacción libre ni nuevas cifras; FAIL bloquea |
| Data Steward | Comparar metadata y emitir propuestas revisables | No descarga ni promueve datos automáticamente |
| Evaluation | Casos etiquetados, goldens, ataques, shadow y denominadores | No altera la respuesta en vivo ni aprende de conversaciones completas |

El Planner consume `intent`, no una frase libre: sus aliases incluyen resumen/comparación/acceso y nombres de tools; los aliases de municipios/grupos siguen resueltos por el core. Para incorporar un LLM planner futuro harían falta un corpus etiquetado, parser estricto, ambigüedades, pruebas de selección y aprobación humana. El 9/9 medido NO prueba ese futuro comportamiento.

## Contratos

Plan: `intent`, `candidate_capability`, `parameters`, `ambiguities`, `missing_inputs`, `out_of_scope`, `expected_evidence`, `followup`. No incluye ningún resultado numérico calculado. Parámetros desconocidos, booleanos donde se espera número, no finitos y contratos de tipo incorrecto bloquean. Los campos de escenario específicos se validan además en el core, devolviendo error controlado; no se inventan coordenadas.

Capability: `id`, `description`, `status`, `required_data`, `tool`, `parameters`, `evidence_requirements`, `limitations`. Estados de diseño: ACTIVE (implementación determinista utilizable), PROTOTYPE (experimento no habilitado), REQUIRES_DATA (falta fuente/contrato) y DISABLED (bloqueo explícito). Actualmente solo 7 entradas ACTIVE y 5 REQUIRES_DATA; no se inventan entradas para rellenar cada estado. Resolver/Executor solo aceptan ACTIVE.

Providers actuales: DemographyProvider (resumen/comparación/envejecimiento) y HealthcareProximityProvider (acceso/coincidencia/escenario). Solo delegan al mismo Executor. MobilityProvider, CapacityProvider, DemandProvider, HousingProvider y EnvironmentProvider rechazan ejecución: REQUIRES_DATA. Consultar fuentes sigue una capacidad de catálogo, no un proveedor de métricas ficticio.

Critic: `status=PASS|WARN|FAIL`, `reasons`, `missing_evidence`, `safe_next_action`; al pasar añade evidencia canónica, hash y versiones. JSON rechaza NaN, Infinity, desbordamiento `1e999` y claves duplicadas. La igualdad canónica rechaza cambios de cifras, booleanos por números, metadatos o fuente falsa. WARN conserva advertencias originales. `source` permite periodo global null porque los periodos están en cada entrada del catálogo.

Composer admite exclusivamente `render(evidence)`: cualquier draft distinto (incluidas causalidad, minutos, capacidad, recomendación o predicción) se rechaza. Es una defensa estricta contra redacción no autorizada, con coste de UX: produce un resumen estructurado, no una conversación pulida. Un atacante con acceso al proceso puede falsificar objetos internos; el hash no es una firma/autenticación. El critic comparte algoritmo con Executor: un error común exige goldens independientes y la batería existente.

## Ejecutar y medir

```sh
python -m pytest tests/next -o addopts= -q
python scripts/evaluation/evaluate_next.py
```

Ejemplo en Python: `NextSession().ask('coincidence', {'categoria_servicio':'primary_care','grupo_edad':'65','cuantil':0.75,'umbral_km':2})`. En esa misma sesión, `ask('seguimiento', {'grupo_edad':'75','cuantil':0.8,'umbral_km':3})` hereda categoría y recalcula; no hay memoria global entre usuarios.

Cada respuesta validada lleva DATA_VERSION, RUNTIME_VERSION, CAPABILITY_VERSION, PROMPT_VERSION y BENCHMARK_VERSION. [Evaluación completa](../../analisis/next/evaluation.json) conserva parámetros, outputs, critic, respuesta y hashes de código; [KPIs](../../analisis/next/quality_kpis.json) separa numerador/denominador/valor/definición. Los tiempos son medidas locales puntuales, no latencias de portal.

## Límites explícitos

- La resolución de source_id acredita pertenencia al catálogo, no que cada campo del sobre lleve todas sus fuentes. Por ejemplo, el resumen compacto declara Eustat y contiene métricas sanitarias cuya procedencia completa requiere FUENTES/metadata y metrics_reference_period. No llamar al KPI «trazabilidad exhaustiva campo a campo».
- Recalcular dos veces protege frente a adulteración del output, pero cuesta tiempo y no corrige un fallo compartido del algoritmo.
- La plantilla no promete «responder como v4». Es una opción de investigación de seguridad, no un reemplazo listo para portal.
- La suite existente y el gate byte a byte son obligatorios tras cualquier experimento.

## Cuando Gipuzkoa esté mejor cubierta

- **LIVE TODAY:** detección de diferencias y descripción `within_threshold`.
- **OFFLINE PROTOTYPE:** efecto geométrico marginal al añadir un registro y **GEOMETRIC SERVICE-REMOVAL SENSITIVITY** al retirarlo. Agregan diferencias que ya calcula el core; no son beneficio social, resiliencia ni localización óptima.
- **PROPOSED:** monitorización longitudinal solo con snapshots temporal y metodológicamente comparables.
- **REQUIRES NEW DATA:** movilidad, capacidad y demanda para estudiar acceso efectivo. Vivienda y ambiente requieren fuentes y contratos propios.

Uso y mejora siguen una política privacy-first: `QueryPatternRecord` conserva intención normalizada, capacidad, éxito/fallo y bucket de latencia, no conversaciones completas. Una frecuencia solo produce `CapabilityGapProposal`; nunca implementa o promueve una capacidad. Promotion requiere cero Critical/High nuevos, goldens, beneficio medido, revisión de latencia/payload/UX, aprobación humana y rollback.

Véase [matrix de tools](TOOL_EVIDENCE_MATRIX.md), [pipeline de datos](../operations/DATA_UPDATE_PIPELINE.md) y [gobierno](../RELEASE_GOVERNANCE.md).
