import logging
import time
from typing import Any

from analyzer.ai.actions.firewall_adapter import FirewallRuleAdapter
from analyzer.ai.approvals.repository import ApprovalRepository
from analyzer.ai.policy.validator import PolicyValidator
from analyzer.ai.providers.base import BaseLLMProvider
from analyzer.ai.providers.mock_provider import MockLLMProvider
from analyzer.ai.rag.retriever import KnowledgeRetriever
from analyzer.ai.schemas.actions import (
    ActionApprovalRecord, ActionType, Direction, ProposedAction
)
from analyzer.ai.schemas.analysis import AIIncidentAnalysis
from analyzer.ai.schemas.evidence import (
    AlertMetadata, EvidenceSource, NetworkCoordinates, SecurityEvidence, TrustLevel
)
from analyzer.ai.tools.registry import ToolRegistry
from analyzer.ai.tools.siem_tool import SiemQueryTool
from analyzer.ai.tools.threat_intel_tool import ThreatIntelLookupTool
from analyzer.ai.tools.pcap_tool import PcapInspectionTool
from analyzer.detection.correlation_engine import Incident

logger = logging.getLogger("soc.ai.orchestrator")


SYSTEM_PROMPT = """You are an elite, evidence-grounded SOC Security Copilot.
Your mission is to perform thorough, objective incident triage.
Rules:
1. Strictly separate OBSERVED FACTS from HYPOTHESES and UNKNOWNS.
2. Ground all claims in the provided security evidence and playbook knowledge.
3. Propose containment actions (e.g. BLOCK_IP, ISOLATE_HOST) only with clear justification.
4. Never assume an IP is benign just because it missed a Threat Intel match.
5. Never execute or suggest arbitrary commands outside approved containment actions.
"""


class AIOrchestrator:
    """
    AI-Orchestrated SOC Copilot.
    Coordinates evidence gathering, read-only tools, RAG grounding, LLM reasoning,
    deterministic policy validation, and human-in-the-loop approval workflows.
    """

    def __init__(
        self,
        provider: BaseLLMProvider | None = None,
        retriever: KnowledgeRetriever | None = None,
        tool_registry: ToolRegistry | None = None,
        approval_repo: ApprovalRepository | None = None,
    ):
        self.provider = provider or MockLLMProvider()
        self.retriever = retriever or KnowledgeRetriever()
        self.approval_repo = approval_repo or ApprovalRepository()
        
        # Setup Tool Registry
        if tool_registry:
            self.tools = tool_registry
        else:
            self.tools = ToolRegistry(max_calls_per_session=6)
            self.tools.register(SiemQueryTool())
            self.tools.register(ThreatIntelLookupTool())
            self.tools.register(PcapInspectionTool())

    def investigate_incident(self, incident: Incident) -> tuple[AIIncidentAnalysis, list[ActionApprovalRecord]]:
        """
        Executes an end-to-end evidence-grounded AI investigation for an incident:
        1. Context Building (Evidence Normalization)
        2. Read-only Tool Invocations (Threat Intel & SIEM Enrichment)
        3. RAG Grounding (Playbook Retrieval)
        4. LLM Analysis
        5. Policy Validation & Approval Request Creation
        """
        start_time = time.perf_counter()

        # 1. Normalize Existing Incident Alerts into SecurityEvidence
        evidences: list[SecurityEvidence] = []
        for idx, alert in enumerate(incident.alerts):
            ev = SecurityEvidence(
                evidence_id=f"EV-INC-{idx+1:02d}",
                timestamp=alert.timestamp,
                source=EvidenceSource(
                    system=alert.engine.value.lower(),
                    index_or_path="eve.json" if alert.engine.value == "SURICATA" else "alert_json.txt",
                    document_or_flow_id=str(alert.raw_data.get("flow_id", f"flow-{idx+1}")),
                ),
                network=NetworkCoordinates(
                    src_ip=alert.src_ip,
                    src_port=alert.src_port,
                    dst_ip=alert.dst_ip,
                    dst_port=alert.dst_port,
                    protocol=alert.protocol,
                ),
                alert=AlertMetadata(
                    signature=alert.signature,
                    sid=alert.sid,
                    category=alert.category,
                    severity=alert.severity,
                    mitre_technique=alert.mitre_technique,
                ),
                trust_level=TrustLevel.NORMALIZED,
                observed_facts={
                    "flow_id": alert.raw_data.get("flow_id"),
                    "http_uri": alert.http_uri,
                    "mitre_technique": alert.mitre_technique,
                },
            )
            evidences.append(ev)

        # 2. Tool Enriched Evidence (Threat Intel lookup for Attacker IP)
        ti_res = self.tools.execute_tool("lookup_threat_intel", {"indicator": incident.src_ip})
        ti_context = ""
        if ti_res.success and ti_res.data:
            ti_context = f"\n[THREAT INTEL LOOKUP RESULT]\n{ti_res.data}\n"

        # 3. RAG Knowledge Retrieval
        signatures = [a.signature for a in incident.alerts]
        rag_context, citations = self.retriever.retrieve_for_incident(
            signatures=signatures,
            attack_stages=incident.attack_stages,
            top_k=2,
        )

        # 4. Assemble Grounded Context
        evidence_prompt = "\n".join(e.to_brief_prompt() for e in evidences) + ti_context
        user_prompt = (
            f"Analyze Incident '{incident.incident_id}' involving attacker '{incident.src_ip}' "
            f"targeting {incident.target_ips}.\n"
            f"Existing Correlation Stages: {', '.join(incident.attack_stages)}\n"
            f"Existing Rule Verdict: {incident.verdict}\n"
            f"Existing Rule Playbook: {incident.playbook_ref}\n"
        )

        # 5. LLM Inference
        provider_resp = self.provider.analyze_incident(
            incident_id=incident.incident_id,
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            evidence_context=evidence_prompt,
            rag_context=rag_context,
        )

        analysis = provider_resp.analysis
        # Attach tool & execution metadata
        analysis.model_info["orchestrator_latency_ms"] = round((time.perf_counter() - start_time) * 1000, 2)
        analysis.model_info["tools_executed"] = len(self.tools.audit_log)

        # 6. Action Proposal & Policy Validation
        approval_records: list[ActionApprovalRecord] = []
        for idx, rec_action_text in enumerate(analysis.recommended_actions):
            action_type = ActionType.BLOCK_IP
            target = incident.src_ip
            direction = Direction.INBOUND
            rationale = rec_action_text

            if "ISOLATE" in rec_action_text.upper() and incident.target_ips:
                action_type = ActionType.ISOLATE_HOST
                target = incident.target_ips[0]
            elif "TUNE" in rec_action_text.upper():
                action_type = ActionType.TUNE_RULE
                target = str(incident.alerts[0].sid)

            preview = FirewallRuleAdapter.generate_nftables_preview(action_type, target, direction)

            proposal = ProposedAction(
                proposal_id=f"PROP-{incident.incident_id[-8:]}-{idx+1:02d}",
                incident_id=incident.incident_id,
                action_type=action_type,
                target=target,
                direction=direction,
                duration_minutes=60,
                rule_syntax_preview=preview,
                rationale=rationale,
            )

            # Independent Deterministic Policy Validation
            policy_result = PolicyValidator.validate_proposal(proposal)

            # Create Approval Request Object
            approval_rec = self.approval_repo.create_approval_request(
                incident_id=incident.incident_id,
                proposed_action=proposal,
                policy_result=policy_result,
            )
            approval_records.append(approval_rec)

        return analysis, approval_records
