# Revisión portable del paquete R2 de W2

El verificador `scripts/vnext_product/package_review.py` comprobó un ZIP
reconstruido desde W2 `f4615b36d0af93966e6ca0f2044288841e6574b8`.
Con CPython 3.12, la huella del ZIP coincidió exactamente con la publicada
por W2: `1992cc739e8e89cd4512ad45919d1ebc102a6385628f82689a23de49de6f2661`.
El informe legible por máquina está en
[`r4_package_review.json`](../../../resultados/vnext/r4_package_review.json).

El resultado `PASS_STATIC_INTEGRITY_ONLY` cubre 13 miembros, sus hashes, bytes
fuente capturados, límites de tamaño, rutas seguras, ausencia de nombres de
fixture/holdout y comprobación estática de imports declarados. Se extrajo en
un directorio temporal y se importaron `main` y `tools` con Python 3.12.
No se hizo ninguna invocación de modelo ni portal. Los patrones de secretos
son heurísticos; un hash concordante no prueba autoría ni ejecución futura.

El primer intento de ensamblado declaró solo `studio` y falló por el import
de `langchain`; al revisar el código se declaró esa dependencia también. Un
rebuild con Python 3.14 cambió la huella del ZIP. Ambos hechos hacen que el
intérprete y las dependencias formen parte de la identidad de generación.

Esta revisión **no** incluye W1 en el ZIP ni convierte el baseline R2 en un
producto sanitario. La aceptación sigue bloqueada por la sustitución de
municipio y el linaje incompleto de indicadores reproducidos en
[`c_r3_report.json`](../../../resultados/vnext/r4_independent/c_r3_report.json).
