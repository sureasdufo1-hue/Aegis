from fastapi.testclient import TestClient
from dashboard.app import app, approval_repo, action_executor
from analyzer.ai.schemas.actions import (
    ProposedAction, ActionType, Direction, PolicyValidationResult, PolicyVerdict, ApprovalStatus
)

client = TestClient(app)


def test_ai_health_endpoint():
    response = client.get("/api/ai/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "provider" in data
    assert "tools_available" in data
    assert data["tools_available"] >= 3
    assert "rag_documents_loaded" in data
    assert data["approval_stats"]["total"] >= 0
    assert "protected_assets_count" in data


def test_ai_provider_select_endpoint():
    # 1. Select mock
    resp_mock = client.post("/api/ai/provider/select", json={"provider": "mock"})
    assert resp_mock.status_code == 200
    assert resp_mock.json()["is_mock_provider"] is True
    assert "mock" in resp_mock.json()["provider"]

    # 2. Select ollama with qwen3.5:9b (Ollama is currently running)
    resp_ollama = client.post("/api/ai/provider/select", json={"provider": "ollama", "model": "qwen3.5:9b"})
    assert resp_ollama.status_code == 200
    assert resp_ollama.json()["is_mock_provider"] is False
    assert resp_ollama.json()["provider_model"] == "qwen3.5:9b"

    # 3. Select non-installed model (should return 503 Service Unavailable)
    resp_err = client.post("/api/ai/provider/select", json={"provider": "ollama", "model": "invalid-model-xyz"})
    assert resp_err.status_code == 503

    # Reset back to mock for subsequent test isolation
    client.post("/api/ai/provider/select", json={"provider": "mock"})


def test_ai_protected_assets_endpoint():
    response = client.get("/api/ai/protected-assets")
    assert response.status_code == 200
    data = response.json()
    assert "protected_ips" in data
    assert "protected_networks" in data
    assert "10.77.10.1" in data["protected_ips"]
    assert any("10.77.10.0/24" in net for net in data["protected_networks"])


def test_ai_investigate_nonexistent_incident():
    response = client.post("/api/incidents/NONEXISTENT-999/ai-investigate")
    assert response.status_code == 404
    assert "not found" in response.json()["error"]


def test_ai_get_analysis_not_found():
    response = client.get("/api/incidents/UNKNOWN-INC-001/ai-analysis")
    assert response.status_code == 404
    assert "No AI analysis found" in response.json()["error"]


def test_action_proposals_list_and_lifecycle():
    # 1. Create a valid proposal in approval repository
    prop = ProposedAction(
        proposal_id="PROP-TEST-01",
        incident_id="INC-TEST-001",
        action_type=ActionType.BLOCK_IP,
        target="10.77.20.99",
        direction=Direction.INBOUND,
        rule_syntax_preview="nft add element inet filter blacklist { 10.77.20.99 }",
        rationale="Simulated test attack",
    )
    pol_res = PolicyValidationResult(
        target="10.77.20.99",
        is_valid=True,
        verdict=PolicyVerdict.ALLOWED,
        violations=[],
    )
    rec = approval_repo.create_approval_request(
        incident_id="INC-TEST-001",
        proposed_action=prop,
        policy_result=pol_res,
    )
    approval_id = rec.approval_id

    # 2. Query list of proposals
    list_resp = client.get("/api/action-proposals")
    assert list_resp.status_code == 200
    proposals = list_resp.json()
    assert any(p["approval_id"] == approval_id for p in proposals)

    # 3. Query single proposal
    get_resp = client.get(f"/api/action-proposals/{approval_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["approval_id"] == approval_id

    # 4. Approve and auto-execute dry run
    app_resp = client.post(
        f"/api/action-proposals/{approval_id}/approve",
        json={"reviewer": "test-analyst", "notes": "Approved for lab test", "auto_execute": True}
    )
    assert app_resp.status_code == 200
    app_data = app_resp.json()
    assert app_data["status"] == "success"
    assert app_data["record"]["status"] in [ApprovalStatus.APPROVED.value, ApprovalStatus.EXECUTED.value]
    assert "DRY-RUN EXECUTION SIMULATION" in app_data["execution_output"]


def test_action_proposal_rejection():
    prop = ProposedAction(
        proposal_id="PROP-TEST-REJECT",
        incident_id="INC-TEST-002",
        action_type=ActionType.BLOCK_IP,
        target="10.77.20.88",
        direction=Direction.INBOUND,
        rule_syntax_preview="nft add element inet filter blacklist { 10.77.20.88 }",
        rationale="Simulated test for rejection",
    )
    pol_res = PolicyValidationResult(
        target="10.77.20.88",
        is_valid=True,
        verdict=PolicyVerdict.ALLOWED,
        violations=[],
    )
    rec = approval_repo.create_approval_request(
        incident_id="INC-TEST-002",
        proposed_action=prop,
        policy_result=pol_res,
    )
    approval_id = rec.approval_id

    rej_resp = client.post(
        f"/api/action-proposals/{approval_id}/reject",
        json={"reviewer": "test-analyst", "notes": "False positive suspected"}
    )
    assert rej_resp.status_code == 200
    assert rej_resp.json()["record"]["status"] == ApprovalStatus.REJECTED.value


def test_action_proposal_cannot_approve_policy_violation():
    # Target is protected Gateway 10.77.10.1
    prop = ProposedAction(
        proposal_id="PROP-TEST-PROTECTED",
        incident_id="INC-TEST-003",
        action_type=ActionType.BLOCK_IP,
        target="10.77.10.1",
        direction=Direction.INBOUND,
        rule_syntax_preview="nft add element inet filter blacklist { 10.77.10.1 }",
        rationale="Dangerous proposal to block Gateway",
    )
    pol_res = PolicyValidationResult(
        target="10.77.10.1",
        is_valid=False,
        verdict=PolicyVerdict.DENIED_PROTECTED_ASSET,
        violations=["Explicitly protected gateway: 10.77.10.1"],
    )
    rec = approval_repo.create_approval_request(
        incident_id="INC-TEST-003",
        proposed_action=prop,
        policy_result=pol_res,
    )
    approval_id = rec.approval_id

    # Attempt to approve
    app_resp = client.post(
        f"/api/action-proposals/{approval_id}/approve",
        json={"reviewer": "malicious-actor", "notes": "Try bypass policy", "auto_execute": True}
    )
    assert app_resp.status_code == 400
    assert "Policy validation failed" in app_resp.json()["error"]
