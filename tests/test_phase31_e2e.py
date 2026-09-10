from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from analyzer.detection.correlation_engine import CorrelationEngine
from analyzer.models import EngineType, EventType, NormalizedAlert, Severity
from analyzer.parsers.eve_parser import parse_eve_record, stream_eve_log
from dashboard.app import app

client = TestClient(app)


def test_normal_eve_ingestion_and_parsing():
    sample_record = {
        "timestamp": "2026-08-26T07:00:00.123456+00:00",
        "flow_id": 999111222333,
        "event_type": "alert",
        "src_ip": "10.77.20.20",
        "src_port": 45678,
        "dest_ip": "10.77.30.20",
        "dest_port": 3000,
        "proto": "TCP",
        "community_id": "1:test_comm_id",
        "alert": {
            "action": "allowed",
            "gid": 1,
            "signature_id": 9010001,
            "rev": 1,
            "signature": "SOC-ATTACK: Web SQL Injection - UNION SELECT Pattern Detected",
            "category": "Web Application Attack",
            "severity": 2,
            "metadata": {
                "attack_technique": ["T1190"]
            }
        },
        "http": {
            "hostname": "victim-shop.local",
            "url": "/rest/products/search?q=test",
            "http_user_agent": "Mozilla/5.0"
        }
    }
    alert = parse_eve_record(sample_record)
    assert alert is not None
    assert alert.engine == EngineType.SURICATA
    assert alert.sid == 9010001
    assert alert.src_ip == "10.77.20.20"
    assert alert.dst_ip == "10.77.30.20"
    assert alert.dst_port == 3000
    assert alert.severity == Severity.HIGH
    assert alert.mitre_technique == "T1190"
    assert alert.http_hostname == "victim-shop.local"


def test_invalid_json_handling(tmp_path: Path):
    bad_log = tmp_path / "corrupted_eve.json"
    bad_log.write_text(
        '{"timestamp": "2026-08-26T07:00:00+00:00", "event_type": "alert"}\n'
        'THIS IS NOT JSON AND SHOULD BE SAFELY SKIPPED\n'
        '{"broken": json\n'
        '{"timestamp": "2026-08-26T07:00:01+00:00", "event_type": "alert", "src_ip": "10.77.20.20", "dest_ip": "10.77.30.20", "alert": {"signature": "Valid Alert", "signature_id": 9000001, "severity": 3}}\n',
        encoding="utf-8"
    )
    alerts = list(stream_eve_log(bad_log))
    assert len(alerts) == 2


def test_duplicate_event_handling():
    engine = CorrelationEngine(window_minutes=30)
    now = datetime.now(UTC)

    alert = NormalizedAlert(
        id="alert-dup-1",
        timestamp=now,
        engine=EngineType.SURICATA,
        event_type=EventType.ALERT,
        signature="SOC-SCAN: Nmap Stealth NULL Scan Detected",
        sid=9000001,
        src_ip="10.77.20.20",
        dst_ip="10.77.30.20",
        dst_port=80,
        severity=Severity.MEDIUM,
    )
    inc1 = engine.process_alert(alert)
    inc2 = engine.process_alert(alert)
    assert inc1 is None
    assert inc2 is None


def test_out_of_order_stage_events():
    engine = CorrelationEngine(window_minutes=60)
    now = datetime.now(UTC)

    # Initial Access arrives first
    alert_exploit = NormalizedAlert(
        id="alert-exploit",
        timestamp=now - timedelta(minutes=10),
        engine=EngineType.SURICATA,
        event_type=EventType.ALERT,
        signature="SOC-ATTACK: Web SQL Injection - UNION SELECT Pattern",
        sid=9010001,
        src_ip="10.77.20.20",
        dst_ip="10.77.30.20",
        dst_port=3000,
        severity=Severity.HIGH,
    )
    # C2 arrives second
    alert_c2 = NormalizedAlert(
        id="alert-c2",
        timestamp=now - timedelta(minutes=5),
        engine=EngineType.SURICATA,
        event_type=EventType.ALERT,
        signature="SOC-MALWARE: Interactive Reverse Shell Session Established",
        sid=9030010,
        src_ip="10.77.20.20",
        dst_ip="10.77.30.20",
        dst_port=4444,
        severity=Severity.CRITICAL,
    )
    # Recon arrives last
    alert_recon = NormalizedAlert(
        id="alert-recon",
        timestamp=now,
        engine=EngineType.SURICATA,
        event_type=EventType.ALERT,
        signature="SOC-SCAN: Nmap Stealth NULL Scan Detected",
        sid=9000001,
        src_ip="10.77.20.20",
        dst_ip="10.77.30.20",
        dst_port=80,
        severity=Severity.MEDIUM,
    )

    engine.process_alert(alert_exploit)
    engine.process_alert(alert_c2)
    final_inc = engine.process_alert(alert_recon)

    assert final_inc is not None
    assert len(final_inc.attack_stages) == 3
    assert final_inc.highest_severity == Severity.CRITICAL
    assert final_inc.playbook_ref == "playbooks/04_malware_c2_investigation.md"


def test_correlation_time_window_expiry():
    engine = CorrelationEngine(window_minutes=15)
    t0 = datetime(2026, 8, 26, 6, 0, 0, tzinfo=UTC)

    # Event 1: Recon at 06:00
    alert1 = NormalizedAlert(
        id="alert-recon-old",
        timestamp=t0,
        engine=EngineType.SURICATA,
        event_type=EventType.ALERT,
        signature="SOC-SCAN: Nmap Stealth NULL Scan Detected",
        sid=9000001,
        src_ip="10.77.20.20",
        dst_ip="10.77.30.20",
        severity=Severity.MEDIUM,
    )
    engine.process_alert(alert1)

    # Event 2: Initial Access at 06:30 (30 min later, window is 15 min -> expired)
    alert2 = NormalizedAlert(
        id="alert-exploit-late",
        timestamp=t0 + timedelta(minutes=30),
        engine=EngineType.SURICATA,
        event_type=EventType.ALERT,
        signature="SOC-ATTACK: Web SQL Injection - UNION SELECT Pattern",
        sid=9010001,
        src_ip="10.77.20.20",
        dst_ip="10.77.30.20",
        severity=Severity.HIGH,
    )
    inc = engine.process_alert(alert2)
    assert inc is None


def test_incident_idempotency():
    engine1 = CorrelationEngine(window_minutes=60)
    engine2 = CorrelationEngine(window_minutes=60)

    t0 = datetime(2026, 8, 26, 7, 0, 0, tzinfo=UTC)
    alerts = [
        NormalizedAlert(
            id="alert-recon",
            timestamp=t0,
            engine=EngineType.SURICATA,
            event_type=EventType.ALERT,
            signature="SOC-SCAN: Nmap Stealth NULL Scan Detected",
            sid=9000001,
            src_ip="10.77.20.20",
            dst_ip="10.77.30.20",
            severity=Severity.MEDIUM,
        ),
        NormalizedAlert(
            id="alert-exploit",
            timestamp=t0 + timedelta(minutes=5),
            engine=EngineType.SURICATA,
            event_type=EventType.ALERT,
            signature="SOC-ATTACK: Web SQL Injection - UNION SELECT Pattern",
            sid=9010001,
            src_ip="10.77.20.20",
            dst_ip="10.77.30.20",
            severity=Severity.HIGH,
        ),
        NormalizedAlert(
            id="alert-c2",
            timestamp=t0 + timedelta(minutes=10),
            engine=EngineType.SURICATA,
            event_type=EventType.ALERT,
            signature="SOC-MALWARE: Interactive Reverse Shell Session Established",
            sid=9030010,
            src_ip="10.77.20.20",
            dst_ip="10.77.30.20",
            severity=Severity.CRITICAL,
        ),
    ]

    inc1 = None
    for a in alerts:
        res = engine1.process_alert(a)
        if res:
            inc1 = res

    inc2 = None
    for a in alerts:
        res = engine2.process_alert(a)
        if res:
            inc2 = res

    assert inc1 is not None
    assert inc2 is not None
    assert inc1.incident_id == inc2.incident_id
    assert inc1.attack_stages == inc2.attack_stages
    assert inc1.highest_severity == inc2.highest_severity
    assert inc1.verdict == inc2.verdict


def test_console_api_empty_state(monkeypatch, tmp_path: Path):
    empty_eve = tmp_path / "empty_eve.json"
    empty_snort = tmp_path / "empty_snort.txt"
    empty_eve.write_text("", encoding="utf-8")
    empty_snort.write_text("", encoding="utf-8")

    monkeypatch.setattr("dashboard.app.SURICATA_LOG", empty_eve)
    monkeypatch.setattr("dashboard.app.SNORT_LOG", empty_snort)

    # 1. Health check
    res_health = client.get("/api/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"

    # 2. Stats
    res_stats = client.get("/api/stats")
    assert res_stats.status_code == 200
    stats = res_stats.json()
    assert stats["total_alerts"] == 0
    assert stats["critical_alerts"] == 0
    assert stats["incident_count"] == 0

    # 3. Alerts
    res_alerts = client.get("/api/alerts")
    assert res_alerts.status_code == 200
    assert res_alerts.json() == []

    # 4. Incidents
    res_inc = client.get("/api/incidents")
    assert res_inc.status_code == 200
    assert res_inc.json() == []

    # 5. HTML Index
    res_html = client.get("/")
    assert res_html.status_code == 200
    assert "Security Operations Center" in res_html.text


def test_wazuh_indexer_resilience():
    import urllib.error
    def mock_urlopen(*args, **kwargs):
        raise urllib.error.URLError("Connection refused [Simulated]")

    try:
        mock_urlopen()
    except urllib.error.URLError as e:
        assert "Connection refused" in str(e.reason)
