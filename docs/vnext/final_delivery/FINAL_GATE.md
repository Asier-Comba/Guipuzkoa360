# Gate final — borrador, no publicar

Estado global: RELEASE_GO=NO. Auditoría offline no cierra el High real del agente.

1. Ingeniería del agente revisa generación de opcionales usando M05 y schema servido; no convertir basura en defaults del productor. Esta es la **única siguiente acción**. Nuevo candidato → nuevo SHA/ZIP/manifiesto → aceptación independiente antes de portal.
2. Operador W3 prueba principal, variación, duración, fuentes, límite y sesión limpia en versión privada exacta. Mantener 5/12 usados, 7 restantes. No enviar más prompts al candidato actualmente fallido. Registrar tool, args, output, final e intervalos; cero Critical/High reales antes del holdout. Eliminar un deadline offline no es reparación demostrada del LLM.
3. Con candidato congelado y gate real verde, custodio W3 confirma corpus privado de 12 casos SHA-256 `4dda59721932f620cba53e5686df288f7cf0e0e968ec30540216ffb1f52ec5c0`, sin mostrarlo a autores. W1 no tiene el archivo montado, no puede acreditar físicamente su custodia; hash histórico declarado, contenido no leído.
4. **Holdout una sola ejecución:** usar runner/validador/criterios del commit W3 `f4fd0a3c79ff2827c19a1200c0c76f7c5815eab7` y hashes de holdout_seal.json. Antes de abrir, fijar candidato/configuración/ensamblado/modelo/corpus/criterios y crear registro exclusivo `HOLDOUT_STARTED` (no sobrescribible). Capturar cada caso en sesión nueva con contexto previsto; guardar trazas y fallos, sin retries de usuario ni adaptación del esperado. Usar `scripts/vnext_product/score_runs.py` para puntuar las trazas, no como runner de generación LLM. Un aborto cuenta como intento consumido y exige decisión humana, no reinicio silencioso. No mezclar 48 desarrollo+12 holdout con 60 turnos de conversación ni con tools offline. Objetivo 57/60 y críticos correctos es criterio del proyecto, no requisito oficial.
5. Revisar selección pública: identidad exacta del equipo, principal/variación/límite reales y cifra contrastada. Demo/HTML opcionales no son prueba del agente. No anunciar comparación pública de 2–4 visitas. Excluir HTML/PADI originales con derecho específico no verificado; conservar referencias y derivados explícitos. Revisar atribución OSM/ODbL.
6. Agente: **PENDING_FINAL_AGENT_GREEN**. Track: **PENDING_HUMAN_SELECTION**. Confirmación/publicación: **PENDING_HUMAN_GATE**. No reemplazar por supuestos. Solo humanos revisan vista previa y deciden publicar; esta ronda no cambia el portal.

## Reconciliación única

- W1 R14 PASS y CIs verdes acreditan límites offline, no portal. M04 histórico permanece fallido en su versión; M05 demuestra campos planos pero falla por un opcional vacío. No hay cierre retrospectivo del High.
- W3 readiness conserva CI del evaluador anterior `9a49672`/36765616561; el CI más reciente verificado del HEAD `f4fd0a3` es **36774476469 SUCCESS**, sin borrar el registro previo. W1 **4bf9755** CI36770251523 y hotfix **094745b** CI36765784442 siguen separados.
- Current agent: Critical0, High1; Medium3 = fuentes/derivación pendientes + sandbox separado + comparación sanitaria pública anunciada sin interfaz lista. Los dos primeros son hallazgos W3; el tercero se confirma estáticamente en prompt/catálogo frente a firmas públicas. No implica fallo matemático de comparación interna.
- W1 históricos Medium3: grafo explicativo DERIVED circular; reproducción raw+derivado sanitario; términos específicos HTML/PADI no verificados. No sumarlos como nuevos fallos del agente ni ocultarlos.
- Corpus protocol R2 es criterio interno provisional; guía oficial archivada 29/09/2026 exige agente funcional, principal/variación/límite y cifra comprobada. No exige vídeo, RAG, multiagente, 57/60 ni HTML. No se presume estado vivo de campos del portal a partir de capturas históricas.
- Nombres antiguos/versiones, R13/R14 y capturas se conservan como evidencia histórica por SHA, no como nombres públicos propuestos. No renombrar versión ni tocar v4 en esta auditoría.

## Handoff de esta ronda

BASE_SHA=4bf975511ecea46c25662becfccb65713d381aa0; rama audit/final-delivery-w1. HEAD y CI exactos se publican en checkpoint PR15/PR18/Issue16 (evita autorreferencia del hash). Solo scripts/tests de auditoría, resultados/vnext/final_benchmark y estos cuatro documentos; productor/runtime/datos/v4/main/ramas ajenas intactos. Tests completos, Node, identity antes/después, jury/artifact, diff y doble reconstrucción se registran en ese checkpoint con denominadores separados. Después STOP, sin nuevas features ni publicación.
