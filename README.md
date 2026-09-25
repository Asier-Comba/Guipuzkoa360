# GIPUZKOA 360

Un agente para que personal técnico explore dónde coinciden envejecimiento municipal y mayor distancia geométrica a servicios sanitarios, con cálculos verificables sobre datos oficiales.

## Problema

Una cifra provincial no explica las diferencias entre municipios. GIPUZKOA 360 permite contrastar población de 65+ y 75+ con registros sanitarios y proximidad geométrica en los 88 municipios de Gipuzkoa. Es una herramienta exploratoria: no demuestra necesidades individuales ni determina dónde invertir.

## Qué hace

Pregunta natural → herramienta determinista → datos oficiales → cálculo reproducible → respuesta con unidad, periodo, fuente y límites.

## Por qué no es un dashboard estático

Interpreta la intención, selecciona una operación, normaliza municipios y parámetros y calcula el resultado. Conserva el contexto del diálogo: «ahora para 75+ y 3 km» debe producir una nueva llamada. Las vistas visuales complementan esta conversación; sus controles locales no sustituyen una ejecución del agente.

## Ejemplo real

«¿Dónde coinciden una proporción alta de población de 65+ y mayor distancia geométrica a atención primaria? Usa cuantil 0,75, 2 km y población a 1 de enero de 2025.»

El cálculo une **88 filas municipales** y destaca **7 municipios**. Los cortes del cuantil son **23,973 %** y **2.019,2 m**. El umbral solicitado de 2 km se informa por separado: no es el corte estadístico. El seguimiento a 75+, cuantil 0,80 y 3 km recalcula y destaca **4 municipios**.

Son coincidencias territoriales entre fuentes de fechas diferentes, no causalidad ni accesibilidad real. [Cómo comprobarlo](docs/DEMO.md).

## Capacidades

Siete operaciones: consultar fuentes; resumir un municipio; comparar municipios; analizar envejecimiento; medir proximidad a servicios registrados; buscar coincidencias entre indicadores; y simular altas, bajas o cambios de umbral sin alterar los datos observados.

## Datos oficiales

| Fuente | Contenido | Referencia del snapshot |
|---|---|---|
| Eustat | Población total y mayores | 2025-01-01 |
| geoEuskadi | Límites y puntos municipales | 2025-05-07 |
| Open Data Euskadi | 148 registros sanitarios públicos | 2026-09-20 |

Snapshot descargado el 24/09/2026. No son datos en tiempo real. El grupo 75+ se deriva de nacidos hasta 1949 y no incluye posibles nacimientos del 01/01/1950. [Fuentes y transformaciones](FUENTES.md) · [Metodología](docs/METODOLOGIA.md).

## Validación

88 municipios, 148 registros, 7 herramientas. Auditoría local: **146 tests Python**, incluidos 18 de datos; **17 tests Node**, **41 controles QA** y **8 casos deterministas A–H**. No se suman subconjuntos como pruebas independientes.

La validación privada del portal está registrada como **PORTAL GO** para el runtime congelado. Es distinta de la auditoría local y de la autorización de publicación. Esta rama todavía debe integrarse: la rama por defecto del repositorio sigue siendo histórica. [Validación, rendimiento, hash y alcance de la evidencia](docs/VALIDATION.md).

## Reproducir

En un checkout limpio de esta rama, con Python 3.12.4 y Node 24.12.0; en Windows PowerShell:

```powershell
git clone --branch final/oier-release-polish https://github.com/Asier-Comba/Guipuzkoa360.git
cd Guipuzkoa360
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements-release.lock
.venv/Scripts/python scripts/release/reproduce.py
```

El verificador regenera datos desde los originales guardados, ejecuta QA, tests, casos, visualizaciones y benchmark, y compara dos ZIP y los bytes congelados. La instalación necesita acceso al índice de paquetes; la reproducción del snapshot y el runtime no necesitan Internet. El informe queda en `work/release-audit/report.json`, el paquete en `dist/`. No ejecutar la descarga de fuentes vivas para reconstruir este snapshot.

## Límites

Distancia geométrica ≠ tiempo de viaje. Registro ≠ capacidad o citas. Coincidencia ≠ causalidad. Escenario ≠ predicción. Cero registros municipales ≠ ausencia de atención sanitaria.

El punto representativo no está ponderado por población. Los periodos difieren y los municipios pequeños pueden presentar tasas sensibles al denominador. No hay imputación de ausencias ni datos de vivienda, costes o demanda futura. Una persona debe supervisar la interpretación y cualquier decisión. [Preguntas difíciles y respuestas comprobables](docs/DEMO.md#preguntas-del-jurado).

## Equipo

**Oier Duñabeitia** — datos, geografía, QA y release. **Asier Comba** — agente, herramientas, runtime y validación técnica. **Hugo Fernández Díez** — producto, visualización, integración visual y red-team. [Contribuciones verificables](docs/TEAM.md).

La navegación pública canónica es este README, [Fuentes](FUENTES.md), [Metodología](docs/METODOLOGIA.md), [Validación](docs/VALIDATION.md) y [Demo](docs/DEMO.md). Los historiales de ingeniería están separados en `docs/internal/`. No se ha publicado la entrega del hackathon.
