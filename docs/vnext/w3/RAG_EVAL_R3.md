# Evaluación documental independiente R3

**Estado: BLOCKED / NOT_RUN.** W2 declara `RAG_NO_GO`: faltan los textos
oficiales M4/M5 y un corpus documental autorizado, versionado y segmentado.
W3 no asigna preguntas «con evidencia» ni IDs gold a fragmentos que no ha
leído. No se ejecutó retrieval, generación ni revisión humana de respuestas.

El protocolo fijado antes de una ejecución será de **30 preguntas**: 18 con
evidencia, seis que exigen abstención y seis adversarias o con conflicto de
versión. Los IDs, texto exacto de las preguntas, fragmentos gold, versión del
corpus y hash se congelarán **antes** de observar respuestas del candidato.
El conjunto del jurado excluirá formación privada, correos, holdout y datos
personales innecesarios. Sin M4/M5, los 30 enunciados y gold permanecen
pendientes; inventarlos ahora falsearía la procedencia.

Comparadores previstos: (1) fuentes y metodología simple; (2) base navegable;
(3) retrieval vectorial solo si el corpus y la latencia lo justifican.
Registrar por separado recuperación, generación y juicio humano. Las metas
propuestas son 17/18 recuperaciones suficientes, 6/6 abstenciones, 6/6 casos
adversarios seguros, ≥95 % de claims citados sustentados, cero fuentes
inventadas y beneficio frente al baseline simple con coste/latencia aceptables.
Estos números son **gates propuestos**, no resultados ni requisitos oficiales.
Añadir un documento ausente a un sistema no demostraría por sí mismo ventaja
de embeddings.

**Siguiente acción:** obtener M4/M5 y permiso de uso, fijar corpus y fragmentos,
redactar/congelar los 30 casos con gold revisado, y solo después ejecutar los
comparadores. El experimento documental no bloquea el núcleo territorial o
de visitas programadas.
