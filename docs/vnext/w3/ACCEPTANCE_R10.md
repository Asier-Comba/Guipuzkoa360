# Aceptación independiente R10: paquete y producto

Fecha: 30/09/2026. Son ejecuciones **OFFLINE_TOOL**, no conversaciones.

## W2: tres defectos raíz corregidos

W2 `8272988566f5bca2d65d3119732bf831d11382dc`; ZIP
`366cdc7d160ee6743cb125c6709f57e48f6ddfb91ead812a92eb881570233357`.
Extracción limpia del paquete publicado, 30 miembros revisados por SHA.

- C-R3-01: sustitución Aduna→Tolosa rechazada; cero claims públicos.
- C-R3-02/04/09: Aduna no expone tasas sin numerador en `public_result`;
  Tolosa conserva sus ocho tasas atribuidas. No se cerró todo indiscriminadamente.
- C-R3-03: 7 municipios, unidad correcta.

Cinco casos verifican **tres raíces**. Evidencia completa:
`resultados/vnext/r10/w2_retest_evidence.json`; reporte y hashes adyacentes.
El ZIP es territorial/W1 **0.2.0**, no sanitario 0.3.1.
Dos tests fuente incluidos requieren módulos del repositorio no incluidos;
no se presentan como tests ejecutables dentro de ese ZIP. Runtime probado sí ejecuta.

Reproducir desde W3:

```powershell
python -m scripts.vnext_product.retest_w2_r10 --package <ZIP-publicado> --manifest <manifest-publicado> --output-dir resultados/vnext/r10
```

## W1: aceptación sanitaria condicionada

Runtime `cb061a97e78d6b5c967104fef6b935132fdc450f`, `provider_r6`, 0.3.1.
ZIP `c66d44af702eb3410fcea05ae8711f537214f675e83a7fda38c39c3b39a1b910`;
reconstrucción idéntica del empaquetador publicado en una copia aislada.
No se recompuso W1+W2. 26 miembros revisados; ocho solicitudes, cinco estados.
Schemas de resultado, comparación y catálogo validados con jsonschema en entorno aislado.

Contraste propio, sin oracle/helper de aceptación de W1: filas del GTFS original
por trip/stop/sequence, horas, pickup/dropoff; longitudes de geometría fijada con
haversine independiente; fórmula publicada del paseo; intervalos, total y holgura.
No prueba optimalidad exhaustiva ni reconstruye toda la red peatonal desde XML.

09:30 = 10.691 s; 09:45 = 8.591 s; diferencia = **−2.100 s / −35 min**.
Escenario condicionado por paradas, fecha, horario y paseo modelado. No ahorro
real observado o garantizado. Evidencia: `health_review.json`, `health_evidence.json`.

```powershell
uv run --no-project --python 3.12 --with jsonschema -m scripts.vnext_product.review_health_r10 --w1-root <copia-6ebf41e> --package <ZIP-W1-R6> --output-dir resultados/vnext/r10
python -m scripts.vnext_product.audit_support_r10 --w1-root <copia-6e284af> --support-pin 6e284aff347cfcf5fbb3d7eb9cb89a227b83e0d5 --output resultados/vnext/r10/support_review.json
python -m scripts.vnext_product.build_health_visual
```

Support R10: 9 entradas disponibles / 25 descritas; 11 UNAVAILABLE y 5 OUT_OF_SCOPE
excluidas. Son entradas de answerability, no herramientas. Referencias comprobadas
por bytes/SHA. `status_error_semantics_ref` corrige causas de unknown. **Medium**:
la tabla inline heredada `status_semantics[unknown]` todavía dice fecha no validada;
consumir mapping externo por status+error.code. W3 evita esa generalización.
Medium W1 R7: DAG explicativo externo, finding de procedencia DERIVED permanece.
No invalidan por sí mismos el contraste numérico; no son incidentes LLM observados.

## Producto explícito

`resultados/vnext/health.html` autocontenido; versión 0.3.1 separada del producto
0.1/0.2. Timeline, etiquetas de paradas, total, holgura, fuentes/periodos, parámetros,
comparabilidad y límites. JavaScript presenta intervalos y valida coherencia;
no calcula rutas. Null permanece «No disponible»/«No fijado».

Importación `W3-HEALTH-QUERY-1`, paquete/provider pin, schema de resultado y binding
semántico; 256 KiB, duplicados/profundidad/tipos/URLs/defaults/fuentes rechazados.
Las cifras importadas son compatibles, **no autenticadas**. Un hash copiado no
prueba procedencia ni verdad. Comparación guardada se oculta al importar.
No se copiaron páginas completas HEALTH_PAGE ni PADI; solo metadata pública y
resultados del productor. No se cambió v4, W1, W2 ni portal.
