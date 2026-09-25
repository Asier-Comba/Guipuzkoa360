# Validación de GIPUZKOA 360

Esta síntesis distingue cálculo local, presentación visual y conversación privada. Un check de
propiedad no equivale a una conversación ni demuestra impacto social. Datos: 88 municipios y 148
registros sanitarios, con fechas y límites en [Fuentes](../FUENTES.md).

## Evidencia comprobable

La suite de integración ampliada ejecutó **152/152 tests Python**, incluidos los **18 de datos**, y
**17/17 Node**. Se conservan los casos deterministas A–H, los contrastes fijos contra fuente y el control
de las tres listas de coincidencia. Los 41 controles QA son de datos, no 41 conversaciones.

El benchmark original conserva **72.673/72.673 checks**, **31.545/31.545 outputs numéricos trazables**,
**20/20 inyecciones controladas** y **1.000 llamadas sin deriva**. El denominador y la cobertura están
en [Benchmark](BENCHMARKS.md). La ejecución única sobre el candidato final `84e9516` repitió esos
resultados: 72.673/72.673, cero fallos y 1 Medium. Se almacena separadamente en
`analisis/final/`. A–H pasó 8/8, contrastes fijos 4/4 y QA de datos 41/41.

La presentación se compara íntegramente con un recálculo: cada fila, porcentaje, distancia, fuente,
geometría y escenario. El gate rechaza nueve alteraciones deliberadas: números falsos, corte fijo del
25 %, filas omitidas, fuente inventada, escenario alterado y reutilización del grupo de edad anterior.
El navegador confirmó las listas 7/4/2 y 88 contornos, además de la selección mediante teclado.

## Identidad y reproducibilidad

El runtime congelado es `195b4980fa5998b096c308296a55e452380b0371`. Dos archivos Python y diez archivos
de contexto se comparan byte a byte con ese commit. Las siete entradas del manifiesto se contrastan
con tamaños y hashes físicos. El builder no escribe en esos archivos.

La discrepancia histórica del ZIP está demostrada: `requirements.txt` tenía **66 bytes con LF** o
**67 con CRLF**. Reproducir ese único cambio recupera exactamente los ZIP de 48.338 y 48.339 bytes y
sus SHA históricos; todos los otros miembros y metadatos coinciden. Evidencia: `analisis/zip_root_cause.json`.
El nuevo builder valida UTF-8, normaliza CRLF a LF solo dentro del archivo ZIP y fija orden, fecha,
permisos y plataforma ZIP. La prueba independiente de tres worktrees está en
`analisis/cross_worktree_reproducibility.json`. Su alcance es la misma versión de Python/zlib, no toda
implementación de compresión. La identidad del paquete y la del código privado son controles distintos.

## Portal y latencia

Existe evidencia histórica de preparación y conversación para la familia del runtime congelado, con
regresión de escenario observada en `urban-challenge-rc2-195b498 · v4`. Las pruebas anteriores se
repartieron entre versiones; no se atribuyen todas a v4 por compartir el nombre del agente.
El smoke actual y sus intentos están registrados en [gate final](FINAL_RELEASE_GATE.md).

Los tiempos locales miden motor y serialización. Los históricos de portal incluyen inferencia y
sandbox: normalmente 26–47 segundos, con una respuesta que terminó después del output inicial.
No constituyen garantía de latencia. El [guion](DEMO.md) incluye recuperación por runner ocupado.

## Riesgo de salida extensa

El escenario extremo 1→10 km devuelve **20.155 caracteres** porque conserva **66 filas afectadas de 88 analizadas**.
El escenario de Aduna devuelve **2 filas y 3.581 caracteres** y tiene evidencia privada histórica, pero eso no demuestra que el extremo
funcione en el portal. Se acepta preservar la evidencia municipal y se mantiene **1 Medium abierto**
por incertidumbre operativa de ese extremo. No se recorta el runtime para ocultarlo.

No hay capacidad, citas, tiempos de viaje ni inferencia causal en los datos. Los municipios pequeños
requieren interpretar denominadores. Las hipótesis no son predicciones y toda decisión requiere revisión
humana. La validación técnica tampoco autoriza la publicación de una entrega.
