from __future__ import annotations

import sys
import types

import main


def test_build_agent_uses_platform_model_and_seven_tools(monkeypatch):
    captured = {}

    def create_agent(**kwargs):
        captured.update(kwargs)
        return "AGENT"

    langchain = types.ModuleType("langchain")
    agents = types.ModuleType("langchain.agents")
    agents.create_agent = create_agent
    langchain.agents = agents
    monkeypatch.setitem(sys.modules, "langchain", langchain)
    monkeypatch.setitem(sys.modules, "langchain.agents", agents)

    model = object()
    assert main.build_agent(model) == "AGENT"
    assert captured["model"] is model
    assert len(captured["tools"]) == 7
    assert captured["system_prompt"] == main.SYSTEM_PROMPT
