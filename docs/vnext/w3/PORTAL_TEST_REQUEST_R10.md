# Solicitud única de prueba privada R10 — borrador bloqueado

**PORTAL_TEST_REQUEST_READY=BLOCKED_IDENTITY_NOT_FIXED.** No se solicita permiso
prematuramente: W2 aún no publicó ZIP integrado sanitario 0.3.1. No hubo uploads,
preparación, versión privada, ejecución, reset ni cambios en Entrega.

Identidades aceptadas **por separado**:

- W1 runtime cb061a97e78d6b5c967104fef6b935132fdc450f, 0.3.1, ZIP
  c66d44af702eb3410fcea05ae8711f537214f675e83a7fda38c39c3b39a1b910.
- W2 8272988566f5bca2d65d3119732bf831d11382dc, ZIP territorial/stop-only 0.2.0
  366cdc7d160ee6743cb125c6709f57e48f6ddfb91ead812a92eb881570233357.
- NO SHA conjunto: no cargar estas dos piezas manualmente como si fueran uno.

Cuando W2 publique paquete fijo y W3 lo pruebe, completar la única solicitud con
SHA exactos de ZIP/manifiesto/W1/W2/datos/catalogo/UI, modo de despliegue y lista
exacta de archivos. Crear versión privada separada `G360 vNext R10 <SHA corto>`;
conservar version_id/fingerprint visible y prueba de pertenencia de archivos.
El nombre no sustituye identidad. Mantener intactos v4 y Entrega.

Alcance autorizado a solicitar: comprobar preparación, crear versión privada,
ejecutar las 12 conversaciones (36 turnos) del SMOKE_PLAN_R10; probes auxiliares
solo si explícitamente incluidos en presupuesto. Presupuesto de tokens/model calls,
modelo/configuración e historial a acordar antes de consumo. No publicación,
track, merge, confirmación de Entrega ni reset del entorno ajeno. Único operador W3.

Preflight ya leído: máximo diez tools, nombre 2–80, instrucciones 10–8.000;
Datos declara 100 MB/archivo y 24 MB/paquete de ejecución. Unidad exacta y base
comprimida/descomprimida sin confirmar: comprobar tamaño de ambos; paquetes
revisados actuales <2 MB expandidos. Rutas desde raíz en STUDIO_CONTEXT_FILES;
workspace admite carpetas/scripts, pero ZIP almacenado no implica extracción
automática o cierre de imports. W2 debe declarar módulos y dependencias ejecutables.
`build_agent(model)` síncrono con modelo proporcionado. Memoria y límites reales
por versión deben observarse; la configuración del borrador no prueba la candidata.

Parar si preparación falla: guardar mensaje exacto/artefacto, sin atribuir HTTP/red
no observados. Parar el lote afectado por Critical/High y preservar todos los intentos.
Nueva identidad invalida pruebas afectadas, exige revisión/nueva versión. No ejecutar
holdout para ajuste. No usar conversaciones de un paquete para aceptar otro.
Estado hasta entonces: PORTAL_LLM NOT_RUN, invocaciones 0, autorización ausente.
