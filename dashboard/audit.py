import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

AUDIT_LOG_FILE = Path("logs/audit_log.jsonl")


class AuditLogRecord(BaseModel):
    id: str = Field(description="Unique audit record ID")
    timestamp: str = Field(description="ISO 8601 timestamp")
    type: str = Field(description="Event category: AUTH, POLICY, INCIDENT, AI_ACTION, SYSTEM")
    actor: str = Field(description="User or system triggering the event")
    action: str = Field(description="Short human-readable action description")
    result: str = Field(default="SUCCESS", description="SUCCESS, FAILED, BLOCKED, REVIEWED")
    detail: str = Field(default="", description="Extended context or technical parameters")


INITIAL_AUDIT_SEEDS: list[dict[str, Any]] = [
    {
        "id": "AUD-001",
        "timestamp": "2026-09-16T17:08:33+09:00",
        "type": "AUTH",
        "actor": "admin",
        "action": "Administrator login",
        "result": "SUCCESS",
        "detail": "Console login via Web UI (10.10.70.151) using local credentials.",
    },
    {
        "id": "AUD-002",
        "timestamp": "2026-09-16T17:07:21+09:00",
        "type": "SYSTEM",
        "actor": "system",
        "action": "Suricata rule reload",
        "result": "SUCCESS",
        "detail": "Live reload signal sent to PID 1240. 128 active rules verified (suricata -T ok).",
    },
    {
        "id": "AUD-003",
        "timestamp": "2026-09-16T17:06:19+09:00",
        "type": "INCIDENT",
        "actor": "wazuh-agent",
        "action": "Wazuh alert received",
        "result": "SUCCESS",
        "detail": "Event forwarded from soc-sensor to soc-wazuh-manager (10.77.10.10:1514).",
    },
    {
        "id": "AUD-004",
        "timestamp": "2026-09-16T17:05:14+09:00",
        "type": "AI_ACTION",
        "actor": "ai-copilot",
        "action": "AI correlation completed",
        "result": "SUCCESS",
        "detail": "Cross-correlated 3 attack stages for IP 10.77.20.20 -> INC-10.77.20.20.",
    },
    {
        "id": "AUD-005",
        "timestamp": "2026-09-16T17:04:02+09:00",
        "type": "POLICY",
        "actor": "soc-analyst",
        "action": "IP block approved",
        "result": "SUCCESS",
        "detail": "HITL proposal APR-20.20-001 approved in Dry-Run mode for gateway nftables.",
    },
]


def init_audit_log_if_needed() -> None:
    if not AUDIT_LOG_FILE.exists():
        AUDIT_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(AUDIT_LOG_FILE, "w", encoding="utf-8") as f:
            f.writelines(json.dumps(item, ensure_ascii=False) + "\n" for item in INITIAL_AUDIT_SEEDS)


def record_audit_log(
    event_type: str,
    action: str,
    actor: str = "soc-analyst",
    result: str = "SUCCESS",
    detail: str = "",
) -> AuditLogRecord:
    init_audit_log_if_needed()
    now_str = datetime.now(UTC).isoformat()
    record_id = f"AUD-{int(datetime.now(UTC).timestamp() * 1000) % 1000000:06d}"
    rec = AuditLogRecord(
        id=record_id,
        timestamp=now_str,
        type=event_type,
        actor=actor,
        action=action,
        result=result,
        detail=detail,
    )
    with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec.model_dump(), ensure_ascii=False) + "\n")
    return rec


def get_audit_logs(limit: int = 100) -> list[AuditLogRecord]:
    init_audit_log_if_needed()
    records: list[AuditLogRecord] = []
    if not AUDIT_LOG_FILE.exists():
        return records
    try:
        with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(AuditLogRecord.model_validate(json.loads(line)))
                    except (json.JSONDecodeError, ValueError, KeyError):
                        continue
    except OSError:
        pass
    records.sort(key=lambda x: x.timestamp, reverse=True)
    return records[:limit]
