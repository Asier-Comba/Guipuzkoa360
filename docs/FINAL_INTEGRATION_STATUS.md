# Estado de integración final · 24/09/2026

## Cadena comprobada

`datos_originales/` → pipeline Work 1 + QA (PR #4) → `resultados/metricas_municipales.csv` / runtime → tools deterministas Work 2 → `docs/examples/*.json` → `scripts/adapt_agent_tool_result.mjs` → contrato Work 3 → `scripts/enrich_work1_result.mjs` → `resultados/demo_work2/*/*.html`.

El adaptador comprueba antes de publicar un HTML que los códigos municipales son únicos y existen, que las distancias de Work 2 coinciden con Work 1 a 0,1 m, que los porcentajes coinciden, que las fuentes esperadas están presentes y que el escenario conserva base, diferencia y resultado. El JSON registra hashes SHA-256 de salidas y archivos leídos, `rows_used`, periodos, unidades y `source_id`.

## Evidencia real disponible

| Consulta | Tool | Resultado | Tipo de evidencia |
|---|---:|---:|---|
| Coincidencia cuantil 0,75 | `analizar_coincidencia` | 7 de 88 destacados | Datos y cálculo Work 2; salida original en `docs/examples/coincidence_primary_care_65.json` |
| Coincidencia cuantil 0,85 | `analizar_coincidencia` | 2 de 88 destacados | Nueva ejecución con argumento distinto; `docs/examples/coincidence_primary_care_65_q85.json` |
| Comparación Tolosa/Beasain/Azpeitia | `comparar_municipios` | 3 filas verificadas | Códigos, recuentos, porcentajes y distancia |
| Alta hipotética de centro en punto de Beasain | `simular_escenario` | 1 de 88 cambia; Beasain 3.617,3 m → 0 m | Contrafactual explícito, no predicción |
| Municipio inexistente | `obtener_resumen_territorial` | `municipality_not_found` | Error controlado, sin cifra fabricada |
| Contraste independiente | Work 1 | Donostia / San Sebastián: 183.388 habitantes | Coincide con fila original Eustat y preparado; prueba E2E |

Los archivos principales `resultados/demo.html`, `informe_principal.html` y `scenario_comparison.html` son reales y autocontenidos. La entrada recomendada es `resultados/demo_work2/index.html`. El fixture sintético permanece en `tests/fixtures/` y puede renderizarse en `resultados/dev_sintetico/`, sin mezclarse con la demo real.

## Pendiente para afirmar “agente end-to-end en portal”

1. Subir el paquete de Work 2 al workspace del portal sin sobrescribir cambios de otros integrantes; crear versión privada fija.
2. Ejecutar las consultas de `docs/README_DEMO_JURADO.md` en Pruebas y conservar una traza en la que el coordinador elige la tool, observa su resultado y responde.
3. Capturar esa traza en el envelope de `docs/WORK2_AGENT_ENVELOPE.md`, regenerar el HTML como `execution_mode=agent` y comprobar una cifra.
4. Revisar visualmente el HTML en el entorno real del portal y la vista previa de entrega. Esta revisión aún no se ha realizado.
5. Completar ficha, seleccionar versión y track; la publicación final requiere autorización humana expresa.

## Riesgos que pueden costar puntos

- **Funcionamiento (25 %):** las tools sí funcionan, pero los ejemplos actuales se ejecutaron directamente. La selección de herramientas por el coordinador no se ha probado en el portal.
- **Semántica:** `analizar_coincidencia` selecciona por doble cuantil. `threshold_km` solo determina `within_threshold`, no el conjunto `highlighted`; variar ese umbral no demuestra un cambio del ranking. La demo varía el cuantil 0,75→0,85.
- **Territorio:** el mapa de cada HTML muestra solo las unidades comparadas (2–5), no los 88 polígonos. El recuento 7/88 o 2/88 sí usa todas las filas.
- **Interpretación:** distancia euclídea desde punto representativo municipal; no mide recorrido, capacidad, cita, accesibilidad universal ni acceso individual.
- **Temporalidad:** demografía 2025-01-01, geometría 2025-05-07, centros 2026-09-20; separación máxima 627 días.
- **Escenario:** el punto hipotético de Beasain coincide con el punto usado para el cálculo y da distancia 0 m allí; no demuestra una ubicación óptima ni efecto social.
