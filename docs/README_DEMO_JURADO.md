# Demo de jurado · 2–3 minutos

Abrir `resultados/demo_real/index.html`. Los cuatro resultados enlazados usan los datos oficiales preparados por Work 1 y una herramienta **local** reproducible. El agente de Work 2 aún no está integrado: decirlo al presentar esta versión. Cada resultado tiene JSON de entrada/salida, traza, hash del CSV, fuentes, periodos, método, limitaciones y un HTML autocontenido.

## Secuencia exacta

| Tiempo | Acción | Evidencia que se enseña |
|---|---|---|
| 0:00–0:25 | Enunciar: “Buscamos municipios que combinan alta proporción de mayores con mayor distancia geométrica desde un punto representativo municipal hasta atención primaria.” | Unidad de análisis, definición precisa de la distancia y periodos |
| 0:25–1:00 | Abrir **1 · Panorama**. Leer criterios ≥25 % de ≥65 y >2 km. | 5/88; mapa de los cinco municipios, tabla, `source_id` y primer `LOCAL-*` visible en el índice |
| 1:00–1:30 | Abrir **2 · Nuevo umbral** (>2,5 km). | 2/88 y un segundo `LOCAL-*` distinto: argumentos y resultado nuevos de `compare_municipal_services_local` |
| 1:30–2:05 | Abrir **3 · Comparar**, seleccionar Donostia en el mapa y mostrar detalle. | 183.388 habitantes; `municipality_code=20069`; la fila original Eustat y `analisis/verificaciones_manuales.csv` confirman esa cifra |
| 2:05–2:30 | Abrir **4 · Caso límite** (≥90 % de ≥75 y >100 km). | 0/88; las filas de contexto están etiquetadas como no coincidentes. Explicar que un cero de coincidencias no significa ausencia de necesidad |
| 2:30–2:50 | Abrir “Cómo se calculó” y “Limitaciones”. | Demografía 2025-01-01, centros 2026-09-20 y límites 2025-05-07; distancia euclídea desde punto representativo, sin inferir viaje o acceso individual |

Cuando Work 2 esté disponible, repetir las mismas preguntas en la **versión fija del agente del portal**. Enseñar sus llamadas reales a herramientas, los dos `output_ref` distintos, una respuesta de límite y el HTML generado. En ese momento se puede usar el término “agente” para la nueva ejecución. Un selector del HTML o esta herramienta local por sí solos no acreditan esa parte de la rúbrica.

## Reproducción

Desde la raíz del repositorio combinado:

```powershell
node scripts/build_jury_demo.mjs
node --test tests/e2e/*.test.mjs
```

El comando reconstruye los cuatro JSON, añade geometría desde `datos_preparados/runtime_municipios.geojson` y genera los HTML. Para una consulta distinta, ejecutar `scripts/run_local_analysis.mjs` con `--age`, `--share`, `--distance`, `--service` y `--output`, después `scripts/enrich_work1_result.mjs` y `scripts/build_results.mjs`. El paquete de la plataforma puede tener un límite de 24 MB: seleccionar solo los archivos de runtime y el artefacto final necesario.

## Respuesta breve a objeciones

- **¿Acceso real?** No. Es proximidad geométrica aproximada; no incorpora red, horarios, capacidad ni barreras individuales.
- **¿Por qué años distintos?** Son los periodos disponibles documentados; la comparación es exploratoria y la separación máxima es 627 días.
- **¿Por qué no es solo un dashboard?** La versión final deberá mostrar al agente interpretando preguntas, ejecutando tools y recalculando. La demo local actual prueba el cálculo y la interfaz, pero aún no ese paso.
