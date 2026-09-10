from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ActionType(StrEnum):
    BLOCK_IP = "BLOCK_IP"
    ISOLATE_HOST = "ISOLATE_HOST"
    RATE_LIMIT = "RATE_LIMIT"
    GENERATE_TICKET = "GENERATE_TICKET"
    TUNE_RULE = "TUNE_RULE"


class Direction(StrEnum):
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"
    BOTH = "BOTH"


class ExecutionMode(StrEnum):
    DRY_RUN = "DRY_RUN"
    TICKET_ONLY = "TICKET_ONLY"
    MOCK = "MOCK"
    LIVE = "LIVE"


class PolicyVerdict(StrEnum):
    ALLOWED = "ALLOWED"
    DENIED_PROTECTED_ASSET = "DENIED_PROTECTED_ASSET"
    DENIED_INVALID_TARGET = "DENIED_INVALID_TARGET"
    DENIED_SYNTAX_ERROR = "DENIED_SYNTAX_ERROR"
    DENIED_FAIL_CLOSED = "DENIED_FAIL_CLOSED"


class PolicyValidationResult(BaseModel):
    is_valid: bool = False
    verdict: PolicyVerdict = PolicyVerdict.DENIED_FAIL_CLOSED
    target: str
    violations: list[str] = Field(default_factory=list)
    protected_asset_details: str | None = None
    validated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ProposedAction(BaseModel):
    proposal_id: str = Field(description="Unique proposal ID, e.g. PROP-xxx")
    incident_id: str
    action_type: ActionType
    target: str = Field(description="Target IP, CIDR, or rule identifier")
    direction: Direction = Direction.INBOUND
    duration_minutes: int = Field(default=60, description="Recommended temporary quarantine TTL")
    rule_syntax_preview: str = Field(description="Exact dry-run firewall rule preview")
    rationale: str = Field(description="Grounded explanation for this proposed action")


class ApprovalStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"


class ActionApprovalRecord(BaseModel):
    """
    Human-in-the-Loop (HITL) Action Approval Object.
    Separates AI recommendations from deterministic policy verification and human authorization.
    """
    approval_id: str = Field(description="Unique approval record ID, e.g. APR-xxx")
    incident_id: str
    proposed_action: ProposedAction
    policy_validation: PolicyValidationResult
    status: ApprovalStatus = ApprovalStatus.PENDING
    execution_mode: ExecutionMode = ExecutionMode.DRY_RUN
    
    # Audit trail
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    review_notes: str | None = None
    
    # Execution telemetry
    execution_output: str | None = None
    executed_at: datetime | None = None
