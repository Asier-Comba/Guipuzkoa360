# R24: NO_GO — parada en la primera prueba real

Runtime probado: `7d1d2da3a88c5f8880bf228dd4ae70855bff3866`. Base exacta R23: `6e960e873972b06fbd9e5125e7a498eef61c6d3a`.
ZIP `bfba5c253ced6edff365f42d72c1f53aebbf7e82c7a5a8de90e51611fbfe824e`, 244208 bytes; manifiesto `ddb3f4bd53be3c595a669832abc3bad179e4449564503fd8c2fd33cc45891b47`.

CI exacto antes de Studio: [rápido 37118525514](https://github.com/Asier-Comba/Guipuzkoa360/actions/runs/37118525514) y [R24 37118525519](https://github.com/Asier-Comba/Guipuzkoa360/actions/runs/37118525519), Ubuntu y Windows PASS. Ambos logs de R24 verifican checkout, hashes, 864 Python, 17 Node, 901 raw, 7 oracle, 5000 fuzz, identity antes/después, jury/artifacts y build reproducible. Cero findings offline. No se transfirió CI R23.

Nueva versión privada: `agentv_2f4548f8eec54336ade99904daf9686b`, nombre GIPUZKOA 360, v1, carpeta `agentes/gipuzkoa_360_6`. Main/tools descargados desde el portal tras guardar y comparados por SHA-256; 15 context assets descargados y verificados uno a uno. Diez tools en preparación y catálogo realmente servido, memoria activa, Internet desactivado. Main/prompt idénticos a R23. El módulo de ejecución añadido automáticamente por Studio no es una tool pública ni fue editado.

## Primera pregunta, sin adaptar el protocolo

«Desde Zegama quiero ir al Ambulatorio de Beasain el 29/09/2026, con cita a las 09:30 y consulta de 20 minutos, y volver a las paradas. ¿Cuánto tiempo completo ocupa y qué límites tiene?»

Llamadas reales:

1. `consultar_capacidades({})`
2. `plan_visit({"origin_id":"zegama_center_stops","destination_id":"beasain_official_centre_anchor","date":"2026-09-29","appointment_time":"09:30","duration_minutes":20})`

Output válido, total 10691 s = 2 h 58 min 11 s; presencia inicial 08:09:37, regreso 11:07:48; `journey_scope` identifica anchor intermedio y endpoint de regreso. El antiguo R23-H01 no se reprodujo en esta ejecución. **Eso no acredita aceptación completa.**

## Nuevo R24-H01: desglose narrado incompatible

| Concepto | Herramienta observada | Respuesta final |
|---|---|---|
| Espera inicial | 180 s / 3 min | 3 min, fila separada |
| Espera antes de consulta | 2572 s / 42 min 52 s | «Esperas y margen previo a la cita: 45 min 52 s» |
| Espera para regreso | 1430 s / 23 min 50 s | No separada; supuestamente incluida en fila siguiente |
| Vehículo de regreso | 2278 s / 37 min 58 s | «Espera y regreso en autobús: 38 min 28 s» |
| Espera + vehículo de regreso | 3708 s / 1 h 1 min 48 s | 2308 s / 38 min 28 s |

Las siete duraciones publicadas suman **9471 s (2 h 37 min 51 s)**, no 10691 s. Descuadre **1220 s (20 min 20 s)**. La primera espera agrupada incluye aparentemente los 180 s iniciales y vuelve a publicarlos por separado; la agrupación de regreso no coincide con ningún desglose compatible observado. Dos afirmaciones numéricas materiales no fundamentadas, agrupadas en un único finding High por incongruencia del desglose. No defecto del motor, no fallo de datos ni de transporte.

Literal de respuesta, argumentos, catálogo, output completo y observaciones: `outputs/r24/portal/real-acceptance.json`; captura `outputs/r24/portal/health-failure.png`; snapshot expandido `health-expanded.txt`. No reconstrucción desde un ensayo local.

Latencias: a 28746 ms la pantalla seguía trabajando sin tool visible; a 65534 ms se observaron llamadas, resultados y respuesta ya finalizada. Intervalo observado (28,746–65,534 s), límite superior 65,534 s para herramienta/output/final. No telemetría del servidor ni marcas exactas de cada fase; no se inventan tiempos precisos.

## Parada aplicada

1 mensaje: 0 PASS, 1 FAIL. Critical 0 / High 1 / Medium 0 / Low 0. Unsupported material claims 2. Health scope PASS acotado; health global FAIL; claim grounding FAIL. Follow-up 09:45, sources y familias restantes NOT_RUN_STOP. No otra pregunta, versión, parche ni R25; no cambios de Entrega ni presentación tras el fallo.

R24 versus fallback v4: R24 conserva motor correcto y scope corregido, pero la explicación real no es aceptable para cerrar con High=0. Fallback v4 territorial permanece byte-idéntico y tiene evidencia histórica de su propio alcance; **no se declara capaz ni validado para la visita sanitaria nueva**, ni se selecciona automáticamente. Una decisión humana es necesaria antes de cambiar alcance o autorizar otra intervención.

## Estado de Entrega tras STOP

Releída desde portal: BORRADOR PRIVADO; versión histórica v3 `agentv_64c72bcb772143968038a2f620944bf1` sigue seleccionada; conversación histórica no sustituida; PPT original permanece seleccionado, no aprobado; HTML antiguo no seleccionado; Servicios intacto; 3/3 confirmados; checkbox final sin marcar; Publicar deshabilitado. No se publica el fallo ni se selecciona R24 en Entrega.

PPT: ocho slides renderizadas/revisadas; contiene afirmaciones de tiempo real, origen desde casa y un ejemplo sin respaldo con final en Beasain. FACT/PUBLIC_LANGUAGE FAIL; no conversión ni sustitución después del STOP. Detalle por slide en R24_MATERIALS_BASELINE.md. HTML encontrado TERRITORIAL_ONLY, no nuevo soporte sanitario; Pages y repositorio abiertos y verificados en su alcance territorial histórico. Preview final y coherencia global no aprobados.

**FINAL_PROJECT_STATE=NO_GO; AGENT_ENGINEERING_COMPLETE=NO; DELIVERY_CONTENT_COMPLETE=NO; READY_FOR_HUMAN_FINAL_GATE=NO.** Main y v4 intactos; confirmación/publicación pendientes del humano. PR29 permanece draft. No merge.
