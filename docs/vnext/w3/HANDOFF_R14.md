# W3 R14 — corrección lista; aceptación independiente pendiente

PORTAL_BINDING_HOTFIX_READY. READY_FOR_FEEDBACK=NO. RELEASE_GO=NO.

## Identidad

- W3 base: 46657c9fc966052dce8b5de75959f8c68282cfb4.
- Hotfix separado: hotfix/r14-portal-binding, 094745b26bc57aee5cc1a5e003401743d96a914f.
- Base runtime exacta: 8c94f8c3cf9d732c4ce94af7b4bef8f6e154c243.
- ZIP: 9c6fa5c692df178afe36366c6291e7c0e7c3da06134381b09d853f55d6707252.
- Manifest: d6c0122b475284c468fdfc3e343b9ab0d9d175cf20513048c915281cedf4e911.
- main.py: bc955c57558ae3f8f00aa6d8ad1452732ad7ead40faea794fa9e0f1e39ee6f23.
- tools.py: 46498d6be4f65642784e3a721e408b7d22a0910f937f91660d095b7e57de807c (byte-idéntico).
- ZIP/manifest nuevos en scripts/vnext_agent/dist/r14 de la rama hotfix.
- Único miembro del paquete cambiado: main.py. Quince assets, productor W1 y nested ZIP intactos. Double-build PASS.
- W1 soporte final: 106879509a667b75baec4860e28a16b9720fdc71; W2 documental: 5e3b43cce61e29693d8b11a01beaeb0e497c97d6.

## Evidencia

Firma: cinco campos requeridos y cinco opcionales planos. None opcional se omite; sin defaults nuevos ni parser. La llamada interna sigue siendo _run("plan_visit", {"request": request}). Nueve tools. Dos reglas genéricas añadidas al prompt, sin respuestas gold.

Paridad completa de public_result (status, effective request, raw hash, claims, mobility, fuentes y límites), con ID de prueba fijo: siete casos truth pack y fixtures de tres orígenes, márgenes, duración, legacy, errores y None. Contraste numérico/semántico contra el truth pack final PASS. 5.000 combinaciones, seed360014, 10.000 ejecuciones direct/wrapper, sin crashes ni fallos de mapping o claims autoritativos en errores. No implica cobertura exhaustiva ni aceptación del LLM.

Hotfix: 378 Python y 17 Node PASS. Evaluador: 321 Python y 37 Node PASS. V4, jury y artifact gates PASS. Tests focales 76 PASS; recorder actualizado 1 PASS adicional tras la suite para evitar regenerar el ZIP histórico. Los tests de comparación continúan llamando al contrato interno: no se expone una interfaz nested al modelo. Los tests incluidos dentro del ZIP son auditoría histórica patch3 preservada; los tests planos actuales viven fuera del paquete.

Intentos previos conservados como incidencias del verificador: assertion demasiado estricta para error con evidencia explicativa, Python3.14 no reproduce ZIP W1, mezcla de numpy3.14/Python3.12 y callers de firma histórica. Corregidos sin tocar datos/math/tools.py. Un recorder antiguo regeneraba artefactos históricos durante tests; ahora usa el constructor R14. Las copias locales generadas por ese test fueron restauradas a sus bytes base exactos.

## Portal y gates

W1_R14_FRONTDOOR_ACCEPTANCE=PENDING. No candidato nuevo cargado. No mensajes nuevos: 4/12 consumidos, 8 restantes. R13 M04 se conserva como HIGH real; el hotfix offline no lo reclasifica. Medium de fuentes/derivación pendiente de retest real. Critical0 / High1 / Medium1. Schema Studio completo NOT_OBSERVED; firma/esquema local esperado no se presenta como schema servido.

El usuario exige PASS independiente W1 sobre SHA y ZIP exactos antes de cargar Studio. Esta es la única dependencia que impide continuar el portal. No corresponde pedir otra autorización al usuario ni consumir mensajes para probar sin W1. Después: nueva versión privada identificable, rehash de dos módulos y quince assets, observar parámetros planos, ejecutar plan congelado M05–M12 y detenerse ante High/Critical. No tocar R13v1, Entrega, track, main, v4 ni holdout.

## Reanudación exacta

1. Leer PR15/Issue16 y comprobar W1_R14_FRONTDOOR_ACCEPTANCE=PASS para esta identidad; fetch y verificar que no hay candidato posterior.
2. Crear una versión privada independiente: GIPUZKOA 360 vNext R14 binding 094745b2.
3. Conservar presupuesto histórico, usar SMOKE_PLAN_R14.json, 14 dimensiones por turno. M05 debe ejecutar productor; M06/M07 requieren nuevas llamadas; M12 sesión nueva real.
4. Actualizar evidencia/producto solo sobre capacidades realmente observadas. No confundir HTML offline con chat conectado.
5. Con 0 Critical/High y gates clave PASS: READY_FOR_FEEDBACK=YES y STOP. Benchmark/holdout/release requieren alcance posterior.

Para W1: ZIP/manifest R14, constructor build_r14_binding.py, verify_r14_binding.py, parity.json, fuzz.json, truth_pack_contrast.json, historical_m04_replay.json y firma esperada. Reproducción: python -m scripts.vnext_agent.verify_r14_binding --oracle docs/vnext/w3/r14/FINAL_ORACLE_R13.json --output resultados/vnext/r14. No necesita credenciales ni red ni framework/modelo. No benchmark completo ejecutado.

## Publicación y CI confirmadas

- Hotfix draft PR18: https://github.com/Asier-Comba/Guipuzkoa360/pull/18 . CI36765784442 SUCCESS, Ubuntu y Windows, exacto094745b26bc57aee5cc1a5e003401743d96a914f.
- Evaluador PR14: CI36765616561 SUCCESS, Ubuntu y Windows, exacto9a49672672388a871874c93f23300283477d9483. El commit posterior solo incorpora este estado documental de publicación/CI.
- Issue16: https://github.com/Asier-Comba/Guipuzkoa360/issues/16#issuecomment-5918172714 . W1 PR15: https://github.com/Asier-Comba/Guipuzkoa360/pull/15#issuecomment-5918173041 . PR14: https://github.com/Asier-Comba/Guipuzkoa360/pull/14#issuecomment-5918173332 .
- Confirmación de último fetch/lectura: no PASS independiente W1 R14 publicado aún. No equivalencia entre CI y aceptación W1/LLM. HOTFIX_SHA/ZIP/manifest no cambian al publicar este cierre del evaluador.
- Trece tests finales package/flat/recorder PASS tras guard de constructor y cambio de recorder. 5.000 combinaciones aleatorias eran errores controlados; no equivalen a viajes válidos. Los 18 probes explícitos cubren respuestas positivas y negativas.
- Reconciliación reproducible adicional: python -m scripts.vnext_agent.reconcile_r14_reports. Constructor requiere CPython3.12; no usar la identidad comprimida3.14 experimental.
