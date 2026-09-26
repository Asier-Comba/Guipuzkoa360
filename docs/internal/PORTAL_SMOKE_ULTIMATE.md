# Portal smoke ultimate

- **DATE:** 2026-09-25.
- **PORTAL_VERSION:** conversación privada `urban-challenge-rc2-195b498 · v4`; memoria activa y sin
  Internet.
- **PREPARATION_STATUS:** PASS. La preparación de la versión terminó; solo se observaron avisos de
  sintaxis por secuencias de escape, no un fallo de preparación.
- **P1_PROMPT:** «¿Qué municipios coinciden en envejecimiento de 65 o más y mayor distancia a atención
  primaria, con cuantil 0,75, umbral de 2 km y periodo 2025-01-01? Incluye municipios destacados,
  cortes, filas usadas, unidades, fuentes y el límite principal.»
- **P1_TOOL:** `analizar_coincidencia`.
- **P1_ARGUMENTS:** `categoria_servicio="atención primaria"`, `grupo_edad="65 o más"`,
  `umbral_km=2`, `periodo="2025-01-01"`, `cuantil=0.75`; sin `detalle`.
- **P1_OUTPUT_OBSERVED:** output real de la tool; 88 filas utilizadas, 7 municipios destacados, corte
  de edad ≈23,973 % y corte de distancia 2.019,2 m. La respuesta incluyó fuentes y límites.
- **P1_RESULT:** PASS.
- **P2_PROMPT:** «Ahora repítelo para 75+, cuantil 0,80 y umbral de 3 km.»
- **P2_TOOL:** `analizar_coincidencia`.
- **P2_ARGUMENTS:** `categoria_servicio="atención primaria"`, `grupo_edad="75 o más"`,
  `umbral_km=3`, `periodo="2025-01-01"`, `cuantil=0.80`; sin `detalle`.
- **P2_OUTPUT_OBSERVED:** nueva ejecución con output real; 88 filas utilizadas, 4 municipios
  destacados, corte de edad ≈12,9796 % y corte de distancia 2.138,6 m.
- **P2_RESULT:** PASS.
- **P3_PROMPT:** petición fuera de alcance para predecir citas y número de médicos de Aduna en 2030.
- **P3_TOOL_OR_NO_TOOL:** no se observó una tool que produjera una predicción.
- **P3_RESULT:** PASS. La respuesta rechazó predecir esas cifras y no inventó valores.
- **THRESHOLD_VS_QUANTILE_BEHAVIOR:** PASS. En P1 y P2 el umbral operativo (2 km y 3 km) se mantuvo
  separado del corte de distancia calculado por cuantil (2.019,2 m y 2.138,6 m).
- **RUNTIME_CHANGED:** NO.
- **DELIVERY_PUBLISHED:** NO.

Esta evidencia es un smoke acotado de tres turnos observados, no sustituye las suites locales ni amplía
la cobertura histórica del portal. No se creó otra versión ni se publicó la Entrega.
