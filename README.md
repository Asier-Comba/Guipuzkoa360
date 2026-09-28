# GIPUZKOA 360

Un agente para explorar dónde coinciden envejecimiento municipal y mayor distancia geométrica a servicios sanitarios en Gipuzkoa.

La pregunta se convierte en una operación reproducible sobre datos oficiales. Siete herramientas consultan fuentes, resumen y comparan municipios, analizan envejecimiento y proximidad, identifican coincidencias y simulan cambios hipotéticos. Al cambiar los parámetros del diálogo, el agente vuelve a calcular.

Pensado para **personal técnico municipal y territorial** que necesita detectar patrones y contrastar diferencias entre municipios antes de profundizar con información sectorial adicional. No se afirma implantación administrativa ni validación con usuarios reales.

## Ver el proyecto

Abra **[la demo territorial](resultados/demo.html)** descargando el HTML: funciona sin servidor ni Internet. Sus tres consultas y el escenario son cálculos reales guardados; la conversación en vivo se realiza en el portal privado. [Guion de demostración](docs/DEMO.md).

La entrada es única: pregunta, hallazgo y mapa. Después se puede cambiar el criterio, abrir «Cómo se calcula», comparar municipios o explorar Aduna. La página [Cómo se comprueba](resultados/control_center.html) explica la fiabilidad en lenguaje sencillo y conserva la validación técnica completa en un desplegable secundario.

- **[Una página para el jurado](docs/JURY_ONE_PAGER.md):** problema, destinatario, evidencia y límite.
- **[Guía para empezar](docs/PRODUCT_GUIDE.md):** qué preguntar, cómo leer los criterios y cómo comprobar una cifra.
- **[44 preguntas del jurado](docs/JURY_QA.md):** respuestas breves con punteros de evidencia.

El **caso principal** identifica 7 municipios al combinar población de 65 o más años y mayor distancia geométrica a atención primaria. Una consulta distinta para mayores de 75 años, con otro criterio, identifica 4 municipios. Una tercera consulta para 65 o más años, con un nivel de exigencia mayor, identifica 2. Son tres preguntas diferentes: juntas demuestran que el agente recalcula cuando cambian la edad y los criterios.

## Datos y límites

| Fuente | Contenido | Periodo |
|---|---|---|
| Eustat | Población de 88 municipios | 2025-01-01 |
| geoEuskadi | Geometría municipal | 2025-05-07 |
| Open Data Euskadi | 148 registros sanitarios públicos | 2026-09-20 |

Distancia geométrica no es tiempo de viaje. Registro no es capacidad ni cita disponible. Coincidencia no demuestra causalidad. Escenario no es predicción. El punto municipal no está ponderado por población y las fuentes tienen fechas distintas. Una persona supervisa la interpretación.

## Entender y reproducir

La lectura principal se limita a seis documentos: este README, [Fuentes](FUENTES.md), [Metodología](docs/METODOLOGIA.md), [Validación](docs/VALIDATION.md), [Pruebas automatizadas](docs/BENCHMARKS.md) y [Demo](docs/DEMO.md). La evidencia histórica y los informes de ingeniería son material de apoyo.

Con Python 3.12 y Node, desde este repositorio:

```powershell
py -3.12 -m pip install -r requirements.txt
py -3.12 -m pytest -q
node --test tests/e2e/contract_flow.test.mjs
py -3.12 scripts/release/build_jury_data.py
node scripts/build_jury.mjs
py -3.12 scripts/release/verify_final_artifacts.py
py -3.12 scripts/benchmark/full_validation.py --output-dir analisis/final
py -3.12 scripts/agent/build_portal_package.py
```

Se usan los datos versionados; reconstruir esta evidencia no requiere descargar fuentes nuevas. La instalación inicial de dependencias sí puede requerir red.

## Equipo y contribuciones

**Oier Duñabeitia**: datos, geografía, calidad y reproducibilidad. **Asier Comba**: agente, validación y cierre técnico. **Hugo Fernández Díez**: producto, diseño visual, integración y pruebas conversacionales. [Equipo y contribuciones](docs/TEAM.md).

El cierre técnico está preparado para revisión. La publicación de la entrega requiere una decisión humana.
