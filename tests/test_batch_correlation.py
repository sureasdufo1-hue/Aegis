from datetime import UTC, datetime, timedelta

from analyzer.detection.batch_correlation import (
    AttackPatternType,
    BatchCorrelationEngine,
)
from analyzer.detection.correlation_engine import CorrelationEngine
from analyzer.models import EngineType, EventType, NormalizedAlert, Severity


def test_batch_correlation_detects_low_and_slow_campaign():
    """
    Validates RSK-001 resolution:
    Alerts separated by hours are missed by the 15-minute sliding window,
    but caught and correlated by the 24-hour BatchCorrelationEngine.
    """
    sliding_engine = CorrelationEngine(window_minutes=15)
    batch_engine = BatchCorrelationEngine(lookback_hours=24, low_and_slow_threshold_minutes=30.0)

    t0 = datetime(2026, 9, 30, 0, 0, 0, tzinfo=UTC)

    # Hour 0: Recon (Port scan)
    a1 = NormalizedAlert(
        id="ALT-BATCH-001",
        engine=EngineType.SURICATA,
        event_type=EventType.ALERT,
        sid=9000001,
        signature="SOC-ATTACK: Nmap SYN Stealth Port Scan",
        severity=Severity.MEDIUM,
        src_ip="198.51.100.77",
        dst_ip="10.77.30.20",
        timestamp=t0,
        mitre_technique="T1046",
    )

    # Hour 3.5: Web Injection probe
    a2 = NormalizedAlert(
        id="ALT-BATCH-002",
        engine=EngineType.SURICATA,
        event_type=EventType.ALERT,
        sid=9010001,
        signature="SOC-ATTACK: Web SQL Injection - UNION SELECT Pattern",
        severity=Severity.HIGH,
        src_ip="198.51.100.77",
        dst_ip="10.77.30.20",
        timestamp=t0 + timedelta(hours=3, minutes=30),
        mitre_technique="T1190",
    )

    # Hour 8: Reverse shell execution
    a3 = NormalizedAlert(
        id="ALT-BATCH-003",
        engine=EngineType.SURICATA,
        event_type=EventType.ALERT,
        sid=9030011,
        signature="SOC-ATTACK: Reverse Shell Payload Connection",
        severity=Severity.CRITICAL,
        src_ip="198.51.100.77",
        dst_ip="10.77.30.20",
        timestamp=t0 + timedelta(hours=8),
        mitre_technique="T1059",
    )

    # 1. Verify sliding window FAILS to correlate across hours
    inc1 = sliding_engine.process_alert(a1)
    inc2 = sliding_engine.process_alert(a2)
    inc3 = sliding_engine.process_alert(a3)
    # Because each alert is hours apart, a2 cannot correlate with a1 (a1 has expired from 15m window)
    # inc2 will be None because only 1 stage is present in its window
    assert inc2 is None

    # 2. Verify BatchCorrelationEngine correlates all across 24h
    alerts = [a1, a2, a3]
    campaigns = batch_engine.analyze_alert_batch(alerts, reference_time=t0 + timedelta(hours=8))

    assert len(campaigns) == 1
    cmp = campaigns[0]
    assert cmp.attacker_ip == "198.51.100.77"
    assert cmp.dwell_time_hours >= 8.0
    assert cmp.is_low_and_slow is True
    assert cmp.pattern_type == AttackPatternType.LOW_AND_SLOW
    assert len(cmp.stages_detected) >= 2
    assert "1. Reconnaissance" in cmp.stages_detected
    assert "2. Initial Access / Exploitation" in cmp.stages_detected
    assert cmp.highest_severity == Severity.CRITICAL
    assert cmp.remediation_priority == "P0-CRITICAL"
    assert "T1046" in cmp.mitre_techniques
    assert "T1190" in cmp.mitre_techniques


def test_rapid_multi_stage_campaign():
    batch_engine = BatchCorrelationEngine(lookback_hours=24)
    t0 = datetime(2026, 9, 30, 12, 0, 0, tzinfo=UTC)

    a1 = NormalizedAlert(
        id="ALT-RAPID-001",
        engine=EngineType.SURICATA,
        event_type=EventType.ALERT,
        sid=9000001,
        signature="SOC-ATTACK: Port Scan",
        severity=Severity.MEDIUM,
        src_ip="10.77.20.50",
        dst_ip="10.77.30.20",
        timestamp=t0,
        mitre_technique="T1046",
    )
    a2 = NormalizedAlert(
        id="ALT-RAPID-002",
        engine=EngineType.SURICATA,
        event_type=EventType.ALERT,
        sid=9010001,
        signature="SOC-ATTACK: Web Directory Traversal",
        severity=Severity.HIGH,
        src_ip="10.77.20.50",
        dst_ip="10.77.30.20",
        timestamp=t0 + timedelta(minutes=5),
        mitre_technique="T1190",
    )

    campaigns = batch_engine.analyze_alert_batch([a1, a2])
    assert len(campaigns) == 1
    cmp = campaigns[0]
    assert cmp.dwell_time_hours <= 0.5
    assert cmp.is_low_and_slow is False
    assert cmp.pattern_type == AttackPatternType.RAPID_MULTI_STAGE


def test_batch_correlation_window_cutoff():
    batch_engine = BatchCorrelationEngine(lookback_hours=24)
    t_now = datetime(2026, 9, 30, 18, 0, 0, tzinfo=UTC)

    old_alert = NormalizedAlert(
        id="ALT-OLD",
        engine=EngineType.SURICATA,
        event_type=EventType.ALERT,
        sid=9000001,
        signature="SOC-ATTACK: Old Scan",
        severity=Severity.MEDIUM,
        src_ip="10.77.20.88",
        dst_ip="10.77.30.20",
        timestamp=t_now - timedelta(hours=30),  # > 24 hours ago
        mitre_technique="T1046",
    )

    campaigns = batch_engine.analyze_alert_batch([old_alert], reference_time=t_now)
    assert len(campaigns) == 0
