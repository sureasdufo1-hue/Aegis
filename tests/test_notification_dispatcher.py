from datetime import datetime, timezone
import pytest
import httpx

from analyzer.models import EngineType, NormalizedAlert, Severity
from analyzer.detection.correlation_engine import Incident
from analyzer.alerting.dispatcher import (
    NotificationChannel,
    NotificationConfig,
    NotificationDispatcher,
    DispatchStatus,
)


@pytest.fixture
def sample_incident() -> Incident:
    now_utc = datetime.now(timezone.utc)
    alert1 = NormalizedAlert(
        id="ALERT-TEST-001",
        timestamp=now_utc,
        engine=EngineType.SURICATA,
        sid=9000001,
        rev=1,
        signature="SCAN Nmap TCP SYN Port Scan Detected",
        category="Reconnaissance",
        severity=Severity.MEDIUM,
        src_ip="10.77.20.20",
        dst_ip="10.77.30.20",
        src_port=49152,
        dst_port=80,
        protocol="TCP",
        mitre_technique="T1046",
    )
    alert2 = NormalizedAlert(
        id="ALERT-TEST-002",
        timestamp=now_utc,
        engine=EngineType.SURICATA,
        sid=9010001,
        rev=1,
        signature="WEB-ATTACK SQL Injection Attempt Detected (UNION SELECT)",
        category="Web Application Attack",
        severity=Severity.HIGH,
        src_ip="10.77.20.20",
        dst_ip="10.77.30.20",
        src_port=49153,
        dst_port=80,
        protocol="TCP",
        mitre_technique="T1190",
    )
    return Incident(
        incident_id="INC-10.77.20.20-1773098400",
        src_ip="10.77.20.20",
        target_ips=["10.77.30.20"],
        attack_stages=["1. Reconnaissance", "2. Initial Access / Exploitation"],
        alerts=[alert1, alert2],
        start_time=now_utc,
        last_seen=now_utc,
        highest_severity=Severity.CRITICAL,
        verdict="Suspicious Multi-Stage Exploit Attempt Detected: 1. Reconnaissance -> 2. Initial Access / Exploitation",
        playbook_ref="playbooks/03_web_attack_investigation.md",
        activity_status="CONFIRMED_COMPROMISE",
    )


def test_slack_block_kit_formatting(sample_incident: Incident):
    dispatcher = NotificationDispatcher(config=NotificationConfig(dashboard_base_url="http://soc-test:8501"))
    payload = dispatcher.format_slack_payload(sample_incident)

    assert "blocks" in payload
    assert "text" in payload
    blocks = payload["blocks"]
    assert len(blocks) >= 5

    # Check header
    header = blocks[0]
    assert header["type"] == "header"
    assert "CRITICAL" in header["text"]["text"]

    # Check isolation command presence
    flattened_text = " ".join(
        str(b.get("text", {}).get("text", "")) + " " +
        " ".join(f.get("text", "") for f in b.get("fields", []))
        for b in blocks
    )
    assert "nft add element inet filter blocklist { 10.77.20.20 }" in flattened_text
    assert "INC-10.77.20.20-1773098400" in flattened_text
    assert "T1046" in flattened_text
    assert "T1190" in flattened_text


def test_discord_embed_formatting(sample_incident: Incident):
    dispatcher = NotificationDispatcher()
    payload = dispatcher.format_discord_payload(sample_incident)

    assert "embeds" in payload
    embed = payload["embeds"][0]
    assert embed["color"] == 0xE02424  # Critical red
    assert "INC-10.77.20.20-1773098400" in embed["title"]

    field_names = [f["name"] for f in embed["fields"]]
    assert "공격자 IP" in field_names
    assert "피해 대상 자산" in field_names
    assert "🛡️ 초동 격리 명령 (NFTables)" in field_names

    nft_field = next(f for f in embed["fields"] if "NFTables" in f["name"])
    assert "10.77.20.20" in nft_field["value"]


def test_generic_webhook_formatting(sample_incident: Incident):
    dispatcher = NotificationDispatcher()
    payload = dispatcher.format_generic_payload(sample_incident)

    assert payload["source"] == "Aegis-SOC-CorrelationEngine"
    assert payload["event_type"] == "security_incident"
    inc_data = payload["incident"]
    assert inc_data["incident_id"] == "INC-10.77.20.20-1773098400"
    assert inc_data["src_ip"] == "10.77.20.20"
    assert "T1190" in inc_data["mitre_techniques"]
    assert "recommended_action" in inc_data


@pytest.mark.asyncio
async def test_mock_webhook_delivery_success(sample_incident: Incident):
    sent_requests: list[httpx.Request] = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        sent_requests.append(request)
        return httpx.Response(200, json={"status": "ok"})

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        config = NotificationConfig(
            slack_webhook_url="https://hooks.slack.com/services/TEST/SLACK",
            discord_webhook_url="https://discord.com/api/webhooks/TEST/DISCORD",
            generic_webhook_url="https://siem.corp.internal/webhook",
            cooldown_minutes=10,
        )
        dispatcher = NotificationDispatcher(config=config, http_client=client)

        result = await dispatcher.dispatch_incident(sample_incident)

        assert result["status"] == "completed"
        assert len(result["dispatched_channels"]) == 3
        assert all(c["status"] == "success" for c in result["dispatched_channels"])
        assert len(sent_requests) == 3


@pytest.mark.asyncio
async def test_cooldown_deduplication(sample_incident: Incident):
    def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": "ok"})

    transport = httpx.MockTransport(mock_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        config = NotificationConfig(
            slack_webhook_url="https://hooks.slack.com/services/TEST/SLACK",
            cooldown_minutes=10,
        )
        dispatcher = NotificationDispatcher(config=config, http_client=client)

        # 1st dispatch: Should succeed
        res1 = await dispatcher.dispatch_incident(sample_incident)
        assert res1["status"] == "completed"
        assert res1["dispatched_channels"][0]["status"] == "success"

        # 2nd immediate dispatch: Should be throttled
        res2 = await dispatcher.dispatch_incident(sample_incident)
        assert res2["status"] == "throttled"

        # 3rd dispatch with force=True: Should bypass throttle
        res3 = await dispatcher.dispatch_incident(sample_incident, force=True)
        assert res3["status"] == "completed"
        assert res3["dispatched_channels"][0]["status"] == "success"


@pytest.mark.asyncio
async def test_diagnostic_suppression():
    alert_ping = NormalizedAlert(
        id="ALERT-PING-001",
        timestamp=datetime.now(timezone.utc),
        engine=EngineType.SURICATA,
        sid=9000020,
        rev=1,
        signature="ICMP Echo Request (Diagnostic Ping)",
        category="Diagnostic",
        severity=Severity.INFO,
        src_ip="10.77.20.20",
        dst_ip="10.77.30.20",
        protocol="ICMP",
    )
    diag_incident = Incident(
        incident_id="INC-DIAG-01",
        src_ip="10.77.20.20",
        target_ips=["10.77.30.20"],
        attack_stages=["Diagnostic / Telemetry"],
        alerts=[alert_ping],
        start_time=datetime.now(timezone.utc),
        last_seen=datetime.now(timezone.utc),
        highest_severity=Severity.INFO,
        verdict="Non-malicious diagnostic telemetry",
        activity_status="DIAGNOSTIC",
    )

    dispatcher = NotificationDispatcher(config=NotificationConfig(dry_run=True))
    res = await dispatcher.dispatch_incident(diag_incident)
    assert res["status"] == "suppressed"


@pytest.mark.asyncio
async def test_webhook_failure_resilience(sample_incident: Incident):
    def mock_failure_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Internal Server Error")

    transport = httpx.MockTransport(mock_failure_handler)
    async with httpx.AsyncClient(transport=transport) as client:
        config = NotificationConfig(
            slack_webhook_url="https://hooks.slack.com/services/FAIL/SLACK",
            cooldown_minutes=10,
        )
        dispatcher = NotificationDispatcher(config=config, http_client=client)

        res = await dispatcher.dispatch_incident(sample_incident)
        assert res["status"] == "completed"
        assert res["dispatched_channels"][0]["status"] == "failed"

        # Verify history captures error
        history = dispatcher.history
        assert len(history) >= 1
        assert history[-1].status == DispatchStatus.FAILED
        assert "HTTP 500" in (history[-1].error_message or "")


@pytest.mark.asyncio
async def test_send_test_notification():
    dispatcher = NotificationDispatcher(config=NotificationConfig(dry_run=True))
    res = await dispatcher.send_test_notification()
    assert res["status"] == "completed"
    assert len(res["dispatched_channels"]) == 3
    assert all(c["status"] == "dry_run" for c in res["dispatched_channels"])


def test_masked_config():
    config = NotificationConfig(
        slack_webhook_url="https://hooks.slack.com/services/T00/B00/X1234567890",
        discord_webhook_url="https://discord.com/api/webhooks/123/XYZSECRETTOKEN",
        generic_webhook_url=None,
    )
    dispatcher = NotificationDispatcher(config=config)
    masked = dispatcher.get_masked_config()

    assert masked["slack_configured"] is True
    assert "X1234567890" not in masked["slack_url_masked"]
    assert "..." in masked["slack_url_masked"]
    assert masked["discord_configured"] is True
    assert masked["webhook_configured"] is False
