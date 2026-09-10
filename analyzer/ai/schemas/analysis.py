from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from analyzer.models import Severity


class AnalysisStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class AttackTechniqueMapping(BaseModel):
    technique_id: str = Field(description="MITRE ATT&CK Technique ID, e.g. T1046")
    technique_name: str
    tactic: str
    confidence: str = Field(default="HIGH", description="Confidence level: HIGH, MEDIUM, LOW")
    grounded_in_evidence: list[str] = Field(default_factory=list, description="Evidence IDs proving this technique")


class RiskAssessment(BaseModel):
    level: Severity
    rationale: str
    blast_radius: str = Field(default="Single Target Host", description="Estimated scope of impact")
    data_loss_risk: bool = Field(default=False)


class KnowledgeCitation(BaseModel):
    document_title: str
    chunk_id: str
    file_path: str
    relevance_score: float = 1.0
    key_takeaway: str


class AIIncidentAnalysis(BaseModel):
    """
    Structured AI Analysis Output.
    Enforces strict separation between observed facts, hypotheses, unknowns, and recommendations.
    """
    incident_id: str
    analysis_status: AnalysisStatus = AnalysisStatus.COMPLETED
    summary: str = Field(description="Executive incident summary grounded in evidence")
    
    # Strict separation
    observed_facts: list[str] = Field(default_factory=list, description="Verifiable facts observed in telemetry")
    hypotheses: list[str] = Field(default_factory=list, description="Inferred possibilities regarding attacker intent and next steps")
    unknowns: list[str] = Field(default_factory=list, description="Unconfirmed aspects, gaps, and blind spots")
    
    risk_assessment: RiskAssessment
    attack_mapping: list[AttackTechniqueMapping] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list, description="IDs of all cited security evidences")
    knowledge_refs: list[KnowledgeCitation] = Field(default_factory=list, description="Playbook / ATT&CK citations")
    
    recommended_investigations: list[str] = Field(default_factory=list, description="Read-only investigation suggestions")
    recommended_actions: list[str] = Field(default_factory=list, description="Proposed containment and response actions")
    
    model_info: dict[str, Any] = Field(default_factory=dict, description="Metadata about the LLM provider, latency, and tokens")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
