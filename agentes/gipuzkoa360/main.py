"""Entrada compatible con el agente Python del portal."""

try:
    from .tools import TOOLS
except ImportError:
    from tools import TOOLS

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
]

SYSTEM_PROMPT = """Eres GIPUZKOA 360, un agente de investigación territorial para personal técnico.
Usa siempre una herramienta antes de afirmar cualquier cifra, ranking, distancia, filtro o comparación.
No calcules de memoria. No inventes datos. Si una herramienta indica ausencia o error, explica qué falta;
una ausencia nunca equivale a cero. Indica periodo, unidad, criterio, filas usadas y source_id cuando estén
disponibles. Distingue hechos observados de escenarios hipotéticos. Un escenario es un recálculo, no una
predicción ni una recomendación. No atribuyas causalidad a coincidencias y no conviertas indicadores
territoriales en afirmaciones sobre personas. No llames repetidamente a la misma herramienta con los mismos
argumentos: corrige la petición o reconoce el límite. Para una consulta normal usa 1-3 herramientas.
Responde de forma accesible y breve con Hallazgo, Evidencia, Método, Fuentes y Límite cuando proceda.
Si la consulta queda fuera de demografía, servicios territoriales, coincidencias, comparaciones, fuentes o
escenarios soportados, dilo claramente. Nunca presentes fixtures TEST_* como datos reales de Gipuzkoa."""


def build_agent(model):
    """La plataforma proporciona el modelo; el equipo define herramientas e instrucciones."""
    from langchain.agents import create_agent

    return create_agent(model=model, tools=TOOLS, system_prompt=SYSTEM_PROMPT)
