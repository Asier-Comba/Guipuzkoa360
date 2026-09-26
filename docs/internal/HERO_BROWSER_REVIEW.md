# Inspección real de la hero

Fecha: 2026-09-25. Archivo: `resultados/demo.html`, servido localmente con `python -m http.server`.
Se reutilizó el estilo visual existente. No se modificó el runtime.

- Carga en navegador: sin errores visibles; título, controles, fuentes y escenario legibles.
- Selección 65+/q0,75/2 km: siete nombres canónicos, cortes 23,9730 % y 2.019,2 m; 88 contornos.
- Click 75+/q0,80/3 km: cuatro nombres canónicos, cortes 12,9796 % y 2.138,6 m; 88 contornos y cuatro resaltados.
- Click 65+/q0,85/2 km: Legazpi y Hondarribia; cortes 25,3557 % y 2.308,7 m; dos resaltados.
- Regreso al primer caso: se recuperan sus valores, sin contaminación del seguimiento.
- Selección por Enter de Aduna: muestra 14,793 % y 2.756,2 m del caso 65+.
- Captura inspeccionada: mapa con los 88 contornos oficiales, norte arriba, siete áreas destacadas, tabla
  legible y límite de interpretación. La proyección de pantalla corrige longitud por cos(43°), sin
  utilizarse para calcular distancias.
- Escenario visible: 2.756,2→0,0 m, diferencia −2.756,2 m, 148→149 registros sanitarios totales.
- Etiqueta persistente: resultados guardados, no conversación en vivo.

El gate numérico compara además todo el JSON incrustado y sus geometrías con un recálculo del core y
rechaza nueve corrupciones. La inspección cubre el tamaño de escritorio observado; no se afirma una
matriz exhaustiva de navegadores o dispositivos.
