# Demo de jurado · 2–3 minutos

Abrir `resultados/demo_work2/index.html`. Los resultados enlazados proceden de las herramientas deterministas de Work 2 ejecutadas directamente contra los datos reales de Work 1. El adaptador comprueba cada distancia y porcentaje frente al CSV preparado antes de producir JSON y HTML. **La prueba privada del coordinador en el portal todavía no ha completado una consulta válida**; detalles en `docs/PORTAL_PRIVATE_TEST_2026-09-24.md`. Las páginas indican que son ejecuciones directas de tools.

## Secuencia exacta

| Tiempo | Acción | Evidencia que se enseña |
|---|---|---|
| 0:00–0:20 | Enunciar: “Cruzamos envejecimiento y distancia geométrica aproximada a atención primaria por municipio.” | Unidad territorial; no es tiempo de viaje ni acceso individual |
| 0:20–0:55 | Abrir **1 · Pregunta principal**, cuantil 0,75. | 7/88 destacados, mapa de cinco, método de doble cuantil, fuente y primera traza `WORK2-TOOL-*` |
| 0:55–1:25 | Abrir **2 · Nuevo cálculo**, cuantil 0,85. | 2/88 y segunda traza distinta; la tool se volvió a ejecutar con otro argumento |
| 1:25–1:55 | Abrir **3 · Comparación** Tolosa, Beasain y Azpeitia. | Códigos, población, proporción de ≥65 y distancia en metros convertida a km; filas y fuentes visibles |
| 1:55–2:25 | Abrir **4 · Escenario** en Beasain. | Base 3.617,3 m → hipótesis 0 m; un municipio cambia; supuestos y etiqueta “ESCENARIO HIPOTÉTICO” |
| 2:25–2:45 | Abrir **5 · Dato ausente**. | `municipality_not_found` y ningún número inventado. Cerrar con periodos y límite metodológico |

Antes de la entrega, repetir las mismas preguntas en la **versión fija del agente del portal**. Enseñar que el coordinador selecciona la tool, observa la salida, responde a la pregunta de límite y entrega el artefacto. Los HTML actuales acreditan las herramientas y la integración, todavía no ese paso del coordinador.

## Reproducción

Desde la raíz del repositorio combinado:

```powershell
python scripts/agent/generate_examples.py
python scripts/generate_work2_variation.py
node scripts/build_work2_demo.mjs
node --test tests/e2e/*.test.mjs
```

Los comandos regeneran las salidas originales de Work 2, la variación de cuantil, el error controlado, los JSON canónicos, contornos y HTML. La demo local anterior sigue en `resultados/demo_real/index.html` como contraste independiente; está marcada “cálculo local”. El paquete de ejecución del portal tiene límite observado de 24 MB; seleccionar solo runtime y materiales necesarios.

## Respuesta breve a objeciones

- **¿Acceso real?** No. Es proximidad geométrica aproximada; no incorpora red, horarios, capacidad ni barreras individuales.
- **¿Por qué años distintos?** Son los periodos disponibles documentados; la comparación es exploratoria y la separación máxima es 627 días.
- **¿Por qué no es solo un dashboard?** Dos ejecuciones de `analizar_coincidencia` con argumentos y salidas distintos prueban recálculo de la tool. La versión fija del portal debe mostrar también la interpretación y selección de tool por el coordinador.
