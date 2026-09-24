# Fuentes de GIPUZKOA 360

Fecha de descarga común: **2026-09-24**. Los códigos `municipality_code` son códigos Eustat/INE de cinco caracteres y se conservan como texto.

## EUSTAT_EMH_2025

- Institución: Eustat — Instituto Vasco de Estadística.
- Recurso: *Población de la C.A. de Euskadi por ámbitos territoriales, grandes grupos de edad cumplida y sexo* y tabla complementaria por año de nacimiento.
- API: `https://www.eustat.eus/bankupx/api/v1/es/DB/PX_010154_cepv1_ep06b.px` y `PX_010154_cepv1_ep10b.px`.
- Operación: Censo de población y viviendas. Estructura de la población (010154).
- Periodo: 2025-01-01. Territorio: 88 municipios de Gipuzkoa.
- Licencia: Creative Commons, según la ficha de la operación.
- Fila original: municipio × grupo de edad (o año de nacimiento) × sexo; consulta limitada a sexo total y periodo 2025-01-01.
- Campos usados: ámbito, grupo de edad/año de nacimiento, población.
- Clave: código municipal obtenido de los metadatos de la misma API, no inferido del nombre.
- Transformación: pivote de `Total` y `>= 65`; suma de nacidos en 1949 o antes para `population_75_plus`.
- Ausencias/eliminaciones: ninguna entre los 88 municipios; sin imputación.
- Limitación: 75+ se deriva por año de nacimiento. En 2025-01-01, usar <=1949 evita incluir a quienes cumplen 75 durante 2025; no incorpora posibles nacimientos del propio 1 de enero de 1950.
- Originales: `datos_originales/eustat_*.csv`, metadatos JSON. Derivados: `demografia.csv`, `municipios.csv`.

## ODE_HEALTH_CENTRES_2026

- Institución: Gobierno Vasco — Departamento de Salud.
- Recurso: *Centros de salud, ambulatorios y hospitales públicos de Euskadi*.
- URL: `https://opendata.euskadi.eus/catalogo/-/centros-de-salud-publicos-en-euskadi/`.
- Periodo/actualización: 2026-09-20; frecuencia semanal.
- Licencia: reutilización abierta conforme a la ficha de Open Data Euskadi. Debe citarse la fuente y fecha y no alterarse ni desnaturalizarse el contenido.
- Fila original: un centro público. Campos usados: código, nombre, tipo, coordenadas WGS84, dirección, municipio y provincia.
- Filtro: `Provincia == Gipuzkoa`; 148 de 528 registros. No se eliminaron registros del filtro por coordenadas ausentes.
- Clave: `Código del centro`; 148 valores únicos.
- CRS: coordenadas WGS84 (EPSG:4326); asignación municipal por unión espacial con los límites.
- Categorías analíticas: `primary_care` (Centro de Salud, Consultorio, Ambulatorio, PAC), `hospital`, `mental_health`, `other_health`.
- Limitación: presencia o conteo no representa capacidad, plazas, citas, calidad, horario efectivo ni accesibilidad universal.
- Original: `centros-salud.xlsx`. Derivados: `servicios.csv`, `runtime_servicios.csv`.

## GEOEUSKADI_MUNICIPIOS_2025

- Institución: Eusko Jaurlaritza / Gobierno Vasco — geoEuskadi.
- Recurso: *Límites Administrativos del País Vasco — Municipios 1:5.000*.
- URL: `https://www.geo.euskadi.eus/limites-administrativos-del-pais-vasco/webgeo00-dataset/es/`.
- Actualización: 2025-05-07.
- Licencia: cualquier uso citando `Eusko Jaurlaritza / Gobierno Vasco`.
- Fila original: entidad territorial poligonal. CRS original y de cálculo: ETRS89 / UTM zona 30N (EPSG:25830).
- Campos: `EUSTAT`, `NOMBRE_TOP`, `TERRITORIO`, geometría.
- Filtros: territorio Gipuzkoa y código presente en el catálogo municipal Eustat. Se excluyen 3 entidades no municipales (Enirio-Aralar y dos parzonerías), documentadas en `analisis/entidades_no_municipales_excluidas.csv`.
- Salida: GeoJSON maestro en EPSG:4326. Runtime simplificado con tolerancia de 25 m aplicada en EPSG:25830, preservando topología.
- Limitación oficial: el catálogo indica que el conjunto no reúne los requisitos para considerarse cartografía oficial conforme a Ley 7/1986 y RD 1545/2007; algunas líneas pueden ser provisionales.

## Trazabilidad derivada

`datos_preparados/metadata_sources.json` replica estos metadatos en formato legible por máquina. `datos_originales/download_manifest.json` contiene tamaño y SHA-256 de cada descarga/consulta. No se han utilizado blogs, prensa ni datos sintéticos en resultados.

