from fastapi.testclient import TestClient

from dashboard.app import app, interpreter

client = TestClient(app)


def test_localization_dictionary_endpoint():
    response = client.get("/api/localization/dictionary")
    assert response.status_code == 200
    data = response.json()
    assert "common_ui" in data
    assert "severities" in data
    assert "engines" in data
    assert "attack_stages" in data
    assert "signatures" in data
    assert "mitre_techniques" in data
    assert "policy_verdicts" in data
    assert "approval_statuses" in data
    assert "action_types" in data
    assert "execution_modes" in data

    # Verify key translations
    assert data["severities"]["CRITICAL"]["ko"] == "심각"
    assert data["severities"]["HIGH"]["ko"] == "높음"
    assert "보호 인프라" in data["policy_verdicts"]["DENIED_PROTECTED_ASSET"]["ko"]
    assert "Dry-Run" in data["execution_modes"]["DRY_RUN"]["ko"]


def test_ai_interpret_alert_endpoint():
    payload = {
        "target_type": "alert",
        "signature": "SOC-ATTACK: Web SQL Injection - UNION SELECT Pattern Detected",
        "category": "Web Application Attack",
        "severity": "HIGH",
        "mitre_id": "T1190"
    }
    response = client.post("/api/ai/interpret", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "korean_title" in data
    assert "SQL 인젝션" in data["korean_title"]
    assert "security_meaning" in data
    assert "compromise_status" in data
    assert "추가" in data["compromise_status"] or "검증" in data["compromise_status"]
    assert len(data["recommended_checks"]) >= 1


def test_ai_interpret_alert_generic_fallback():
    payload = {
        "target_type": "alert",
        "signature": "CUSTOM-ALERT: Suspicious Beacon To Unknown Host",
        "category": "Network Anomaly",
        "severity": "MEDIUM"
    }
    response = client.post("/api/ai/interpret", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "korean_title" in data
    assert "보안 경보" in data["korean_title"]
    assert len(data["recommended_checks"]) >= 1


def test_ai_interpret_invalid_request():
    # Neither signature nor incident_id provided
    response = client.post("/api/ai/interpret", json={"target_type": "alert"})
    assert response.status_code == 400
    assert "must be provided" in response.json()["error"]


def test_ai_interpret_caching_behavior():
    sig = "SOC-SCAN: Nmap Stealth NULL Scan Detected (Zero Flags)"
    res1 = interpreter.interpret_alert(sig, severity="MEDIUM")
    res2 = interpreter.interpret_alert(sig, severity="MEDIUM")
    assert res1 == res2
    assert "Nmap" in res1["korean_title"]


def test_dashboard_ui_html_elements():
    response = client.get("/")
    assert response.status_code == 200
    html = response.text
    # Check Korean SOC title
    assert "보안관제 센터" in html
    # Check view mode controls
    assert "btn-mode-orig" in html
    assert "btn-mode-ko" in html
    assert "btn-mode-split" in html
    # Check Provider Badge
    assert "provider-badge" in html
    # Check Pretendard & JetBrains Mono font references
    assert "Pretendard" in html
    assert "JetBrains+Mono" in html
    # Check KPI titles
    assert "CRITICAL SEVERITY" in html
    assert "CORRELATED INCIDENTS" in html
    assert "HITL APPROVALS" in html


def test_ai_health_provider_transparency():
    response = client.get("/api/ai/health")
    assert response.status_code == 200
    data = response.json()
    assert "is_mock_provider" in data
    assert "provider_status_label" in data
    if data["is_mock_provider"]:
        assert "Mock" in data["provider_status_label"]
        assert "실제 LLM 아님" in data["provider_status_label"]
