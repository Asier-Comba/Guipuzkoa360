"""Build-time public action wrappers. No analytical implementation here."""

def _run(name: str, args: dict[str, Any]) -> str:
    try:
        root = evidence._workspace_root()
    except evidence.ContractViolation:
        root = None
    return evidence.public_call(name, args, uuid4().hex, root=root)

@tool
def analizar_acceso_general(categoria_servicio: Literal['primary_care', 'hospital', 'mental_health', 'other_health'], umbral_km: float) -> str:
    """Analiza los 88 puntos municipales: distancia geométrica en metros al registro más cercano y clasificación con umbral >0 y <=100 km. No recibe municipios. No mide población cubierta, viaje ni accesibilidad individual."""
    return _run('analizar_acceso_general', locals())

@tool
def analizar_acceso_municipios(categoria_servicio: Literal['primary_care', 'hospital', 'mental_health', 'other_health'], umbral_km: float, municipios: list[str]) -> str:
    """Analiza municipios concretos: lista obligatoria de 1–88 nombres/códigos resolubles, sin vacíos ni duplicados. Distancia geométrica desde punto municipal, en metros; umbral >0 y <=100 km. Ofrece la identidad observada del registro más cercano para una eventual simulación de retirada. No mide residentes ni tiempo de viaje."""
    return _run('analizar_acceso_municipios', locals())

@tool
def simular_anadir_servicio(categoria_servicio: Literal['primary_care', 'hospital', 'mental_health', 'other_health'], latitud: float, longitud: float, umbral_km: float) -> str:
    """Añade un punto sanitario hipotético en coordenadas WGS84 indicadas por el usuario y compara distancias municipales. Latitud [-90,90], longitud [-180,180], números finitos; umbral >0 y <=100 km. No pide identidad técnica. No predice ni recomienda ubicación, atención ni ahorro real."""
    return _run('simular_anadir_servicio', locals())

@tool
def simular_retirar_servicio(categoria_servicio: Literal['primary_care', 'hospital', 'mental_health', 'other_health'], service_id: str, umbral_km: float) -> str:
    """Retira hipotéticamente un registro existente de la categoría y compara distancias. service_id obligatorio: copiarlo de una salida observada de acceso, nunca inventarlo ni pedir al usuario un código técnico. Umbral >0 y <=100 km. No elimina datos reales; no predice desaparición de atención."""
    return _run('simular_retirar_servicio', locals())

@tool
def simular_cambiar_umbral(categoria_servicio: Literal['primary_care', 'hospital', 'mental_health', 'other_health'], umbral_actual_km: float, nuevo_umbral_km: float) -> str:
    """Compara la clasificación de puntos municipales cambiando exclusivamente el umbral. Ambos umbrales obligatorios, finitos, >0 y <=100 km. Distancias y registros no cambian: no cuenta vecinos cubiertos ni demuestra mejora real de atención."""
    return _run('simular_cambiar_umbral', locals())

@tool
def consultar_capacidades() -> str:
    """Catálogo completo de las doce operaciones públicas, decisiones necesarias, cobertura, fuentes, fechas y límites, incluidas opciones de visita sanitaria. Sin argumentos. No ejecuta análisis ni autoriza inferencias adicionales."""
    return _run('consultar_capacidades', {})

@tool
def comparar_municipios(municipios: list[str], grupo_edad: Literal['65', '75'] = '65') -> str:
    """Compara población y proporción del grupo de edad entre 2–20 municipios resolubles distintos, sin vacíos. Referencia demográfica fija. Para comparar distancias usa analizar_acceso_municipios; para un cruce descriptivo usa analizar_coincidencia."""
    return _run('comparar_municipios', locals())
