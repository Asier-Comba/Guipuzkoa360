# Auditoría cualitativa para jurado · 24/09/2026

No se asigna una nota. Esta rama combina datos reales, las tools de Work 2 y producto. Aún no acredita una ejecución del coordinador en una versión fija del portal.

| Criterio | Evidencia existente | Evidencia ausente | Riesgo | Acción |
|---|---|---|---|---|
| Utilidad urbana | Pregunta de atención primaria, 88 municipios y comparación real | Validación con técnicos municipales y ficha del portal | Utilidad práctica sin contrastar con usuarios | Revisar con destinatario y completar ficha |
| Análisis y fuentes | 3 fuentes oficiales, periodos, hashes, fila, método; tools cotejadas con Work 1 y cifra de Donostia cotejada con original | Salida del coordinador en versión fija | Ejemplos directos de tool no acreditan coordinación | Probar en portal y conservar conversación |
| Funcionamiento y herramientas | Dos ejecuciones de `analizar_coincidencia`: 7/88 y 2/88 con refs distintos | Selección de tool por coordinador en portal | Ser percibido como pipeline estático | Enseñar llamada y observación del agente en prueba fija |
| Claridad | HTML real con mapa GeoJSON, barras, tabla, detalle y escenario Beasain | Revisión visual en el portal | Interpretar mapa parcial como todo Gipuzkoa | Mantener etiqueta “unidades comparadas” y revisar visualmente |
| Fiabilidad y límites | Error `municipality_not_found`, validación de nulos, periodos separados, escenario marcado hipotético | Respuesta del coordinador a límite metodológico | Sobreinterpretar “acceso” | Probar pregunta de acceso individual en portal |

## Ensayo de jurado hostil

| Pregunta | Evidencia necesaria | Disponible ahora | Gap / respuesta antes de entrega |
|---|---|---|---|
| ¿Por qué esa métrica? | Definición y vínculo con decisión municipal | Proporción ≥65 y distancia geométrica desde punto representativo, con cuantiles separados | Explicar utilidad exploratoria y alternativas viarias |
| ¿Por qué mezcláis esos años? | Periodo por fuente, compatibilidad y cautela | Demografía 2025-01-01; centros 2026-09-20; límites 2025-05-07; diferencia máxima 627 días | Explicar carácter exploratorio; no afirmar simultaneidad |
| ¿Qué ocurre con municipios pequeños? | Denominadores, recuentos y sensibilidad | Tabla real muestra población y recuentos por municipio | Señalar sensibilidad de porcentajes con denominador pequeño |
| ¿Qué significa exactamente “acceso”? | Nombre y unidad literal de la métrica | Advertencia geométrica | No usar “acceso” como etiqueta si solo hay tasa o distancia |
| ¿Cómo sé que hizo un cálculo nuevo? | Dos trazas con argumentos/resultados distintos | Tool Work 2: cuantil 0,75 → 0,85, 7/88 → 2/88 y refs distintos | Falta demostrar elección/observación por coordinador |
| ¿De dónde sale esta cifra? | Fuente original, transformación y cálculo manual | Donostia 183.388 cotejada con CSV original Eustat | Mostrar fila y hash en demo |
| ¿Por qué debería usarlo un ayuntamiento? | Tarea concreta y comparación accionable | Flujo propuesto | Validar caso de uso sin prometer decisión automática |
| ¿Qué ocurre si falta un dato? | Política de nulos y señalización | Tool devuelve `municipality_not_found`; adaptador rechaza valores ausentes | Coordinador debe explicar la ausencia al usuario |
| ¿Predice el escenario lo que ocurrirá? | Supuestos y diferencia frente a base | Etiquetas visibles | Responder “no”; es un contrafactual condicionado |
| ¿Qué aporta el agente frente al dashboard? | Interpretación de consulta, tool y recálculo | Tools y nuevo artefacto probados sin coordinador | Mostrar ejecución del coordinador en versión fija |

Prioridad: 1) prueba del coordinador en versión fija; 2) revisión visual en portal; 3) ficha y materiales; 4) entrega humana.
