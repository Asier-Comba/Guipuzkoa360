"""Contratos de entrada y salida independientes del framework del agente."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class ResultEnvelope:
    status: str = "ok"
    question: str = ""
    filters: dict[str, Any] = field(default_factory=dict)
    period: str | None = None
    metric: str | None = None
    unit: str | None = None
    rows_used: int = 0
    data: list[dict[str, Any]] = field(default_factory=list)
    method: str = ""
    sources: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def error_result(
    code: str,
    message: str,
    available_options: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "status": "error",
        "error_code": code,
        "message": message,
        "available_options": available_options or [],
    }


class DataContractError(ValueError):
    """Error de datos esperado y presentable al usuario."""

    def __init__(
        self,
        code: str,
        message: str,
        available_options: list[str] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.available_options = available_options or []

    def as_result(self) -> dict[str, Any]:
        return error_result(self.code, self.message, self.available_options)
