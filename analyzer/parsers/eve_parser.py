import json
import uuid
from datetime import datetime, timezone
from typing import Any, Generator
from pathlib import Path

from analyzer.models import EngineType, EventType, NormalizedAlert, Severity


def parse_suricata_severity(raw_severity: int | str | None, msg: str = "") -> Severity:
    if isinstance(raw_severity, int):
        if raw_severity == 1:
            return Severity.CRITICAL if ("RCE" in msg or "Shell" in msg or "Cobalt" in msg) else Severity.HIGH
        elif raw_severity == 2:
            return Severity.HIGH
        elif raw_severity == 3:
            return Severity.MEDIUM
        elif raw_severity >= 4:
            return Severity.LOW
            
    # Heuristics based on signature text
    msg_upper = msg.upper()
    if any(k in msg_upper for k in ["CRITICAL", "RCE", "LOG4J", "REVERSE SHELL", "COBALT"]):
        return Severity.CRITICAL
    if any(k in msg_upper for k in ["SQL INJECTION", "EXFILTRATION", "BRUTE FORCE", "HIGH"]):
        return Severity.HIGH
    if any(k in msg_upper for k in ["XSS", "TRAVERSAL", "SCAN", "MEDIUM"]):
        return Severity.MEDIUM
    if any(k in msg_upper for k in ["INFO", "PING"]):
        return Severity.INFO
    return Severity.MEDIUM


def parse_eve_record(record: dict[str, Any]) -> NormalizedAlert | None:
    event_type_str = record.get("event_type", "alert")
    if event_type_str not in ["alert", "anomaly", "http", "dns", "tls"]:
        return None

    # Timestamp
    ts_raw = record.get("timestamp")
    try:
        ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00")) if ts_raw else datetime.now(timezone.utc)
    except Exception:
        ts = datetime.now(timezone.utc)

    # Network 5-tuple
    src_ip = record.get("src_ip", "0.0.0.0")
    src_port = record.get("src_port")
    dst_ip = record.get("dest_ip", record.get("dst_ip", "0.0.0.0"))
    dst_port = record.get("dest_port", record.get("dst_port"))
    proto = record.get("proto", "TCP")
    comm_id = record.get("community_id")

    if event_type_str == "alert":
        alert_data = record.get("alert", {})
        signature = alert_data.get("signature", "Unknown Suricata Alert")
        sid = alert_data.get("signature_id", 0)
        rev = alert_data.get("rev", 1)
        gid = alert_data.get("gid", 1)
        category = alert_data.get("category", "General Alert")
        severity = parse_suricata_severity(alert_data.get("severity"), signature)
        
        # MITRE Attack extraction
        metadata = alert_data.get("metadata", {})
        mitre = None
        if "attack_technique" in metadata:
            mitre = ", ".join(metadata["attack_technique"]) if isinstance(metadata["attack_technique"], list) else str(metadata["attack_technique"])

        # HTTP/Payload enrichment
        http_data = record.get("http", {})
        payload = alert_data.get("payload_printable", record.get("payload_printable"))

        return NormalizedAlert(
            id=str(uuid.uuid4()),
            timestamp=ts,
            engine=EngineType.SURICATA,
            event_type=EventType.ALERT,
            signature=signature,
            sid=sid,
            rev=rev,
            gid=gid,
            category=category,
            severity=severity,
            src_ip=src_ip,
            src_port=src_port,
            dst_ip=dst_ip,
            dst_port=dst_port,
            protocol=proto,
            community_id=comm_id,
            mitre_technique=mitre,
            payload_printable=payload,
            http_hostname=http_data.get("hostname"),
            http_uri=http_data.get("url"),
            http_user_agent=http_data.get("http_user_agent"),
            raw_data=record,
        )
        
    return None


def stream_eve_log(file_path: Path | str) -> Generator[NormalizedAlert, None, None]:
    path = Path(file_path)
    if not path.exists():
        return

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                alert = parse_eve_record(record)
                if alert:
                    yield alert
            except Exception:
                continue
