from fastapi.testclient import TestClient

from dashboard.app import app

client = TestClient(app)


def test_get_multistage_killchain_hypotheses():
    """Verify GET /api/ai/hypotheses/{incident_id} returns 3 competing hypotheses for IR-06 Multi-Stage Kill Chain."""
    res = client.get("/api/ai/hypotheses/IR-06?scenario=MULTI")
    assert res.status_code == 200
    data = res.json()
    assert data["incident_id"] == "IR-06"
    assert "가설 1 입증" in data["top_concluded_hypothesis"]
    assert "가설 2 기각" in data["top_concluded_hypothesis"]

    hypotheses = data["hypotheses"]
    assert len(hypotheses) == 3

    # Check HYP-01 (Web SQLi / Log4j RCE)
    hyp1 = next(h for h in hypotheses if h["id"] == "HYP-01")
    assert hyp1["status"] == "PROVEN"
    assert hyp1["confidence_score"] >= 90
    assert len(hyp1["supporting_evidences"]) >= 2
    assert any("SQL" in e["description"] for e in hyp1["supporting_evidences"])
    assert any("Log4j" in e["description"] for e in hyp1["supporting_evidences"])

    # Check HYP-02 (C2 Reverse Shell)
    hyp2 = next(h for h in hypotheses if h["id"] == "HYP-02")
    assert hyp2["status"] == "REFUTED"
    assert hyp2["confidence_score"] <= 20
    assert len(hyp2["refuting_evidences"]) >= 2
    assert any("nftables" in e["source"] for e in hyp2["refuting_evidences"])
    assert any("PCAP" in e["source"] for e in hyp2["refuting_evidences"])

    # Check HYP-03 (SSH Credential Access fallback)
    hyp3 = next(h for h in hypotheses if h["id"] == "HYP-03")
    assert hyp3["status"] == "INVESTIGATING"
    assert 70 <= hyp3["confidence_score"] <= 85
    assert len(hyp3["supporting_evidences"]) >= 1


def test_get_bruteforce_hypotheses():
    """Verify GET /api/ai/hypotheses/{incident_id} evaluates SSH brute-force competing hypotheses."""
    res = client.get("/api/ai/hypotheses/IR-02?scenario=BRUTEFORCE")
    assert res.status_code == 200
    data = res.json()
    assert "SSH 무차별 대입 공격 확인" in data["top_concluded_hypothesis"]

    hypotheses = data["hypotheses"]
    assert len(hypotheses) == 3

    hyp1 = hypotheses[0]
    assert hyp1["status"] == "PROVEN"
    assert "Credential Access" in hyp1["kill_chain_stage"]
    assert hyp1["confidence_score"] >= 90

    hyp2 = hypotheses[1]
    assert hyp2["status"] == "REFUTED"
    assert "False Positive" in hyp2["kill_chain_stage"]

    hyp3 = hypotheses[2]
    assert hyp3["status"] == "REFUTED"
    assert "Lateral Movement" in hyp3["kill_chain_stage"]


def test_get_scan_recon_hypotheses():
    """Verify GET /api/ai/hypotheses/{incident_id} evaluates Nmap port scan hypotheses."""
    res = client.get("/api/ai/hypotheses/IR-01?scenario=SCAN")
    assert res.status_code == 200
    data = res.json()
    assert "Nmap SYN 스캔 확인" in data["top_concluded_hypothesis"]
    hypotheses = data["hypotheses"]
    assert len(hypotheses) == 3
    assert hypotheses[0]["status"] == "PROVEN"
    assert hypotheses[1]["status"] == "REFUTED"


def test_get_dos_flood_hypotheses():
    """Verify GET /api/ai/hypotheses/{incident_id} evaluates DoS SYN Flood hypotheses."""
    res = client.get("/api/ai/hypotheses/IR-05?scenario=DOS")
    assert res.status_code == 200
    data = res.json()
    assert "TCP SYN Flood DoS 확인" in data["top_concluded_hypothesis"]
    hypotheses = data["hypotheses"]
    assert len(hypotheses) == 3
    assert hypotheses[0]["status"] == "PROVEN"
    assert hypotheses[1]["status"] == "REFUTED"


def test_post_custom_evaluate_hypothesis():
    """Verify POST /api/ai/hypotheses/evaluate executes multi-source hypothesis assessment."""
    payload = {
        "incident_id": "INC-TEST-CUSTOM",
        "attacker_ip": "10.77.20.20",
        "target_ip": "10.77.30.20",
        "scenario": "BRUTEFORCE"
    }
    res = client.post("/api/ai/hypotheses/evaluate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["incident_id"] == "INC-TEST-CUSTOM"
    assert len(data["hypotheses"]) == 3
    assert data["hypotheses"][0]["status"] == "PROVEN"


def test_hypothesis_matrix_ui_in_index_html():
    """Verify index.html contains the Hypothesis Matrix section, badges, and JS functions."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    assert 'id="ai-hypothesis-section"' in html
    assert 'id="hypo-scenario-select"' in html
    assert 'id="hypo-summary-banner"' in html
    assert 'id="hypo-cards-grid"' in html
    assert "loadSecurityHypotheses" in html
    assert "refreshSecurityHypotheses" in html
    assert "carvePcapForHypothesis" in html
    assert "openPcapForensicModal" in html
