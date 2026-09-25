# Validación de GIPUZKOA 360

Fecha de síntesis: 25/09/2026. Las cifras siguientes proceden de la evidencia publicada por Asier; no se han vuelto a ejecutar los benchmarks durante este rescate.

## Cobertura

**88 municipios**, **148 registros sanitarios** y **7 herramientas**. Fuentes: Eustat (población, 2025-01-01), geoEuskadi (geometría, 2025-05-07) y Open Data Euskadi (centros, 2026-09-20). Son snapshots de fechas distintas, no una fotografía temporal homogénea. [Fuentes](../FUENTES.md).

## Evidencia técnica

| Comprobación | Resultado |
|---|---:|
| Benchmark funcional y de propiedades | 72.673 / 72.673 checks |
| Defectos Critical / High del benchmark | 0 / 0 |
| Outputs numéricos con trazabilidad | 31.545 / 31.545 |
| Inyecciones de fallo controladas | 20 / 20 |
| Soak | 1.000 llamadas; 0 drift |
| Suite Python del gate de Asier | 148 / 148 |
| Integración Node | 17 / 17 |

Fuentes verificadas en Git:
[benchmark de Asier](https://github.com/Asier-Comba/Guipuzkoa360/blob/a1b0ecb/docs/BENCHMARKS.md) y
[gate de release](https://github.com/Asier-Comba/Guipuzkoa360/blob/70c0e06/docs/FINAL_RELEASE_GATE.md).

Un check es una evaluación sujeto × propiedad; no una conversación independiente.
La trazabilidad exige periodo, unidad, método y fuentes resolubles para outputs analíticos numéricos.
Los 148 tests pertenecen a la rama del gate, que incluye dos pruebas adicionales; la ejecución anterior de Oier tenía 146. No se suman ambos totales.

La auditoría previa de datos comprobó 41 controles QA y 18 tests de datos. Los casos A–H son aceptación determinista local, no prueba por sí solos del razonamiento del modelo. Los cuatro contrastes fijos de fuente tampoco son cuatro conversaciones de portal.

## Portal

**PORTAL GO histórico** asociado al runtime
`195b4980fa5998b096c308296a55e452380b0371` y la versión privada
`urban-challenge-rc2-195b498 · v4`.

Debe distinguirse el registro histórico de una nueva validación: el gate actual informa de runner ocupado y de un smoke que seleccionó la herramienta sin llegar a producir output. No se declara ese intento PASS ni se publica la entrega.

La revisión anterior de Oier también observó pruebas repartidas entre versiones previas y una regresión de escenario en v4. Asier debe conservar la versión exacta de cada traza, no atribuir todas las conversaciones al SHA final por el nombre mostrado del agente.

## Packaging: WARN en investigación

**No está demostrada la reproducibilidad del ZIP entre cualquier worktree o representación.**
Asier obtuvo 48.339 bytes y, en otro checkout, 48.338: diferencia de **1 byte**. Diez builds iguales en un entorno acreditan repetibilidad allí, no portabilidad universal. El hash histórico de 48.355 bytes es otra evidencia distinta.

El checkpoint de rescate de Oier contiene además una corrección de la guía incluida en el ZIP: produjo un candidato de 47.900 bytes, sin cambiar código ni contexto. **No adoptarlo como paquete final ni mezclar sus hashes con los de Asier.** Deben reconciliarse los miembros, los finales de línea y el procedimiento antes de fijar una identidad única.

## Rendimiento y límites

El benchmark local mide cálculo y serialización; no latencia del portal. El mayor p95 caliente registrado fue 39,184 ms. Las observaciones históricas del portal son de decenas de segundos y no constituyen una garantía.

Existe un WARN de payload: un escenario extremo conserva 88 filas y alcanza 20.155 caracteres. No afirmar que todos los outputs quedan por debajo de 15.000.

Distancia geométrica no es viaje ni accesibilidad real; registros no son capacidad o citas; coincidencia no es causalidad y escenarios no son predicciones. Las tasas de municipios pequeños requieren mirar el denominador. El benchmark no valida impacto social ni elimina la supervisión humana.

**Estado:** evidencia técnica disponible; packaging, smoke actual e integración visual/final deben cerrarse antes de publicar.
