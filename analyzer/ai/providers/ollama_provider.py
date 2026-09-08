import json
import logging
import os
import time
import urllib.error
import urllib.request
from typing import Any

from analyzer.ai.providers.base import BaseLLMProvider, ProviderResponse
from analyzer.ai.providers.mock_provider import MockLLMProvider
from analyzer.ai.schemas.analysis import (
    AIIncidentAnalysis,
    AnalysisStatus,
    AttackTechniqueMapping,
    KnowledgeCitation,
    RiskAssessment,
)
from analyzer.models import Severity

logger = logging.getLogger("soc.ai.providers.ollama")

SCHEMA_GUIDE = """{
  "incident_id": "<string>",
  "analysis_status": "completed",
  "summary": "<string>",
  "observed_facts": ["<string>"],
  "hypotheses": ["<string>"],
  "unknowns": ["<string>"],
  "risk_assessment": {
    "level": "LOW|MEDIUM|HIGH|CRITICAL",
    "rationale": "<string>",
    "blast_radius": "<string>",
    "data_loss_risk": false
  },
  "attack_mapping": [
    {
      "technique_id": "T1046|T1190|T1059.004|...",
      "technique_name": "<string>",
      "tactic": "<string>",
      "confidence": "HIGH|MEDIUM|LOW",
      "grounded_in_evidence": ["EV-INC-01", ...]
    }
  ],
  "evidence_refs": ["EV-INC-01", ...],
  "knowledge_refs": [],
  "recommended_investigations": ["<string>"],
  "recommended_actions": ["BLOCK_IP: 10.77.20.20", "ISOLATE_HOST: 10.77.30.20"]
}"""


class OllamaProvider(BaseLLMProvider):
    """
    Local Ollama Inference Provider.
    Supports Qwen3.5 9B with 8,192 token context, strict JSON Structured Output,
    and clear Live vs Mock separation.
    """

    def __init__(
        self,
        endpoint: str | None = None,
        model: str | None = None,
        timeout_seconds: float | None = None,
        enable_fallback: bool | None = None,
        execution_mode: str | None = None,
    ):
        self.endpoint = (endpoint or os.getenv("LLM_BASE_URL", "http://127.0.0.1:11434")).rstrip("/")
        self.model = model or os.getenv("LLM_MODEL", "qwen3.5:9b")
        self.timeout = float(timeout_seconds if timeout_seconds is not None else os.getenv("LLM_TIMEOUT", "240.0"))
        
        if enable_fallback is not None:
            self.enable_fallback = enable_fallback
        else:
            self.enable_fallback = os.getenv("LLM_ENABLE_FALLBACK", "false").lower() in ("true", "1")
            
        self.execution_mode = execution_mode or os.getenv("LLM_EXECUTION_MODE", "LIVE_LOCAL")
        self._fallback_provider = MockLLMProvider()

    @property
    def provider_name(self) -> str:
        return "ollama-local"

    @property
    def model_name(self) -> str:
        return self.model

    def health_check(self) -> bool:
        """Verifies Ollama API reachability and confirms model availability."""
        try:
            req = urllib.request.Request(f"{self.endpoint}/api/tags")
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                if resp.status != 200:
                    return False
                data = json.loads(resp.read().decode("utf-8"))
                installed = [m.get("name", "") for m in data.get("models", [])]
                # Check if model or model:latest matches
                return any(self.model in name for name in installed)
        except Exception as e:
            logger.warning("Ollama health check failed: %s", e)
            return False

    def analyze_incident(
        self,
        incident_id: str,
        system_prompt: str,
        user_prompt: str,
        evidence_context: str,
        rag_context: str,
    ) -> ProviderResponse:
        start_time = time.perf_counter()

        system_instruction = (
            f"{system_prompt}\n\n"
            f"[CRITICAL FORMAT INSTRUCTION]\n"
            f"You MUST output valid JSON conforming strictly to this format:\n"
            f"{SCHEMA_GUIDE}\n"
            f"Ensure incident_id is '{incident_id}'. Keep all summaries, facts, and hypotheses concise (1-2 sentences each). Separate observed_facts, hypotheses, and unknowns strictly."
        )

        prompt_payload = {
            "model": self.model,
            "system": system_instruction,
            "prompt": f"{user_prompt}\n\n[SECURITY EVIDENCE]\n{evidence_context}\n\n[PLAYBOOK KNOWLEDGE]\n{rag_context}",
            "format": "json",
            "stream": False,
            "think": False,
            "options": {
                "temperature": 0.1,
                "num_ctx": 8192,
                "num_predict": 1024,
            },
        }

        try:
            req = urllib.request.Request(
                f"{self.endpoint}/api/generate",
                data=json.dumps(prompt_payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw_res = json.loads(resp.read().decode("utf-8"))
                response_text = raw_res.get("response", "{}").strip()
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                elif response_text.startswith("```"):
                    response_text = response_text[3:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                response_text = response_text.strip()
                parsed_json = json.loads(response_text)
                # Enforce incident_id
                parsed_json["incident_id"] = incident_id
                
                # Defensive normalization for knowledge_refs (string -> KnowledgeCitation dict)
                if isinstance(parsed_json.get("knowledge_refs"), list):
                    norm_k = []
                    for k in parsed_json["knowledge_refs"]:
                        if isinstance(k, str):
                            norm_k.append({
                                "document_title": os.path.basename(k),
                                "chunk_id": k,
                                "file_path": k,
                                "relevance_score": 1.0,
                                "key_takeaway": f"Referenced playbook: {k}",
                            })
                        elif isinstance(k, dict):
                            norm_k.append(k)
                    parsed_json["knowledge_refs"] = norm_k

                # Defensive normalization for attack_mapping (string -> AttackTechniqueMapping dict)
                if isinstance(parsed_json.get("attack_mapping"), list):
                    norm_a = []
                    for a in parsed_json["attack_mapping"]:
                        if isinstance(a, str):
                            norm_a.append({
                                "technique_id": a,
                                "technique_name": a,
                                "tactic": "Initial Access",
                                "confidence": "HIGH",
                                "grounded_in_evidence": [],
                            })
                        elif isinstance(a, dict):
                            norm_a.append(a)
                    parsed_json["attack_mapping"] = norm_a
                
                # Schema validation
                analysis = AIIncidentAnalysis.model_validate(parsed_json)
                latency = (time.perf_counter() - start_time) * 1000
                
                # Enrich with Live LLM Metadata
                analysis.model_info.update({
                    "provider": self.provider_name,
                    "model_name": self.model,
                    "is_mock": False,
                    "execution_mode": self.execution_mode,
                    "tokens_used": raw_res.get("eval_count", 0),
                    "prompt_tokens": raw_res.get("prompt_eval_count", 0),
                    "eval_duration_ms": round(raw_res.get("eval_duration", 0) / 1e6, 2),
                    "prompt_eval_duration_ms": round(raw_res.get("prompt_eval_duration", 0) / 1e6, 2),
                    "latency_ms": round(latency, 2),
                })
                
                return ProviderResponse(
                    analysis=analysis,
                    model_name=self.model,
                    tokens_used=raw_res.get("eval_count", 0),
                    latency_ms=latency,
                    raw_output=response_text,
                )

        except Exception as e:
            logger.error("Ollama live inference error: %s", e)
            if self.enable_fallback:
                logger.warning("Ollama fallback enabled. Generating grounded mock response.")
                fallback_res = self._fallback_provider.analyze_incident(
                    incident_id=incident_id,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    evidence_context=evidence_context,
                    rag_context=rag_context,
                )
                fallback_res.analysis.model_info.update({
                    "notice": f"Ollama live model failed ({e}); fell back to grounded mock.",
                    "is_mock": True,
                    "execution_mode": "MOCK_FALLBACK",
                })
                return fallback_res
            else:
                raise RuntimeError(f"Ollama live inference failed (fallback disabled): {e}") from e
