# Contrato de despliegue observado · R10

Observación en vivo el **30/09/2026**, cuenta participante Hugo, workspace
GIPUZKOA 360. Solo lectura de Agentes, ayuda de Python, Datos, ayuda de Datos
y panel inicial de preparación de versión. No comprobación de preparación,
subida, edición, creación de versión, prueba, reset o publicación.

| Observación | Demuestra | Pendiente |
|---|---|---|
| Ayuda Python: entrada normalmente `main.py`, `build_agent(model)` síncrono; `create_agent` recibe modelo/tools/system_prompt; plataforma proporciona modelo. | Entrada contractual documentada. | Identidad/configuración del modelo y funcionamiento del paquete W2. |
| `STUDIO_CONTEXT_FILES` declara rutas desde raíz; ayuda menciona `tools.py` y `ejecucion.py`. | Contexto con rutas y existencia documentada de un módulo adicional. | Cierre transitivo de imports: que todos los módulos del ZIP W2 se incluyan y sean importables al crear versión. |
| Datos muestra carpetas anidadas, scripts Python y ZIP como archivo almacenado; destino de subida es carpeta de workspace. | Workspace admite archivos y carpetas; subir un ZIP no prueba su extracción automática como runtime. | Formato de importación de un agente completo, política de ejecución de `.py` adicional y resolución de rutas relativas. |
| Ayuda Datos: subida hasta **100 MB por archivo**, paquete de ejecución del agente **24 MB en total**. | Límite runtime publicado ahora; sustituye la incertidumbre R3. | MB decimal/binario y base comprimida/descomprimida no precisadas. Los 100 MB no son el límite runtime. |
| Ayuda Python: nombre 2–80, instrucciones 10–8.000, hasta 10 tools. | Límites publicados. | Dependencias disponibles/versiones exactas y presupuesto. |
| Borrador genérico visible: memoria True, Internet False, 8 iteraciones. | Configuración de ese borrador. | Semántica de historial real y aislamiento de sesiones del candidato W2. |
| Panel de versión: fija copia de código/datos; primero comprobar preparación, después crear y conversar en Pruebas. | Flujo documentado de congelación/versionado. | Fingerprint por bytes y miembros efectivamente empaquetados; requiere smoke autorizado. |

**PORTAL_DEPLOYMENT_CONTRACT_VERIFIED=PARTIAL_READ_ONLY**. La ayuda no limita
el runtime expresamente a dos editores, pero tampoco prueba que un ZIP local
con subpaquetes se pueda cargar directamente. W2 debe declarar un modo de
despliegue concreto y su cierre de archivos. La extracción local solo acepta
el formato local, no el portal. No se invocó el botón de comprobación para
resolver estas dudas porque implica ejecución y no está autorizado en R10.
