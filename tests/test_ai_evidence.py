from datetime import datetime, timezone
from analyzer.ai.schemas.evidence import (
    SecurityEvidence, EvidenceSource, NetworkCoordinates, AlertMetadata, TrustLevel
)
from analyzer.models import Severity


def test_security_evidence_creation_and_prompt_formatting():
    ev = SecurityEvidence(
        evidence_id="EV-TEST-001",
        timestamp=datetime(2026, 9, 7, 12, 0, 0, tzinfo=timezone.utc),
        source=EvidenceSource(
            system="wazuh-indexer",
            index_or_path="wazuh-alerts-*",
            document_or_flow_id="doc-12345",
        ),
        network=NetworkCoordinates(
            src_ip="10.77.20.20",
            src_port=49152,
            dst_ip="10.77.30.20",
            dst_port=80,
            protocol="TCP",
        ),
        alert=AlertMetadata(
            signature="SOC-SCAN: Nmap Stealth NULL Scan Detected",
            sid=9000001,
            category="Attempted Information Leak",
            severity=Severity.MEDIUM,
            mitre_technique="T1046",
        ),
        trust_level=TrustLevel.NORMALIZED,
        observed_facts={"flags": "0"},
    )

    prompt_summary = ev.to_brief_prompt()
    assert "[EV-TEST-001]" in prompt_summary
    assert "10.77.20.20:49152 -> 10.77.30.20:80 (TCP)" in prompt_summary
    assert "SID 9000001" in prompt_summary
    assert "T1046" in prompt_summary
    assert ev.trust_level == TrustLevel.NORMALIZED


def test_untrusted_evidence_handling():
    raw_ev = SecurityEvidence(
        evidence_id="EV-RAW-001",
        source=EvidenceSource(system="pcap", index_or_path="sample.pcap"),
        network=NetworkCoordinates(src_ip="10.77.20.20", dst_ip="10.77.30.20"),
        alert=AlertMetadata(signature="Raw Packet Capture", sid=0),
        trust_level=TrustLevel.UNTRUSTED,
    )
    assert raw_ev.trust_level == TrustLevel.UNTRUSTED
