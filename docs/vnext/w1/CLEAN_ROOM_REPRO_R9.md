# Clean-room reproduction R9

La reproducción se ejecutó sin red y en un árbol temporal nuevo.

- Snapshot R4 idéntico: `True` (`62e00c04edb96ccde0a5ce4fe81574452ddcacdb4c173b030ca49b000f5a084b`).
- Snapshot sanitario idéntico: `True` (`59fcded9e4236ee094eeb0881c4eb94f521b96fb6c8c89c881c3e9f6d5140901`).
- Claims canónicos idénticos: `True`; delta `-2100 s`.
- Reproducible desde raw fijado + derivados fijados: `true`.
- Reproducible íntegramente desde raw original: `false`.

La reconciliación sanitaria parte de `HEALTH_DESTINATION_R4.json`, un derivado fijado. Los bytes del OSM histórico de la PoC no están disponibles; el OSM del modelo R6 sí está fijado y reproducido. Por tanto no se afirma identidad histórica de la PoC.
