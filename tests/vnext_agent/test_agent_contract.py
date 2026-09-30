"""Structural portal entrypoint test; intentionally not a reasoning acceptance test."""

from __future__ import annotations

import sys
from types import ModuleType

from agentes.gipuzkoa360_vnext import main


def test_build_agent_uses_supplied_model_and_real_tool_set(monkeypatch):
    langchain = ModuleType("langchain")
    agents = ModuleType("langchain.agents")
    calls = []

    def create_agent(*, model, tools, system_prompt):
        calls.append((model, tools, system_prompt))
        return {"model": model, "tools": tools}

    agents.create_agent = create_agent
    monkeypatch.setitem(sys.modules, "langchain", langchain)
    monkeypatch.setitem(sys.modules, "langchain.agents", agents)
    supplied_model = object()
    agent = main.build_agent(supplied_model)
    assert agent["model"] is supplied_model
    assert calls[0][0] is supplied_model
    assert len(calls[0][1]) == len({tool.__name__ for tool in calls[0][1]}) == 9
    assert 2 <= len(main.AGENT_NAME) <= 80
    assert 10 <= len(calls[0][2]) <= 8000
    assert main.STUDIO_INTERNET_ENABLED is False
