import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from analyzer.ai.schemas.actions import (
    ActionApprovalRecord,
    ApprovalStatus,
    ExecutionMode,
    PolicyValidationResult,
    ProposedAction,
)


class ApprovalRepository:
    """
    In-memory and JSON-backed Repository for HITL Approval Records.
    Maintains persistent audit trail of AI proposals, policy checks, and human decisions.
    """

    def __init__(self, storage_path: Path | None = None):
        self.storage_path = storage_path or Path("logs/approvals_store.json")
        self._records: dict[str, ActionApprovalRecord] = {}
        self._load()

    def _load(self) -> None:
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text(encoding="utf-8"))
                for item in data:
                    rec = ActionApprovalRecord.model_validate(item)
                    self._records[rec.approval_id] = rec
            except Exception:
                pass

    def _save(self) -> None:
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            export_data = [r.model_dump(mode="json") for r in self._records.values()]
            self.storage_path.write_text(json.dumps(export_data, indent=2), encoding="utf-8")
        except Exception:
            pass

    def create_approval_request(
        self,
        incident_id: str,
        proposed_action: ProposedAction,
        policy_result: PolicyValidationResult,
        ttl_minutes: int = 60,
    ) -> ActionApprovalRecord:
        approval_id = f"APR-{incident_id[-8:]}-{len(self._records)+1:03d}"
        now = datetime.now(UTC)
        record = ActionApprovalRecord(
            approval_id=approval_id,
            incident_id=incident_id,
            proposed_action=proposed_action,
            policy_validation=policy_result,
            status=ApprovalStatus.PENDING,
            execution_mode=ExecutionMode.DRY_RUN,
            created_at=now,
            expires_at=now + timedelta(minutes=ttl_minutes),
        )
        self._records[approval_id] = record
        self._save()
        return record

    def get(self, approval_id: str) -> ActionApprovalRecord | None:
        rec = self._records.get(approval_id)
        if rec and rec.status == ApprovalStatus.PENDING and rec.expires_at:
            if datetime.now(UTC) > rec.expires_at:
                rec.status = ApprovalStatus.EXPIRED
                self._save()
        return rec

    def list_all(self, incident_id: str | None = None) -> list[ActionApprovalRecord]:
        records = list(self._records.values())
        if incident_id:
            records = [r for r in records if r.incident_id == incident_id]
        records.sort(key=lambda x: x.created_at, reverse=True)
        return records

    def review_approval(
        self,
        approval_id: str,
        decision: ApprovalStatus,  # APPROVED or REJECTED
        reviewer: str = "soc-analyst",
        notes: str | None = None,
    ) -> tuple[bool, ActionApprovalRecord | str]:
        rec = self.get(approval_id)
        if not rec:
            return False, f"Approval request '{approval_id}' not found."

        if rec.status != ApprovalStatus.PENDING:
            return False, f"Cannot review approval in status '{rec.status.value}' (TOCTOU guard)."

        if decision == ApprovalStatus.APPROVED and not rec.policy_validation.is_valid:
            return False, f"Cannot approve action: Policy validation failed ({rec.policy_validation.verdict})."

        rec.status = decision
        rec.reviewed_by = reviewer
        rec.reviewed_at = datetime.now(UTC)
        rec.review_notes = notes or ("Approved by analyst" if decision == ApprovalStatus.APPROVED else "Rejected by analyst")
        self._save()
        return True, rec
