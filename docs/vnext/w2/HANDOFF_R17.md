# R17 — cierre mínimo de interfaz pública

Base exacta: c859a26396838d59a52b8d91f1eda5ef6b69e4cd.
ZIP base: 374af43fa6ce58b513a10477fc216215c7472f54bd28eada4fc0908da6f3dd6c.
Manifest base: a46415845f86c5c22ad648965b45e5bd109c839e9cb6cc14daee0ef37d7f788e.
Rama hotfix/r17-final-public-schema; PR draft contra R16, no main.

## Delta y no-delta

El ZIP se deriva directamente del blob Git fijado, no del checkout mutable.
Solo main.py/tools.py cambian. Los otros 23 miembros, quince assets, ZIP W1,
datos/fuentes, GTFS/paseo/routing, fórmulas y v4 permanecen byte-idénticos.
La implementación R16 de time_summary se conserva literalmente.

Las 88 filas demográficas tienen una única referencia: 2025-01-01.
obtener_resumen_territorial público solo acepta municipio: str y envía ese único
campo al motor, que resuelve su periodo. La capacidad anunciada muestra el
periodo como información, no como argumento. No hay coerción de vacío a None.

Las otras cinco herramientas conservan sus firmas: comparación/envejecimiento/
coincidencia seleccionan demografía; acceso/simulación admiten referencias de
servicios/geografía distintas, no una foto temporal homogénea ni serie histórica.
No se aprovecha esta ronda para simplificar otros contratos ya probados.

La proyección pública oculta metadata técnica redundante y humaniza únicamente
frases de procedencia identificadas. Raw, evidencia original y assets conservan
su trazabilidad completa. Los source_id históricos W1_*/W2_* se conservan como
claves, no se renombran ni se confunden con títulos/instituciones públicos.

Derivación 75+: scripts/data/01_download_sources.py selecciona los años <=1949,
incluida la categoría anterior; 03_prepare_demography.py suma por municipio y
sexo total y calcula porcentaje con tres decimales. La metadata original lo
confirma. La nueva vista explica la regla y su límite: datos agregados por año,
sin cumpleaños individuales; no identifica nacidos el propio 01/01/1950.
No cambia population_75_plus ni se inventa una edad individual exacta.

## Gates reproducibles

Usar CPython 3.12.14 canónico local (CI 3.12.10 ya compatible), requirements.txt.
No usar 3.12.4: el formateo AST del generador histórico puede cambiar bytes.

```text
python -m scripts.vnext_agent.build_r17
python -m pytest -q tests/vnext_agent/test_r17_public_schema.py -o addopts= -p no:cacheprovider
python -m scripts.vnext_agent.verify_r17 --output work/r17-audit.json
python -m pytest -q -o addopts= -p no:cacheprovider --junitxml=work/r17-pytest.xml
node --test tests/e2e/contract_flow.test.mjs
python scripts/ops/verify_runtime_identity.py
python scripts/benchmark/verify_jury_results.py --output work/r17-jury.json
python scripts/release/verify_final_artifacts.py
python -m scripts.vnext_agent.build_r17
git diff --check
```

Checkpoint temprano: 13 focales PASS. Full y CI aún pendientes aquí; no se
atribuyen resultados R16 al nuevo SHA. Auditoría acotada: matrix publicada,
paridad raw y claims, siete oráculos, tiempo R16, nueve firmas/capacidades,
metadata humana. No fuzz gigante, productor 20k, modelo ni holdout.

Primer intento de auditoría/focal conservado en outputs/r17/attempts: detectó
frases W1/W2 residuales en method/assumptions/coverage, sin cambio matemático
(335/335 raw iguales). Se corrigieron solo esas etiquetas antes de Studio.
Focal inicial: 12 PASS/1 FAIL; focal corregido: 13 PASS. No borrar el intento.

## Prueba real y entrega, aún no autorizadas por el checkpoint

Solo después de commit/push y CI exactos verdes: NUEVA versión privada, nunca
editar v2 agentv_f4ca979c0c5b415da187711e96ba2c4d. main/tools y quince assets
deben descargarse y coincidir con el manifiesto. Nueve tools, plan_visit cinco
campos, resumen un campo, memoria ON e Internet OFF. Máximo cuatro mensajes:
Aduna en A vacía; principal y variación en B vacía; límite/cobertura en C vacía.
STOP-on-High y STOP-on-Medium reproducible. Presupuestos anteriores preservados.

Solo si real C0/H0/M0: copy público en voz del equipo, seleccionar versión y
conversación sanitaria limpias, guardar borrador y revisar preview completo.
Track, confirmación y publicación exclusivamente humanas. No merge ni R18.
HOLDOUT=SEALED_NOT_EXECUTED. RELEASE_GO=NO.

## Cierre posterior al checkpoint inicial

Runtime probado 77ac63d5b68a3ecbf51461e3aaa0de0566d6f2c3; PR22 draft contra R16.
ZIP 1b263724110c68efab69c14e479f50ed2d101f935c6c83102bb0e5d4c699dc79,
231758 bytes; manifest246f703e1e1881fe984598fe7b428b1b18380c43e7555c03fca2b53dd1982fee.
Solo main/tools cambian frente al ZIP R16; ningún cambio posterior a Studio.
Una suite completa local681/681 en304,04s; Node17, identity14 antes/después,
jury/artifacts/diff PASS. CI runtime36928182340 Ubuntu/Windows cada uno681,
Node17,335parity,7oracle,41time summaries,build reproducible,gates PASS.
Fast36928182347 SUCCESS. No transferencia de resultados al SHA documental:
el cierre final y sus runs exactos se fijan en PR22 después del push.

Nueva versión privada agentv_64c72bcb772143968038a2f620944bf1, Visita sanitaria v3:
preparación válida, nueve tools, resumen1campo, plan5campos, memoriaON/InternetOFF.
main/tools+15assets descargados por UI tras crear versión:17/17 exactos.
No se afirma exportación ZIP de la versión congelada ni identidad de toda la carpeta.
Cuatro mensajes reales4/4: Aduna36/507/7,101% a la primera con municipio solo,
regla<=1949 explícita; main10691s; variación8591s y35minmenos condicionales;
límites/cobertura rechaza casa/realtime/mejor hora/citas, admite3orígenes.
Critical0/High0/Medium0/Low1: IDs técnicos/anglicismo en respuesta M4, solo estilo.
La selección pública es B sanitaria2turnos, no M4. v2 no se modifica.

FINAL_EVIDENCE/FINAL_GATE/FINAL_MANIFEST distinguen R17 vigente y R16 histórico,
sin borrar aquel Medium recuperado. DELIVERY_COPY en voz del equipo y texto
literal guardado en Entrega. Capturas y outputs originales en outputs/r17/portal.
FichaGipuzkoa., utilidad88municipios+visita; equipo3/3 y nombres completos;
v3 seleccionada, solo demo territorial etiquetada honestamente+repositorio,
0archivos seleccionados, preview completa y segunda revisión sin contradicción.
Connection Error genérico y etiquetas Respuesta vacías/Markdown literal de
preview conservados como observaciones de UI, no atribuibles a fallo matemático.
Una lectura de status ambigua se corrigió por consulta de todos los status;
no se reenvió prompt ni se alteró evidencia.

DELIVERY_CONTENT_COMPLETE=YES; R17_FINAL_CANDIDATE=PASS para este protocolo
acotado, no evaluación oficial ni aceptación independiente del autor.
TRACK=PENDING_HUMAN_SELECTION; FINAL_CONFIRMATION=PENDING_HUMAN;
PUBLICATION=PENDING_HUMAN; HOLDOUT=SEALED_NOT_EXECUTED; RELEASE_GO=NO.
NEXT_EXACT_ACTION=Human chooses preferred track, performs final preview, checks the publication acknowledgement and clicks Publicar entrega.
STOP: sin R18, features, merges ni publicación automática.
