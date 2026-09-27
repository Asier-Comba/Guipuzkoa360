# GIPUZKOA 360 · Validación técnica independiente

## Alcance y sistema evaluado

Esta validación somete a una segunda ruta de cálculo al release integrado en `main`
`6991c6c20d2de467d7cf25236f2e4b1274c17067`. La identidad congelada del runtime es
`195b4980fa5998b096c308296a55e452380b0371`. La evaluación no modifica runtime,
datos, firmas de herramientas, comportamiento del agente ni versión seleccionada en
el portal.

El sistema bajo prueba contiene 88 municipios, 148 registros sanitarios, dos grupos
de edad, cuatro categorías sanitarias y siete herramientas públicas. El oráculo
independiente lee directamente cinco archivos versionados:

- `datos_preparados/municipios.csv`;
- `datos_preparados/demografia.csv`;
- `datos_preparados/runtime_municipality_points.csv`;
- `datos_preparados/runtime_servicios.csv`;
- `datos_preparados/metadata_sources.json`.

El oráculo no importa `agentes.gipuzkoa360`, `tools.py` ni helpers de cálculo,
percentiles o escenarios del producto. Reimplementa búsqueda municipal, porcentajes,
distancias euclídeas en EPSG:25830, selección del servicio más cercano, cuantiles,
criterios de coincidencia y escenarios de adición/eliminación.

## Resultado

**PASS técnico independiente.** No se encontró ningún Critical ni High. Las 14
familias terminaron en PASS, con cero desacuerdos no explicados, cero invariantes
deterministas fallidos, cero excepciones públicas no controladas y cero corrupciones
silenciosas.

Los denominadores son independientes y no se suman:

| Evidencia | Resultado | Qué cuenta |
|---|---:|---|
| Suite Python integrada | 264/264 | tests |
| Suite Node integrada | 17/17 | tests |
| Benchmark original | 72.673/72.673 | checks publicados; definición histórica intacta |
| Trazabilidad original | 31.545/31.545 | outputs numéricos trazables según la definición publicada |
| Inyección original | 20/20 | fallos controlados |
| Soak original | 1.000 | llamadas |
| Oráculo independiente | 3.595.648/3.595.648 | comparaciones de campos y resultados |
| Cuadrícula de propiedades | 2.539.976/2.539.976 | evaluaciones sujeto-propiedad |
| Cuadrícula base | 387.200 | combinaciones edad-categoría-cuantil-umbral-municipio |
| Metamórficas | 30/30 | transformaciones independientes |
| Mutaciones | 66/66 detectadas | mutaciones no equivalentes; score 100 % |
| Fuzz determinista | 100.000 | 98.000 rechazos controlados y 2.000 normalizaciones válidas |
| Corpus de lenguaje | 1.000 | consultas distintas con intención, herramienta, parámetros, fuentes y límites esperados |
| Ejecuciones reales de lenguaje en portal | 0 | no se fabrican métricas de portal |
| Sesiones offline | 100/100 | sesiones estructuradas de cinco turnos |
| Trazabilidad de campo V2 | 259.072/259.072 | aserciones campo-origen-periodo-unidad-método-fila-servicio |
| Soak extendido | 10.000 | llamadas mixtas sin deriva ni excepción |
| Oráculo geoespacial | 352/352 | distancias publicadas contrastadas por categoría y municipio |

## Familias independientes

### Oráculo numérico

Se compararon los 88 municipios, 65+/75+, las cuatro categorías, todos los umbrales
públicos válidos, cuantiles 0,50–0,95, servicios más cercanos, cifras de control y
escenarios canónicos. Las 3.595.648 comparaciones coincidieron.

La tolerancia se fijó por representación: `1e-9` absoluto y `1e-12` relativo para
valores sin redondear; 0,0001 puntos porcentuales para cortes publicados con cuatro
decimales; 0,1 m para distancias publicadas con un decimal. El mayor error observado
fue 0,0001 puntos porcentuales, dentro de la tolerancia de presentación. No cambió
ninguna selección ni cifra de control.

Los cuantiles 0,96–0,99 y el umbral 0 se incluyeron en la cuadrícula matemática, pero
no se presentan como soportados por la frontera pública actual, que acepta cuantiles
hasta 0,95 y umbrales mayores que cero.

### Propiedades, metamorfismo y mutación

La cuadrícula comprobó implicaciones de selección, rangos, no negatividad, monotonía
de cortes y recuentos, independencia del conjunto destacado respecto del umbral,
estado de umbral, fuentes, periodos y filas usadas. No falló ninguna de las 2.539.976
evaluaciones.

Las 30 transformaciones cubrieron repetición, orden de registros, cambio aislado de
umbral, monotonía de cuantil, aislamiento de escenarios y equivalencia numérica entre
salida compacta y detallada. Las 66 mutaciones controladas incluyeron operadores de
borde, índices de percentil, grupos de edad, unidades, fuentes, categorías, joins,
NaN/Infinity, recuentos y truncación. Todas las mutaciones no equivalentes fueron
detectadas; no hubo supervivientes.

### Entradas adversariales, lenguaje y sesiones

Los 100.000 casos de fuzz recorrieron las siete herramientas con texto vacío, Unicode,
acentos, cadenas largas, rutas aparentes, tipos erróneos, umbrales y cuantiles fuera
de rango, NaN e infinitos. Hubo 98.000 rechazos controlados, 2.000 normalizaciones
válidas, cero excepciones no controladas y cero corrupciones silenciosas.

El corpus de 1.000 consultas cubre preguntas directas, paráfrasis, lenguaje informal,
errores tipográficos, seguimientos, fuentes, escenarios, ambigüedad y solicitudes fuera
de alcance. Es un corpus versionado; no se afirma que esas 1.000 consultas se hayan
ejecutado contra el modelo del portal. Las 100 sesiones offline verifican herencia de
parámetros, cambio aislado de cuantil, consulta de fuente, rechazo y retorno a una
consulta válida, además de que un escenario no contamine el baseline posterior.

### Geoespacial, seguridad y reproducibilidad

Los 88 códigos y las 88 geometrías coinciden; todas las geometrías son válidas y los
88 puntos representativos están dentro o en el límite de su municipio. La conversión
alternativa con PROJ a EPSG:25830 difiere como máximo 0,0061 m en puntos municipales y
0 m en servicios. Las 352 distancias publicadas coinciden, con error máximo 0 m.

El escaneo de archivos versionados no encontró patrones de credenciales, cabeceras
Bearer, cookies privadas, sesiones ni rutas locales de usuario. `pip check` no encontró
dependencias rotas. Las superficies JSON rechazaron o normalizaron de forma controlada
los textos de inyección probados; no hay JavaScript externo, analítica, cookies ni
tracking en el producto estático.

La regeneración de los seis artefactos fue byte-reproducible, 100 consultas repetidas
produjeron una única salida canónica, el manifiesto pasó y el runtime conservó su
identidad. El paquete canónico bajo Python 3.12 ocupa 48.338 bytes y tiene SHA-256
`2808110d14e0bc30a53018cab1ec39b926e1e6ca1f1be19f0b2c9cf21106680a`.
La identidad ZIP se limita a la herramienta validada: una variación de bytes bajo
Python 3.14 es variación de entorno, no defecto del producto.

## Rendimiento offline

Las latencias son locales y no representan al portal ni a un modelo conversacional.
Sobre las herramientas calientes, la mediana de las medianas fue 1,543 ms; el mayor
p95 entre familias fue 9,393 ms y el mayor p99, 9,686 ms. El arranque frío tuvo mediana
111,078 ms en 10 procesos. Se midieron por separado resumen, envejecimiento, acceso,
coincidencia, escenario y fuente, con tamaño de payload mediano/p95/máximo por familia
en `analisis/research_grade/performance_summary.json`.

## Hallazgos y decisión de release

No hay Critical ni High conocidos.

- **M-01 · Medium conocido.** El escenario extremo de umbral 1→10 km produce 20.155
  caracteres, 66 municipios afectados y 88 evaluados. No son 88 afectados.
- **M-02 · Medium conocido.** Un fallback histórico del portal, cuando el runner estaba
  ocupado, confundió umbral y cuantil; no hubo salida de herramienta ni evidencia de
  fallo numérico del core.
- **M-03 · Medium nuevo.** Reordenar servicios puede elegir otro `service_id` entre
  registros con coordenadas exactamente idénticas. Ocurre en ocho filas, conservadas
  en `metamorphic_summary.json`. Distancia, estado de umbral, conjuntos destacados y
  conclusiones numéricas no cambian. Se documenta y no se rompe el runtime congelado
  para resolver una identidad empatada sin efecto analítico.

M-03 es una ambigüedad de trazabilidad entre registros co-localizados, no una diferencia
de distancia ni una corrupción silenciosa. No requiere reemplazar la versión de portal.

## Producto estático y recorrido de jurado

Las cuatro vistas locales pasaron 24 combinaciones: 1920×1080, 1366×768, 1024×768,
390×844 y equivalentes de reflow al 125 % y 150 %. No hubo overflow horizontal,
solapes, recortes ni texto visible `NaN/undefined`. Cada vista renderizó 88 geometrías
municipales más el contorno. También pasaron 7→4→2, selector municipal, sincronía de
clic del mapa, detalles, enlaces de fuentes, Tab, Shift+Tab, Enter, Space y foco visible.
Esto no constituye una certificación formal WCAG.

La copia de `gh-pages` pasó 15 combinaciones de escritorio, tablet y móvil. Sus cinco
HTML tienen rutas y anclas válidas, los dos JSON de evidencia existen, no hay nombres
con retorno de carro ni dependencias de código externas.

### Tres revisores

1. **Política municipal.** En menos de un minuto puede localizar la pregunta, entender
   que 7 es la intersección de dos cortes, cambiar a 4 y 2, leer el mapa y encontrar el
   aviso de que no mide accesibilidad real.
2. **Ciencia de datos.** Fuente, periodo, unidad, método, cuantil, umbral, identidad de
   runtime y definición de benchmark aparecen en evidencia y validación, sin sumar
   denominadores incompatibles.
3. **Revisión técnica hostil.** La demo estática es evidencia de apoyo, no “el agente”.
   El 7 procede de q0,75 en ambas métricas; el umbral solo cambia `within_threshold`;
   el cuantil explica 7→4→2; cero registros internos en Aduna no significa cero médicos;
   0 m es un contrafactual en el punto representativo; no hay predicción 2030; y las
   fechas de fuente distintas se muestran porque no forman una fotografía simultánea.

## Alineación con la rúbrica

| Criterio | Claim | Evidencia | Ruta de demo | Límite |
|---|---|---|---|---|
| 25 % utilidad urbana | Permite localizar coincidencias territoriales y contrastar variaciones | `demo.html`, oráculo y controles 7→4→2 | Hallazgo → cambiar criterio → municipio | No recomienda inversión |
| 25 % análisis, fuentes y trazabilidad | Cada cifra enlaza fuente, periodo, unidad, método y filas | 259.072/259.072 aserciones V2 | Evidencia → trazabilidad → fuente original | Fechas de fuentes distintas |
| 25 % agente y herramientas | Siete herramientas recalculan consultas y rechazan fuera de alcance | 264 Python, 17 Node, 100.000 fuzz | Pregunta → herramienta → dato → resultado | HTML guardado no conversa |
| 15 % claridad | El recorrido separa hallazgo, evidencia, escenario y límites | matriz responsive y teclado | Navegación superior y controles 7→4→2 | Sin certificación WCAG formal |
| 10 % fiabilidad y supervisión | Runtime congelado, oráculo independiente y límites visibles | 3.595.648 comparaciones; 10.000 soak | Validación → método y límites | Decisión final permanece humana |

No se calcula ni se predice una puntuación del hackatón.

## Límites científicos

La distancia es euclídea desde un punto representativo municipal no ponderado por
población. No es tiempo de viaje, distancia de red, acceso peatonal, accesibilidad
universal, capacidad, citas, calidad ni apertura. Las fechas de demografía, geometría y
servicios no coinciden. Una coincidencia estadística no demuestra causalidad. Un
escenario no es predicción ni recomendación.

## Reproducción

Con Python 3.12 y Node disponibles, desde la raíz del repositorio:

```text
py -3.12 scripts/ops/verify_runtime_identity.py
py -3.12 -m pytest -o addopts= -q
node --test tests/e2e/contract_flow.test.mjs
py -3.12 scripts/evaluation/build_nl_gold.py
py -3.12 scripts/evaluation/run_research_grade.py
git diff --check
```

Los resultados agregados están en `analisis/research_grade/`. No se versionan dumps de
millones de filas. Semillas, configuración, corpus, scripts, denominadores y ejemplos
de fallo quedan versionados para repetir la evaluación.

## Identidad de release

- Fuente evaluada: `6991c6c20d2de467d7cf25236f2e4b1274c17067`.
- Runtime congelado: `195b4980fa5998b096c308296a55e452380b0371`.
- Runtime cambiado por esta evaluación: no.
- Datos cambiados por esta evaluación: no.
- Agente cambiado por esta evaluación: no.
- Critical conocidos: 0.
- High conocidos: 0.
- Medium conocidos anteriores: 2.
- Medium nuevo documentado: 1.
