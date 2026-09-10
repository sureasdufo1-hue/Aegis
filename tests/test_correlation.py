from datetime import UTC, datetime, timedelta

from analyzer.detection.correlation_engine import CorrelationEngine
from analyzer.models import EngineType, EventType, NormalizedAlert, Severity


def test_multi_stage_correlation():
    engine = CorrelationEngine(window_minutes=30)
    now = datetime.now(UTC)

    # Stage 1: Port Scan
    alert1 = NormalizedAlert(
        id="alert-1",
        timestamp=now - timedelta(minutes=10),
        engine=EngineType.SURICATA,
        event_type=EventType.ALERT,
        signature="SOC-SCAN: Nmap Stealth NULL Scan Detected",
        sid=9000001,
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
        sid=9010001,
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
    assert inc2.activity_status == "SUSPICIOUS_ATTEMPT"
    assert inc2.playbook_ref == "playbooks/03_web_attack_investigation.md"


def test_normal_diagnostic_ping_does_not_trigger_incident():
    """Verify that routine ICMP ping telemetry does not escalate into an incident."""
    engine = CorrelationEngine(window_minutes=30)
    now = datetime.now(UTC)

    ping_alert = NormalizedAlert(
        id="alert-ping",
        timestamp=now - timedelta(minutes=15),
        engine=EngineType.SURICATA,
        event_type=EventType.ALERT,
        signature="SOC-INFO: ICMP Ping Echo Diagnostic Received",
        sid=9000020,
        src_ip="10.77.20.20",
        dst_ip="10.77.30.20",
        severity=Severity.INFO,
    )
    inc = engine.process_alert(ping_alert)
    assert inc is None

    # Adding a single web attack after ping should NOT create a multi-stage incident
    # because ping is diagnostic, not an attack stage
    web_alert = NormalizedAlert(
        id="alert-sqli",
        timestamp=now - timedelta(minutes=5),
        engine=EngineType.SURICATA,
        event_type=EventType.ALERT,
        signature="SOC-ATTACK: Web SQL Injection - Boolean or Time-Based Injection Attempt",
        sid=9010002,
        src_ip="10.77.20.20",
        dst_ip="10.77.30.20",
        severity=Severity.HIGH,
    )
    inc2 = engine.process_alert(web_alert)
    assert inc2 is None, "Ping diagnostic + single web attack must NOT trigger multi-stage incident"


def test_confirmed_compromise_with_reverse_shell():
    """Verify that C2 / Reverse shell triggers CONFIRMED_COMPROMISE status and Critical playbook."""
    engine = CorrelationEngine(window_minutes=30)
    now = datetime.now(UTC)

    # Initial Web Exploit
    web_alert = NormalizedAlert(
        id="alert-log4j",
        timestamp=now - timedelta(minutes=10),
        engine=EngineType.SURICATA,
        event_type=EventType.ALERT,
        signature="SOC-ATTACK: Remote Code Execution - Apache Log4j JNDI Exploit Attempt (${jndi:})",
        sid=9010040,
        src_ip="10.77.20.88",
        dst_ip="10.77.30.20",
        severity=Severity.CRITICAL,
    )
    inc1 = engine.process_alert(web_alert)
    # Even on single critical, incident is generated
    assert inc1 is not None
    assert inc1.highest_severity == Severity.CRITICAL

    # Followed by interactive reverse shell
    shell_alert = NormalizedAlert(
        id="alert-shell",
        timestamp=now - timedelta(minutes=2),
        engine=EngineType.SURICATA,
        event_type=EventType.ALERT,
        signature="SOC-MALWARE: Potential Interactive Reverse Shell Session (/bin/sh Prompt on High Port)",
        sid=9030010,
        src_ip="10.77.20.88",
        dst_ip="10.77.30.20",
        severity=Severity.CRITICAL,
    )
    inc2 = engine.process_alert(shell_alert)
    assert inc2 is not None
    assert inc2.activity_status == "CONFIRMED_COMPROMISE"
    assert "3. Command & Control / Execution" in inc2.attack_stages
    assert inc2.playbook_ref == "playbooks/04_malware_c2_investigation.md"


def test_sliding_window_expiration():
    """Verify that attacks occurring outside the 30-minute window expire and do not correlate."""
    engine = CorrelationEngine(window_minutes=30)
    now = datetime.now(UTC)

    # Old recon scan 35 minutes ago
    old_scan = NormalizedAlert(
        id="alert-old-scan",
        timestamp=now - timedelta(minutes=35),
        engine=EngineType.SURICATA,
        event_type=EventType.ALERT,
        signature="SOC-SCAN: Nmap Stealth XMAS Scan Detected (FPU Flags)",
        sid=9000002,
        src_ip="198.51.100.99",
        dst_ip="10.77.30.20",
        severity=Severity.MEDIUM,
    )
    engine.process_alert(old_scan)

    # New web attack now (35 min later)
    new_web = NormalizedAlert(
        id="alert-new-web",
        timestamp=now,
        engine=EngineType.SURICATA,
        event_type=EventType.ALERT,
        signature="SOC-ATTACK: Web SQL Injection - UNION SELECT Pattern Attempt",
        sid=9010001,
        src_ip="198.51.100.99",
        dst_ip="10.77.30.20",
        severity=Severity.HIGH,
    )
    inc = engine.process_alert(new_web)
    assert inc is None, "Alerts older than window (35m > 30m) must expire and not trigger multi-stage incident"


def test_ssh_brute_force_account_takeover_correlation():
    """Verify that network connection anomaly + host authentication success triggers CONFIRMED_COMPROMISE."""
    engine = CorrelationEngine(window_minutes=30)
    now = datetime.now(UTC)

    # 1. Network IDS detects SSH connection threshold anomaly
    conn_alert = NormalizedAlert(
        id="alert-net-ssh",
        timestamp=now - timedelta(minutes=5),
        engine=EngineType.SURICATA,
        event_type=EventType.ALERT,
        signature="SOC-ANOMALY: High-Frequency SSH Connection Threshold Exceeded (Potential Brute Force Attempt)",
        sid=9020001,
        src_ip="10.77.20.50",
        dst_ip="10.77.30.20",
        severity=Severity.MEDIUM,
    )
    inc1 = engine.process_alert(conn_alert)
    assert inc1 is None  # Single stage attempt, not confirmed compromise yet

    # 2. Host Auth Success alert arrives from same IP
    auth_success_alert = NormalizedAlert(
        id="alert-host-success",
        timestamp=now - timedelta(minutes=2),
        engine=EngineType.WAZUH,
        event_type=EventType.ALERT,
        signature="sshd: authentication success.",
        sid=5715,
        src_ip="10.77.20.50",
        dst_ip="10.77.30.20",
        severity=Severity.HIGH,
    )
    inc2 = engine.process_alert(auth_success_alert)
    assert inc2 is not None
    assert inc2.activity_status == "CONFIRMED_COMPROMISE"
    assert inc2.highest_severity == Severity.CRITICAL
    assert "Confirmed Account Takeover" in inc2.verdict
    assert inc2.playbook_ref == "playbooks/05_ssh_brute_force_investigation.md"

