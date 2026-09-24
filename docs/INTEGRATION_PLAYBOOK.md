# Playbook operativo de integración

## Orden

1. Work 1 — datos: recibir originales, preparados, diccionario, fuentes y comprobaciones.
2. Work 2 — agente: recibir versión, herramientas, formato de resultado y traza.
3. Work 3 — visualización: adaptar a `docs/EXPECTED_RESULT_SCHEMA.md` v1.0.0 y generar HTML.
4. Tests E2E y contraste manual de una cifra.
5. Subir la versión preparada al portal; verificar límites de archivos/contexto.
6. Crear y probar una versión fija; seleccionar la versión de entrega.
7. Revisar vista previa y publicar solo con autorización humana.

## Qué copiar

De Work 1, acordar rutas antes de copiar: `datos_originales/`, `datos_preparados/`, `FUENTES.md`, scripts de preparación, diccionario de columnas, licencias y comprobaciones de filas. De Work 2: `agentes/<nombre>/main.py`, `tools.py`, dependencias, instrucciones, versión de contrato, ejemplo de salida, traza de llamada y tests. Si su estructura difiere, registrar las rutas exactas en el handoff; no asumirlas.

Work 1 ya está disponible en la rama `work/data-foundation` (PR #1). Campos confirmados: `municipality_code` (texto de 5 dígitos), `population_total`, `population_65_plus`, `population_75_plus`, `distance_to_nearest_primary_care_m`, `distance_to_nearest_hospital_m`, `services_primary_care`, `reference_period` y `metrics_reference_period`. Las distancias son desde un punto representativo municipal en EPSG:25830, no tiempos de viaje. Las fuentes se identifican en `datos_preparados/metadata_sources.json`. No se copian esos archivos a esta rama para evitar duplicar trabajo del PR #1.

## Archivos que no se sobrescriben

No sobrescribir originales, `FUENTES.md`, `ejecucion.py`, `main.py` o `tools.py` de otros Work, ni una versión fija del portal. Conservar el JSON original del agente. Crear `scripts/adapt_work2.mjs` para mapear nombres/campos; dejar los archivos de origen intactos. Revisar diferencias antes de integrar ramas.

## Comandos locales

Desde la raíz del proyecto:

```powershell
node scripts/build_results.mjs tests/fixtures/synthetic_agent_result.json resultados
node --test tests/e2e/contract_flow.test.mjs
```

Al recibir una salida real JSON:

```powershell
node scripts/build_results.mjs ruta\al\resultado_real.json resultados
```

Para añadir geometría municipal después de integrar Work 1:

```powershell
node scripts/enrich_work1_result.mjs ruta\al\resultado_real.json resultado_con_mapa.json
node scripts/build_results.mjs resultado_con_mapa.json resultados
```

El comando falla si faltan fuentes, referencias o traza. Antes de subir resultados al portal, comprobar que `data_mode` es `real`, abrir los HTML sin red y revisar etiquetas, unidades, periodo, escenarios y ausencia de marca sintética. El fixture actual solo permite probar la interfaz y el contrato.

## Compatibilidad y fallos

- **Work 1 sin métrica de distancia geométrica:** no transformarla en km. Cambiar el adaptador y etiquetas a la métrica real; revisar fórmula y prueba. Si solo hay servicios por 10.000 mayores, presentar esa tasa con su denominador.
- **Periodos distintos:** mostrarlos por fuente y explicar por qué se comparan; si la mezcla induce a error, retirar la comparación.
- **Unidad ausente o sin fuente:** bloquear generación del resultado real y pedir salida corregida.
- **Tool no ejecutada o sin `output_ref`:** bloquear entrega como demostración de agente; usar la prueba fija anterior solo si es verificable y declarada.
- **Dato ausente:** representarlo explícitamente; no convertirlo a cero. El contrato v1 requiere filas completas para la comparación inicial, así que excluir la fila con explicación o ampliar el schema.
- **Mapa real sin geometría:** usar tabla y barras con etiqueta territorial; no atribuir geometría al mapa abstracto.
- **Falla HTML en portal:** conservar informe autocontenido y adjuntarlo como material; la versión del agente sigue siendo requisito independiente.

## Prueba E2E final que falta

Registrar una pregunta y el identificador de versión fija; observar llamada y argumentos de la tool; verificar que leyó un archivo preparado con referencia al original; conservar salida estructurada; generar HTML; comprobar una cifra a mano y cada `source_id`. La prueba local incluida comprueba la continuidad del contrato con fixture, no suplanta este recorrido real.
