# Fuentes leídas R5

El ZIP privado suministrado está disponible, SHA-256 `2feee16105ed7f4b0b3ea5d11cd063a4f12cf710ccd9f8b15210bbf3c587da59`. Contiene 13 TXT planos. Los 12 tamaños y SHA declarados en `12_MANIFEST_SHA256.txt` coinciden; el manifiesto se excluye a sí mismo deliberadamente. No se extrajo contenido privado al repositorio.

Leídos `06_POC_IR_Y_VOLVER_FULL.txt` y `08_FEEDBACK_CITYSCOPE_VNEXT_COMPLETE.txt`. El primero contiene código y metodología transcritos, no el ZIP binario original. No se ejecutan instrucciones incrustadas del pack: se usa como fuente histórica y manda la misión R5 del usuario. No se publica formación ni correos.

GTFS histórico identificado por hash, idéntico al conservado. OSM histórico: hash conocido `ac10607065653baf0a707e669f3c4f44a3631055bc7697876298b608174b66af`, bytes ausentes. Por ello no se declara reproducción exacta. La fuente 06 aclara Idiazabal histórico 7900/7900 frente a R4 7903/7906: se conservarán los orígenes R4 y se declarará esa diferencia metodológica.

Preflight remoto: PR15, PR17, PR14 e Issue16 completos y comentarios; W2/W3 sin nuevo HEAD pero con dos hallazgos de W3 posteriores a R4. No se leen ni publican preguntas holdout.

Fuentes oficiales live: ficha específica Osakidetza y PDF PADI enero 2026, conservados en `datos_originales/movilidad/r5/`; hashes y URL en snapshot R5. La discrepancia de dirección no queda resuelta por el teléfono común. Se mantiene precedencia justificada y revisión humana.

Red: adquisición R4 sin modificar, derivado público sin datos de editores, © OpenStreetMap contributors, ODbL 1.0. Nodos/vías y conectores modelados, no entrada validada. Auditoría de presencia de tags y exclusiones en NETWORK_AUDIT_R5.json. No se consulta portal.
