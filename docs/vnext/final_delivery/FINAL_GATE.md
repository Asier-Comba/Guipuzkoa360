# Gate vigente R16 — borrador privado; no publicar

R16_AUTHOR_DELTA_CHECK=PASS. No es una aceptación independiente del autor.
R16_FINAL_CANDIDATE=FAIL según el protocolo completo real: M1–M4 PASS; M5 FAIL por un primer periodo vacío, recuperado sin repetir la llamada. REAL_CRITICAL=0, REAL_HIGH=0, REAL_MEDIUM=1, REAL_LOW=2. H-01 cerrado en dos sesiones limpias. No se abre otra ronda ni se cambia runtime para cosmética.

Runtime probado: d4dd2e65434c6c7f9f33c74ef1041b0f136cde69. ZIP 374af43fa6ce58b513a10477fc216215c7472f54bd28eada4fc0908da6f3dd6c; manifiesto a46415845f86c5c22ad648965b45e5bd109c839e9cb6cc14daee0ef37d7f788e. Un commit documental posterior no crea otro candidato runtime: su SHA/CI final se fija en PR21 conservando esos mismos bytes.

Versión privada: agentv_f4ca979c0c5b415da187711e96ba2c4d, GIPUZKOA 360 · Visita sanitaria · v2. Cinco mensajes R16 consumidos (5/5), separados del histórico R15 12/12. Sin más prompts. Internet desactivado, memoria activa, modelo visible openai:gpt-5.6-luna, nueve herramientas, cinco campos públicos de plan_visit. main/tools y quince assets descargados desde UI: 17/17 hashes coinciden. El portal incluye su archivo de ejecución generado, no importado ni registrado como herramienta; no se afirma identidad byte a byte entre la carpeta completa del portal y el ZIP.

CI del SHA probado: [36892707817](https://github.com/Asier-Comba/Guipuzkoa360/actions/runs/36892707817), Ubuntu 668/668 y Windows 668/668; Node 17/17; parity 333/333; oráculo 7/7; identity 14/14; jury/artifacts PASS. Fast CI [36892707797](https://github.com/Asier-Comba/Guipuzkoa360/actions/runs/36892707797). La suite local completa se ejecutó una vez: 667 PASS y un timeout histórico; solo ese test se repitió y pasó. No se borra el primer resultado ni se llama a ese recorrido «668 PASS en una sola ejecución local».

DELIVERY_CONTENT_COMPLETE=YES: copy humano completo, sin placeholders públicos. Borrador guardado con v2, conversación A de tres turnos y solo demo territorial + repositorio; sin archivos históricos seleccionados. Resumen actualizado y vista previa revisada. El portal conserva «sin evaluar»: revisión/selección de contenido no equivale a evaluación oficial de plataforma.

TECHNICAL_RELEASE_READY=NO: el protocolo completo no está verde; falta decisión humana sobre el Medium recuperado y los Low documentados, además de la revisión independiente del delta. PORTAL_REAL_AGENT=FAIL (criterio estricto), no fallo de las cifras principales ni del motor. HOLDOUT=SEALED_NOT_EXECUTED, no abierto/reconstruido; no es requisito oficial de publicación.

TRACK=PENDING_HUMAN_SELECTION. PUBLICATION=PENDING_HUMAN_GATE. RELEASE_GO=NO.

NEXT_EXACT_ACTION=Revisión coordinadora del delta y decisión humana explícita sobre el Medium recuperado de Aduna; después revisión final de la vista previa, elección de track y confirmación/publicación exclusivamente humanas.

## Checklist de jurado, sin puntuación inventada

- Utilidad (25 %): destinatarios y pregunta sobre tiempo completo de visita; alcance territorial y sanitario diferenciados.
- Análisis/fuentes/trazabilidad (25 %): 10.691/8.591 s contrastados, componentes, fuentes/periodos; atribución OSM y conflicto de dirección conservados.
- Agente/herramientas (25 %): conversación A real muestra capacidades, dos plan_visit y resultados observados. El error recuperado de Aduna se registra aparte, no se selecciona como demostración sin errores.
- Claridad (15 %): título, pregunta, explicación y defensa humana; sin hashes, nombres internos ni fallos históricos en copy público.
- Fiabilidad/límites (10 %): no realtime, domicilio, entrada verificada, capacidad/citas, causalidad, predicción ni mejor hora. Segunda revisión sin contradicción de duración; sí primer periodo vacío M5 y límites de metadata/explicación.

## Histórico superseded: gate documental importado de R15

El texto siguiente es procedencia, no estado vigente. Sus presupuestos, acciones pendientes y referencias al «último» agente eran los de ese documento histórico. R16 no convierte retrospectivamente intentos R14/R15 en PASS.

# Histórico: Gate final — borrador, no publicar

Estado global: RELEASE_GO=NO. Auditoría offline no cierra el High real del agente.

1. W2 prepara R15 desde R14: `plan_visit` público con solo `origin_id`, `destination_id`, `date`, `appointment_time` y `duration_minutes`; opcionales y comparación batch permanecen únicamente en el motor interno. La comparación pública requiere llamadas individuales, observar cada resultado y comparar solo salidas válidas. No convertir basura en defaults del productor ni atribuir al modelo un schema completo que no se observó. Identidad y validación offline exactas en FINAL_MANIFEST.json y handoff R15. La siguiente acción tras congelar R15 es aceptación independiente W1 de esos mismos bytes; después Hugo/W3 hace el retest real acotado.
2. Operador W3 prueba principal, variación, duración, fuentes, límite y sesión limpia en versión privada exacta. Mantener el presupuesto histórico en 5/12 usados, 7 restantes hasta nuevos mensajes reales; W2 R15 no consume ninguno. No enviar más prompts al candidato actualmente fallido. Registrar tool, args, output, final e intervalos; cero Critical/High reales antes del holdout. Eliminar un deadline offline no es reparación demostrada del LLM.
3. Con candidato congelado y gate real verde, custodio W3 confirma corpus privado de 12 casos SHA-256 `4dda59721932f620cba53e5686df288f7cf0e0e968ec30540216ffb1f52ec5c0`, sin mostrarlo a autores. W1 no tiene el archivo montado, no puede acreditar físicamente su custodia; hash histórico declarado, contenido no leído.
4. **Holdout una sola ejecución:** usar runner/validador/criterios del commit W3 `f4fd0a3c79ff2827c19a1200c0c76f7c5815eab7` y hashes de holdout_seal.json. Antes de abrir, fijar candidato/configuración/ensamblado/modelo/corpus/criterios y crear registro exclusivo `HOLDOUT_STARTED` (no sobrescribible). Capturar cada caso en sesión nueva con contexto previsto; guardar trazas y fallos, sin retries de usuario ni adaptación del esperado. Usar `scripts/vnext_product/score_runs.py` para puntuar las trazas, no como runner de generación LLM. Un aborto cuenta como intento consumido y exige decisión humana, no reinicio silencioso. No mezclar 48 desarrollo+12 holdout con 60 turnos de conversación ni con tools offline. Objetivo 57/60 y críticos correctos es criterio del proyecto, no requisito oficial.
5. Revisar selección pública: identidad exacta del equipo, principal/variación/límite reales y cifra contrastada. Demo/HTML opcionales no son prueba del agente. No anunciar que una llamada pública acepta un batch de 2–4 visitas. Una comparación por llamadas individuales solo cuenta como demostración conversacional cuando existan outputs reales válidos y respuesta fundada. Excluir HTML/PADI originales con derecho específico no verificado; conservar referencias y derivados explícitos. Revisar atribución OSM/ODbL.
6. Agente: **PENDING_FINAL_AGENT_GREEN**. Track: **PENDING_HUMAN_SELECTION**. Confirmación/publicación: **PENDING_HUMAN_GATE**. No reemplazar por supuestos. Solo humanos revisan vista previa y deciden publicar; esta ronda no cambia el portal.

## Reconciliación única

- W1 R14 PASS y CIs verdes acreditan límites offline, no portal. M04 histórico permanece fallido en su versión; M05 demuestra campos planos pero falla por un opcional vacío. No hay cierre retrospectivo del High.
- W3 readiness conserva CI del evaluador anterior `9a49672`/36765616561; el CI más reciente verificado del HEAD `f4fd0a3` es **36774476469 SUCCESS**, sin borrar el registro previo. W1 **4bf9755** CI36770251523 y hotfix **094745b** CI36765784442 siguen separados.
- Último agente real observado R14: Critical0, High1; Medium3 = fuentes/derivación pendientes + sandbox separado + comparación sanitaria pública anunciada sin interfaz lista. Los dos primeros son hallazgos W3; el tercero se confirmó estáticamente en prompt/catálogo frente a firmas públicas. R15 reconcilia su contrato público offline; esto no borra R14 ni cierra retrospectivamente sus hallazgos. High1/Medium3 permanecen OPEN para aceptación real hasta el retest correspondiente. No implica fallo matemático de comparación interna.
- W1 históricos Medium3: grafo explicativo DERIVED circular; reproducción raw+derivado sanitario; términos específicos HTML/PADI no verificados. No sumarlos como nuevos fallos del agente ni ocultarlos.
- Corpus protocol R2 es criterio interno provisional; guía oficial archivada 29/09/2026 exige agente funcional, principal/variación/límite y cifra comprobada. No exige vídeo, RAG, multiagente, 57/60 ni HTML. No se presume estado vivo de campos del portal a partir de capturas históricas.
- Nombres antiguos/versiones, R13/R14 y capturas se conservan como evidencia histórica por SHA, no como nombres públicos propuestos. No renombrar versión ni tocar v4 en esta auditoría.

## Procedencia y revisión técnica R15

Estos cuatro documentos se importan de PR19, commit exacto `3a8e2b0948bb06df87af7a0f5769a369da568eff`, de la rama W1 `audit/final-delivery-w1`. Esa auditoría partía de `4bf975511ecea46c25662becfccb65713d381aa0`; no es la base del runtime R15. La rama nueva W2 `work/vnext-w2-r15-final-agent` parte del runtime R14 `094745b26bc57aee5cc1a5e003401743d96a914f`.

Revisión documental acotada: se conservan copy, cifras offline 10.691/8.591 s y diferencia condicional −35 min, fuentes, periodos, límites, licencias y gates humanos. Solo se actualizan el contrato público de cinco campos, comparación mediante llamadas individuales (entre orígenes, solo lado a lado sin delta), periodos permitidos según selector o fuente, acceso al método de derivación ya existente, separación del motor interno y procedencia histórica R14 frente a identidad R15. FINAL_MANIFEST.json conserva los reportes de PR19 explícitamente como históricos; no les transfiere un PASS a R15. Hugo revisará después el producto/copy.

Fuentes leídas completas: los cuatro documentos de PR19; `docs/vnext/w3/HANDOFF_R14.md`, `resultados/vnext/r14/M05.json`, `M05_normalized.json` y `SERVED_INTERFACE_R14.json` en `f4fd0a3c79ff2827c19a1200c0c76f7c5815eab7`. La traza original y la normalizada concuerdan: tres payloads iguales con `return_deadline=""`, dos errores de dominio, un error de sandbox y final sin cifra. Solo se observaron diez nombres planos de parámetros R14; el schema completo servido sigue NOT_OBSERVED.

La identidad, comprobaciones y CI del nuevo candidato se publican en su handoff exacto y FINAL_MANIFEST.json. Ninguna comprobación offline sustituye aceptación W1 ni retest de Hugo. STOP después del handoff: sin Studio, Entrega, track, holdout, merge, nuevas features ni cambio de v4.
