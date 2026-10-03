# Inclusión del límite y de la distancia cero

Base congelada: R22 `202352adc10e90a4b98125387af8e0ff7a438073`.
Corrección única: el parámetro del umbral es positivo; la distancia observada puede ser cero.

El cálculo existente se conserva: distancia disponible y `distance <= threshold_km * 1000`.
La vista pública añade operador inclusivo, umbral real en km/m, inclusión del cero, exclusión de distancia ausente y significado humano. Conserva las clasificaciones booleanas observadas.

Verificación cerrada: nuevo resultado determinista con el mismo digest que la observación pública, filtro igual al argumento recibido, distancia/identidad/clasificación iguales a la función original usando distancia sin redondear. Si falla, cero afirmaciones públicas. La segunda ejecución es local, no una nueva llamada del modelo ni acceso a Internet.

Solo cambian main.py (dos descripciones) y tools.py (sufijo verificador). Los otros 23 miembros, los 15 assets, W1 y v4 permanecen idénticos. No cambian el prompt, firmas, datos ni fórmulas.

La guía oficial de [function calling](https://developers.openai.com/api/docs/guides/function-calling) recomienda expresar el contrato y trasladar verificaciones al código: por eso la regla figura en una estructura verificada, no solo en instrucciones al modelo.

El protocolo real está congelado en outputs/r23/real-protocol.json. Las pruebas locales no acreditan respuestas reales del modelo. R22 conserva su HIGH histórico; el R23 no se declara verde hasta observar sus propios resultados.

Registro de desarrollo: el primer pase focal dio 12/14 porque el nuevo verificador buscaba el digest en el nivel superior de la vista pública, donde se oculta. Se corrigió para contrastar los digests de las identidades observadas conservadas; el siguiente pase focal dio 14/14. No se trasladan esos resultados preliminares al candidato congelado.
