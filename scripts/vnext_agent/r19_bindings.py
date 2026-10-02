"""Build-time replacement functions; only the generated main is shipped."""

@tool
def comparar_municipios(municipios: list[str], grupo_edad: Literal['65', '75'] = '65') -> str:
    """Compara población y proporción del grupo de edad entre 2–20 municipios distintos. Nombres o códigos en lista. Solo la referencia demográfica fija indicada en la salida. Para comparar distancias usa analizar_acceso_servicios con varios municipios; para un cruce, analizar_coincidencia."""
    return _run('comparar_municipios', locals())

@tool
def analizar_envejecimiento(grupo_edad: Literal['65', '75'] = '65', medida: Literal['percentage', 'count'] = 'percentage', top_n: int = 10) -> str:
    """Ordena municipios por porcentaje o recuento del grupo de edad. top_n: entero 1–100. La referencia demográfica es fija y figura en la salida; no selecciona años históricos."""
    return _run('analizar_envejecimiento', locals())

@tool
def analizar_acceso_servicios(categoria_servicio: Literal['primary_care', 'hospital', 'mental_health', 'other_health'], umbral_km: float = 1.0, municipios: list[str] | None = None) -> str:
    """Distancia euclídea en metros desde un punto representativo municipal no ponderado por población al registro sanitario más cercano. umbral_km: >0 y <=100 km, clasifica puntos municipales, no residentes. municipios: lista de nombres/códigos; omitido/null usa todos. Snapshots fijas, con fechas propias en la salida. No mide viaje ni accesibilidad individual ni población cubierta."""
    return _run('analizar_acceso_servicios', locals())

@tool
def analizar_coincidencia(categoria_servicio: Literal['primary_care', 'hospital', 'mental_health', 'other_health'], grupo_edad: Literal['65', '75'] = '65', umbral_km: float = 1.0, cuantil: float = 0.75) -> str:
    """Cruce descriptivo entre proporción municipal de edad y distancia desde punto municipal a registro. umbral_km: >0 y <=100 km; cuantil: nivel de exigencia entre 0.5 y 0.95. Snapshots fijas con fechas distintas. No mide causalidad ni residentes próximos ni cobertura individual."""
    return _run('analizar_coincidencia', locals())

@tool
def simular_escenario(accion: Literal['add_service', 'remove_service', 'change_threshold'], categoria_servicio: Literal['primary_care', 'hospital', 'mental_health', 'other_health'], umbral_km: float = 1.0, latitud: float | None = None, longitud: float | None = None, service_id: str | None = None, nuevo_umbral_km: float | None = None) -> str:
    """Hipótesis, no predicción/recomendación. add_service requiere coordenadas WGS84 latitud/longitud; service_id puede nombrar el registro hipotético. remove_service requiere service_id existente observado en resultados. change_threshold requiere nuevo_umbral_km. Omite/null los campos que no corresponden a la acción. Umbrales >0 y <=100 km. Snapshots fijas, sin elección de fecha. Nunca enviar texto vacío como omisión."""
    return _run('simular_escenario', locals())

@tool
def consultar_fuente(source_id: str) -> str:
    """Procedencia, fecha, método y límites de una fuente. source_id es obligatorio y se obtiene del catálogo o de un resultado real, nunca se inventa ni se pide al usuario. No URL ni prosa ni cadena vacía. Para listado general usa consultar_capacidades sin argumentos."""
    return _run('consultar_fuente', {'source_id': source_id})

@tool
def consultar_capacidades() -> str:
    """Catálogo completo de nueve operaciones, campos públicos, cobertura, fuentes, fechas y límites; incluye opciones de visita. Sin argumentos. No ejecuta análisis ni autoriza inferencias adicionales."""
    return _run('consultar_capacidades', {})
