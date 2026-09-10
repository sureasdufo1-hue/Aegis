from datetime import UTC, datetime

from analyzer.ai.orchestrator import AIOrchestrator
from analyzer.detection.correlation_engine import Incident
from analyzer.models import EngineType, EventType, NormalizedAlert, Severity


def test_ai_orchestrator_investigate_incident():
    orchestrator = AIOrchestrator()

    alerts = [
        NormalizedAlert(
            id="alert-1",
            timestamp=datetime(2026, 9, 7, 10, 0, 0, tzinfo=UTC),
            engine=EngineType.SURICATA,
            event_type=EventType.ALERT,
            signature="SOC-SCAN: Nmap Stealth NULL Scan Detected (Zero Flags)",
            sid=9000001,
            category="Attempted Information Leak",
            severity=Severity.MEDIUM,
            src_ip="10.77.20.20",
            src_port=49152,
            dst_ip="10.77.30.20",
            dst_port=80,
            protocol="TCP",
            mitre_technique="T1046",
        ),
        NormalizedAlert(
            id="alert-2",
            timestamp=datetime(2026, 9, 7, 10, 5, 0, tzinfo=UTC),
            engine=EngineType.SURICATA,
            event_type=EventType.ALERT,
            signature="SOC-ATTACK: Web SQL Injection - UNION SELECT Pattern Detected",
            sid=9010001,
            category="Web Application Attack",
            severity=Severity.HIGH,
            src_ip="10.77.20.20",
            src_port=49153,
            dst_ip="10.77.30.20",
            dst_port=3000,
            protocol="TCP",
            http_uri="/rest/products/search?q=' UNION SELECT--",
            mitre_technique="T1190",
        ),
        NormalizedAlert(
            id="alert-3",
            timestamp=datetime(2026, 9, 7, 10, 10, 0, tzinfo=UTC),
            engine=EngineType.SURICATA,
            event_type=EventType.ALERT,
            signature="SOC-MALWARE: Interactive Reverse Shell Session Established (/bin/sh prompt detected)",
            sid=9030010,
            category="A Network Trojan was detected",
            severity=Severity.CRITICAL,
            src_ip="10.77.20.20",
            src_port=49154,
            dst_ip="10.77.30.20",
            dst_port=4444,
            protocol="TCP",
            mitre_technique="T1059.004",
        ),
    ]

    incident = Incident(
        incident_id="INC-10.77.20.20-TEST",
        src_ip="10.77.20.20",
        target_ips=["10.77.30.20"],
        attack_stages=[
            "1. Reconnaissance",
            "2. Initial Access / Exploitation",
            "3. Command & Control / Execution",
        ],
        alerts=alerts,
        start_time=alerts[0].timestamp,
        last_seen=alerts[-1].timestamp,
        highest_severity=Severity.CRITICAL,
        verdict="Multi-stage attack chain confirmed.",
        playbook_ref="playbooks/04_malware_c2_investigation.md",
    )

    analysis, approvals = orchestrator.investigate_incident(incident)

    # Assert structured analysis
    assert analysis.incident_id == incident.incident_id
    assert analysis.risk_assessment.level == Severity.CRITICAL
    assert len(analysis.observed_facts) >= 3
    assert len(analysis.hypotheses) > 0
    assert len(analysis.unknowns) > 0
    assert len(analysis.attack_mapping) >= 3
    
    # Assert ATT&CK techniques mapped
    technique_ids = [m.technique_id for m in analysis.attack_mapping]
    assert "T1046" in technique_ids
    assert "T1190" in technique_ids
    assert "T1059.004" in technique_ids

    # Assert HITL Approval objects generated
    assert len(approvals) > 0
    first_appr = approvals[0]
    assert first_appr.incident_id == incident.incident_id
    assert first_appr.proposed_action.target == "10.77.20.20"
    assert first_appr.policy_validation.is_valid is True
    assert first_appr.status.value == "PENDING"
