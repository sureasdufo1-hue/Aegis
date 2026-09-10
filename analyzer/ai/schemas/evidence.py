from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from analyzer.models import Severity


class TrustLevel(StrEnum):
    UNTRUSTED = "untrusted"          # Raw payload or network packet that attacker controls
    NORMALIZED = "normalized"        # Parsed and enriched by IDS/SIEM
    VERIFIED = "verified"            # Cryptographically verified (e.g. hashed PCAP, signed event)


class EvidenceSource(BaseModel):
    system: str = Field(description="Originating system: wazuh-indexer, suricata-eve, snort-alert, pcap")
    index_or_path: str = Field(description="Index name or relative file path")
    document_or_flow_id: str | None = Field(default=None, description="Document ID or Flow ID")


class NetworkCoordinates(BaseModel):
    src_ip: str
    src_port: int | None = None
    dst_ip: str
    dst_port: int | None = None
    protocol: str = "TCP"


class AlertMetadata(BaseModel):
    signature: str
    sid: int
    category: str = "Generic Security Event"
    severity: Severity = Severity.MEDIUM
    mitre_technique: str | None = None
    stage: str | None = None


class SecurityEvidence(BaseModel):
    """
    Immutable Security Evidence Contract.
    Converts raw IDS/SIEM/PCAP records into bounded, grounded facts for AI investigation.
    """
    evidence_id: str = Field(description="Unique deterministic evidence ID, e.g. EV-SURI-xxx")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source: EvidenceSource
    network: NetworkCoordinates
    alert: AlertMetadata
    raw_reference: str | None = Field(default=None, description="Pointer to raw log line or packet offset")
    sha256: str | None = Field(default=None, description="SHA-256 hash of associated raw file/PCAP")
    trust_level: TrustLevel = Field(default=TrustLevel.UNTRUSTED)
    observed_facts: dict[str, Any] = Field(default_factory=dict, description="Concrete verifiable facts extracted from telemetry")

    def to_brief_prompt(self) -> str:
        """Returns a concise, prompt-safe summary of the evidence without raw untrusted payloads."""
        return (
            f"[{self.evidence_id}] {self.timestamp.isoformat()} | "
            f"{self.network.src_ip}:{self.network.src_port or '-'} -> {self.network.dst_ip}:{self.network.dst_port or '-'} ({self.network.protocol}) | "
            f"SID {self.alert.sid}: {self.alert.signature} | Sev: {self.alert.severity.value} | ATT&CK: {self.alert.mitre_technique or 'N/A'}"
        )
