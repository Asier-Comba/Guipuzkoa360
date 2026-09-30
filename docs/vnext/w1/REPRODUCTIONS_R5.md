# Evidencia de errores y controles R5

## Fallo real reproducido y corregido

CI Ubuntu 36630418307, código f8dc08a: 457 PASS, 1 FAIL (`test_source_conflict_and_snapshot_rebuild`). El XML público histórico es texto Git: el checkout Windows usaba CRLF y Linux LF. El constructor obtenía hashes de red distintos, con la misma geometría. Windows pasó. No era una avería de rutas ni una fuente sanitaria desaparecida.

Corrección en fa95fbf: canonicalización de finales de línea para el derivado R5 y su fingerprint. Sin modificar la adquisición OSM ni los archivos R4. Nueva regresión CRLF/LF; la reconstrucción exige nuevamente igualdad exacta de bytes, **no se relajó a una tolerancia**. El HTML oficial descargado se fija como binario con atributos locales para preservar sus bytes. CI Linux posterior 36630925794 PASS; estado final de ambas plataformas se registra en PR15.

## Controles negativos dirigidos

Rechazados: conector 100,1 m; fuentes/hash alterados; segundos walking corruptos; NaN/infinitos en métricas/coordenadas; entrada fingida; conflicto de dirección eliminado; perfil por edad inexistente; datos fuera de cobertura; JSON anidado con propiedades desconocidas; paradas desconectadas. Conector 100 m admitido. Empty graph/bbox externo no devuelve una ruta ficticia. La parada 7214 real permanece desconectada. Retorno un segundo antes del instante mínimo se rechaza; slack cero se admite; el siguiente bus sustituye al perdido.

Desempates no dependen del orden de entrada: mismo total → menos metros de paseo → horarios → trip_id/stop_id. Matriz 135 contra lectura CSV independiente usando extremos factibles, no el mismo selector. Geometría recalculada con separación angular atan2 independiente de la fórmula haversine del builder. Dijkstra contrastado con Floyd–Warshall en fixture; eliminación de tramo crítico rompe conectividad.

Los controles negativos fueron ejecutados sobre el candidato; no se afirma que cada uno tuviera una fase RED previa ni se presentan fixtures como fallos reales. La única regresión nueva observada en remoto fue la identidad de red según salto de línea.

## Preservación y denominadores

459 tests Python totales (195 movilidad: 135 previos +60 R5). La matriz contiene 135 escenarios, incluidos dentro de una prueba del total y además emitidos como evidencia detallada: **no se suman como otros 135 tests unitarios**. Node 17. Se compararon 135 resultados R4 serializados entre el dispatcher y el proveedor original: idénticos; los diez archivos del paquete R4 conservan hashes. v4 conserva 14/14 identidades.

No hay ejecuciones de LLM/portal, aceptación W3 ni implementación W2 en esta ronda. Los hallazgos W3 sobre W2 CRITICAL (binding de municipio), HIGH (fuente del numerador) y MEDIUM (unidad municipal) no se atribuyen al proveedor de movilidad ni se declaran corregidos.
