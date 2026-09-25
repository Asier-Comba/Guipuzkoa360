# Evolución medida, propuestas y shadow

OBSERVE → MEASURE → PROPOSE → SHADOW TEST → BENCHMARK → HUMAN APPROVAL → PROMOTE.

No self-modifying production, self-deploy ni conexión de Internet a un CSV estable. `ImprovementProposal` admite ALIAS, DATA, METRIC, PROMPT, PERFORMANCE o UX y contiene evidence, frequency, expected_benefit, risk, required_tests y rollback. Una propuesta no es una capacidad habilitada.

## Privacidad primero

`QueryPatternRecord`: normalized_intent, capability, success, failure_category, latency_bucket, missing_capability. No conservar pregunta literal, respuesta completa, nombres de personas, identificadores de sesión, correo o ubicación del usuario. Normalizar intención a vocabulario cerrado, agregar counts y aplicar retención mínima aprobada; no existe colector de telemetría desplegado. Los casos guardados de evaluación son sintéticos/territoriales públicos, no conversaciones de usuarios.

`capability_gaps` solo cuenta mobility/capacity/demand/housing/environment y emite CapabilityGapProposal si alcanza una frecuencia configurada (ejemplo 3). No significa demanda representativa ni crea la métrica. Cualquier texto libre queda fuera de ese resultado. Un posible piloto necesitaría consentimiento/política de retención, acceso restringido y umbrales que reduzcan singularización.

## Escalera de capacidad

| Etapa | Estado real | Evidencia / condición |
|---|---|---|
| 1. Detección de diferencias territoriales | LIVE TODAY en core; portal histórico y smoke actual separado | 88 municipios, demografía y proximidad geométrica; no «necesidad asistencial» |
| 2. Saturación de cobertura geométrica | SUPPORTED OFFLINE | Matriz de umbrales; fracción de puntos representativos dentro de distancia, no población cubierta |
| 3. Efecto geométrico marginal | PROTOTYPE sobre escenarios existentes | Agregación offline de add_service, sin nueva fórmula territorial |
| 4. GEOMETRIC SERVICE-REMOVAL SENSITIVITY | PROTOTYPE sobre remove_service existente | Cambios de distancia tras retirar un registro, no resiliencia sanitaria |
| 5. Monitorización longitudinal | REQUIRES DATA | Al menos dos snapshots comparables, cambios de esquema/geometría/periodo controlados |
| Movilidad, capacidad, demanda, vivienda, ambiente | REQUIRES DATA | Fuente oficial reproducible, schema, cobertura, límites, QA y benchmark específicos |
| Equidad y apoyo a planificación | REQUIRES DATA + revisión humana | No deducir necesidades individuales ni localización óptima solo de puntos/distancias |

## Efecto geométrico, denominadores transparentes

`geometric_effect` agrega **las diferencias ya calculadas** por el core de escenarios: municipios con cambio de distancia no nulo; suma de reducción (add) o aumento (remove), mediana entre esos municipios afectados, máximo y transiciones within_threshold. Usa diferencias redondeadas a 0,1 m, municipios equiponderados, no residentes. Los cambios de umbral sin distancia no pertenecen a la mediana; se cuentan aparte como transiciones. Caso sin cambios: count/suma/mediana/máximo 0, definido explícitamente.

No se llama beneficio social, mejora de salud, resiliencia sanitaria ni ubicación óptima. [Ejemplos medidos](../../analisis/next/evaluation.json), campo geometric_examples, conservan el id retirado y los límites. El escenario es hipotético y no altera servicios originales.

## Shadow ejecutado

Mismos 8 casos (7 capacidades y alias) en Executor del core estable y NextSession. Se comparan output canónico, resolución de fuentes, campos de trazabilidad, tiempo medido con reloj monotónico, bytes y bloqueo. Además: un seguimiento, 6 fuera de alcance, 8 goldens y 16 inyecciones. Ver campos shadow/records/attacks/goldens del informe. No hay concurrencia, LLM ni distribución estadística de latencias; inicialización/cachés pueden influir. No anunciar speedup.

EvaluationRecord consume query, plan, tool, tool_output, critic y response; devuelve tool_selection_correct, parameters_correct, numeric_grounding, source_grounding, limitation_present, followup_recalculated, out_of_scope_handled, unsupported_claim. No aplica = null, nunca falso o cero para inflar denominadores. `numeric_grounding` usa igualdad con el mismo core, no prueba independiente; los goldens son constantes separadas de controles versionados. `unsupported_claim` se mide contra la plantilla, no un juez semántico.

Promoción exige: cero Critical/High nuevos; goldens íntegros; beneficio medido en el objetivo; revisión del coste de latencia/payload/UX; aprobación humana y rollback. Resultado presente: prototipo útil para evaluar controles, **no candidato a sustituir v4**. Una solicitud repetida de movilidad solo produce propuesta, nunca implementación automática.
