from analyzer.ai.actions.executor import ActionExecutor
from analyzer.ai.approvals.repository import ApprovalRepository
from analyzer.ai.policy.protected_assets import is_protected_asset
from analyzer.ai.policy.validator import PolicyValidator
from analyzer.ai.schemas.actions import (
    ActionType,
    ApprovalStatus,
    Direction,
    ExecutionMode,
    PolicyVerdict,
    ProposedAction,
)


def test_protected_assets_detection():
    # Gateway IP
    is_prot, desc = is_protected_asset("10.77.10.1")
    assert is_prot is True
    assert "Gateway" in desc

    # SIEM / Host MGMT
    is_prot, desc = is_protected_asset("10.77.10.10")
    assert is_prot is True

    # DNS
    is_prot, desc = is_protected_asset("8.8.8.8")
    assert is_prot is True

    # Host in MGMT subnet
    is_prot, desc = is_protected_asset("10.77.10.99")
    assert is_prot is True

    # Malicious attacker IP
    is_prot, desc = is_protected_asset("10.77.20.20")
    assert is_prot is False


def test_policy_validator_rejects_protected_asset_blocking():
    # Attempting to block the gateway
    bad_proposal = ProposedAction(
        proposal_id="PROP-BAD-01",
        incident_id="INC-001",
        action_type=ActionType.BLOCK_IP,
        target="10.77.10.1",
        direction=Direction.INBOUND,
        rule_syntax_preview="nft add rule inet filter input ip saddr 10.77.10.1 drop",
        rationale="False positive block suggestion",
    )

    result = PolicyValidator.validate_proposal(bad_proposal)
    assert result.is_valid is False
    assert result.verdict == PolicyVerdict.DENIED_PROTECTED_ASSET
    assert len(result.violations) > 0


def test_policy_validator_allows_attacker_blocking():
    valid_proposal = ProposedAction(
        proposal_id="PROP-VALID-01",
        incident_id="INC-002",
        action_type=ActionType.BLOCK_IP,
        target="10.77.20.20",
        direction=Direction.INBOUND,
        rule_syntax_preview="nft add rule inet filter input ip saddr 10.77.20.20 counter drop",
        rationale="Hostile scanning and exploitation source",
    )

    result = PolicyValidator.validate_proposal(valid_proposal)
    assert result.is_valid is True
    assert result.verdict == PolicyVerdict.ALLOWED


def test_approval_state_machine_and_executor_dry_run():
    repo = ApprovalRepository()
    executor = ActionExecutor(mode=ExecutionMode.DRY_RUN)

    proposal = ProposedAction(
        proposal_id="PROP-TEST-02",
        incident_id="INC-TEST-002",
        action_type=ActionType.BLOCK_IP,
        target="10.77.20.20",
        direction=Direction.INBOUND,
        rule_syntax_preview="nft add rule inet filter input ip saddr 10.77.20.20 counter drop",
        rationale="Active attacker quarantine",
    )
    policy_res = PolicyValidator.validate_proposal(proposal)

    # 1. Create approval record
    rec = repo.create_approval_request("INC-TEST-002", proposal, policy_res)
    assert rec.status == ApprovalStatus.PENDING

    # Cannot execute while PENDING
    exec_ok, _ = executor.execute_approved_action(rec)
    assert exec_ok is False

    # 2. Approve via HITL
    ok, updated = repo.review_approval(rec.approval_id, ApprovalStatus.APPROVED, reviewer="analyst-kim")
    assert ok is True
    assert updated.status == ApprovalStatus.APPROVED
    assert updated.reviewed_by == "analyst-kim"

    # TOCTOU guard: cannot re-review
    ok_retry, _ = repo.review_approval(rec.approval_id, ApprovalStatus.REJECTED)
    assert ok_retry is False

    # 3. Execute approved action in dry-run mode
    exec_ok, output = executor.execute_approved_action(updated)
    assert exec_ok is True
    assert updated.status == ApprovalStatus.EXECUTED
    assert "DRY-RUN EXECUTION SIMULATION" in output
    assert "nft add rule" in output
