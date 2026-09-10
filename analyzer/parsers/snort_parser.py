import json
import uuid
from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from analyzer.models import EngineType, EventType, NormalizedAlert, Severity


def parse_snort_severity(msg: str) -> Severity:
    msg_upper = msg.upper()
    if any(k in msg_upper for k in ["CRITICAL", "RCE", "LOG4J", "REVERSE SHELL", "ROOT"]):
        return Severity.CRITICAL
    if any(k in msg_upper for k in ["SQL INJECTION", "EXPLOIT", "BRUTE", "HIGH"]):
        return Severity.HIGH
    if any(k in msg_upper for k in ["XSS", "TRAVERSAL", "SCAN", "MEDIUM"]):
        return Severity.MEDIUM
    if any(k in msg_upper for k in ["INFO", "PING"]):
        return Severity.INFO
    return Severity.MEDIUM


def parse_snort_record(record: dict[str, Any]) -> NormalizedAlert | None:
    # Timestamp parsing
    ts_raw = record.get("timestamp")
    try:
        ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00")) if ts_raw else datetime.now(UTC)
    except Exception:
        ts = datetime.now(UTC)

    msg = record.get("msg", "Unknown Snort Alert")
    sid = record.get("sid", 0)
    rev = record.get("rev", 1)
    gid = record.get("gid", 1)
    category = record.get("class", "Generic Security Event")

    src_ip = record.get("src_addr", "0.0.0.0")
    src_port = record.get("src_port")
    dst_ip = record.get("dst_addr", "0.0.0.0")
    dst_port = record.get("dst_port")
    proto = record.get("proto", "TCP")

    return NormalizedAlert(
        id=str(uuid.uuid4()),
        timestamp=ts,
        engine=EngineType.SNORT,
        event_type=EventType.ALERT,
        signature=msg,
        sid=sid,
        rev=rev,
        gid=gid,
        category=category,
        severity=parse_snort_severity(msg),
        src_ip=src_ip,
        src_port=src_port,
        dst_ip=dst_ip,
        dst_port=dst_port,
        protocol=proto,
        raw_data=record,
    )


def stream_snort_log(file_path: Path | str) -> Generator[NormalizedAlert, None, None]:
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
                alert = parse_snort_record(record)
                if alert:
                    yield alert
            except Exception:
                continue
