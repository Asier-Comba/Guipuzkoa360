# Operación del agente privado

Producto: **GIPUZKOA 360**. No publicar Entrega.

## Identidad y construcción

Runtime congelado: `195b4980fa5998b096c308296a55e452380b0371`.
Versión privada existente: `urban-challenge-rc2-195b498 · v4`; conservar sin renombrar.
Esta rama actualiza solo esta guía entre los miembros del ZIP: no modifica código ni contexto.
El nuevo checksum está fuera del archivo, en el manifiesto generado que lo acompaña.

Desde checkout limpio y con `requirements-release.lock` instalado:

```text
python scripts/release/reproduce.py
```

No descargar fuentes vivas para reconstruir el snapshot. Detenerse si falla la auditoría,
el manifiesto, los dos builds o la comparación con los bytes congelados.

## Archivos exactos

Extraer `dist/gipuzkoa360-urban-challenge-rc2.zip`. Los dos Python están en la raíz del ZIP:
**main.py** y **tools.py**. `agentes/gipuzkoa360/portal/` es su ruta en el repositorio, no en el ZIP.
El ZIP añade `requirements.txt` (sin dependencias adicionales), esta guía y los diez archivos:

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

La lista es exactamente `STUDIO_CONTEXT_FILES`. Conservar rutas relativas. No cargar
originales, geometría maestra, HTML, tests, entornos ni informes de auditoría como contexto.

## Contrato

Entrada síncrona: `build_agent(model)`; el portal aporta `studio` y `langchain`.
Sin instalaciones adicionales ni Internet durante ejecución. Configuración:
`STUDIO_MAX_ITERATIONS=8`, memoria activa e Internet desactivado.
Conservar el `SYSTEM_PROMPT` de main.py, no sustituirlo por otro texto.

Tools: `consultar_fuente`, `obtener_resumen_territorial`, `comparar_municipios`,
`analizar_envejecimiento`, `analizar_acceso_servicios`, `analizar_coincidencia`,
`simular_escenario`. Ninguna firma pública admite `detalle`.

## Verificar antes de crear otra versión

1. En Pruebas, elegir la versión privada existente. Comprobar el número, no solo el nombre
   del agente: este puede aparecer actualizado en conversaciones de versiones anteriores.
2. Consultar docs/DEMO.md y docs/VALIDATION.md en el repositorio. La auditoría encontró
   G-01…G-06 y red-team distribuidos entre versiones previas; no llamarlos todos pruebas de v4.
3. Para cerrar la brecha, repetir en v4 G-01…G-06, siete herramientas y ataques críticos.
   Guardar pregunta, argumentos, salida real, respuesta, versión, identidad del código y
   latencias hasta tool, output y respuesta. No requiere otra versión si el runtime no cambia.
4. Si hace falta crear una versión: un solo operador autorizado coteja archivos, pega
   main.py/tools.py en el agente elegido, conserva las rutas y pulsa Comprobar preparación.
   No tocar otro agente ni el fichero administrado ejecucion.py.
5. Tras preparación correcta, Crear versión fija código y contexto. Registrar su identidad
   y repetir toda la batería. Cambiar código/contexto invalida evidencia anterior; no corregir
   cifras ni relajar validaciones para conseguir PASS.
6. Conservar la versión privada. **No abrir Entrega ni publicar.**

Registrar fallos del runner antes de reintentar. Cero registros no prueba ausencia de
atención; distancia no es tiempo; registros no son citas; escenarios no son predicciones.
