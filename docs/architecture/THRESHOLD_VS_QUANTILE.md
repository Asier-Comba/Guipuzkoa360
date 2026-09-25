# Umbral operativo y cuantil responden a preguntas distintas

**¿Por qué pedimos 2 km si los destacados dependen del cuantil?** El cuantil selecciona extremos relativos de la distribución provincial; 2 km permite además saber si cada punto queda dentro de una referencia geométrica elegida. No son dos nombres para el mismo filtro.

```text
highlighted = age_percent >= age_quantile_cut
              AND distance_m >= distance_quantile_cut
within_threshold = distance_m <= threshold_km * 1000
```

El algoritmo calcula ambos cortes por separado sobre las 88 filas municipales unidas. Los empates se incluyen (`>=`); no se garantiza un número fijo de destacados. Se usa distancia euclídea EPSG:25830 del punto representativo, no rutas, minutos ni cobertura de residentes.

| Caso | Corte edad | Corte distancia | Destacados |
|---|---:|---:|---:|
| 65+, q0,75, 2 km | 23,973 % | 2.019,2 m | 7 |
| 65+, q0,85, 2 km | 25,3557 % | 2.308,7 m | 2 |
| 75+, q0,80, 3 km | 12,9796 % | 2.138,6 m | 4 |

Fuente ejecutable: [jury_coincidence_results](../../analisis/jury_coincidence_results.json), regenerado con `scripts/benchmark/verify_jury_results.py`. El benchmark completo recorre 320 configuraciones. Con grupo/categoría/periodo/cuantil fijos, variar solo threshold no cambia highlighted; sí puede cambiar within_threshold. q0,75→q0,85 reduce 7→2 en esta matriz, no una ley para futuros datasets.

Respuesta para jurado: «Destacamos municipios simultáneamente en la cola superior de ambas distribuciones; mostramos 2 km como referencia adicional. No seleccionamos simplemente todos los que superan 2 km».

No se cambia el runtime congelado. El nuevo smoke de ingeniería encontró esa confusión en el texto de fallback cuando el runner falla: [registro](../operations/PORTAL_SMOKE_ENGINEERING.md). Es un riesgo explícito, no una validación del cálculo.
