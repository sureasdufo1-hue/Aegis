"""
tests/test_attack_simulator_api.py
Integration & unit tests for the 1-Click Red Team Attack Scenario Emulator API.
Verifies scenario catalog integrity, simulation launch, live telemetry injection, and error handling.
"""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from dashboard.app import app
from dashboard.attack_simulator import AttackSimulatorEngine, SCENARIOS_CATALOG


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def tmp_simulator(tmp_path: Path):
    eve_path = tmp_path / "logs" / "suricata" / "eve.json"
    snort_path = tmp_path / "logs" / "snort" / "alert_json.txt"
    return AttackSimulatorEngine(eve_log_path=eve_path, snort_log_path=snort_path)


def test_scenario_catalog_integrity(tmp_simulator):
    scenarios = tmp_simulator.get_catalog()
    assert len(scenarios) == 6

    expected_ids = {"recon_nmap", "web_sqli", "log4j_rce", "ssh_bruteforce", "c2_reverse_shell", "syn_flood"}
    actual_ids = {s.id for s in scenarios}
    assert expected_ids == actual_ids

    for s in scenarios:
        assert 9000000 <= s.suricata_sid <= 9099999, f"Invalid Suricata SID: {s.suricata_sid}"
        assert 9100000 <= s.snort_sid <= 9199999, f"Invalid Snort SID: {s.snort_sid}"
        assert s.technique_id.startswith("T")
        assert len(s.attacker_ip) > 0
        assert len(s.target_ip) > 0
        assert s.target_port > 0


def test_api_get_scenarios(client):
    res = client.get("/api/simulator/scenarios")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 6
    assert any(s["id"] == "log4j_rce" for s in data)


def test_simulator_launch_unit(tmp_simulator):
    res = tmp_simulator.launch("log4j_rce", intensity=2, live_inject=True)
    assert res.status == "SUCCESS"
    assert res.scenario_id == "log4j_rce"
    assert res.technique_id == "T1190"
    assert res.suricata_sid == 9010040
    assert res.alerts_generated == 2

    # Check that logs were written
    assert tmp_simulator.eve_log_path.exists()
    assert tmp_simulator.snort_log_path.exists()

    with open(tmp_simulator.eve_log_path, "r", encoding="utf-8") as f:
        eve_lines = [json.loads(line) for line in f if line.strip()]
    assert len(eve_lines) == 2
    assert eve_lines[0]["alert"]["signature_id"] == 9010040
    assert eve_lines[0]["src_ip"] == "10.77.20.20"

    with open(tmp_simulator.snort_log_path, "r", encoding="utf-8") as f:
        snort_lines = [json.loads(line) for line in f if line.strip()]
    assert len(snort_lines) == 2
    assert snort_lines[0]["sid"] == 9100013


def test_api_launch_success_and_history(client):
    payload = {
        "scenario_id": "recon_nmap",
        "intensity": 3,
        "live_inject": True,
    }
    res = client.post("/api/simulator/launch", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert data["scenario_id"] == "recon_nmap"
    assert data["technique_id"] == "T1046"
    assert data["alerts_generated"] == 3

    # Check history endpoint
    hist_res = client.get("/api/simulator/history")
    assert hist_res.status_code == 200
    history = hist_res.json()
    assert len(history) >= 1
    assert history[0]["scenario_id"] == "recon_nmap"


def test_api_launch_invalid_scenario(client):
    payload = {
        "scenario_id": "non_existent_attack",
        "intensity": 1,
    }
    res = client.post("/api/simulator/launch", json=payload)
    assert res.status_code == 400
    assert "Unknown attack scenario ID" in res.json()["detail"]
