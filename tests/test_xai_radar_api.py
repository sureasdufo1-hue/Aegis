from fastapi.testclient import TestClient

from dashboard.app import app

client = TestClient(app)


def test_xai_explain_sqli_threat():
    """Verify POST /api/ai/xai/explain calculates 5-axis threat feature radar for SQLi."""
    res = client.post("/api/ai/xai/explain", json={"scenario": "SQLI", "dest_port": 80, "sid": 9010001})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["verdict"] == "CONFIRMED_EXPLOIT"
    assert data["overall_score"] >= 80

    # Verify all 5 radar dimensions
    axes = data["axes"]
    assert len(axes) == 5
    axis_ids = [a["id"] for a in axes]
    assert "payload_anomaly" in axis_ids
    assert "signature_confidence" in axis_ids
    assert "port_protocol_deviation" in axis_ids
    assert "target_asset_risk" in axis_ids
    assert "frequency_entropy" in axis_ids

    for a in axes:
        assert 0 <= a["score"] <= 100
        assert len(a["reason"]) > 0

    assert data["top_contributor"]["id"] == "payload_anomaly"
    assert "XAI 종합 위험도" in data["explain_summary"]


def test_xai_explain_bruteforce_threat():
    """Verify POST /api/ai/xai/explain reflects high frequency/entropy for SSH Brute Force."""
    res = client.post("/api/ai/xai/explain", json={"scenario": "BRUTEFORCE", "dest_port": 22})
    assert res.status_code == 200
    data = res.json()
    assert data["verdict"] == "CREDENTIAL_ATTACK"
    assert data["top_contributor"]["id"] == "frequency_entropy"
    assert data["top_contributor"]["score"] >= 90


def test_xai_default_scenario_get():
    """Verify GET /api/ai/xai/default/{scenario} endpoint returns predefined threat profile."""
    res = client.get("/api/ai/xai/default/LOG4J")
    assert res.status_code == 200
    data = res.json()
    assert data["verdict"] == "CRITICAL_RCE"
    assert data["overall_score"] >= 85
    assert data["top_contributor"]["id"] == "payload_anomaly"


def test_xai_radar_ui_in_index_html():
    """Verify index.html contains XAI radar card container, SVG element, and rendering scripts."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.text
    assert 'id="insp-xai-card"' in html
    assert 'id="xaiRadarSvg"' in html
    assert 'id="xai-score-badge"' in html
    assert 'id="xai-top-feature"' in html
    assert "renderXaiRadarChart" in html
    assert "updateXaiRadarForNode" in html
