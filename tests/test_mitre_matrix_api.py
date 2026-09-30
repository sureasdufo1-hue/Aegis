from fastapi.testclient import TestClient

from dashboard.app import app

client = TestClient(app)


def test_get_mitre_matrix_report():
    """Verify GET /api/threats/mitre/matrix returns 14 tactics and complete ATT&CK matrix."""
    res = client.get("/api/threats/mitre/matrix")
    assert res.status_code == 200
    data = res.json()

    # Framework metadata
    assert data["framework_version"] == "v19.2"
    assert data["total_tactics"] == 14
    assert len(data["tactics"]) == 14
    assert data["coverage_percentage"] == 100.0
    assert data["total_detections"] > 0
    assert data["active_threat_techniques"] > 0

    # Tactic order verification: TA0043 (Recon) -> TA0040 (Impact)
    tactics = data["tactics"]
    assert tactics[0]["id"] == "TA0043"
    assert "정찰" in tactics[0]["name_ko"]
    assert tactics[-1]["id"] == "TA0040"
    assert "타격" in tactics[-1]["name_ko"]

    # Verify techniques presence across tactics
    total_techs = sum(len(t["techniques"]) for t in tactics)
    assert total_techs >= 25

    # Check Initial Access (TA0001) has T1190
    initial_access = next(t for t in tactics if t["id"] == "TA0001")
    t1190 = next(tech for tech in initial_access["techniques"] if tech["id"] == "T1190")
    assert t1190["name"] == "Exploit Public-Facing Application"
    assert t1190["hit_count"] >= 5
    assert t1190["severity"] == "CRITICAL"
    assert t1190["active"] is True
    assert 9010001 in t1190["mapped_sids"]


def test_get_mitre_technique_detail_t1190():
    """Verify GET /api/threats/mitre/techniques/T1190 returns full detail and mitigation."""
    res = client.get("/api/threats/mitre/techniques/T1190")
    assert res.status_code == 200
    data = res.json()

    assert data["id"] == "T1190"
    assert data["name"] == "Exploit Public-Facing Application"
    assert data["tactic_id"] == "TA0001"
    assert "침투" in data["tactic_name_ko"]
    assert data["severity"] == "CRITICAL"
    assert data["active"] is True
    assert len(data["mapped_sids"]) >= 3
    assert "WAF" in data["mitigation"] or "격리" in data["mitigation"]
    assert "description" in data and len(data["description"]) > 20


def test_get_mitre_technique_detail_t1046():
    """Verify GET /api/threats/mitre/techniques/T1046 returns Discovery tactic info."""
    res = client.get("/api/threats/mitre/techniques/T1046")
    assert res.status_code == 200
    data = res.json()

    assert data["id"] == "T1046"
    assert data["name"] == "Network Service Discovery"
    assert data["tactic_id"] == "TA0007"
    assert "탐색" in data["tactic_name_ko"]
    assert 9000001 in data["mapped_sids"]


def test_get_mitre_technique_not_found():
    """Verify GET /api/threats/mitre/techniques/{unknown} returns 404."""
    res = client.get("/api/threats/mitre/techniques/T9999")
    assert res.status_code == 404
    assert "T9999" in res.json()["detail"]


def test_index_html_contains_mitre_components():
    """Verify GET / dashboard template contains MITRE ATT&CK Matrix UI and Modal elements."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    # Section & Grid
    assert 'id="mitre-matrix-section"' in html
    assert 'id="mitre-tactics-grid"' in html
    assert 'id="mitre-badge-coverage"' in html
    assert 'id="mitre-badge-active-threats"' in html
    assert 'id="mitre-badge-total-detections"' in html

    # Modal & Inspection Actions
    assert 'id="mitreTechniqueModal"' in html
    assert 'id="mitre-modal-pcap-btn"' in html
    assert "openTechniqueDetailModal" in html
    assert "closeTechniqueDetailModal" in html
    assert "triggerMitrePcapCarving" in html
    assert "fetchMitreMatrix()" in html
