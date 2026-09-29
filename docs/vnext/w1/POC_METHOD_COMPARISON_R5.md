# Contraste histórico, sin heredar resultados

Se ha reconstruido el método sobre otra adquisición OSM. No se ha reproducido exactamente el archivo histórico: su hash aparece en la transcripción privada, pero sus bytes no están disponibles.

El GTFS sí es idéntico por SHA-256. El perfil de paseo conserva 50 m/min y 120 s por enlace completo y sentido; cada conector debe medir como máximo 100 m. Se usan metros crudos antes del redondeo temporal. La selección por mínimo intervalo se contrasta mediante una selección independiente de la salida más tardía y llegada de regreso más temprana. Para una cita fija, los dos conjuntos factibles son independientes: minimizar `regreso - salida + margen` equivale a esos extremos. Los desempates por metros, horarios e IDs no alteran ese mínimo.

Diferencias importantes: R5 conserva los orígenes R4 (Idiazabal 7903/7906; la PoC utilizaba 7900). La parada 7200 queda fuera del bbox R4 y no se usa. La 7214 sigue desconectada; las tres paradas utilizables son 7215, 7218 y 7219. Se soportan restricciones peatonales de sentido, aunque no aparecen en esta adquisición. La dirección de vehículos no restringe por sí sola el paseo.

El cálculo nuevo desde Zegama da 10.691 s para 09:30/20 min y 8.591 s para 09:45/20 min: diferencia observada de 2.100 s. No se codificó ese valor ni se usó como expected. Con 40 minutos, son 10.691 y 10.372 s: diferencia de 319 s. Las 135 combinaciones y sus filas CSV están en HEALTH_MATRIX_R5.json; también se registran diferencias nulas y cambios de ida/vuelta, no solo casos vistosos.

La matriz produce 135 resultados viables en el alcance acotado. Eso no prueba viabilidad de cualquier hora: las pruebas dirigidas incluyen vuelta perdida, regreso posterior y ausencia de pareja. Tampoco son citas disponibles, recomendaciones clínicas ni ahorros medidos.

Clasificaciones y hashes por componente en POC_METHOD_COMPARISON_R5.json.
