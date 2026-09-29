# W3 R2 · comparación de alcance publicada, no benchmark competitivo

**OFFICIAL (MIT):** [CityScope](https://www.media.mit.edu/projects/cityscope/overview/)
se describe como familia de plataformas tangibles y digitales para diseño y
planificación urbana, con simulación, análisis y colaboración. La
[documentación de CityScopeJS](https://cityscope.media.mit.edu/cityscopejs/Introduction/)
declara una interfaz web y módulos de tráfico, simulación basada en agentes,
ruido, aguas pluviales y acceso. La
[arquitectura publicada](https://cityscope.media.mit.edu/intro/system/) menciona
módulos de movilidad y cityIO.

**VERIFIED_LIVE (W3):** se leyeron esas tres páginas oficiales el 29/09/2026.
No se ejecutó una instancia de CityScope ni se midió una tarea pareada. La
existencia de esos módulos en la documentación no prueba que todos estén
disponibles en cada despliegue.

**VERIFIED_LOCAL (GIPUZKOA 360):** el prototipo offline W1 fijado en
`c68eb5c55dec72a267b7435b4c364049f6eab408` calcula viabilidad directa
programada entre paradas catalogadas del GO01 para la fecha validada
29/09/2026. Cinco outputs guardados están en
`resultados/vnext/provider_evidence.json`. No se ha observado todavía una
conversación del candidato vNext en el portal.

**PROPOSAL:** comparar tareas concretas con ambas plataformas solo si se
consigue una instancia CityScope con datos y funciones equivalentes, idéntico
caso de uso, fuentes y método de medición. Hasta entonces no se afirma
superioridad, ausencia de una función de CityScope ni mejora de vNext frente
a v4. El feedback literal atribuido a Iván no estaba en el paquete montado;
no se reconstruye por memoria.
