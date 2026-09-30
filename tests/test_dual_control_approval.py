import pytest
from datetime import UTC, datetime, timedelta
from pathlib import Path

from analyzer.ai.approvals.dual_control import (
    ApprovalSignature,
    DualApprovalStatus,
    DualControlManager,
    UserRole,
)
from analyzer.ai.schemas.actions import (
    ActionType,
    ExecutionMode,
    PolicyValidationResult,
    PolicyVerdict,
    ProposedAction,
)
from analyzer.ai.actions.executor import ActionExecutor


@pytest.fixture
def manager(tmp_path):
    store_file = tmp_path / "dual_approvals.json"
    return DualControlManager(storage_path=store_file, ttl_minutes=30)


@pytest.fixture
def sample_proposal():
    action = ProposedAction(
        proposal_id="PROP-HIGH-001",
        incident_id="INC-10.77.20.20-1001",
        action_type=ActionType.BLOCK_IP,
        target="10.77.20.20",
        rule_syntax_preview="nft add element inet filter soc_blocked { 10.77.20.20 } timeout 120m",
        rationale="Severe C2 Beaconing Isolation",
    )
    pol_res = PolicyValidationResult(
        is_valid=True,
        verdict=PolicyVerdict.ALLOWED,
        target="10.77.20.20",
    )
    return action, pol_res


def test_dual_control_lifecycle_happy_path(manager, sample_proposal):
    action, pol_res = sample_proposal
    rec = manager.create_request(incident_id=action.incident_id, proposed_action=action, policy_result=pol_res)

    assert rec.status == DualApprovalStatus.PENDING_FIRST
    assert rec.first_approval is None
    assert rec.second_approval is None

    # 1. First approval by L2 analyst
    ok, res1 = manager.first_approve(rec.request_id, approver_id="analyst_l2", role=UserRole.L2_ANALYST, comment="Verified threat")
    assert ok is True
    assert res1.status == DualApprovalStatus.PENDING_SECOND
    assert res1.first_approval.approver_id == "analyst_l2"

    # 2. Second approval by L3 lead
    ok, res2 = manager.second_approve(rec.request_id, approver_id="lead_l3", role=UserRole.L3_LEAD, comment="Isolation authorized")
    assert ok is True
    assert res2.status == DualApprovalStatus.APPROVED
    assert res2.second_approval.approver_id == "lead_l3"

    # 3. Execution
    executor = ActionExecutor(mode=ExecutionMode.DRY_RUN)
    ok_exec, out = manager.execute_approved(rec.request_id, executor)
    assert ok_exec is True
    assert "DUAL-CONTROL ACTION EXECUTED" in out
    assert "First Approver: analyst_l2" in out
    assert "Second Approver: lead_l3" in out
    assert manager.get(rec.request_id).status == DualApprovalStatus.EXECUTED


def test_anti_self_approval_enforcement(manager, sample_proposal):
    """The same user MUST NOT be both first and second approver."""
    action, pol_res = sample_proposal
    rec = manager.create_request(incident_id=action.incident_id, proposed_action=action, policy_result=pol_res)

    # First approve as user_alice
    ok, _ = manager.first_approve(rec.request_id, approver_id="user_alice", role=UserRole.L2_ANALYST)
    assert ok is True

    # Try second approve as user_alice (with elevated role) -> MUST BE REJECTED
    ok, err = manager.second_approve(rec.request_id, approver_id="user_alice", role=UserRole.SOC_MANAGER)
    assert ok is False
    assert "distinct first and second approvers" in err
    assert manager.get(rec.request_id).status == DualApprovalStatus.PENDING_SECOND


def test_unauthorized_second_approver_role(manager, sample_proposal):
    """L1 or L2 analyst cannot provide second approval."""
    action, pol_res = sample_proposal
    rec = manager.create_request(incident_id=action.incident_id, proposed_action=action, policy_result=pol_res)

    manager.first_approve(rec.request_id, approver_id="analyst_1", role=UserRole.L2_ANALYST)

    # Try second approve with L2 role
    ok, err = manager.second_approve(rec.request_id, approver_id="analyst_2", role=UserRole.L2_ANALYST)
    assert ok is False
    assert "is not authorized for second approval" in err


def test_dual_control_rejection(manager, sample_proposal):
    action, pol_res = sample_proposal
    rec = manager.create_request(incident_id=action.incident_id, proposed_action=action, policy_result=pol_res)

    ok, res = manager.reject(rec.request_id, rejecter_id="manager_bob", role=UserRole.SOC_MANAGER, reason="Potential false positive")
    assert ok is True
    assert res.status == DualApprovalStatus.REJECTED
    assert res.rejected_by == "manager_bob (SOC_MANAGER)"
    assert res.rejection_reason == "Potential false positive"


def test_dual_control_expiration(tmp_path, sample_proposal):
    store_file = tmp_path / "dual_exp.json"
    manager = DualControlManager(storage_path=store_file, ttl_minutes=0)
    action, pol_res = sample_proposal

    rec = manager.create_request(incident_id=action.incident_id, proposed_action=action, policy_result=pol_res)
    # Manually backdate created_at and expires_at
    rec.expires_at = datetime.now(UTC) - timedelta(seconds=10)
    manager._records[rec.request_id] = rec

    fetched = manager.get(rec.request_id)
    assert fetched.status == DualApprovalStatus.EXPIRED


def test_dual_control_fastapi_endpoints():
    from fastapi.testclient import TestClient
    from dashboard.app import app

    client = TestClient(app)

    # 1. Propose action
    prop_payload = {
        "incident_id": "INC-API-TEST-001",
        "action_type": "BLOCK_IP",
        "target": "10.77.20.99",
        "rule_syntax_preview": "nft add element inet filter soc_blocked { 10.77.20.99 }",
        "rationale": "API integration verification",
        "ttl_minutes": 45,
    }
    resp = client.post("/api/v1/approval/dual/propose", json=prop_payload)
    assert resp.status_code == 200
    data = resp.json()
    req_id = data["request_id"]
    assert data["record"]["status"] == "PENDING_FIRST"

    # 2. First approval
    resp1 = client.post(
        "/api/v1/approval/dual/first-approve",
        json={"request_id": req_id, "approver_id": "analyst_api_1", "role": "L2_ANALYST", "comment": "L2 signoff"}
    )
    assert resp1.status_code == 200
    assert resp1.json()["record"]["status"] == "PENDING_SECOND"

    # 3. Anti-self-approval enforcement via API
    resp_self = client.post(
        "/api/v1/approval/dual/second-approve",
        json={"request_id": req_id, "approver_id": "analyst_api_1", "role": "SOC_MANAGER"}
    )
    assert resp_self.status_code == 400
    assert "distinct first and second approvers" in resp_self.json()["error"]

    # 4. Valid second approval with execution
    resp2 = client.post(
        "/api/v1/approval/dual/second-approve",
        json={"request_id": req_id, "approver_id": "manager_api_2", "role": "SOC_MANAGER", "comment": "Manager approved", "auto_execute": True}
    )
    assert resp2.status_code == 200
    assert resp2.json()["record"]["status"] == "EXECUTED"
    assert "DUAL-CONTROL ACTION EXECUTED" in resp2.json()["execution_output"]

    # 5. Check status endpoint
    resp_stat = client.get(f"/api/v1/approval/dual/status/{req_id}")
    assert resp_stat.status_code == 200
    assert resp_stat.json()["status"] == "EXECUTED"
