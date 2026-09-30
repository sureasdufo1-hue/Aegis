from fastapi.testclient import TestClient

from dashboard.app import app

client = TestClient(app)


def test_get_incident_report_json_multistage():
    """Verify GET /api/incidents/{id}/report returns full 7-section KISA/NIST compliant report."""
    res = client.get("/api/incidents/IR-06/report?scenario=MULTI")
    assert res.status_code == 200
    data = res.json()

    # Metadata & Compliance
    meta = data["metadata"]
    assert meta["doc_number"].startswith("IR-")
    assert "KISA" in meta["standard_compliance"]
    assert "NIST SP 800-61" in meta["standard_compliance"]
    assert "AEGIS SOC" in meta["issuing_cert"]

    # Section 1: Executive Summary
    exec_sum = data["executive_summary"]
    assert exec_sum["incident_id"] == "IR-06"
    assert exec_sum["severity"] == "CRITICAL"
    assert exec_sum["verdict"] == "TRUE_POSITIVE"
    assert exec_sum["threat_actor_ip"] == "10.77.20.20"
    assert exec_sum["target_asset_ip"] == "10.77.30.20"
    assert "MTTD" in exec_sum["mttd"] or "0.4s" in exec_sum["mttd"]

    # Section 2: Asset & Actor Profile
    actor = data["asset_and_actor"]
    assert actor["attacker_ip"] == "10.77.20.20"
    assert "ZONE-ATTACK" in actor["attacker_zone"]
    assert actor["victim_ip"] == "10.77.30.20"
    assert "ZONE-VICTIM" in actor["victim_zone"]
    assert len(actor["victim_services"]) >= 2

    # Section 3: Kill Chain Stages
    stages = data["kill_chain_stages"]
    assert len(stages) >= 3
    sids = [s["suricata_sid"] for s in stages]
    assert 9000001 in sids  # Recon
    assert any(sid in [9010001, 9010002] for sid in sids)  # Web Exploitation

    # Section 4: Forensic Evidence
    evidence = data["forensic_evidence"]
    assert len(evidence["pcap_hash_sha256"]) == 64  # SHA256 hex string
    assert "100%" in evidence["snort_cross_check"]
    assert evidence["packet_count"] > 0
    assert "alert" in evidence["eve_json_snippet"]

    # Section 5: AI & XAI
    ai = data["ai_and_xai"]
    assert "가설 1 입증" in ai["ach_verdict"]
    assert ai["confidence_score"] >= 90
    assert len(ai["xai_top_features"]) >= 3

    # Section 6: SOAR Containment
    soar = data["soar_containment"]
    assert "QRN-" in soar["quarantine_id"]
    assert soar["target_ip"] == "10.77.20.20"
    assert soar["ttl_seconds"] == 3600
    assert "1-Click" in soar["rollback_safeguard"]

    # Section 7: Root Cause & Remediation
    rem = data["root_cause_and_remediation"]
    assert len(rem["root_cause_analysis"]) > 20
    assert len(rem["short_term_actions"]) >= 2
    assert len(rem["mid_term_actions"]) >= 2
    assert len(rem["long_term_actions"]) >= 2


def test_get_incident_report_json_bruteforce():
    """Verify GET /api/incidents/{id}/report adapts to SSH Brute Force scenario."""
    res = client.get("/api/incidents/IR-02/report?scenario=BRUTEFORCE")
    assert res.status_code == 200
    data = res.json()

    exec_sum = data["executive_summary"]
    assert exec_sum["incident_id"] == "IR-02"
    assert exec_sum["severity"] == "HIGH"
    assert "SSH" in exec_sum["incident_title"] or "무차별 대입" in exec_sum["incident_title"]

    stages = data["kill_chain_stages"]
    sids = [s["suricata_sid"] for s in stages]
    assert 1000003 in sids


def test_get_incident_report_markdown():
    """Verify GET /api/incidents/{id}/report/markdown returns clean Markdown with document headers."""
    res = client.get("/api/incidents/IR-06/report/markdown")
    assert res.status_code == 200
    assert "text/markdown" in res.headers["content-type"]
    text = res.text

    assert "# [공식] SOC 침해사고 종합 분석 및 대응 보고서" in text
    assert "## 1. 경영진 요약 (Executive Summary)" in text
    assert "## 3. 다단계 공격 킬체인 타임라인" in text
    assert "## 4. 포렌식 증적 상세" in text
    assert "## 6. SOAR 초동 대응 및 능동 격리 내역" in text
    assert "IR-2026" in text


def test_get_incident_report_printable_html():
    """Verify GET /api/incidents/{id}/report/print returns standalone printable A4 HTML view."""
    res = client.get("/api/incidents/IR-06/report/print")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    html = res.text

    assert "@media print" in html
    assert "window.print()" in html
    assert "침해사고 조사 및 대응 결과 보고서" in html
    assert "KISA" in html or "NIST SP 800-61" in html
    assert "AEGIS SOC" in html
    assert "10.77.20.20" in html
    assert "10.77.30.20" in html


def test_index_html_contains_incident_report_components():
    """Verify dashboard index.html contains incident report modal and action buttons."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    # Modal presence
    assert 'id="incidentReportModal"' in html
    assert 'id="rep-modal-doc-num"' in html
    assert 'id="rep-modal-summary"' in html
    assert 'id="rep-modal-stages-body"' in html

    # Buttons and functions
    assert "openIncidentReportModal" in html
    assert "closeIncidentReportModal" in html
    assert "printIncidentReport" in html
    assert "downloadIncidentReportMarkdown" in html
    assert 'id="inv-btn-view-report"' in html
