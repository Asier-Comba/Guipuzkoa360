# Evidencia de la ejecución final

Candidato: 84e95167bfb9718ebb5f26b533f12cd885901e20.
Rama: final/gipuzkoa360-integration. Runtime: 195b4980fa5998b096c308296a55e452380b0371.

El harness se ejecutó una sola vez con --output-dir analisis/final para preservar los informes
originales. Resultados: 72.673 checks, cero fallos, 136,949 s totales.
Después se corrigió únicamente la explicación editorial del Medium en los tres informes:
decía 88 afectados, pero el control dirigido demostró 66 afectados de 88 analizados.
Cifras, distribuciones, checks y timestamps de ejecución no se recalcularon ni alteraron.
El harness ahora genera esa explicación desde summary.affected_rows y total_result_rows.

La errata se sustenta en ../payload_decision.json y scripts/release/inspect_payload.py.
El escenario pequeño no acredita el extremo en portal. Medium sigue abierto.
Las latencias citadas de portal son históricas, no tiempos del cálculo local.
