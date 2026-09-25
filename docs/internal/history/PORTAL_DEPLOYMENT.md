# HISTÓRICO — Despliegue del release candidate en el portal

Guía anterior conservada para auditoría. Contiene rutas y asignaciones de operador superadas.
No seguir como procedimiento actual. Véase [guía vigente](../../PORTAL_DEPLOYMENT.md).

Release: `urban-challenge-rc2`. RC1 es histórico. Esta guía prepara una versión privada; no autoriza ni describe la publicación de la entrega final.

## 1. Construir y verificar

Desde la raíz del repositorio:

```text
python scripts/data/build_all.py
python scripts/agent/build_portal_sources.py
python scripts/agent/run_release_e2e.py
python -m pytest -q
node --test tests/e2e/contract_flow.test.mjs
python scripts/agent/benchmark_tools.py
python scripts/agent/build_portal_package.py
```

El último comando crea `dist/gipuzkoa360-urban-challenge-rc2.zip` y su manifiesto SHA-256. El ZIP reproduce la estructura que debe existir en la raíz del workspace del portal. Construirlo dos veces sin cambios debe producir exactamente el mismo tamaño y SHA-256.

## 2. Archivos exactos

En **Datos**, conservar las rutas relativas del ZIP y subir/cotejar:

```text
FUENTES.md
docs/METODOLOGIA.md
docs/RESULT_SCHEMA.md
docs/PORTAL_DEPLOYMENT.md
datos_preparados/municipios.csv
datos_preparados/demografia.csv
datos_preparados/runtime_municipality_points.csv
datos_preparados/runtime_servicios.csv
datos_preparados/metadata_sources.json
datos_preparados/data_contract.json
datos_preparados/runtime_manifest.json
```

En **Agentes → Python → Agente principal**, reemplazar el contenido de los dos editores con:

- `main.py` ← `agentes/gipuzkoa360/portal/main.py` del ZIP.
- `tools.py` ← `agentes/gipuzkoa360/portal/tools.py` del ZIP.

`tools.py` es autocontenido porque el portal expone esos dos archivos Python. Se genera desde `schemas.py`, `metrics.py`, `data_access.py` y `tools.py`; no debe editarse a mano.

## 3. Configuración que debe verse en `main.py`

- Entrada síncrona: `build_agent(model)`.
- Constructor: `langchain.agents.create_agent`.
- `STUDIO_MAX_ITERATIONS = 8`.
- `STUDIO_MEMORY_ENABLED = True` para seguimientos.
- `STUDIO_INTERNET_ENABLED = False`.
- Siete tools deterministas, sin tool de ejecución arbitraria.
- Ninguna firma pública de Studio expone `detalle`; las respuestas del coordinador son compactas por diseño.
- Sin secretos, tokens, llamadas HTTP ni rutas locales.

`STUDIO_CONTEXT_FILES` debe ser exactamente:

```text
FUENTES.md
docs/METODOLOGIA.md
docs/RESULT_SCHEMA.md
datos_preparados/municipios.csv
datos_preparados/demografia.csv
datos_preparados/runtime_municipality_points.csv
datos_preparados/runtime_servicios.csv
datos_preparados/metadata_sources.json
datos_preparados/data_contract.json
datos_preparados/runtime_manifest.json
```

Dependencias del agente: ninguna adicional. El portal aporta `langchain` y `studio`; el bundle usa solo biblioteca estándar de Python. `requirements.txt` se incluye como registro y no requiere instalar paquetes.

## 4. Comprobar y crear versión

1. Abrir `main.py` y pulsar **Comprobar preparación**.
2. Abrir `tools.py` y repetir la comprobación si el portal lo permite.
3. Corregir únicamente errores de importación o archivos ausentes; no cambiar cifras ni relajar validaciones.
4. Pulsar **Crear versión del agente**. Nombrarla `urban-challenge-rc2` e identificar el SHA exacto indicado por Work 1.
5. Ir a **Pruebas**, seleccionar esa versión y ejecutar, en orden, `docs/JURY_TEST_PLAN.md` y los casos A–H de `analisis/release_e2e_report.json`.
6. Confirmar que cada respuesta muestra tool, argumentos, periodo, unidad, fuente y límite; revisar especialmente Aduna, Eibar y el caso fuera de alcance.
7. Si todas pasan, conservar la versión como candidata. **No abrir Entrega ni publicar** hasta la autorización del equipo.

Work 3 es el único operador del portal durante esta puerta. No editar el agente ni lanzar pruebas en paralelo. Si
falla una prueba, registrar versión, SHA, pregunta, tool, argumentos, salida y tiempo; Work 1 aplicará únicamente
el parche mínimo y entregará un SHA nuevo que invalida cualquier evidencia anterior.

## 5. Tools definitivas

| Tool | Uso |
|---|---|
| `obtener_resumen_territorial` | Perfil demográfico e indicadores sanitarios de un municipio. |
| `comparar_municipios` | Comparación de 2–20 municipios, con acceso opcional. |
| `analizar_envejecimiento` | Ranking 65+/75+ por porcentaje o personas. |
| `analizar_acceso_servicios` | Distancia geométrica por categoría y umbral. |
| `analizar_coincidencia` | Cruce explícito de envejecimiento y distancia. |
| `simular_escenario` | Alta/baja hipotética o cambio de umbral. |
| `consultar_fuente` | Ficha oficial de procedencia y limitaciones. |

## 6. Criterio de aceptación en plataforma

Una versión es válida solo si `build_agent(model)` termina, las siete tools aparecen, no hay archivo ausente y las ocho pruebas A–H son correctas. El caso H no debe invocar una tool irrelevante. Una respuesta que confunda cero registros con ausencia de atención, distancia con accesibilidad, registro con capacidad o coincidencia con causalidad invalida la versión.
