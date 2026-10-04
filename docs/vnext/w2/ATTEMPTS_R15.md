# R15 — intentos, entorno y alcance de cada resultado

Este registro evita ocultar intentos fallidos del arnés o transferir resultados
de un build intermedio al candidato final. No es evidencia conversacional.

## Reproducciones antes del parche

La reproducción de periodos, whitespace, parámetros de acción y umbral se
publicó antes de aplicar validación en
[Issue16](https://github.com/Asier-Comba/Guipuzkoa360/issues/16#issuecomment-5927721280).
Los valores observados y controles previos están en
`R15_PERIOD_REPRODUCTION.md` y `R15_ADVERSARIAL_REPRODUCTION.md`.
Un intento inicial del arnés leyó `effective_request=None` como un objeto;
ese fallo del lector no se contabilizó como excepción del producto. Corregido
el lector, se observaron los envelopes de error seguros y los defectos
numéricos reproducibles documentados.

## Intérprete y focales source

- El launcher `py -3.12` apuntaba al ejecutable de Microsoft Store y falló
  con acceso denegado antes de ejecutar pytest: cero pruebas ejecutadas.
- El intérprete CPython 3.12.14 del runtime de Codex funcionaba, pero el
  primer `-m pytest` no encontró pytest: cero pruebas ejecutadas.
- Se reutilizó el site-packages Python312 ya instalado mediante PYTHONPATH;
  no se instalaron dependencias nuevas. Primer focal source: 56 PASS
  (45 R15 + 11 históricos R14). Hubo solo avisos de escritura en la caché
  global de pytest, sin fallos de tests; posteriormente se desactivó esa caché.
- Tras los últimos refinamientos de metadata y del contrato público, el focal
  sobre código final terminó con **183 PASS en 16.60 s**: 127 en
  `test_r15_period.py`, 45 en `test_r15_public_contract.py` y 11 en
  `test_r14_binding.py`. Los 56 anteriores no son 56 casos adicionales.

## Focales de paquete generado

Selección inicial:

```text
tests/vnext_agent/test_package.py
tests/vnext_agent/test_health_r10.py
tests/vnext_agent/test_r12_generated.py
```

Opciones: `-q -o addopts= -p no:cacheprovider --tb=short`.
El primer intento tuvo **11 errores de setup por PermissionError** al usar
el directorio global existente de pytest. No se etiquetan como defectos del
producto; tampoco se ocultan ni convierten ese intento en PASS.

Con `--basetemp=work/r15-focal-01`, esa selección terminó con **12 PASS en
157.32 s**. Fue un build intermedio anterior al refinamiento final de metadata
(prefijo de hash e0ae…), no el ZIP final f937…; por tanto no acredita por sí
solo esos doce casos contra el candidato canónico. La suite completa final
es la que debe volver a cubrirlos sin reutilizar ese PASS.

## Tests nuevos de artifact R15

En `test_r15_artifact.py` hubo dos aserciones incorrectas del test durante
su autoría: el fixture usado tenía hora 09:45 mientras se esperaba el resultado
09:30; y se supuso una clave `request` anidada en un envelope que proyecta
los argumentos de forma plana. Se corrigieron **solo las expectativas/inputs
del test**: fijar explícitamente la hora probada y leer la forma real del
envelope. No se cambió producto para que cumpliera esas aserciones.

Después, **2 PASS en 4.36 s** sobre el ZIP canónico
`f937ed8124ba1107c78d2a516c5404626a97b9efe38b576a03b6cd98f781efd0`.
Incluyen doble build byte-idéntico de ZIP/manifest, inventario/diff por miembro,
contrato público generado, casos de oráculo, rechazo de opcionales públicos,
legacy/batch internos conservados y recuperación tras error.

## Auditoría dirigida y cierre

El primer borrador de `verify_r15.py` informó 333 casos, 101 casos de paridad,
7 de oráculo y 231 entradas inválidas, sin findings. Es un intento previo de
la auditoría, no una segunda muestra sumable. El resultado autoritativo final
es exclusivamente `R15_AUDIT.json`, con su propio hash del script y ZIP,
denominadores y dos procesos fríos. Rerun final: **PASS**, 333 casos, 101 paridad
raw/vista, 7 oracle, 231 inválidos, 42 periodos, 17 fuentes; 331 ejecuciones R14
y 326 R15, cero findings en 86.969 s. Sockets denegados y cero llamadas al modelo.
SHA-256 del reporte: `3a5bde7c5bbcc49920214f540f446e87eb728a7902d3bb37a19b567ded076578`;
script: `7f4a8bcfa44680e25a8a0ebe053cd2848eb3b7582785153df21321ca33e91324`.
El ZIP final se reconstruyó dos veces de nuevo, byte-idéntico, antes del run
completo local. No se suma el borrador del audit a la muestra final.

Python completo local: **552 PASS en 169.25 s**, una única ejecución completa,
sin failures, errors ni skips. Incluye las doce pruebas generadas contra el
artefacto final; no se suman conteos de focales. Node: **17/17 PASS**, tres
comprobaciones de sintaxis PASS. v4: 14/14 archivos protegidos byte-idénticos
antes/después; jury PASS, artifact 7/7 PASS y diff check PASS. CI exacto se
registra en el handoff final del PR, sin atribuirle todavía un PASS.
CI de Ubuntu/Windows ejecuta sus propios gates; no es otra ejecución local
oculta ni se suma al denominador local. R14 y sus hashes permanecen intactos.

No se enviaron prompts a Studio, no se abrió holdout y no se consumió presupuesto
de portal: 5/12 histórico, 7 restantes. El High real no está cerrado por estos
intentos offline.
