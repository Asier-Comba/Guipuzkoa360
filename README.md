# GIPUZKOA 360

Un agente para explorar dónde coinciden envejecimiento municipal y mayor distancia geométrica a servicios sanitarios en Gipuzkoa.

La pregunta se convierte en una operación reproducible sobre datos oficiales. Siete herramientas consultan fuentes, resumen y comparan municipios, analizan envejecimiento y proximidad, identifican coincidencias y simulan cambios hipotéticos. Al cambiar los parámetros del diálogo, el agente vuelve a calcular.

## Ver el proyecto

Abra **[la demo territorial](resultados/demo.html)** descargando el HTML: funciona sin servidor ni Internet. Sus tres consultas y el escenario son cálculos reales guardados; la conversación en vivo se realiza en el portal privado. [Guion de demostración](docs/DEMO.md).

Con 65+, cuantil 0,75 y atención primaria, **7 de 88 municipios** cumplen ambos cortes: **23,973 %** y **2.019,2 m**. El seguimiento a 75+ y cuantil 0,80 produce **4**; elevar el cuantil de 65+ a 0,85 produce **2**. El umbral en km se informa por separado y no sustituye al cuantil.

## Datos y límites

| Fuente | Contenido | Periodo |
|---|---|---|
| Eustat | Población de 88 municipios | 2025-01-01 |
| geoEuskadi | Geometría municipal | 2025-05-07 |
| Open Data Euskadi | 148 registros sanitarios públicos | 2026-09-20 |

Distancia geométrica no es tiempo de viaje. Registro no es capacidad ni cita disponible. Coincidencia no demuestra causalidad. Escenario no es predicción. El punto municipal no está ponderado por población y las fuentes tienen fechas distintas. Una persona supervisa la interpretación.

## Entender y reproducir

La lectura principal se limita a seis documentos: este README, [Fuentes](FUENTES.md), [Metodología](docs/METODOLOGIA.md), [Validación](docs/VALIDATION.md), [Benchmark](docs/BENCHMARKS.md) y [Demo](docs/DEMO.md). La evidencia histórica y los informes de ingeniería son material de apoyo.

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

## Equipo

**Oier Duñabeitia**: datos, geografía, calidad y reproducibilidad. **Asier Comba**: agente, runtime, benchmark y cierre técnico. **Hugo Fernández Díez**: producto, diseño visual, integración y pruebas conversacionales. [Contribuciones y uso de IA](docs/TEAM.md).

El cierre técnico está preparado para revisión. La publicación de la entrega requiere una decisión humana.
