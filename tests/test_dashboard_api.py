from fastapi.testclient import TestClient

from dashboard.app import app

client = TestClient(app)


def test_dashboard_index_html():
    response = client.get("/")
    assert response.status_code == 200
    assert "Security Operations Center" in response.text
    assert "Suricata & Snort Lab" in response.text


def test_dashboard_api_stats():
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_alerts" in data
    assert "critical_alerts" in data
    assert "engine_distribution" in data


def test_dashboard_api_alerts():
    response = client.get("/api/alerts?limit=10")
    assert response.status_code == 200
    alerts = response.json()
    assert isinstance(alerts, list)


def test_dashboard_api_incidents():
    response = client.get("/api/incidents")
    assert response.status_code == 200
    incidents = response.json()
    assert isinstance(incidents, list)


def test_dashboard_api_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "soc-dashboard"


def test_dashboard_api_notifications_config():
    response = client.get("/api/notifications/config")
    assert response.status_code == 200
    data = response.json()
    assert "cooldown_minutes" in data
    assert "auto_dispatch" in data
    assert "slack_configured" in data


def test_dashboard_api_notifications_history():
    response = client.get("/api/notifications/history")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_dashboard_api_notifications_test_dispatch():
    # Test simulation endpoint
    response = client.post("/api/notifications/test", json={"channel": "slack"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("completed", "dry_run", "suppressed", "throttled")
    assert "incident_id" in data


