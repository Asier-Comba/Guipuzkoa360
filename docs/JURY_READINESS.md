# Auditoría cualitativa para jurado · 24/09/2026

No se asigna una nota. Esta rama dependiente de PR #1 contiene un recorrido real de datos y herramienta local. Aún no acredita una ejecución del agente de Work 2 en una versión fija del portal.

| Criterio | Evidencia existente | Evidencia ausente | Riesgo | Acción |
|---|---|---|---|---|
| Utilidad urbana | Pregunta de atención primaria, 88 municipios y comparación real | Validación con técnicos municipales y ficha del portal | Utilidad práctica sin contrastar con usuarios | Revisar con destinatario y completar ficha |
| Análisis y fuentes | 3 fuentes oficiales, periodos, CSV con hash, fila, método y cifra de Donostia cotejada con original | Salida del agente en versión fija | La demo local no acredita al agente | Integrar Work 2 y repetir consultas |
| Funcionamiento y herramientas | Dos ejecuciones reales de herramienta local: 5/88 y 2/88 | Agente que seleccione tool y observe salida | Ser percibido como dashboard | Mostrar llamadas y `output_ref` de la versión fija |
| Claridad | HTML real con mapa GeoJSON de unidades comparadas, barras, tabla y detalle | Revisión visual en el portal y escenario real si se propone | Interpretar el mapa parcial como todo Gipuzkoa | Mantener etiqueta “unidades comparadas” y revisar visualmente |
| Fiabilidad y límites | Cero coincidencias con umbral extremo, validación de nulos, periodos separados, distancia definida | Respuesta del agente a límite metodológico | Sobreinterpretar “acceso” | Probar la pregunta de acceso individual en el portal |

## Ensayo de jurado hostil

| Pregunta | Evidencia necesaria | Disponible ahora | Gap / respuesta antes de entrega |
|---|---|---|---|
| ¿Por qué esa métrica? | Definición y vínculo con decisión municipal | Solo ejemplo de distancia geométrica | Justificar métrica real y alternativas |
| ¿Por qué mezcláis esos años? | Periodo por fuente, compatibilidad y cautela | Demografía 2025-01-01; centros 2026-09-20; límites 2025-05-07; diferencia máxima 627 días | Explicar carácter exploratorio; no afirmar simultaneidad |
| ¿Qué ocurre con municipios pequeños? | Denominadores, recuentos y sensibilidad | Tabla con población de prueba | Añadir cautela por tamaños reales |
| ¿Qué significa exactamente “acceso”? | Nombre y unidad literal de la métrica | Advertencia geométrica | No usar “acceso” como etiqueta si solo hay tasa o distancia |
| ¿Cómo sé que hizo un cálculo nuevo? | Dos trazas con argumentos/resultados distintos | Tool local: 5/88 → 2/88 y refs distintos | Falta demostrarlo con el agente |
| ¿De dónde sale esta cifra? | Fuente original, transformación y cálculo manual | Donostia 183.388 cotejada con CSV original Eustat | Mostrar fila y hash en demo |
| ¿Por qué debería usarlo un ayuntamiento? | Tarea concreta y comparación accionable | Flujo propuesto | Validar caso de uso sin prometer decisión automática |
| ¿Qué ocurre si falta un dato? | Política de nulos y señalización | Ingesta local rechaza fila incompleta antes de emitir resultado | Agente debe explicar la ausencia al usuario |
| ¿Predice el escenario lo que ocurrirá? | Supuestos y diferencia frente a base | Etiquetas visibles | Responder “no”; es un contrafactual condicionado |
| ¿Qué aporta el agente frente al dashboard? | Interpretación de consulta, tool y recálculo | Solo mock de interfaz | Mostrar ejecución real y nuevo artefacto |

Prioridad: 1) agente con trazas reales; 2) prueba en versión fija; 3) revisión visual en portal; 4) ficha y materiales; 5) entrega humana.
