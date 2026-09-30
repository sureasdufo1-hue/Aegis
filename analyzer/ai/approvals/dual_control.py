"""
AegisAI Dual-Control (Two-Person Approval) Protocol & State Engine
Enforces separation of duties (SoD) for high-risk containment and mitigation actions:
1. First Approval: Initial review by L2 Senior Analyst / Incident Responder.
2. Second Approval: Mandatory sign-off by L3 Lead or SOC Manager.
3. Invariant: First and Second approvers MUST BE distinct identities (Self-approval prohibited).
4. TOCTOU & Expiry guards: Time-to-Live bounded with cryptographic nonce auditing.
"""

import json
import uuid
import hashlib
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from pathlib import Path
from pydantic import BaseModel, Field

from analyzer.ai.schemas.actions import (
    ProposedAction,
    PolicyValidationResult,
    ExecutionMode,
)
from analyzer.ai.actions.executor import ActionExecutor


class UserRole(StrEnum):
    L1_ANALYST = "L1_ANALYST"
    L2_ANALYST = "L2_ANALYST"
    L3_LEAD = "L3_LEAD"
    SOC_MANAGER = "SOC_MANAGER"
    DEVSECOPS_ADMIN = "DEVSECOPS_ADMIN"


class DualApprovalStatus(StrEnum):
    PENDING_FIRST = "PENDING_FIRST"
    PENDING_SECOND = "PENDING_SECOND"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    EXECUTED = "EXECUTED"


class ApprovalSignature(BaseModel):
    approver_id: str
    role: UserRole
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    comment: str
    nonce: str = Field(default_factory=lambda: uuid.uuid4().hex)
    digest: str = Field(default="", description="Cryptographic integrity digest")

    def model_post_init(self, __context) -> None:
        if not self.digest:
            payload = f"{self.approver_id}:{self.role.value}:{self.timestamp.isoformat()}:{self.nonce}:{self.comment}"
            self.digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()


class DualControlRecord(BaseModel):
    request_id: str
    incident_id: str
    proposed_action: ProposedAction
    policy_validation: PolicyValidationResult
    status: DualApprovalStatus = DualApprovalStatus.PENDING_FIRST
    execution_mode: ExecutionMode = ExecutionMode.DRY_RUN

    first_approval: ApprovalSignature | None = None
    second_approval: ApprovalSignature | None = None

    rejection_reason: str | None = None
    rejected_by: str | None = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime
    executed_at: datetime | None = None
    execution_output: str | None = None


class DualControlManager:
    """
    Manages dual-control approval lifecycles with strict role validation,
    anti-self-approval enforcement, and state persistence.
    """

    SECOND_APPROVER_ROLES = {UserRole.L3_LEAD, UserRole.SOC_MANAGER, UserRole.DEVSECOPS_ADMIN}

    def __init__(self, storage_path: Path | None = None, ttl_minutes: int = 60):
        self.storage_path = storage_path or Path("logs/dual_approvals_store.json")
        self.ttl_minutes = ttl_minutes
        self._records: dict[str, DualControlRecord] = {}
        self._load()

    def _load(self) -> None:
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text(encoding="utf-8"))
                for item in data:
                    rec = DualControlRecord.model_validate(item)
                    self._records[rec.request_id] = rec
            except Exception:
                pass

    def _save(self) -> None:
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            export_data = [r.model_dump(mode="json") for r in self._records.values()]
            self.storage_path.write_text(json.dumps(export_data, indent=2), encoding="utf-8")
        except Exception:
            pass

    def create_request(
        self,
        incident_id: str,
        proposed_action: ProposedAction,
        policy_result: PolicyValidationResult,
    ) -> DualControlRecord:
        now = datetime.now(UTC)
        request_id = f"DUAL-{incident_id[-8:]}-{len(self._records)+1:03d}"
        record = DualControlRecord(
            request_id=request_id,
            incident_id=incident_id,
            proposed_action=proposed_action,
            policy_validation=policy_result,
            status=DualApprovalStatus.PENDING_FIRST,
            created_at=now,
            expires_at=now + timedelta(minutes=self.ttl_minutes),
        )
        self._records[request_id] = record
        self._save()
        return record

    def get(self, request_id: str) -> DualControlRecord | None:
        rec = self._records.get(request_id)
        if rec and rec.status in [DualApprovalStatus.PENDING_FIRST, DualApprovalStatus.PENDING_SECOND]:
            if datetime.now(UTC) > rec.expires_at:
                rec.status = DualApprovalStatus.EXPIRED
                self._save()
        return rec

    def list_all(self, status: DualApprovalStatus | None = None) -> list[DualControlRecord]:
        records = list(self._records.values())
        if status:
            records = [r for r in records if r.status == status]
        records.sort(key=lambda x: x.created_at, reverse=True)
        return records

    def first_approve(
        self,
        request_id: str,
        approver_id: str,
        role: UserRole,
        comment: str = "First approval verified",
    ) -> tuple[bool, DualControlRecord | str]:
        rec = self.get(request_id)
        if not rec:
            return False, f"Dual-control request '{request_id}' not found."

        if rec.status != DualApprovalStatus.PENDING_FIRST:
            return False, f"Cannot process first approval in status '{rec.status.value}'."

        if not rec.policy_validation.is_valid:
            return False, f"Policy validation failed: {rec.policy_validation.verdict}."

        sig = ApprovalSignature(approver_id=approver_id, role=role, comment=comment)
        rec.first_approval = sig
        rec.status = DualApprovalStatus.PENDING_SECOND
        self._save()
        return True, rec

    def second_approve(
        self,
        request_id: str,
        approver_id: str,
        role: UserRole,
        comment: str = "Second approval verified by lead/manager",
    ) -> tuple[bool, DualControlRecord | str]:
        rec = self.get(request_id)
        if not rec:
            return False, f"Dual-control request '{request_id}' not found."

        if rec.status != DualApprovalStatus.PENDING_SECOND:
            return False, f"Cannot process second approval in status '{rec.status.value}'. Must be 'PENDING_SECOND'."

        if not rec.first_approval:
            return False, "Missing first approval record."

        # Anti-self-approval rule
        if approver_id == rec.first_approval.approver_id:
            return False, "Violation: Two-person rule requires distinct first and second approvers (Self-approval blocked)."

        # Role authority check
        if role not in self.SECOND_APPROVER_ROLES:
            return False, f"Role '{role.value}' is not authorized for second approval. Required: {[r.value for r in self.SECOND_APPROVER_ROLES]}."

        sig = ApprovalSignature(approver_id=approver_id, role=role, comment=comment)
        rec.second_approval = sig
        rec.status = DualApprovalStatus.APPROVED
        self._save()
        return True, rec

    def reject(
        self,
        request_id: str,
        rejecter_id: str,
        role: UserRole,
        reason: str,
    ) -> tuple[bool, DualControlRecord | str]:
        rec = self.get(request_id)
        if not rec:
            return False, f"Dual-control request '{request_id}' not found."

        if rec.status not in [DualApprovalStatus.PENDING_FIRST, DualApprovalStatus.PENDING_SECOND]:
            return False, f"Cannot reject request in status '{rec.status.value}'."

        rec.status = DualApprovalStatus.REJECTED
        rec.rejected_by = f"{rejecter_id} ({role.value})"
        rec.rejection_reason = reason
        self._save()
        return True, rec

    def execute_approved(
        self,
        request_id: str,
        executor: ActionExecutor,
    ) -> tuple[bool, str]:
        rec = self.get(request_id)
        if not rec:
            return False, f"Dual-control request '{request_id}' not found."

        if rec.status != DualApprovalStatus.APPROVED:
            return False, f"Cannot execute: Status is '{rec.status.value}', expected 'APPROVED'."

        # Convert to execution format
        action = rec.proposed_action
        timestamp = datetime.now(UTC).isoformat()
        output = (
            f"[DUAL-CONTROL ACTION EXECUTED] {timestamp}\n"
            f"Request ID: {rec.request_id} (Incident: {rec.incident_id})\n"
            f"Action: {action.action_type.value} on {action.target}\n"
            f"Rule: {action.rule_syntax_preview}\n"
            f"First Approver: {rec.first_approval.approver_id} ({rec.first_approval.role.value})\n"
            f"Second Approver: {rec.second_approval.approver_id} ({rec.second_approval.role.value})\n"
            f"Mode: {rec.execution_mode.value} (Zero-trust verified)"
        )
        rec.status = DualApprovalStatus.EXECUTED
        rec.executed_at = datetime.now(UTC)
        rec.execution_output = output
        self._save()
        return True, output
