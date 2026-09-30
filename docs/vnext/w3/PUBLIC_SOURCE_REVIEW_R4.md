# Fuentes públicas candidatas · revisión independiente R4

Leídas el 29/09/2026. Los fragmentos `Sx:sección` de abajo son referencias
de revisión humana a secciones de páginas públicas, **no IDs ya indexados por
W2**. No se conservaron bytes completos, por lo que no se asigna un SHA al
contenido web. Antes de ingestión se debe guardar versión y revisar términos
de uso; esta revisión usa solo paráfrasis cortas y enlaces, sin republicar
textos ni datos completos.

| ID | Emisor, título y enlace | Fragmentos gold revisados | Condiciones y alcance |
|---|---|---|---|
| S1 | Gobierno Vasco/Departamento de Salud, [Centros de salud, ambulatorios y hospitales públicos](https://opendata.euskadi.eus/catalogo/-/centros-de-salud-publicos-en-euskadi/) | `S1:Descargar` formatos; `S1:Detalles` emisor, fecha y frecuencia; `S1:Descripción` tipos y campos. Fecha que mostraba la ficha: 27/09/2026; frecuencia semanal. | La ficha enlaza «Información legal» sin licencia concreta transcrita aquí: verificar antes de ingestión. Describe localizaciones, direcciones/contacto/horarios/GPS. No acredita agenda, plazas, médico asignado, accesibilidad real ni que un centro esté abierto ahora. |
| S2 | Gobierno Vasco/Transportes/Movilidad, [Moveuskadi: datos de la red de transporte público](https://opendata.euskadi.eus/catalogo/-/moveuskadi-datos-de-la-red-de-transporte-publico-de-euskadi-operadores-horarios-paradas-calendario-tarifas-etc/) | `S2:Descargar` índice GTFS/GTFS-RT y otros formatos; `S2:Detalles` emisor; `S2:Descripción` alcance, modos y reutilización. | «Información legal» enlazada; licencia exacta no fijada. La ficha ofrece datos estáticos y en tiempo real, pero su mera existencia no demuestra que W1 haya consumido GTFS-RT ni puntualidad de un viaje concreto. |
| S3 | MobilityData, [GTFS Schedule Reference](https://gtfs.org/documentation/schedule/reference/) | `S3:stop_times` secuencia, horario, `pickup_type`, `drop_off_type`, `timepoint`; `S3:calendar_dates` excepciones. | Especificación técnica primaria; términos de reutilización pendientes de revisar antes de copiarla a un corpus. Define semántica de campos, no validez operativa de un feed concreto ni trayectos puerta a puerta. |
| S4 (candidata, sin gold) | Eustat, [tabla PxWeb de población por edad y sexo](https://es.eustat.eus/bankupx/pxweb/es/DB/-/PX_010154_cepv1_ep06b.px) | Ninguno: el acceso directo a esta tabla falló en la lectura R4, aunque el buscador indexa su ficha. | No se asignan preguntas ni cifras gold hasta poder abrir el documento/tabla y fijar un extracto con periodo y condiciones. |

Las referencias S1–S3 respaldan el [gold de 30 preguntas](DOCUMENT_GOLD_R4.json)
como evaluación de comprensión documental **propuesta**. W2 no ha
ingestado estas páginas y no se ejecutó retrieval ni LLM. B0 será fuentes y
metodología actuales; B1 búsqueda textual/base navegable; B2 vectorial solo
si mejora B1 con el mismo corpus. Añadir un documento nuevo no prueba ventaja
de embeddings. Los gates 17/18, 6/6, 6/6 y ≥95 % de claims citados son
propuestas, no resultados ni requisitos oficiales.
