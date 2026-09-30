# Contrato Ir y volver 0.1.0

Interfaz congelada para el primer incremento de W1:

- `get_capabilities() -> dict`
- `plan_visit(request: dict) -> dict`
- `compare_visits(requests: list[dict]) -> dict`

El proveedor solo usa horarios programados y búsqueda directa entre paradas del catálogo. `origin_id` no representa todas las viviendas de un municipio. Solo `status=ok` autoriza un itinerario y un total. `unknown` separa fallos o cobertura incompleta de `no_feasible_journey`, que solo se emite tras una búsqueda completa dentro del alcance declarado.

Los márgenes son restricciones, no componentes adicionales: `components_s` contiene esperas reales y no vuelve a sumar los buffers. Todos los cálculos internos usan segundos.
