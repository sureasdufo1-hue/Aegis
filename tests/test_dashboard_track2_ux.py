from fastapi.testclient import TestClient

from dashboard.app import app

client = TestClient(app)


def test_track2_provider_selector_in_html():
    """Verify Track 2 requirement 1: Top header one-click provider selector UI elements."""
    response = client.get("/")
    assert response.status_code == 200
    html = response.text

    # Header provider selector dropdown
    assert 'id="provider-select"' in html
    assert 'onchange="switchAiProvider(this.value)"' in html
    assert 'value="mock"' in html
    assert 'value="qwen3.5:4b"' in html
    assert 'value="qwen3.5:9b"' in html

    # Status badge and animated dot
    assert 'id="provider-badge"' in html
    assert 'id="provider-status-dot"' in html
    assert 'id="provider-status-text"' in html


def test_track2_investigation_progress_modal_in_html():
    """Verify Track 2 requirement 2: AI investigation progress modal, live timer and stepper."""
    response = client.get("/")
    assert response.status_code == 200
    html = response.text

    # Modal container
    assert 'id="investigationModal"' in html
    assert "AI 심층 침해사고 조사 파이프라인" in html

    # Stopwatch elapsed timer and progress bar
    assert 'id="inv-timer-display"' in html
    assert 'id="inv-progress-bar"' in html
    assert 'id="inv-progress-pct"' in html
    assert 'id="inv-progress-label"' in html
    assert 'id="inv-model-display"' in html
    assert 'id="inv-hw-hint"' in html

    # 4-stage stepper
    assert 'id="inv-step-1"' in html
    assert "1단계. 보안 증적 수집 및 읽기 도구 실행" in html
    assert 'id="inv-step-2"' in html
    assert "2단계. RAG 보안 플레이북 검색 및 컨텍스트 바운딩" in html
    assert 'id="inv-step-3"' in html
    assert "3단계. 로컬 LLM 인과관계 추론 및 구조화 생성" in html
    assert 'id="inv-step-4"' in html
    assert "4단계. 독립 정책 검증(PolicyValidator) 및 인간 승인 큐 등록" in html

    # Floating minimized pill and toast container
    assert 'id="inv-minimized-pill"' in html
    assert 'id="pill-timer"' in html
    assert 'id="toast-container"' in html
    assert 'id="inv-btn-view-result"' in html


def test_track2_provider_select_aliases():
    """Verify API handles provider_type and model_name aliases smoothly."""
    # 1. Select mock using provider_type
    res1 = client.post("/api/ai/provider/select", json={"provider_type": "mock"})
    assert res1.status_code == 200
    assert res1.json()["is_mock_provider"] is True

    # 2. Select qwen3.5:4b using provider_type: real and model_name (200 if online, 503 if offline)
    res2 = client.post("/api/ai/provider/select", json={"provider_type": "real", "model_name": "qwen3.5:4b"})
    assert res2.status_code in (200, 503)
    if res2.status_code == 200:
        assert res2.json()["is_mock_provider"] is False
        assert res2.json()["provider_model"] == "qwen3.5:4b"

    # 3. Select qwen3.5:9b
    res3 = client.post("/api/ai/provider/select", json={"provider_type": "real", "model_name": "qwen3.5:9b"})
    assert res3.status_code in (200, 503)
    if res3.status_code == 200:
        assert res3.json()["is_mock_provider"] is False
        assert res3.json()["provider_model"] == "qwen3.5:9b"

    # Reset back to mock for test isolation
    client.post("/api/ai/provider/select", json={"provider": "mock"})


def test_threat_matrix_page_and_navigation():
    """Verify Next-Gen WebGL 3D Threat Matrix route, static mounting, and main dashboard link."""
    # 1. Access /threat-matrix directly
    res_matrix = client.get("/threat-matrix")
    assert res_matrix.status_code == 200
    assert "AEGIS AI // 3D Interactive Cyber Shield & Threat Matrix" in res_matrix.text
    assert "three.min.js" in res_matrix.text
    assert "SHIELD INTEGRITY" in res_matrix.text
    assert "Real-time AI Shield" in res_matrix.text
    assert "canvas" in res_matrix.text.lower()

    # 2. Access through mounted static directory
    res_static = client.get("/static/threat_matrix.html")
    assert res_static.status_code == 200
    assert "AEGIS AI" in res_static.text

    # 3. Verify main console has the navigation button and embedded Visual Central Hub
    res_index = client.get("/")
    assert res_index.status_code == 200
    assert 'href="/threat-matrix"' in res_index.text
    assert "3D 위협 요격 매트릭스" in res_index.text
    assert 'id="central-shield-hub"' in res_index.text
    assert 'id="threat-matrix-iframe"' in res_index.text
    assert 'src="/threat-matrix?embed=true"' in res_index.text
    assert "시각적 중심 허브" in res_index.text
    assert "Holographic Shield & AI Core" in res_index.text


