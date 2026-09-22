from fastapi.testclient import TestClient
from dashboard.app import app

client = TestClient(app)


def test_dashboard_summary_api():
    res = client.get("/api/dashboard/summary")
    assert res.status_code == 200
    data = res.json()
    assert "kpis" in data
    assert "system_telemetry" in data
    assert "policy_status" in data
    assert "threat_response_status" in data
    assert "timeline" in data
    assert data["kpis"]["critical_alerts"] >= 0
    assert data["kpis"]["active_sensors"] == "4/4"


def test_network_traffic_api():
    res = client.get("/api/network/traffic?time_range=1H")
    assert res.status_code == 200
    data = res.json()
    assert "top_sources" in data
    assert "top_destinations" in data
    assert "top_services" in data
    assert "top_protocols" in data
    assert "top_policies" in data
    assert "top_dest_countries" in data
    assert len(data["top_sources"]) > 0


def test_network_interfaces_api():
    res = client.get("/api/network/interfaces")
    assert res.status_code == 200
    ifaces = res.json()
    assert isinstance(ifaces, list)
    assert len(ifaces) >= 5
    iface_names = [i["interface"] for i in ifaces]
    assert "eth0" in iface_names
    assert "nic-monitor" in iface_names or "eth1" in iface_names


def test_threats_countries_api():
    res = client.get("/api/threats/countries")
    assert res.status_code == 200
    countries = res.json()
    assert isinstance(countries, list)
    assert len(countries) >= 3
    country_names = [c["country"] for c in countries]
    assert any("미국" in c or "United States" in c for c in country_names)


def test_assets_api():
    res = client.get("/api/assets")
    assert res.status_code == 200
    assets = res.json()
    assert isinstance(assets, list)
    asset_names = [a["name"] for a in assets]
    assert any("soc-victim" in a for a in asset_names)
    assert any("soc-gateway" in a for a in asset_names)
    assert any("soc-sensor" in a for a in asset_names)


def test_sensors_api():
    res = client.get("/api/sensors")
    assert res.status_code == 200
    sensors = res.json()
    assert isinstance(sensors, list)
    sensor_names = [s["name"] for s in sensors]
    assert any("Suricata" in s for s in sensor_names)
    assert any("Snort" in s for s in sensor_names)
    assert any("Wazuh" in s for s in sensor_names)


def test_policies_api():
    res = client.get("/api/policies")
    assert res.status_code == 200
    policies = res.json()
    assert isinstance(policies, list)
    # Check for zero-hit policies
    zero_hits = [p for p in policies if p["is_zero_hit"]]
    assert len(zero_hits) >= 1


def test_events_and_ai_analysis_api():
    res = client.get("/api/events?limit=10")
    assert res.status_code == 200
    events = res.json()
    assert len(events) > 0

    first_event = events[0]
    ev_id = first_event["id"]

    # Single event lookup
    res_single = client.get(f"/api/events/{ev_id}")
    assert res_single.status_code == 200
    assert res_single.json()["id"] == ev_id

    # AI Analysis for this event
    res_ai = client.get(f"/api/ai/analysis/{ev_id}")
    assert res_ai.status_code == 200
    ai_data = res_ai.json()
    assert "ai_risk_score" in ai_data
    assert "interpretation" in ai_data


def test_audit_logs_api():
    # 1. Fetch existing audit logs
    res = client.get("/api/audit/logs?limit=5")
    assert res.status_code == 200
    logs = res.json()
    assert isinstance(logs, list)

    # 2. Record new audit log
    payload = {
        "type": "POLICY",
        "action": "Firewall Rule Verified",
        "actor": "test-suite",
        "result": "SUCCESS",
        "detail": "Automated verification test execution"
    }
    res_post = client.post("/api/audit/logs", json=payload)
    assert res_post.status_code == 200
    rec = res_post.json()
    assert rec["actor"] == "test-suite"
    assert rec["action"] == "Firewall Rule Verified"


def test_websocket_stream():
    with client.websocket_connect("/ws/stream") as websocket:
        websocket.send_text("ping")
        data = websocket.receive_json()
        assert data["type"] == "PONG"


def test_enterprise_console_html_structure():
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    # Top Navigation Menus
    assert "tab-dashboard" in html
    assert "tab-monitor" in html
    assert "tab-incidents" in html
    assert "tab-network" in html
    assert "tab-policy" in html
    assert "tab-system" in html

    # High Density Workspaces
    assert "view-dashboard" in html
    assert "view-traffic-analysis" in html
    assert "view-threat-overview" in html
    assert "view-interfaces" in html
    assert "view-attack-map" in html
    assert "view-incidents" in html
    assert "view-ai-analysis" in html
    assert "view-policy" in html
    assert "view-assets" in html
    assert "view-system" in html

    # Operational Logs & Tables
    assert "audit-log-tbody" in html
    assert "interfaces-tbody" in html
    assert "geo-threats-tbody" in html
    assert "policies-tbody" in html
    assert "assets-tbody" in html
    assert "sensors-tbody" in html

    # Drill-down Drawer
    assert "eventDetailDrawer" in html
