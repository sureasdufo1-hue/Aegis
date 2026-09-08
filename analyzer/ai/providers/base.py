from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel

from analyzer.ai.schemas.analysis import AIIncidentAnalysis


class ProviderResponse(BaseModel):
    analysis: AIIncidentAnalysis
    model_name: str
    tokens_used: int = 0
    latency_ms: float = 0.0
    raw_output: str | None = None


class BaseLLMProvider(ABC):
    """Abstract interface for LLM inference providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        pass

    @abstractmethod
    def health_check(self) -> bool:
        pass

    @abstractmethod
    def analyze_incident(
        self,
        incident_id: str,
        system_prompt: str,
        user_prompt: str,
        evidence_context: str,
        rag_context: str,
    ) -> ProviderResponse:
        pass
