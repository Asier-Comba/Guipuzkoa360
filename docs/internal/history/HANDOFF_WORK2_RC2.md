# HISTÓRICO — Handoff Work 2 · hardening independiente para RC2

Registro conservado del 24/09/2026; no es la guía ni el estado actual del release.
Consulte [validación vigente](../../VALIDATION.md) y [plan de integración](../release/INTEGRATION_PLAN.md).
Los estados pendientes, cifras de paquete y mediciones siguientes describen su ejecución original;
no deben trasladarse como hechos actuales sin contrastarlos con la auditoría vigente.

> Documento histórico del trabajo previo de Work 2. El manifiesto desincronizado descrito abajo correspondía
> a aquel checkout y quedó resuelto al regenerar RC2 con finales de línea LF. La recomendación antigua de pedir
> `detalle=true` no aplica a Studio: RC2 ya no expone ese argumento en las firmas públicas; el modo completo se
> conserva exclusivamente para auditoría offline. El estado autoritativo está en `docs/RC2_FINAL_STATUS.md`.

Fecha: 2026-09-24  
Base auditada: `main` en `bacc29d3b4d4d48eab11e5bf1ad00134f5b12a01`  
Rama: `work/agent-runtime-hardening`

Este trabajo no crea un release, no fusiona PRs y no publica nada en el portal. La rama de Work 1
`fix/portal-runtime-rc2` no estaba publicada en `origin` al cerrar esta auditoría, por lo que no fue posible
comparar su implementación.

## Diagnóstico del `KeyError`

### Hechos observados

1. La prueba privada v1 importó las siete tools desde un ZIP. Preparación mostró siete tools, pero una llamada
   a `analizar_coincidencia` terminó en `KeyError: La tool analizar_coincidencia no está registrada`.
2. La v2 declaró siete wrappers físicos en `tools.py` y reprodujo el mismo error.
3. La v3 declaró una única función `@tool` físicamente en `main.py`; esa tool sí se ejecutó y devolvió errores
   controlados de parámetros.
4. Una llamada v3 con parámetros técnicos válidos quedó en curso más de dos minutos. No se observó resultado.
5. En RC1, `main.py` importaba `TOOLS`; el builder fusionaba core y wrappers decorados en `portal/tools.py`.
6. El core local completo no presenta una operación de minutos: el peor cold load medido fue 15,469 ms y la
   peor serialización fue 0,477 ms.

### Explicación compatible con la evidencia, aún no confirmada

El coordinador serializa la llamada por nombre y el runtime la resuelve contra un registry de ejecutores. Los
resultados v1-v3 son compatibles con que Studio construya ese registry ejecutable solo a partir de funciones
decoradas en el ámbito de `main.py`, aunque la preparación pueda descubrir esquemas u objetos importados. En ese
caso, `create_agent` conoce el nombre y puede emitir la llamada, pero el ejecutor no encuentra el nombre en su
registry y lanza el `KeyError`.

No se dispone del código del backend de Studio ni de su registry; por tanto, no se afirma como causa demostrada.
La identidad de tool creada por importación dinámica pudo agravar v1, pero v2 demuestra que el ZIP y el import
dinámico no son necesarios para reproducir el fallo. Tampoco se atribuye el bloqueo >2 min al core: los benchmarks
lo contradicen. Puede estar en el sandbox, la orquestación, el registry o la extracción/importación repetida.

## Arquitectura antes y después

### RC1

`main.py` → importa `TOOLS` → siete objetos decorados en `tools.py` → `build_agent(TOOLS)`.

El builder unía `schemas.py`, `metrics.py`, `data_access.py` y `tools.py` en un `portal/tools.py`. Cada llamada
creaba `DataRepository` de nuevo, recargaba CSV y serializaba hasta 88 filas.

### Prototipo Studio-safe

`portal/main.py` declara físicamente siete funciones `@tool` y construye `TOOLS` con esos mismos siete objetos
locales. Cada wrapper llama a funciones normales de `portal/tools.py`. El core generado no contiene decoradores,
otro `TOOLS`, imports dinámicos, extracción ZIP, `tempfile` ni monkeypatching.

Pruebas estáticas y dinámicas verifican:

- exactamente siete nombres esperados y únicos;
- las siete funciones pertenecen al módulo `main.py` del bundle;
- las siete son invocables;
- `build_agent` recibe la misma lista y las mismas identidades;
- el bundle sigue siendo autocontenido con datos físicos declarados en `STUDIO_CONTEXT_FILES`.

## Normalización previa al análisis

Una capa única normaliza acentos, mayúsculas, espacios, guiones y guiones bajos. Entradas soportadas:

| Dominio | Entradas | Valor canónico |
|---|---|---|
| servicio | `atención primaria`, `atencion primaria`, `primary care`, `primary_care` | `primary_care` |
| servicio | `salud mental`, `mental health`, `mental_health` | `mental_health` |
| servicio | `hospital`, `hospitales` | `hospital` |
| servicio | `other health`, `other_health`, variantes españolas documentadas | `other_health` |
| edad | `65`, `65+`, `≥65`, `>=65` | `65` |
| edad | `75`, `75+`, `≥75`, `>=75` | `75` |
| escenario | `añadir`, `agregar`, `add service` | `add_service` |
| escenario | `eliminar`, `remove` | `remove_service` |
| escenario | `cambiar umbral`, `change threshold` | `change_threshold` |

Una entrada no inequívoca devuelve JSON controlado con `error_code` y `available_options`; no se fuerza al valor
más parecido.

## Contrato completo y compacto

Las matemáticas y el resultado completo permanecen en `TerritorialAnalysis`. Las tools devuelven por defecto una
vista compacta para el coordinador; `detalle=true` devuelve todas las filas reproducibles.

- Coincidencia compacta conserva cortes de edad/distancia, filtros, `rows_used`, las 88 filas unidas como
  agregado, todos los destacados, fuentes, periodos, unidad, método, warnings y limitaciones.
- Acceso general conserva agregados y los diez municipios con mayor distancia; un filtro municipal conserva todas
  las filas pedidas.
- Escenario conserva solo municipios cuya distancia o estado respecto al umbral cambia, además de baseline,
  escenario y agregados.
- La procedencia conserva metadatos completos en `data` y evita duplicarlos íntegramente en `sources`.

Work 3 debe pedir `detalle=true` cuando necesite las 88 filas para una visualización. El default compacto no debe
usarse como sustituto silencioso de un dataset completo.

## Benchmarks con datos reales

Entorno local Windows/Python; once repeticiones calientes. Archivo reproducible:
`analisis/agent_runtime_benchmark.json`. Tiempos en milisegundos; tamaños en caracteres JSON.

| Tool | Cold | Warm mediana | Serialización | Completo | Compacto | Reducción |
|---|---:|---:|---:|---:|---:|---:|
| `consultar_fuente` | 0,988 | 0,333 | 0,184 | 8.975 | 4.896 | 45,4% |
| `obtener_resumen_territorial` | 10,311 | 0,566 | 0,075 | 3.571 | 2.537 | 29,0% |
| `comparar_municipios` | 10,359 | 2,331 | 0,094 | 4.484 | 2.867 | 36,1% |
| `analizar_envejecimiento` | 2,519 | 0,389 | 0,085 | 2.691 | 2.181 | 19,0% |
| `analizar_acceso_servicios` | 13,153 | 4,110 | 0,224 | 17.059 | 3.614 | 78,8% |
| `analizar_coincidencia` | 15,469 | 6,828 | 0,477 | 36.838 | 5.216 | 85,8% |
| `simular_escenario` | 15,358 | 8,265 | 0,398 | 26.719 | 13.664 | 48,9% |

La coincidencia es la operación matemática más cara y la de mayor salida, pero sigue en milisegundos. La cache
por proceso mantiene una instancia de análisis por ruta resuelta. Los datasets se tratan como inmutables; si se
actualizan durante un proceso, debe llamarse `clear_analysis_cache()` o reiniciarse el runtime.

## Tests

- Core/agente y e2e fuera de `tests/data`: **102 passed**.
- Datos: **17 passed, 1 failed**.
- Total: **119 passed, 1 failed**.
- Nuevos casos: aliases bilingües, Unicode, mayúsculas, espacios, nulos, municipio/periodo/categoría inexistentes,
  cuantiles 0,5/0,75/0,85/0,95, umbrales inválidos, escenarios incompletos, JSON válido, límites de tamaño,
  repetición byte a byte, 65/75, Eibar-salud mental, Aduna-cero registros y cortes reales q0,75/q0,85.
- Golden/release cases existentes: pasan.

El único fallo de la suite completa ya existe en `main`: `runtime_manifest.json` está desincronizado. Registra
`demografia.csv` como 6.161 bytes, pero el archivo mide 6.250; y `runtime_servicios.csv` como 25.258, pero mide
25.407. También difieren sus SHA-256. Work 2 no regeneró ni comprometió activos de Work 1 para no pisar RC2.

El bundle se construye: 47.749 bytes, SHA-256
`ea9c7684b4fac85f79e77ec20d76ec1108901e47f5c3cb2c21f817d479ba4b27`, frente al límite de 24 MiB.

## Commits recomendados para cherry-pick

En orden:

1. `9e329d1` — normalización bilingüe y errores controlados.
2. `366364a` — contrato compacto/completo sin cambiar matemáticas.
3. `41ddf05` — cache de datasets, benchmark y límites de salida.
4. `ed41eb2` — hace portable el informe de benchmark; opcional si no se integra el informe.
5. `0a1daca` — wrappers Studio-safe locales en `main.py`; parche mínimo recomendado para el registry.
6. `c2d9c48` — regresiones adversariales con datos reales.

No hay commits deliberadamente experimentales en esta rama. `0a1daca` está respaldado por pruebas locales pero,
por prohibición expresa de publicar/probar en el portal durante esta misión, aún necesita validación privada de
Studio por Work 1 antes de entrar en RC2.

## Incompatibilidades y riesgos abiertos

- `tools.py` ya no exporta una lista de objetos decorados `TOOLS`; los consumidores de agentes deben usar
  `main.TOOLS`. Las funciones Python de `tools.py` siguen siendo invocables directamente.
- El default compacto añade `detail_level` y `summary` y reduce `data` para acceso/coincidencia/escenario. Work 3
  debe solicitar `detalle=true` si necesita el contrato completo.
- No se ha demostrado el algoritmo interno del registry de Studio; solo se ha eliminado la ambigüedad compatible
  con toda la evidencia observada.
- Las pruebas simulan el decorador/registry de Studio, no sustituyen una ejecución real del backend.
- Falta refrescar `runtime_manifest.json` desde la rama propietaria de datos antes de construir RC2.
- Falta comprobar en una versión privada no seleccionada para Entrega las siete tools, aliases, salida compacta,
  `detalle=true` y una repetición idéntica. No debe publicarse ni seleccionarse la entrega durante esa prueba.
