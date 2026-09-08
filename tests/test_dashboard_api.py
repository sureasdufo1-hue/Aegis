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

