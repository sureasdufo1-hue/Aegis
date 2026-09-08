import json
import os
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from analyzer.ai.orchestrator import AIOrchestrator
from analyzer.ai.providers.ollama_provider import OllamaProvider
from analyzer.detection.correlation_engine import Incident
from analyzer.models import EngineType, EventType, NormalizedAlert, Severity


def run_real_model_e2e():
    provider = OllamaProvider(
        endpoint="http://127.0.0.1:11434",
        model=os.getenv("LLM_MODEL", "qwen3.5:4b"),
        timeout_seconds=180.0,
        enable_fallback=False,
    )
    orchestrator = AIOrchestrator(provider=provider)

    alerts = [
        NormalizedAlert(
            id="alert-1",
            timestamp=datetime(2026, 9, 7, 10, 0, 0, tzinfo=timezone.utc),
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
            timestamp=datetime(2026, 9, 7, 10, 5, 0, tzinfo=timezone.utc),
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
    ]

    incident = Incident(
        incident_id="INC-10.77.20.20-REAL-E2E",
        src_ip="10.77.20.20",
        target_ips=["10.77.30.20"],
        attack_stages=["1. Reconnaissance", "2. Initial Access / Exploitation"],
        alerts=alerts,
        start_time=alerts[0].timestamp,
        last_seen=alerts[-1].timestamp,
        highest_severity=Severity.HIGH,
        verdict="Multi-stage reconnaissance and SQLi attack detected.",
        playbook_ref="playbooks/02_web_sql_injection_investigation.md",
    )

    print("[REAL-E2E] Starting End-to-End Investigation with Qwen3.5 9B...")
    t0 = time.time()
    analysis, approvals = orchestrator.investigate_incident(incident)
    elapsed = time.time() - t0

    print(f"[REAL-E2E] Investigation finished in {elapsed:.2f}s!")
    print(f"  Incident ID: {analysis.incident_id}")
    print(f"  Summary: {analysis.summary[:150]}...")
    print(f"  Observed Facts ({len(analysis.observed_facts)}): {analysis.observed_facts}")
    print(f"  Hypotheses ({len(analysis.hypotheses)}): {analysis.hypotheses}")
    print(f"  Unknowns ({len(analysis.unknowns)}): {analysis.unknowns}")
    print(f"  Risk Assessment: {analysis.risk_assessment.level} (Data Loss Risk: {analysis.risk_assessment.data_loss_risk})")
    print(f"  ATT&CK Techniques: {[t.technique_id for t in analysis.attack_mapping]}")
    print(f"  Recommended Actions: {analysis.recommended_actions}")
    print(f"  Approvals Created: {len(approvals)}")
    for a in approvals:
        print(f"    - Action: {a.proposed_action.action_type} on {a.proposed_action.target} (Status: {a.status}, Verdict: {a.policy_validation.verdict})")
    print(f"  Model Info: {json.dumps(analysis.model_info, indent=2)}")

    assert not analysis.model_info.get("is_mock"), "Must be real LLM, not mock!"
    assert "qwen3.5" in analysis.model_info.get("model_name")
    assert len(approvals) >= 1
    print("\n[REAL-E2E] ALL ASSERTIONS PASSED! Real Qwen3.5 validated end-to-end.")


if __name__ == "__main__":
    run_real_model_e2e()
