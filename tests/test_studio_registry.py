from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PORTAL = ROOT / "agentes" / "gipuzkoa360" / "portal"
EXPECTED = [
    "obtener_resumen_territorial",
    "comparar_municipios",
    "analizar_envejecimiento",
    "analizar_acceso_servicios",
    "analizar_coincidencia",
    "simular_escenario",
    "consultar_fuente",
]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_studio_safe_registry_uses_exact_local_objects(monkeypatch):
    class LocalTool:
        def __init__(self, function):
            self.function = function
            self.name = function.__name__

        def invoke(self, arguments):
            return self.function(**arguments)

    studio = types.ModuleType("studio")
    studio.tool = LocalTool
    monkeypatch.setitem(sys.modules, "studio", studio)
    monkeypatch.syspath_prepend(str(PORTAL))
    portal_tools = _load("tools", PORTAL / "tools.py")
    portal_main = _load("portal_main_registry_test", PORTAL / "main.py")

    assert [item.name for item in portal_main.TOOLS] == EXPECTED
    assert len({id(item) for item in portal_main.TOOLS}) == 7
    assert all(item.function.__module__ == "portal_main_registry_test" for item in portal_main.TOOLS)

    captured = {}
    agents = types.ModuleType("langchain.agents")
    agents.create_agent = lambda **kwargs: captured.update(kwargs) or "AGENT"
    langchain = types.ModuleType("langchain")
    langchain.agents = agents
    monkeypatch.setitem(sys.modules, "langchain", langchain)
    monkeypatch.setitem(sys.modules, "langchain.agents", agents)
    model = object()
    assert portal_main.build_agent(model) == "AGENT"
    assert captured["tools"] is portal_main.TOOLS
    assert all(captured["tools"][index] is portal_main.TOOLS[index] for index in range(7))

    monkeypatch.setenv("GIPUZKOA360_DATA_DIR", str(ROOT / "datos_preparados"))
    calls = [
        {"municipio": "Aduna", "periodo": "2025-01-01"},
        {"municipios": ["Tolosa", "Beasain"], "categoria_servicio": "primary care", "periodo": "2025-01-01"},
        {"grupo_edad": "≥75", "periodo": "2025-01-01"},
        {"categoria_servicio": "salud mental", "periodo": "2025-01-01", "municipios": ["Eibar"]},
        {"categoria_servicio": "atención primaria", "grupo_edad": "65+", "periodo": "2025-01-01"},
        {
            "accion": "cambiar umbral",
            "categoria_servicio": "primary_care",
            "periodo": "2025-01-01",
            "nuevo_umbral_km": 2.0,
        },
        {"source_id": "EUSTAT_EMH_2025"},
    ]
    results = [json.loads(item.invoke(arguments)) for item, arguments in zip(portal_main.TOOLS, calls)]
    assert all(result["status"] == "ok" for result in results)
    assert results[4]["filters"]["service_category"] == "primary_care"
