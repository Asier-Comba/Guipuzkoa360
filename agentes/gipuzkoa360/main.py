"""Entrada compatible con el agente Python del portal."""

from typing import Any, Callable

try:
    from studio import tool
except ImportError:
    def tool(function: Callable[..., Any]) -> Callable[..., Any]:
        return function

try:
    from .tools import (
        execute_analizar_acceso_servicios,
        execute_analizar_coincidencia,
        execute_analizar_envejecimiento,
        execute_comparar_municipios,
        execute_consultar_fuente,
        execute_obtener_resumen_territorial,
        execute_simular_escenario,
    )
except ImportError:
    from tools import (
        execute_analizar_acceso_servicios,
        execute_analizar_coincidencia,
        execute_analizar_envejecimiento,
        execute_comparar_municipios,
        execute_consultar_fuente,
        execute_obtener_resumen_territorial,
        execute_simular_escenario,
    )

AGENT_NAME = "GIPUZKOA 360"
STUDIO_MAX_ITERATIONS = 8
STUDIO_MEMORY_ENABLED = True
STUDIO_INTERNET_ENABLED = False
STUDIO_CONTEXT_FILES = [
    "FUENTES.md",
    "docs/METODOLOGIA.md",
    "docs/RESULT_SCHEMA.md",
    "datos_preparados/municipios.csv",
    "datos_preparados/demografia.csv",
    "datos_preparados/runtime_municipality_points.csv",
    "datos_preparados/runtime_servicios.csv",
    "datos_preparados/metadata_sources.json",
    "datos_preparados/data_contract.json",
    "datos_preparados/runtime_manifest.json",
]

SYSTEM_PROMPT = """Eres GIPUZKOA 360, un agente de investigación territorial para personal técnico.
Interpreta primero la intención y conserva el contexto de seguimientos como «repítelo para 75+». Selecciona
la herramienta determinista mínima apropiada y usa su resultado real antes de responder. No inventes cifras,
fuentes ni hechos. Usa siempre una
herramienta antes de afirmar cualquier cifra, ranking, distancia, filtro, comparación o fuente; nunca calcules
de memoria ni completes valores ausentes. Si una herramienta devuelve error o ausencia, explica exactamente
qué falta y qué opciones admite.

En cada cifra indica unidad, periodo, criterio y source_id cuando estén disponibles. Separa explícitamente:
OBSERVACIÓN (fila de fuente), CÁLCULO (transformación reproducible), SIMULACIÓN (recalculo contrafactual) e
HIPÓTESIS (supuesto no observado). Si se comparan periodos distintos, enuméralos y advierte que no son una
fotografía temporal homogénea.

Reglas inviolables: «0 servicios registrados dentro del municipio» no significa «no existe atención
sanitaria»; distancia geométrica no significa accesibilidad real ni tiempo de viaje; un registro de centro no
acredita capacidad, disponibilidad, citas, horario, calidad ni accesibilidad universal; coincidencia o
correlación no demuestra causalidad. No conviertas indicadores territoriales en afirmaciones sobre personas.

No llames repetidamente a la misma herramienta con los mismos argumentos: corrige la petición o reconoce el
límite. Para una consulta normal usa 1-3 herramientas. Responde de forma accesible y breve con Hallazgo,
Evidencia, Método, Fuentes y Límite cuando proceda. Para comparaciones identifica cada municipio y no mezcles
denominadores. Para escenarios etiqueta el resultado como ESCENARIO HIPOTÉTICO y contrástalo con la base.
Si la consulta queda fuera de demografía, servicios territoriales, coincidencias, comparaciones, fuentes o
escenarios soportados, dilo claramente y no llames herramientas irrelevantes. Nunca presentes fixtures TEST_*
como datos reales de Gipuzkoa."""


@tool
def obtener_resumen_territorial(municipio: str, periodo: str | None = None) -> str:
    """Resume demografía y servicios de un municipio; no interpreta ausencia como cero."""
    return execute_obtener_resumen_territorial(municipio, periodo)


@tool
def comparar_municipios(
    municipios: list[str],
    grupo_edad: str = "65",
    categoria_servicio: str | None = None,
    umbral_km: float = 1.0,
    periodo: str | None = None,
) -> str:
    """Compara 2-20 municipios; acepta nombres naturales de edad y servicio."""
    return execute_comparar_municipios(municipios, grupo_edad, categoria_servicio, umbral_km, periodo)


@tool
def analizar_envejecimiento(
    grupo_edad: str = "65", medida: str = "percentage", periodo: str | None = None, top_n: int = 10
) -> str:
    """Calcula ranking de población 65+ o 75+ por porcentaje o recuento."""
    return execute_analizar_envejecimiento(grupo_edad, medida, periodo, top_n)


@tool
def analizar_acceso_servicios(
    categoria_servicio: str,
    umbral_km: float = 1.0,
    periodo: str | None = None,
    municipios: list[str] | None = None,
) -> str:
    """Calcula distancia euclídea EPSG:25830; acepta categorías en lenguaje natural."""
    return execute_analizar_acceso_servicios(categoria_servicio, umbral_km, periodo, municipios)


@tool
def analizar_coincidencia(
    categoria_servicio: str,
    grupo_edad: str = "65",
    umbral_km: float = 1.0,
    periodo: str | None = None,
    cuantil: float = 0.75,
) -> str:
    """Cruza envejecimiento y distancia y devuelve una salida compacta con todos los destacados."""
    return execute_analizar_coincidencia(categoria_servicio, grupo_edad, umbral_km, periodo, cuantil)


@tool
def simular_escenario(
    accion: str,
    categoria_servicio: str,
    umbral_km: float = 1.0,
    periodo: str | None = None,
    latitud: float | None = None,
    longitud: float | None = None,
    service_id: str | None = None,
    nuevo_umbral_km: float | None = None,
) -> str:
    """Recalcula un contrafactual y devuelve solo municipios afectados; acepta acciones naturales."""
    return execute_simular_escenario(
        accion, categoria_servicio, umbral_km, periodo, latitud, longitud, service_id, nuevo_umbral_km
    )


@tool
def consultar_fuente(source_id: str | None = None) -> str:
    """Devuelve procedencia, periodo, institución, unidad, licencia y limitaciones."""
    return execute_consultar_fuente(source_id)


TOOLS = [
    obtener_resumen_territorial,
    comparar_municipios,
    analizar_envejecimiento,
    analizar_acceso_servicios,
    analizar_coincidencia,
    simular_escenario,
    consultar_fuente,
]


def build_agent(model):
    """La plataforma proporciona el modelo; el equipo define herramientas e instrucciones."""
    from langchain.agents import create_agent

    return create_agent(model=model, tools=TOOLS, system_prompt=SYSTEM_PROMPT)
