import json
import os
import pytest
from analyzer.ai.providers.ollama_provider import OllamaProvider
from analyzer.ai.schemas.analysis import AIIncidentAnalysis, AnalysisStatus


def test_ollama_provider_health_check():
    provider = OllamaProvider(endpoint="http://127.0.0.1:11434", model="qwen3.5:9b")
    # Should be True since Ollama is running and qwen3.5:9b is installed
    assert provider.health_check() is True


def test_ollama_provider_health_check_nonexistent_model():
    provider = OllamaProvider(endpoint="http://127.0.0.1:11434", model="nonexistent-model-xyz")
    assert provider.health_check() is False


def test_ollama_provider_fallback_disabled_on_error():
    # Target unreachable port with fallback disabled
    provider = OllamaProvider(endpoint="http://127.0.0.1:59999", model="qwen3.5:9b", timeout_seconds=1.0, enable_fallback=False)
    with pytest.raises(RuntimeError, match="fallback disabled"):
        provider.analyze_incident(
            incident_id="INC-ERR-01",
            system_prompt="Test system prompt",
            user_prompt="Test user prompt",
            evidence_context="Test evidence",
            rag_context="Test rag",
        )


def test_ollama_provider_fallback_enabled_on_error():
    # Target unreachable port with fallback enabled
    provider = OllamaProvider(endpoint="http://127.0.0.1:59999", model="qwen3.5:9b", timeout_seconds=1.0, enable_fallback=True)
    resp = provider.analyze_incident(
        incident_id="INC-FALLBACK-01",
        system_prompt="Test system prompt",
        user_prompt="Test user prompt",
        evidence_context="Test evidence EV-INC-01",
        rag_context="Test rag",
    )
    assert resp.analysis.incident_id == "INC-FALLBACK-01"
    assert resp.analysis.model_info.get("is_mock") is True
    assert "fell back" in resp.analysis.model_info.get("notice", "")


def test_model_lock_integrity():
    lock_path = os.path.join(os.path.dirname(__file__), "..", "docs", "ai", "model-lock.json")
    assert os.path.exists(lock_path), "model-lock.json must exist"
    with open(lock_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    assert data["runtime"]["name"] == "Ollama"
    assert data["runtime"]["version"] == "0.33.3"
    assert "qwen3.5:9b" in data["models"]["primary"]["name"]
    assert len(data["models"]["primary"]["digest"]) == 64
