"""Structured offline follow-up harness; not a claim of natural-language routing."""

from __future__ import annotations

from uuid import uuid4
from typing import Any, Callable

from . import tools


class CandidateSession:
    def __init__(self, executor: Callable[..., dict[str, Any]] = tools.execute) -> None:
        self.session_id = uuid4().hex
        self.sequence = 0
        self.last_tool: str | None = None
        self.last_arguments: dict[str, Any] = {}
        self.executor = executor

    def ask(self, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if tool == "seguimiento":
            if self.last_tool is None:
                raise tools.ContractViolation("followup_without_previous_request")
            tool = self.last_tool
            arguments = {**self.last_arguments, **arguments}
        self.sequence += 1
        request_id = f"{self.session_id}-{self.sequence}"
        result = self.executor(tool, arguments, request_id)
        if result["status"] == "valid":
            self.last_tool = tool
            self.last_arguments = dict(arguments)
        return result
