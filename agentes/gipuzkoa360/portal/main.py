"""Entrada compatible con el agente Python del portal."""

from typing import Any, Callable

try:
    from studio import tool
except ImportError:  # Permite comprobar el contrato fuera de Studio.
    def tool(function: Callable[..., Any]) -> Callable[..., Any]:
        return function

import tools as core

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
Interpreta la intención y usa el resultado real de la herramienta determinista mínima. No inventes cifras,
fuentes ni hechos, no calcules de memoria y no completes valores ausentes.

Selección de herramienta:
- No describas el proceso antes de ejecutar la herramienta.
- Si una consulta puede resolverse con una herramienta, no llames una segunda. No repitas una llamada con los
  mismos argumentos. El resumen compacto contiene la evidencia necesaria: no solicites el payload completo.
- Conserva el contexto de seguimientos. Si el usuario cambia un parámetro —por ejemplo «ahora para 75+»—,
  recalcula con la herramienta adecuada; no reutilices cifras anteriores.
- Usa una herramienta antes de afirmar cualquier cifra, ranking, distancia, filtro, comparación o fuente. Si
  devuelve error o ausencia, explica qué falta y qué valores admite.

Respuesta:
- Empieza por el hallazgo o la respuesta directa. En una consulta normal escribe unas 100-180 palabras, salvo
  que el usuario pida detalle.
- Muestra 2-5 cifras relevantes, con unidad y criterio; no vuelques ni repitas campos del JSON que no ayuden.
- Explica brevemente el cálculo, cita source_id y periodo, y termina con el límite realmente importante.
- Distingue OBSERVACIÓN, CÁLCULO, SIMULACIÓN e HIPÓTESIS solo cuando sea material; evita una plantilla
  burocrática. En comparaciones identifica cada municipio y no mezcles denominadores. En escenarios indica
  ESCENARIO HIPOTÉTICO y contrasta baseline, scenario y differences. En esos resultados, service_count cuenta
  todos los registros sanitarios, no solo los de la categoría elegida.

Límites inviolables: «0 servicios registrados dentro del municipio» no significa «no existe atención
sanitaria»; distancia geométrica no significa accesibilidad real ni tiempo de viaje; un registro no acredita
capacidad, disponibilidad, citas, horario, calidad ni accesibilidad universal; coincidencia o correlación no
demuestra causalidad. No conviertas indicadores territoriales en afirmaciones sobre personas. Si los periodos
de las fuentes difieren, indícalo: no forman una fotografía temporal homogénea. Si la consulta queda fuera de
demografía, servicios territoriales, coincidencias, comparaciones, fuentes o escenarios soportados, dilo y no
llames herramientas irrelevantes. Nunca presentes fixtures TEST_* como datos reales de Gipuzkoa."""


@tool
def obtener_resumen_territorial(municipio: str, periodo: str | None = None) -> str:
    """Resume demografía y servicios de un municipio; no interpreta ausencia como cero."""
    return core.obtener_resumen_territorial(municipio, periodo)


@tool
def comparar_municipios(
    municipios: list[str],
    grupo_edad: str = "65",
    categoria_servicio: str | None = None,
    umbral_km: float = 1.0,
    periodo: str | None = None,
) -> str:
    """Compara 2-20 municipios y opcionalmente su distancia geométrica a servicios."""
    return core.comparar_municipios(
        municipios, grupo_edad, categoria_servicio, umbral_km, periodo
    )


@tool
def analizar_envejecimiento(
    grupo_edad: str = "65",
    medida: str = "percentage",
    periodo: str | None = None,
    top_n: int = 10,
) -> str:
    """Calcula ranking de población >=65 o >=75 por porcentaje o recuento."""
    return core.analizar_envejecimiento(grupo_edad, medida, periodo, top_n)


@tool
def analizar_acceso_servicios(
    categoria_servicio: str,
    umbral_km: float = 1.0,
    periodo: str | None = None,
    municipios: list[str] | None = None,
) -> str:
    """Calcula distancia euclídea EPSG:25830; no representa acceso real."""
    return core.analizar_acceso_servicios(
        categoria_servicio, umbral_km, periodo, municipios
    )


@tool
def analizar_coincidencia(
    categoria_servicio: str,
    grupo_edad: str = "65",
    umbral_km: float = 1.0,
    periodo: str | None = None,
    cuantil: float = 0.75,
) -> str:
    """Cruza envejecimiento y distancia con cortes explícitos y sin inferir causalidad."""
    return core.analizar_coincidencia(
        categoria_servicio, grupo_edad, umbral_km, periodo, cuantil
    )


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
    """Recalcula un contrafactual soportado; no es una predicción ni recomendación."""
    return core.simular_escenario(
        accion,
        categoria_servicio,
        umbral_km,
        periodo,
        latitud,
        longitud,
        service_id,
        nuevo_umbral_km,
    )


@tool
def consultar_fuente(source_id: str | None = None) -> str:
    """Devuelve procedencia, periodo, unidad, licencia y limitaciones documentadas."""
    return core.consultar_fuente(source_id)


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
