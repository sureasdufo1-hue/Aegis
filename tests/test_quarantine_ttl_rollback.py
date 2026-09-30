import time
from datetime import UTC, datetime, timedelta
from fastapi.testclient import TestClient

from dashboard.app import app
from dashboard.quarantine_manager import QuarantineManager, QuarantineStatus

client = TestClient(app)


def test_quarantine_manager_lifecycle(tmp_path):
    """Verify QuarantineManager creates, computes remaining TTL, and executes 1-click rollback."""
    test_storage = tmp_path / "test_quarantine.jsonl"
    qm = QuarantineManager(storage_path=test_storage)

    # 1. Apply quarantine with 1-hour TTL
    rec = qm.quarantine_ip(
        ip="10.77.20.90",
        reason="Test SSH Brute Force",
        ttl_seconds=3600,
        operator="soc-analyst",
    )
    assert rec.ip == "10.77.20.90"
    assert rec.status == QuarantineStatus.ACTIVE
    assert rec.ttl_seconds == 3600
    assert 3590 <= rec.remaining_seconds <= 3600
    assert "nft insert rule" in rec.rule_preview

    # 2. Verify in active list
    active_list = qm.list_quarantines(include_historical=False)
    assert any(r.id == rec.id for r in active_list)

    # 3. Rollback quarantine
    ok, rolled = qm.rollback_quarantine(
        quarantine_id=rec.id,
        operator="soc-lead",
        reason="False positive verification",
    )
    assert ok is True
    assert rolled.status == QuarantineStatus.ROLLED_BACK
    assert rolled.rolled_back_by == "soc-lead"
    assert rolled.rollback_reason == "False positive verification"
    assert rolled.remaining_seconds == 0


def test_quarantine_ttl_auto_expiration(tmp_path):
    """Verify QuarantineManager automatically marks expired records when TTL lapses."""
    test_storage = tmp_path / "test_exp_quarantine.jsonl"
    qm = QuarantineManager(storage_path=test_storage)

    # Create record with already expired timestamp
    rec = qm.quarantine_ip(
        ip="10.77.20.91",
        reason="Short TTL Attack",
        ttl_seconds=1,
        operator="system",
    )
    # Manually backdate expires_at
    past_iso = (datetime.now(UTC) - timedelta(seconds=10)).isoformat()
    with qm._lock:
        qm._records[rec.id].expires_at = past_iso

    expired = qm.check_and_expire()
    assert any(r.id == rec.id for r in expired)
    updated = qm._records[rec.id]
    assert updated.status == QuarantineStatus.EXPIRED
    assert updated.remaining_seconds == 0
    assert "자동 만료" in (updated.rollback_reason or "")


def test_quarantine_permanent_block(tmp_path):
    """Verify permanent quarantine has ttl_seconds=0 and remaining_seconds=-1."""
    test_storage = tmp_path / "test_perm.jsonl"
    qm = QuarantineManager(storage_path=test_storage)
    rec = qm.quarantine_ip(
        ip="10.77.20.92",
        reason="Permanent C2 Blacklist",
        ttl_seconds=0,
        operator="admin",
    )
    assert rec.ttl_seconds == 0
    assert rec.expires_at is None
    assert rec.remaining_seconds == -1


def test_quarantine_api_get_list_and_stats():
    """Verify GET /api/soar/quarantine/list and /api/soar/quarantine/stats endpoints."""
    res = client.get("/api/soar/quarantine/list")
    assert res.status_code == 200
    records = res.json()
    assert isinstance(records, list)
    assert len(records) >= 1
    assert "remaining_seconds" in records[0]

    res_stats = client.get("/api/soar/quarantine/stats")
    assert res_stats.status_code == 200
    stats = res_stats.json()
    assert "active_count" in stats
    assert "expired_count" in stats
    assert "rolled_back_count" in stats
    assert stats["total_count"] >= 1


def test_quarantine_api_apply_and_rollback():
    """Verify POST /api/soar/quarantine/apply and rollback endpoints."""
    apply_payload = {
        "ip": "10.77.20.95",
        "reason": "REST API Integration Test Threat",
        "ttl_seconds": 1800,
        "operator": "test-runner",
    }
    res_apply = client.post("/api/soar/quarantine/apply", json=apply_payload)
    assert res_apply.status_code == 200
    rec = res_apply.json()["record"]
    assert rec["ip"] == "10.77.20.95"
    assert rec["status"] == "ACTIVE"
    qid = rec["id"]

    # Rollback
    rollback_payload = {
        "reason": "Verified benign admin traffic",
        "operator": "test-runner",
    }
    res_rb = client.post(f"/api/soar/quarantine/{qid}/rollback", json=rollback_payload)
    assert res_rb.status_code == 200
    rb_data = res_rb.json()
    assert rb_data["status"] == "success"
    assert rb_data["record"]["status"] == "ROLLED_BACK"

    # Second rollback attempt should fail with 400
    res_rb_fail = client.post(f"/api/soar/quarantine/{qid}/rollback", json=rollback_payload)
    assert res_rb_fail.status_code == 400


def test_quarantine_ui_in_index_html():
    """Verify index.html contains the SOAR Quarantine Section, table, and countdown logic."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    assert 'id="soar-quarantine-section"' in html
    assert 'id="quarantine-tbody"' in html
    assert 'id="qrn-badge-active"' in html
    assert 'id="quarantineModal"' in html
    assert 'id="quarantineRollbackModal"' in html
    assert "fetchQuarantines" in html
    assert "tickQuarantineCountdowns" in html
    assert "openQuarantineModal" in html
    assert "openRollbackModal" in html
    assert "formatCountdown" in html
