"""Unit & Integration tests for KISA/NIST Incident Report CTI & Simulation Linkage

and Sensor Port-Mirror NIC Telemetry Feedback Loop.
"""

from fastapi.testclient import TestClient

from dashboard.app import app
from dashboard.attack_simulator import attack_simulator_engine, LaunchRequest
from dashboard.telemetry import get_network_interfaces_telemetry, get_traffic_analysis_data

client = TestClient(app)


def test_incident_report_contains_threat_intel():
    """Verify GET /api/incidents/{id}/report contains enriched CTI intelligence."""
    res = client.get("/api/incidents/IR-06/report?scenario=MULTI")
    assert res.status_code == 200
    data = res.json()

    assert "threat_intelligence" in data
    ti = data["threat_intelligence"]
    assert ti["indicator"] == "10.77.20.20"
    assert ti["reputation_score"] == 95
    assert ti["verdict"] == "MALICIOUS"
    assert ti["abuseipdb_score"] == 95
    assert ti["total_reports"] >= 180
    assert ti["virustotal_positives"] >= 40
    assert ti["simulation_verified"] is True
    assert any(k in ti["simulation_scenario"] for k in ["Red Team", "Verified", "SID", "Scan", "Attack", "실측"])


def test_incident_report_markdown_contains_cti_section():
    """Verify Markdown export embeds Section 2.1 CTI and Red Team simulation details."""
    res = client.get("/api/incidents/IR-06/report/markdown")
    assert res.status_code == 200
    text = res.text

    assert "### 2.1 사이버 위협 인텔리전스 (CTI) 및 공격 재현 증적" in text
    assert "95/100" in text
    assert "AbuseIPDB" in text
    assert "VirusTotal" in text
    assert "레드팀 모의 침투 실측 검증" in text


def test_incident_report_html_contains_cti_card():
    """Verify HTML export renders styled CTI & Simulation card."""
    res = client.get("/api/incidents/IR-06/report/html")
    assert res.status_code == 200
    html = res.text

    assert "사이버 위협 인텔리전스 (CTI) &amp; 모의 침투 실측 검증" in html
    assert "AbuseIPDB" in html
    assert "VirusTotal" in html
    assert "평판 점수: 95/100" in html


def test_sensor_nic_telemetry_increments_after_attack_simulation():
    """Verify sensor port-mirroring nic-monitor and gateway interfaces reflect injected traffic."""
    # 1. Capture baseline packet counts
    ifaces_before = {i["interface"]: i for i in get_network_interfaces_telemetry()}
    nic_before_pkts = ifaces_before["nic-monitor"]["rx_pkts"]
    eth1_before_pkts = ifaces_before["eth1"]["tx_pkts"]

    # 2. Launch 1-Click attack simulation
    sim_res = attack_simulator_engine.launch_scenario(
        LaunchRequest(scenario_id="recon_nmap", intensity=5, live_inject=False)
    )
    assert sim_res.status == "SUCCESS"
    assert sim_res.alerts_generated == 5

    # 3. Verify telemetry counters incremented dynamically
    ifaces_after = {i["interface"]: i for i in get_network_interfaces_telemetry()}
    nic_after_pkts = ifaces_after["nic-monitor"]["rx_pkts"]
    eth1_after_pkts = ifaces_after["eth1"]["tx_pkts"]

    assert nic_after_pkts > nic_before_pkts, "nic-monitor rx_pkts must increment after attack simulation"
    assert eth1_after_pkts > eth1_before_pkts, "eth1 tx_pkts must increment after attack simulation"

    # 4. Verify traffic analysis ranking data also reflects simulation
    traffic = get_traffic_analysis_data("1H")
    attacker_src = next(s for s in traffic["top_sources"] if s.get("ip") == "10.77.20.20")
    assert attacker_src is not None
    assert "MB" in attacker_src["bytes"]
