# Solicitud preparada de prueba privada · no ejecutada

**Estado:** `BLOCKED` para escritura; esta hoja no constituye autorización.
La entrega pública continúa con v4. Ninguna versión W2 R3 con movilidad
sanitaria y paquete conjunto W1+W2 está fijada todavía.

## Identidades necesarias antes de pedir el gate humano

| Pieza | Identidad conocida | Condición previa |
|---|---|---|
| W1 R2 | `c68eb5c55dec72a267b7435b4c364049f6eab408`, contrato `ir_y_volver` 0.1.0, snapshot `30fc9d638f3576ae0e1084ee1e0c7b0268469bffc8af1dd15fd12430019d968b` | Confirmar si W1 R3 añade destino sanitario y walking validado. |
| W2 R2 | `f4615b36d0af93966e6ca0f2044288841e6574b8`, evidencia/capability 1.0.0, ZIP `1992cc739e8e89cd4512ad45919d1ebc102a6385628f82689a23de49de6f2661` | El paquete publicado aún no expone movilidad. No usarlo como candidato sanitario combinado. |
| Candidato conjunto | `PENDING` HEAD/merge ref/ZIP/manifiesto | Fijar todos los hashes de código, datos, contratos y ZIP; verificar sin modificar v4. |

Nombre reservado propuesto: `GIPUZKOA 360 vNext R3 · prueba privada · <SHA corto>`.
El nombre no sustituye el `version_id` ni los hashes del paquete. Archivos:
`main.py`, `tools.py`, contextos y datos **exactos del manifiesto candidato**;
sin carga manual de piezas W1/W2 no incluidas. Verificar miembros, hashes y
bytes comprimidos/descomprimidos antes de subir.

## Límites observados y no observados

La [lectura del portal](PORTAL_LIMITS_EVIDENCE_R3.md) confirma hasta 10 tools,
instrucciones 10–8.000 caracteres y `AGENT_NAME` 2–80. El límite de 100 MB
observado corresponde solo a materiales opcionales de Entrega. Los 24 MiB de
W2 son un gate del builder local. Límite real del paquete agente, contexto,
tiempo, tokens y presupuesto de pruebas: **no verificados**. Revalidar antes
de autorizar consumo.

## Preflight y primer lote propuesto

1. Revisar SHA del HEAD conjunto, ZIP, manifiesto, contracts y fuentes;
   confirmar `PRODUCT_HEALTH_GO` y compatibilidad del descriptor W1.
2. Pedir autorización humana específica para **crear una versión privada
   separada** y **ejecutar inicialmente 12 pruebas de humo** en Pruebas;
   nunca cambiar Entrega, track ni v4. Delimitar presupuesto antes de usarlo.
3. Preparación del agente en esa versión; si falla importación/contexto, parar
   sin ejecutar preguntas. Guardar `version_id`, nombre y fingerprint visible.
4. Lote de 12 casos de desarrollo: cuatro territoriales/seguimiento, cuatro
   visita/comparación, cuatro errores/límites. No usar holdout. Cada intento
   guarda pregunta, historial real, versión, paquete, datos, llamadas,
   argumentos, resultados, respuesta, tiempos y evidencia privada conforme a
   [TRACE_CONTRACT_R3](TRACE_CONTRACT_R3.md).
5. Un fallo Critical/High de verdad o ejecución detiene el lote afectado; se
   entrega reproducción a su propietario. Reintentos se conservan. Solo tras
   smoke correcto y nueva revisión de coste/permiso se plantea el corpus
   pareado 60+20 y holdout posterior al freeze.

La versión privada se conserva para auditoría. Si hay que corregir paquete,
se genera otro SHA y otra versión; las pruebas afectadas quedan vinculadas a
la anterior. Recuperación: seleccionar el `version_id` anterior en Pruebas
para lectura, sin alterar Entrega. `PORTAL_MUTATIONS=0` al redactar este plan.
