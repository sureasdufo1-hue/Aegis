from datetime import datetime, timedelta, timezone
from analyzer.models import EngineType, EventType, NormalizedAlert, Severity
from analyzer.detection.correlation_engine import CorrelationEngine


def test_multi_stage_correlation():
    engine = CorrelationEngine(window_minutes=30)
    now = datetime.now(timezone.utc)

    # Stage 1: Port Scan
    alert1 = NormalizedAlert(
        id="alert-1",
        timestamp=now - timedelta(minutes=10),
        engine=EngineType.SURICATA,
        event_type=EventType.ALERT,
        signature="SOC-SCAN: Nmap Stealth NULL Scan Detected",
        sid=1000101,
        src_ip="198.51.100.44",
        dst_ip="192.168.1.10",
        severity=Severity.MEDIUM,
    )
    inc1 = engine.process_alert(alert1)
    assert inc1 is None  # Single stage, no incident yet

    # Stage 2: Web SQL Injection
    alert2 = NormalizedAlert(
        id="alert-2",
        timestamp=now - timedelta(minutes=5),
        engine=EngineType.SURICATA,
        event_type=EventType.ALERT,
        signature="SOC-ATTACK: Web SQL Injection - UNION SELECT Attempt",
        sid=1000001,
        src_ip="198.51.100.44",
        dst_ip="192.168.1.10",
        severity=Severity.HIGH,
    )
    inc2 = engine.process_alert(alert2)
    assert inc2 is not None  # Multi-stage triggered!
    assert inc2.src_ip == "198.51.100.44"
    assert len(inc2.attack_stages) == 2
    assert "1. Reconnaissance" in inc2.attack_stages
    assert "2. Initial Access / Exploitation" in inc2.attack_stages
    assert inc2.highest_severity == Severity.HIGH
