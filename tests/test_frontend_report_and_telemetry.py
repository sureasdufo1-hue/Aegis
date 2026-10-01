"""Unit tests for Frontend UI Real-Time Interaction, Modal Enhancement,
and Hyper-V Port-Mirroring Console Feedback in index.html.
"""

from pathlib import Path

INDEX_HTML_PATH = Path(__file__).resolve().parent.parent / "dashboard" / "templates" / "index.html"


def test_incident_report_modal_contains_cti_dom_elements():
    """Verify index.html contains all necessary CTI and simulation validation DOM elements."""
    assert INDEX_HTML_PATH.exists(), f"Missing template file: {INDEX_HTML_PATH}"
    content = INDEX_HTML_PATH.read_text(encoding="utf-8")

    # DOM Elements for CTI Card
    assert 'id="rep-modal-cti-card"' in content
    assert 'id="rep-modal-cti-score"' in content
    assert 'id="rep-modal-sim-badge"' in content
    assert 'id="rep-modal-cti-abuse"' in content
    assert 'id="rep-modal-cti-vt"' in content
    assert 'id="rep-modal-cti-isp"' in content
    assert 'id="rep-modal-cti-categories"' in content
    assert 'id="rep-modal-cti-scenario"' in content
    assert "글로벌 위협 인텔리전스 (CTI) &amp; 레드팀 시뮬레이션 실측" in content


def test_incident_report_modal_js_binding():
    """Verify openIncidentReportModal() binds threat intelligence data to the modal elements."""
    content = INDEX_HTML_PATH.read_text(encoding="utf-8")

    assert "data.threat_intelligence" in content
    assert "ti.simulation_verified" in content
    assert "모의 침투 실측 검증 완료" in content
    assert "rep-modal-cti-score" in content
    assert "rep-modal-cti-abuse" in content


def test_network_interface_port_mirroring_badge_and_pulse():
    """Verify fetchInterfaces() applies port mirroring badge and pulse to nic-monitor."""
    content = INDEX_HTML_PATH.read_text(encoding="utf-8")

    assert "포트 미러링 수신" in content
    assert "isNicMonitor" in content
    assert "animate-pulse" in content
    assert "nic-monitor" in content


def test_attack_simulation_console_port_mirroring_feedback():
    """Verify launchAttackSimulation() console log includes Hyper-V Port Mirroring live confirmation."""
    content = INDEX_HTML_PATH.read_text(encoding="utf-8")

    assert "Hyper-V Port Mirroring Active: Mirrored to nic-monitor" in content
    assert "pkts captured" in content
