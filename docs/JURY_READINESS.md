# Auditoría cualitativa para jurado · 24/09/2026

No se asigna una nota. La evidencia actual es una interfaz y contrato con datos sintéticos; aún no acredita un agente real ni conclusiones territoriales.

| Criterio | Evidencia existente | Evidencia ausente | Riesgo | Acción |
|---|---|---|---|---|
| Utilidad urbana | Pregunta y destinatarios propuestos; flujo de comparación | Validación con fuentes y tarea real del usuario | Problema demasiado amplio | Concretar servicio y unidad después de auditar datos |
| Análisis y fuentes | Schema con IDs, periodo, unidad y método; tests de referencias; Work 1 aporta fuentes y cifras contrastadas en PR #1 | Incorporación de Work 1 a `main` y salida del agente rastreable | Conclusión aún no defendible desde esta rama | Integrar PR #1 y enlazar cada cifra del agente |
| Funcionamiento y herramientas | Traza sintética exigida por contrato | Ejecución de versión fija del agente y recalculación ≥75 | Ser percibido como dashboard | Enseñar dos llamadas reales, argumentos y salidas diferentes |
| Claridad | Tres HTML autocontenidos con mapa abstracto, barras, tabla y escenario; adaptador para GeoJSON de Work 1 | Resultado real del agente y prueba en portal | Confusión del mapa de prueba con Gipuzkoa | Generar mapa real tras integrar el agente y verificar etiquetas |
| Fiabilidad y límites | Banner sintético, separación observado/hipotético y advertencias | Respuesta real del agente a pregunta límite y manejo de nulos | Sobreinterpretar “acceso” | Probar límites y ajustar etiqueta a Work 1 |

## Ensayo de jurado hostil

| Pregunta | Evidencia necesaria | Disponible ahora | Gap / respuesta antes de entrega |
|---|---|---|---|
| ¿Por qué esa métrica? | Definición y vínculo con decisión municipal | Solo ejemplo de distancia geométrica | Justificar métrica real y alternativas |
| ¿Por qué mezcláis esos años? | Periodo por fuente, compatibilidad y cautela | Campo de periodo en schema | Auditar años de Work 1 |
| ¿Qué ocurre con municipios pequeños? | Denominadores, recuentos y sensibilidad | Tabla con población de prueba | Añadir cautela por tamaños reales |
| ¿Qué significa exactamente “acceso”? | Nombre y unidad literal de la métrica | Advertencia geométrica | No usar “acceso” como etiqueta si solo hay tasa o distancia |
| ¿Cómo sé que hizo un cálculo nuevo? | Dos trazas con argumentos/resultados distintos | Contrato de traza | Ejecutar versión fija dos veces |
| ¿De dónde sale esta cifra? | Fuente original, transformación y cálculo manual | IDs sintéticos | Añadir fuente real y cotejo |
| ¿Por qué debería usarlo un ayuntamiento? | Tarea concreta y comparación accionable | Flujo propuesto | Validar caso de uso sin prometer decisión automática |
| ¿Qué ocurre si falta un dato? | Política de nulos y señalización | Validador bloquea fila incompleta | Implementar tratamiento real de ausencias |
| ¿Predice el escenario lo que ocurrirá? | Supuestos y diferencia frente a base | Etiquetas visibles | Responder “no”; es un contrafactual condicionado |
| ¿Qué aporta el agente frente al dashboard? | Interpretación de consulta, tool y recálculo | Solo mock de interfaz | Mostrar ejecución real y nuevo artefacto |

Prioridad: 1) datos y definición de métrica; 2) agente con trazas reales; 3) prueba en versión fija; 4) presentación visual final; 5) entrega humana.
