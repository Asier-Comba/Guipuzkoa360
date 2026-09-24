"""Reproduce la prueba privada v3 del portal; no es la entrada final del agente.

Studio no registró las tools cuando procedían solo del ZIP ni cuando estaban en
tools.py del agente privado. Declarar la tool en main.py permitió ejecutarla,
pero una llamada con parámetros válidos quedó en curso más de dos minutos.
Ver docs/PORTAL_PRIVATE_TEST_2026-09-24.md.
"""

from pathlib import Path
import sys
import tempfile
import zipfile
from studio import tool


AGENT_NAME = "GIPUZKOA 360 · integración jurado"
STUDIO_MAX_ITERATIONS = 8
STUDIO_MEMORY_ENABLED = True
STUDIO_INTERNET_ENABLED = False
STUDIO_CONTEXT_FILES = ["gipuzkoa360-portal.zip"]


def _core():
    archive = Path(__file__).resolve().parents[2] / STUDIO_CONTEXT_FILES[0]
    runtime = Path(tempfile.mkdtemp(prefix="gipuzkoa360-runtime-"))
    with zipfile.ZipFile(archive) as package:
        package.extractall(runtime)
    sys.path.insert(0, str(runtime))
    from agentes.gipuzkoa360 import tools as core

    return core


@tool
def analizar_coincidencia(
    categoria_servicio: str,
    grupo_edad: str = "65",
    umbral_km: float = 1.0,
    periodo: str | None = None,
    cuantil: float = 0.75,
) -> str:
    """Cruza envejecimiento y distancia mostrando ambos componentes."""
    core = _core()
    return core._safe(lambda: core._analysis().coincidencia(
        categoria_servicio, grupo_edad, umbral_km, periodo, cuantil,
    ))


def build_agent(model):
    _core()
    from agentes.gipuzkoa360.main import SYSTEM_PROMPT
    from langchain.agents import create_agent

    return create_agent(
        model=model,
        tools=[analizar_coincidencia],
        system_prompt=SYSTEM_PROMPT,
    )
