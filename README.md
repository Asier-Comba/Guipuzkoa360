# GIPUZKOA 360

Un agente para que personal técnico compare envejecimiento municipal y proximidad geométrica a servicios sanitarios en Gipuzkoa, con cálculos reproducibles y fuentes oficiales.

## Qué problema aborda

Las cifras provinciales ocultan diferencias municipales. GIPUZKOA 360 permite explorar dónde coinciden una mayor proporción de personas mayores y una mayor distancia geométrica a servicios registrados. No determina necesidades individuales ni decide dónde invertir.

## Qué hace el agente

Pregunta natural → herramienta determinista → datos oficiales → cálculo → respuesta con unidades, periodos, fuentes y límites.

Sus siete operaciones permiten consultar fuentes, resumir un municipio, comparar municipios, analizar envejecimiento, medir proximidad, identificar coincidencias y simular cambios hipotéticos sin alterar la base.

No es un dashboard estático: interpreta la intención, normaliza parámetros, conserva el contexto y vuelve a calcular cuando cambia la pregunta. Las visualizaciones complementan la conversación, pero no sustituyen una llamada real.

## Un ejemplo comprobable

«¿Dónde coinciden envejecimiento de 65+ y mayor distancia geométrica a atención primaria, con cuantil 0,75 y umbral de 2 km?»

El cálculo utiliza **88 filas municipales** y destaca **7 municipios**; los cortes estadísticos son **23,973 %** y **2.019,2 m**. El umbral de 2 km se informa por separado. Al cambiar a 75+, cuantil 0,80 y 3 km, una nueva ejecución destaca **4 municipios**.

## Datos oficiales

| Fuente | Datos | Referencia |
|---|---|---|
| Eustat | Población y grupos de edad | 2025-01-01 |
| geoEuskadi | Geometría municipal | 2025-05-07 |
| Open Data Euskadi | 148 registros sanitarios públicos | 2026-09-20 |

Cobertura: **88 municipios**. Snapshot descargado el 24/09/2026; no son datos en tiempo real. [Fuentes y transformaciones](FUENTES.md) · [Metodología](docs/METODOLOGIA.md).

## Cómo se comprueban las cifras

El agente debe consultar una herramienta antes de responder con cifras. Los resultados conservan fuentes, periodo, unidad y método; se contrastan con datos versionados, QA y pruebas adversarias. Esto permite auditar respuestas, no garantiza infalibilidad del modelo.

La evidencia de Asier registra **72.673/72.673 checks**, **31.545/31.545 outputs trazables**, **148 tests Python** y **17 tests Node**. Existe **PORTAL GO histórico** para el runtime congelado; no equivale a autorización de publicación. El empaquetado entre representaciones del checkout mantiene un **WARN en investigación**. [Evidencia y alcance](docs/VALIDATION.md).

## Límites

Distancia geométrica ≠ tiempo de viaje. Registro ≠ capacidad o citas. Coincidencia ≠ causalidad. Escenario ≠ predicción. Cero registros municipales ≠ ausencia de atención.

El punto representativo no está ponderado por población; las fuentes tienen fechas distintas. El grupo 75+ se deriva de nacidos hasta 1949. Una persona debe supervisar la interpretación y cualquier decisión.

## Equipo

**Oier Duñabeitia** — datos, geoespacial, QA, reproducibilidad e integración/release.  
**Asier Comba** — arquitectura del agente, herramientas, runtime, hardening, benchmark y validación técnica.  
**Hugo Fernández Díez** — producto, visualización, integración visual, red-team y experiencia de jurado.

[Contribuciones verificables](docs/TEAM.md). Esta rama preserva trabajo para integración; no es una entrega publicada.
