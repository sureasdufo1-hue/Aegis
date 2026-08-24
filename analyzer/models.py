from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from pydantic import BaseModel, Field


class EngineType(StrEnum):
    SURICATA = "SURICATA"
    SNORT = "SNORT"
    GENERIC = "GENERIC"


class EventType(StrEnum):
    ALERT = "ALERT"
    HTTP = "HTTP"
    DNS = "DNS"
    TLS = "TLS"
    FLOW = "FLOW"
    FILE = "FILE"
    ANOMALY = "ANOMALY"


class Severity(StrEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class NormalizedAlert(BaseModel):
    id: str = Field(description="Unique alert identifier")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    engine: EngineType = Field(default=EngineType.SURICATA)
    event_type: EventType = Field(default=EventType.ALERT)
    
    # Signature & Rule Details
    signature: str = Field(description="Alert message/signature name")
    sid: int = Field(description="Signature ID")
    rev: int = Field(default=1, description="Signature revision")
    gid: int = Field(default=1, description="Generator ID")
    category: str = Field(default="Generic Security Event", description="Classification / Category")
    severity: Severity = Field(default=Severity.MEDIUM)
    
    # 5-Tuple Network Coordinates
    src_ip: str
    src_port: int | None = None
    dst_ip: str
    dst_port: int | None = None
    protocol: str = "TCP"
    
    # Enriched Telemetry
    community_id: str | None = None
    mitre_technique: str | None = None
    payload_printable: str | None = None
    http_hostname: str | None = None
    http_uri: str | None = None
    http_user_agent: str | None = None
    dns_query: str | None = None
    tls_sni: str | None = None
    
    # Raw Event
    raw_data: dict[str, Any] = Field(default_factory=dict)
