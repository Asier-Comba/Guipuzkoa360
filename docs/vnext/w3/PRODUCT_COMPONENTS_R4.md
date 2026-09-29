# Puente de producto para W1 0.2.0

W1 publicó `725a7b73ae0381092cd80edc41b8a25432d75fcd` con contrato
0.2.0. `review_w1_r4.py` lo ejecutó desde un archive aislado, verificó bytes
de provider y snapshot y repitió C-R3-05–08: cuatro propiedades offline PASS.
El resultado real fijado de Zegama 09:30 es **8591 s** desde presencia en
parada hasta llegada a parada de retorno, con holgura de vuelta **1610 s**
informada por el proveedor. No equivale a tiempo puerta a puerta ni acredita
entrada al ambulatorio. El destino sanitario de W1 está bloqueado por falta de
un enlace peatonal verificado.

`w1_r4_viewmodel.py` prepara los datos para una futura vista: secuencia de
ocho intervalos con base y derivación, ida/vuelta, holgura de regreso,
desglose, fuente y estados no viables. Comprueba continuidad, suma contra
`total_s` y presencia de `source_id`. Conserva nulos en estados sin viaje y
rechaza intervalos incoherentes. No ejecuta rutas ni modifica los tiempos.
La proyección reproducible está en
[`w1_r4_product_components.json`](../../../resultados/vnext/r4_independent/w1_r4_product_components.json).

El HTML público existente y su importador siguen rotulados y fijados a W1
0.1.0. Una entrada 0.2.0 **no** se aceptará silenciosamente ahí. El adapter
W2 de PR #17 sigue en 0.1.0; conectar la UI 0.2.0 a W2 requiere una revisión
contractual de W2 y resolver sus fallos críticos/altos de procedencia. Ni el
ZIP R2 de W2 ni este componente suponen `PRODUCT_HEALTH_GO`.
