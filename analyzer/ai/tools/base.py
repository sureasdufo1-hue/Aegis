from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class ToolResult(BaseModel):
    success: bool
    tool_name: str
    data: Any
    error_message: str | None = None
    records_returned: int = 0
    latency_ms: float = 0.0


class BaseInvestigationTool(ABC):
    """Abstract base class for all bounded, read-only SOC investigation tools."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @property
    @abstractmethod
    def parameter_schema(self) -> dict[str, Any]:
        """JSON schema describing acceptable arguments."""

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        pass
