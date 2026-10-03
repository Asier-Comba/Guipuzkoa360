# R24: alcance de la visita completa

Base inmutable: runtime R23 `6e960e873972b06fbd9e5125e7a498eef61c6d3a`.

Único cambio material del paquete: `tools.py`. `main.py`, prompt, diez firmas/orden, 15 assets, datos, proveedor, red, routing, fórmulas, fuentes y v4 permanecen idénticos. El builder valida ZIP/manifiesto base por SHA-256 y añade una proyección, sin reemplazar el motor ni alterar raw.

`journey_scope` separa presencia en parada de origen, punto sanitario intermedio y llegada a parada de regreso. Cada identidad, reloj y segundo se vincula a raw validado, itinerary y time_summary. El inicio distingue explícitamente presencia inicial y salida del autobús. El anchor no es una puerta verificada ni el endpoint del intervalo completo. La frase ambigua del catálogo y del paseo se sustituye solo en la proyección pública, conservando todas las demás limitaciones y cifras.

Si una identidad, scope, reloj, tiempo, entrance o destino de vuelta no concuerda, la frontera existente rechaza la proyección sin claims parciales. Ningún nombre de municipio, hora, cifra del oracle ni patrón de pregunta se codifica en esta delta.

La [documentación oficial de function calling](https://developers.openai.com/api/docs/guides/function-calling) recomienda explicar qué representa el output y usar estructura para evitar estados inválidos. Aquí se aplica al contrato observado, no mediante una promesa sobre la respuesta del modelo. La aceptación conversacional exige una versión real nueva.

Regenerar: `python -m scripts.vnext_agent.build_r24`. Focal: `python -m pytest -q -o addopts= tests/vnext_agent/test_r24_health_scope.py`. Paridad/oracle completo: `python -m scripts.vnext_agent.verify_r24`. Python completo, Node, runtime identity, jury, artifacts, doble build y diff se ejecutan antes de congelar.

Nota de desarrollo: el primer intento focal tuvo seis fallos del verificador en proceso compartido, al importar el proveedor sin el aislamiento que exige el paquete; no seis fallos sanitarios del candidato. Se conserva esta incidencia. El observer específico usa un proceso frío y red denegada, e incluye validaciones de outputs válidos antes de evaluar fault injection. No se cuentan resultados preliminares como aceptación final.

Studio: copiar los bytes generados de main.py/tools.py a una carpeta nueva, conservando los 15 context assets existentes; preparar diez tools, memoria activa e Internet desactivado; versión privada nueva. No modificar R23 ni publicar. El protocolo real queda congelado antes de respuestas; STOP ante cualquier C/H/M material nuevo. Solo tras aceptación real completa se cambia el borrador de Entrega y se revisa presentación/HTML/preview. No R25 automático.
