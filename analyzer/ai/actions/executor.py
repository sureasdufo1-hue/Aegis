from datetime import UTC, datetime

from analyzer.ai.schemas.actions import ActionApprovalRecord, ApprovalStatus, ExecutionMode


class ActionExecutor:
    """
    Bounded Action Executor.
    Executes ONLY human-approved and policy-validated actions.
    Adheres strictly to ADR-004 (Dry-run & Ticket generation initially; zero unauthorized live execution).
    """

    def __init__(self, mode: ExecutionMode = ExecutionMode.DRY_RUN):
        self.mode = mode

    def execute_approved_action(self, record: ActionApprovalRecord) -> tuple[bool, str]:
        # Pre-execution Invariant Checks
        if record.status != ApprovalStatus.APPROVED:
            return False, f"Action execution rejected: Status is '{record.status.value}', expected 'APPROVED'."

        if not record.policy_validation.is_valid:
            return False, "Action execution rejected: Policy validation failed."

        action = record.proposed_action
        timestamp = datetime.now(UTC).isoformat()

        if self.mode in [ExecutionMode.DRY_RUN, ExecutionMode.MOCK]:
            output = (
                f"[DRY-RUN EXECUTION SIMULATION] {timestamp}\n"
                f"Action Type: {action.action_type.value}\n"
                f"Target: {action.target} (Direction: {action.direction.value})\n"
                f"Generated Rule Syntax:\n"
                f"  {action.rule_syntax_preview}\n"
                f"Quarantine TTL: {action.duration_minutes} minutes\n"
                f"Status: PASS (Simulated Dry Run Success - Zero host modification)"
            )
            record.status = ApprovalStatus.EXECUTED
            record.executed_at = datetime.now(UTC)
            record.execution_output = output
            return True, output

        elif self.mode == ExecutionMode.TICKET_ONLY:
            ticket_id = f"SEC-TICKET-{action.proposal_id}"
            output = (
                f"[SECURITY INCIDENT TICKET CREATED] {timestamp}\n"
                f"Ticket ID: {ticket_id}\n"
                f"Incident Ref: {record.incident_id}\n"
                f"Recommended Action: {action.action_type.value} on {action.target}\n"
                f"Rule Preview: {action.rule_syntax_preview}\n"
                f"Assigned To: NetSec Tier 2 Operations"
            )
            record.status = ApprovalStatus.EXECUTED
            record.executed_at = datetime.now(UTC)
            record.execution_output = output
            return True, output

        return False, f"Unsupported execution mode: {self.mode}"
