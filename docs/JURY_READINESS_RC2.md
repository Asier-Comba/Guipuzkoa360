# Preparación de jurado · GIPUZKOA 360 RC2

Fecha: 2026-09-24  
Duración objetivo: 2–3 minutos  
Estado actual: **bloqueado para demo en vivo** hasta superar la puerta G-01…G-06 de `PORTAL_VALIDATION_RC2.md` con una versión privada exacta e inmutable.

## Qué se puede afirmar hoy

- Los datos son reales y trazables: Eustat, geoEuskadi y Open Data Euskadi.
- La suite del candidato Git `e13c3e58d22d8f01d07c27d571711b3a6d0a4a4d` pasa 128/128 tests.
- Las matemáticas, aliases, errores controlados, siete wrappers y contratos compacto/completo están verificados localmente.
- El RC1 exacto no supera la prueba privada del portal: 1/5 cadenas completas.
- El RC2 todavía no tiene evidencia de portal asociada al commit exacto. No debe presentarse como validado hasta fijar y probar esa versión.

## Guion recomendado, condicionado a la puerta RC2

### 0:00–0:20 · Problema y alcance

> “GIPUZKOA 360 ayuda a detectar coincidencias territoriales entre envejecimiento y distancia geométrica a servicios sanitarios registrados. No mide tiempos de viaje, capacidad ni causalidad. Cada cifra conserva periodo, unidad, fuente y método.”

Mostrar la versión inmutable RC2 en Pruebas, con memoria activa y sin Internet. No abrir el RC1 histórico.

### 0:20–0:55 · Pregunta principal y tool real

Prompt exacto:

> ¿Qué municipios coinciden en envejecimiento de 65 o más y mayor distancia a atención primaria, con cuantil 0,75, umbral de 2 km y periodo 2025-01-01? Incluye municipios destacados, cortes, filas usadas, unidades, fuentes y límites.

Evidencia que debe quedar visible:

- tool `analizar_coincidencia`;
- `categoria_servicio` normalizada a `primary_care`;
- `grupo_edad=65`, `cuantil=0.75`, `umbral_km=2`, `periodo=2025-01-01`;
- 88 filas unidas;
- cortes 23,9730% y 2.019,2 m;
- 7 municipios: Legazpi, Ezkio-Itsaso, Hondarribia, Hernialde, Oñati, Idiazabal y Errenteria.

### 0:55–1:20 · Recalcular, no recitar

Seguimiento exacto:

> Repítelo para 75+, cuantil 0,80 y umbral de 3 km. Mantén el periodo y explícame qué cambió.

La evidencia debe mostrar una nueva llamada y argumentos nuevos. Resultado esperado:

- cortes 12,9796% y 2.138,6 m;
- 4 municipios: Legazpi, Errenteria, Hondarribia e Idiazabal;
- explicación de que cambiaron grupo de edad, cuantil y umbral.

### 1:20–1:50 · Comparación territorial verificable

Prompt exacto:

> Compara Eibar y Tolosa para población de 75 o más y atención primaria, con umbral de 2 km y periodo 2025-01-01. Separa porcentajes y distancias y cita los periodos de cada fuente.

Control directo:

- Eibar: 13,744% y 1.223,6 m.
- Tolosa: 12,131% y 1.080,5 m.
- demografía 2025-01-01, geografía 2025-05-07 y servicios 2026-09-20.

Decir en voz alta que los periodos son heterogéneos y que los metros son distancia euclídea desde un punto representativo.

### 1:50–2:20 · Caso límite y ausencia bien explicada

Prompt exacto:

> ¿Tiene Aduna atención primaria registrada dentro del municipio y cuál es la distancia al registro más cercano? No confundas ausencia de registros internos con ausencia de atención.

Resultado esperado:

- 0 registros municipales de atención primaria;
- 2.756,2 m al registro más cercano;
- frase explícita: “0 registros dentro del municipio no significa que la población no tenga atención sanitaria”.

### 2:20–2:50 · Escenario, no predicción

Prompt exacto:

> ESCENARIO HIPOTÉTICO: añade un punto de atención primaria en el punto representativo de Aduna, latitud 43.2134915 y longitud -2.0593393. Compara base y escenario y explica qué no demuestra.

Resultado esperado:

- base 2.756,2 m;
- escenario 0,0 m;
- diferencia −2.756,2 m;
- no afirma coste, demanda, capacidad, uso ni ubicación recomendable.

### 2:50–3:00 · Cierre

> “La aportación no es solo el mapa: es una cadena auditable. La pregunta selecciona una tool, la tool calcula sobre datos físicos, la respuesta usa esa salida y el jurado puede revisar argumentos, filas, fuentes y límites.”

## Qué interfaz mostrar

1. **Agente real del portal:** usar para la interacción principal y abrir al menos una salida cruda de tool.
2. **Resultado offline reproducible:** usar como respaldo de verificación, identificado como cálculo determinista local; no llamarlo ejecución del agente.
3. **HTML o visualización:** usar para lectura territorial, identificado como representación de resultados ya calculados; no presentarlo como prueba de que el modelo llamó una tool.

Una captura o HTML no sustituye el historial visible de prompt, tool, argumentos, salida y respuesta.

## Plan de contingencia

Si el runner responde ocupado una vez, esperar a que termine y repetir en una conversación nueva. Si una llamada supera 60 segundos o falta la salida de tool:

1. detener la ejecución;
2. no continuar una secuencia larga;
3. mostrar el resultado offline con su etiqueta correcta;
4. explicar que la matemática está validada localmente y que la evidencia de orquestación del portal no pasó esa ejecución;
5. evitar cualquier afirmación de “agente validado end-to-end”.

No cambiar a RC1: RC1 ya falló aliases y bloqueó una llamada canónica.

## Objeciones previsibles

### “¿Esto demuestra que hay peor acceso sanitario?”

No. Demuestra distancia geométrica desde un punto representativo a un registro de servicio y permite detectar coincidencias territoriales. No incluye red viaria, transporte, horarios, capacidad, citas, calidad ni accesibilidad universal.

### “¿Por qué mezcláis datos de años distintos?”

La demografía está referida a 2025-01-01, la geografía a 2025-05-07 y el registro de servicios a 2026-09-20. Se muestran por separado y no se presentan como una fotografía temporal homogénea.

### “¿Cero servicios significa que Aduna no tiene atención?”

No. Significa cero registros dentro del límite municipal en la fuente preparada. El registro de atención primaria más cercano al punto representativo está a 2.756,2 m.

### “¿El cuantil 0,75 es una verdad objetiva?”

No. Es un criterio analítico ajustable. La demo recalcula con 0,80 para mostrar sensibilidad. q0,75 produce 7 destacados; con 75+ y q0,80 quedan 4.

### “¿La simulación recomienda construir un centro en ese punto?”

No. Inserta un punto hipotético para medir cómo cambia la misma métrica. No estima coste, demanda, viabilidad, capacidad ni beneficio sanitario.

### “¿El modelo puede inventar una cifra?”

El contrato le exige usar una tool antes de afirmar cifras y el portal permite revisar la salida cruda. Los tests adversariales verifican errores controlados. La garantía operativa final depende de que la versión exacta supere la puerta privada del portal.

### “¿Qué pasa si escribo ‘atención primaria’ o ‘75+’?”

RC2 normaliza aliases españoles e ingleses, acentos, espacios y notaciones de edad. La versión del portal debe demostrarlo antes de la presentación.

## Checklist de ensayo

- [ ] La versión visible corresponde al commit `e13c3e58d22d8f01d07c27d571711b3a6d0a4a4d` o a un sucesor identificado.
- [ ] No hay ediciones concurrentes pendientes en el agente.
- [ ] G-01…G-06 pasan en una conversación nueva o en la secuencia documentada.
- [ ] Las siete tools ejecutan al menos una vez en la versión privada.
- [ ] Se abre una salida cruda de tool delante del jurado.
- [ ] Se verifica al menos una cifra directamente contra CSV; recomendada: Donostia 48.832 personas de 65+.
- [ ] Se pronuncian unidades y los tres periodos heterogéneos.
- [ ] Se explica Aduna sin equiparar cero registros con ausencia de atención.
- [ ] Se etiqueta el escenario como hipotético.
- [ ] La demo completa dura menos de tres minutos con un ensayo cronometrado.
- [ ] El respaldo offline está abierto y claramente etiquetado.
- [ ] No se entra en Entrega ni se selecciona una versión definitiva durante las pruebas.

## Decisión actual

**NO GO para demo en vivo.** El candidato local es sólido, pero falta una versión del portal cuya identidad esté ligada al commit y que complete la puerta G-01…G-06. En cuanto eso ocurra, el guion anterior es la secuencia recomendada.
