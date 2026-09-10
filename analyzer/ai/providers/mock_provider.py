import re
import time
from datetime import UTC, datetime

from analyzer.ai.providers.base import BaseLLMProvider, ProviderResponse
from analyzer.ai.schemas.analysis import (
    AIIncidentAnalysis,
    AnalysisStatus,
    AttackTechniqueMapping,
    KnowledgeCitation,
    RiskAssessment,
)
from analyzer.models import Severity


class MockLLMProvider(BaseLLMProvider):
    """
    Deterministic Grounded Mock Provider.
    Extracts facts directly from evidence context and correlation inputs,
    enforcing strict schema adherence and zero hallucination for tests and offline environments.
    """

    @property
    def provider_name(self) -> str:
        return "mock-grounded"

    @property
    def model_name(self) -> str:
        return "mock-soc-analyst-v1"

    def health_check(self) -> bool:
        return True

    def analyze_incident(
        self,
        incident_id: str,
        system_prompt: str,
        user_prompt: str,
        evidence_context: str,
        rag_context: str,
    ) -> ProviderResponse:
        start_time = time.perf_counter()

        # 1. Grounded Fact Extraction from context
        observed_facts = []
        evidence_refs = []
        attack_mappings = []

        # Extract IPs
        src_ips = list(set(re.findall(r"\b(?:10|192\.168|172\.(?:1[6-9]|2[0-9]|3[0-1]))\.[0-9]{1,3}\.[0-9]{1,3}\b", evidence_context)))
        src_ip = src_ips[0] if src_ips else "10.77.20.20"

        # Check for Evidence IDs
        ev_ids = re.findall(r"\b(EV-[A-Za-z0-9_-]+)\b", evidence_context)
        evidence_refs = list(dict.fromkeys(ev_ids))

        # Check for attacks and MITRE ATT&CK techniques
        is_recon = "NULL" in evidence_context or "SCAN" in evidence_context or "9000001" in evidence_context
        is_sqli = "SQL" in evidence_context or "UNION" in evidence_context or "9010001" in evidence_context
        is_c2 = "SHELL" in evidence_context or "REVERSE" in evidence_context or "9030010" in evidence_context

        if is_recon:
            observed_facts.append(f"Port scanning / Reconnaissance traffic observed from {src_ip} (SID 9000001).")
            attack_mappings.append(AttackTechniqueMapping(
                technique_id="T1046",
                technique_name="Network Service Discovery",
                tactic="Discovery",
                confidence="HIGH",
                grounded_in_evidence=evidence_refs[:1],
            ))

        if is_sqli:
            observed_facts.append("Web SQL Injection attack pattern (UNION SELECT) detected targeting port 3000 (SID 9010001).")
            attack_mappings.append(AttackTechniqueMapping(
                technique_id="T1190",
                technique_name="Exploit Public-Facing Application",
                tactic="Initial Access",
                confidence="HIGH",
                grounded_in_evidence=evidence_refs[1:2] if len(evidence_refs) > 1 else evidence_refs,
            ))

        if is_c2:
            observed_facts.append("Interactive reverse shell command execution (/bin/sh) established on port 4444 (SID 9030010).")
            attack_mappings.append(AttackTechniqueMapping(
                technique_id="T1059.004",
                technique_name="Command and Scripting Interpreter: Unix Shell",
                tactic="Execution",
                confidence="HIGH",
                grounded_in_evidence=evidence_refs[2:3] if len(evidence_refs) > 2 else evidence_refs,
            ))

        if not observed_facts:
            observed_facts.append(f"Security anomaly events recorded for host {src_ip}.")

        # 2. Extract Hypotheses vs Unknowns
        hypotheses = [
            f"The adversary at {src_ip} conducted reconnaissance before executing targeted web exploitation.",
            "Potential persistence or interactive shell access may have been attempted following successful exploitation.",
        ]

        unknowns = [
            "Whether unauthorized database data was successfully exfiltrated outside the victim network.",
            "Whether local privilege escalation was achieved following initial shell execution.",
        ]

        # 3. Knowledge citations from RAG context
        citations = []
        if "04_malware_c2_investigation.md" in rag_context or is_c2:
            citations.append(KnowledgeCitation(
                document_title="Malware & C2 Investigation Playbook",
                chunk_id="playbook-c2-04",
                file_path="playbooks/04_malware_c2_investigation.md",
                relevance_score=0.96,
                key_takeaway="Immediately isolate infected host, terminate shell processes, and block outbound C2 channels.",
            ))
        elif "03_web_attack_investigation.md" in rag_context or is_sqli:
            citations.append(KnowledgeCitation(
                document_title="Web Application Attack Investigation Playbook",
                chunk_id="playbook-web-03",
                file_path="playbooks/03_web_attack_investigation.md",
                relevance_score=0.92,
                key_takeaway="Analyze HTTP access logs, inspect SQL injection payloads, and verify database integrity.",
            ))

        # 4. Determine risk level
        severity = Severity.CRITICAL if is_c2 else (Severity.HIGH if is_sqli else Severity.MEDIUM)

        analysis = AIIncidentAnalysis(
            incident_id=incident_id,
            analysis_status=AnalysisStatus.COMPLETED,
            summary=(
                f"Adversary at {src_ip} performed multi-stage malicious activity targeting internal services. "
                f"Evidence confirms {'reconnaissance, web exploitation, and interactive command execution' if is_c2 else 'active hostile probing'}. "
                "Containment and isolation are strongly recommended."
            ),
            observed_facts=observed_facts,
            hypotheses=hypotheses,
            unknowns=unknowns,
            risk_assessment=RiskAssessment(
                level=severity,
                rationale=f"Multi-stage attack pattern from {src_ip} with confirmed signature matches across network and application layers.",
                blast_radius="Isolated Target Host (10.77.30.20)",
                data_loss_risk=is_sqli or is_c2,
            ),
            attack_mapping=attack_mappings,
            evidence_refs=evidence_refs,
            knowledge_refs=citations,
            recommended_investigations=[
                f"Query OpenSearch SIEM for any secondary connections initiated from {src_ip}.",
                "Inspect victim host auth logs and process execution trees around the time of the reverse shell.",
            ],
            recommended_actions=[
                f"BLOCK_IP: Inbound temporary quarantine for attacker IP {src_ip}.",
                "ISOLATE_HOST: Terminate active reverse shell socket on victim host.",
            ],
            model_info={
                "provider": self.provider_name,
                "model": self.model_name,
                "temperature": 0.0,
            },
            generated_at=datetime.now(UTC),
        )

        latency = (time.perf_counter() - start_time) * 1000
        return ProviderResponse(
            analysis=analysis,
            model_name=self.model_name,
            tokens_used=180,
            latency_ms=latency,
            raw_output=analysis.model_dump_json(indent=2),
        )
