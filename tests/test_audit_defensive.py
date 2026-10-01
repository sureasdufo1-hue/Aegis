"""Unit tests for defensive audit logging serialization."""

import json
from dashboard.audit import record_audit_log, get_audit_logs, AuditLogRecord


def test_audit_log_string_detail():
    rec = record_audit_log(
        event_type="TEST",
        action="Simple String Action",
        actor="soc-tester",
        result="SUCCESS",
        detail="Normal string detail message",
    )
    assert isinstance(rec, AuditLogRecord)
    assert rec.detail == "Normal string detail message"
    assert rec.result == "SUCCESS"
    assert rec.actor == "soc-tester"


def test_audit_log_dict_detail_defensive_serialization():
    payload = {
        "ip": "10.77.20.20",
        "action": "BLOCK",
        "ports": [80, 443, 8080],
        "nested": {"status": "ok", "retries": 0},
    }
    rec = record_audit_log(
        event_type="POLICY",
        action="Dict Payload Serialization Test",
        actor="soc-analyst",
        result="SUCCESS",
        detail=payload,
    )
    assert isinstance(rec, AuditLogRecord)
    # Detail should be serialized as valid JSON
    parsed = json.loads(rec.detail)
    assert parsed["ip"] == "10.77.20.20"
    assert parsed["ports"] == [80, 443, 8080]
    assert parsed["nested"]["status"] == "ok"


def test_audit_log_list_detail_defensive_serialization():
    items = ["indicator-1", "indicator-2", "indicator-3"]
    rec = record_audit_log(
        event_type="INCIDENT",
        action="List Payload Serialization Test",
        actor="soc-system",
        result="REVIEWED",
        detail=items,
    )
    assert isinstance(rec, AuditLogRecord)
    parsed = json.loads(rec.detail)
    assert parsed == items


def test_audit_log_primitive_detail():
    rec = record_audit_log(
        event_type="AUTH",
        action="Int Detail Test",
        actor="system",
        result="SUCCESS",
        detail=404,
    )
    assert isinstance(rec, AuditLogRecord)
    assert rec.detail == "404"


def test_get_audit_logs_retrieval():
    logs = get_audit_logs(limit=10)
    assert isinstance(logs, list)
    assert len(logs) > 0
    assert all(isinstance(log, AuditLogRecord) for log in logs)
