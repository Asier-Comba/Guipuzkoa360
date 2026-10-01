# R15: reproducciones adversariales previas al parche

Ámbito: frontera pública y validación W2 del runtime R14
`094745b26bc57aee5cc1a5e003401743d96a914f`, rama de trabajo R15 creada
desde esa identidad. Reproducciones locales deterministas, sin Studio, sin LLM
y sin acceso al holdout. No son una aceptación independiente W1 ni un retest
real de Hugo. Este registro se escribe antes de corregir estos hallazgos.

## A. Identificador hipotético compuesto solo por espacios

Reproducción mínima:

```python
import json
from agentes.gipuzkoa360_vnext import main

result = json.loads(main.simular_escenario(
    accion="add_service",
    categoria_servicio="primary_care",
    latitud=43,
    longitud=-2,
    service_id="   ",
))
print(result["status"], len(result["claims"]), result["error"])
```

Observado R14: `valid 40 None`. La evidencia interna tiene `raw_result_json`
con `status="ok"` y `scenario.changed_parameters.service_id="   "`.
El identificador vacío semánticamente se acepta y permite claims numéricos.

Causa: `_validate_arguments` comprueba `bool(v)` para strings y `bool(x)`
para elementos de arrays, lo que admite strings con solo whitespace.

Esperado seguro: error controlado de argumentos antes de ejecutar el motor;
`claims=[]`, `outcomes=[]`, `raw_result_json=None`. Rechazar, no recortar ni
convertir el valor a `None`, ni fabricar un identificador alternativo.
La misma comprobación de string no vacío semánticamente debe cubrir los
elementos de `municipios`. En R14 `municipios=["   "]` ya termina sin claims,
pero como `unverified_result`/`unknown`, no como valor de entrada inválido.

## B. Parámetros explícitos de otra acción se ignoran silenciosamente

Reproducción mínima:

```python
result = json.loads(main.simular_escenario(
    accion="change_threshold",
    categoria_servicio="primary_care",
    nuevo_umbral_km=2,
    latitud=43,
    longitud=-2,
))
print(result["status"], len(result["claims"]), result["error"])
```

Observado R14: `valid 40 None`. `effective_request.parameters` conserva
`latitud=43` y `longitud=-2`, pero `scenario.changed_parameters` contiene solo
`action="change_threshold"`, `threshold_km=1.0`, `new_threshold_km=2.0`.
Ambas coordenadas explícitas son descartadas por la semántica del motor.
El mismo resultado ocurre con `latitud=999`, `longitud=-999`: al no pertenecer
a la acción seleccionada ni siquiera se evalúan sus límites geográficos.

Esperado seguro: la frontera W2 rechaza combinaciones explícitas contradictorias,
con error controlado de argumentos, `claims=[]`, `outcomes=[]` y sin raw válido.
No reinterpretar una acción como otra ni relajar el backend.

Grupos de argumentos condicionales derivados de las ramas existentes del motor:

| Acción | Obligatorios de la acción | Opcionales de la acción | No aplicables si no son `None` |
| --- | --- | --- | --- |
| `add_service` | `latitud`, `longitud` | `service_id` | `nuevo_umbral_km` |
| `remove_service` | `service_id` | ninguno | `latitud`, `longitud`, `nuevo_umbral_km` |
| `change_threshold` | `nuevo_umbral_km` | ninguno | `latitud`, `longitud`, `service_id` |

Los argumentos comunes `accion`, `categoria_servicio`, `umbral_km`, `periodo`
no cambian de semántica. `None`/omisión en campos no aplicables siguen siendo
ausencia legítima. Los límites, unidades, cálculo y datos del motor permanecen
intactos. La validación propuesta solo exige coherencia entre la acción
seleccionada y los parámetros explícitos.

## C. Umbral explícito fuera de contrato en comparación sin servicios

Reproducciones mínimas:

```python
for threshold in (0, None):
    result = json.loads(main.comparar_municipios(
        municipios=["Beasain", "Ordizia"], umbral_km=threshold,
    ))
    print(threshold, result["status"], len(result["claims"]), result["error"])
```

Observado R14: ambas llamadas devuelven `valid`, cuatro claims, `error=None`.
Al no pedirse categoría de servicio, el motor compara demografía e ignora el
umbral. El parámetro público está anotado `float` (no nullable); el motor ya
define para un umbral usado el intervalo `0 < threshold_km <= 100`. La misma
entrada no debe ser inválida con categoría y válida sin ella.

Esperado seguro: rechazar el umbral explícito `0` o `None` como argumento fuera
del contrato antes de ejecutar; sin claims, outcomes ni raw válido. El default
legítimo `1.0` y las magnitudes admitidas conservan su comportamiento. Aplicar
los límites existentes del motor no implica nuevos límites ni nuevos cálculos.

## Barrido focal de ocho firmas

Se ejecutaron 210 mutaciones deterministas (cada parámetro de las ocho tools
territoriales/metadata con `""`, whitespace, objeto, lista, booleano, `None` y
`0`) contra el módulo previo al parche de validación, SHA-256 de `tools.py`
`fbc259b390e020d9b1a9c7676889fbb2bf7eb353ff9e82b3ad3100df6d9a142b`.
No escaparon excepciones del producto y ningún resultado de error incluyó
claims u outcomes. Los valores aceptados inesperados correspondieron a los
casos descritos aquí y a los periodos whitespace documentados por separado en
`R15_PERIOD_REPRODUCTION.md`. Se mantuvieron como válidos los `None` legítimos
de periodo, selección municipal y metadata; no son strings explícitos inválidos.

## Controles negativos observados

En estas llamadas R14 ya devuelve error controlado, cero claims y cero outcomes:
`municipios` como prosa, array vacío, edad como entero en vez de string,
umbral booleano o cero, coordenadas como strings, `top_n=True` y `medida=[]`.
Los duplicados municipales fallan cerrados como `contract_violation` y los
identificadores no encontrados no se convierten en cifras. Estos controles no
justifican hacer el motor más permisivo ni nuevas restricciones arbitrarias.

No se contabilizan como excepciones del producto errores del arnés de lectura:
un primer intento de resumir `effective_request=None` falló en el propio arnés;
se corrigió y se repitieron los controles, observando los errores controlados
del producto descritos aquí.
