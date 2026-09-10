import ipaddress
from datetime import UTC, datetime

from analyzer.ai.policy.protected_assets import is_protected_asset
from analyzer.ai.schemas.actions import (
    ActionType,
    PolicyValidationResult,
    PolicyVerdict,
    ProposedAction,
)

DANGEROUS_SHELL_CHARACTERS = [";", "&&", "||", "|", "`", "$", "(", ")", "\n", "\r", "<", ">"]


class PolicyValidator:
    """
    Deterministic External Policy Engine.
    Validates any AI-proposed action independently of LLM reasoning.
    Enforces Fail-Closed security: Any ambiguity or policy violation triggers rejection.
    """

    @staticmethod
    def validate_proposal(action: ProposedAction) -> PolicyValidationResult:
        violations: list[str] = []
        target = action.target.strip()

        # 1. Syntax & Command Injection Guard
        for char in DANGEROUS_SHELL_CHARACTERS:
            if char in target or char in action.rule_syntax_preview:
                violations.append(f"Dangerous character '{char}' detected in target or rule preview.")
                return PolicyValidationResult(
                    is_valid=False,
                    verdict=PolicyVerdict.DENIED_SYNTAX_ERROR,
                    target=target,
                    violations=violations,
                    validated_at=datetime.now(UTC),
                )

        # 2. IP / Target Format Validation
        try:
            if "/" in target:
                ipaddress.ip_network(target, strict=False)
            else:
                ipaddress.ip_address(target)
        except ValueError:
            violations.append(f"Target '{target}' is not a valid IPv4 or IPv6 address/CIDR.")
            return PolicyValidationResult(
                is_valid=False,
                verdict=PolicyVerdict.DENIED_INVALID_TARGET,
                target=target,
                violations=violations,
                validated_at=datetime.now(UTC),
            )

        # 3. Protected Asset Whitelist Check (P0 Safety Invariant)
        if action.action_type in [ActionType.BLOCK_IP, ActionType.ISOLATE_HOST, ActionType.RATE_LIMIT]:
            is_prot, prot_detail = is_protected_asset(target)
            if is_prot:
                violations.append(f"Target '{target}' is a PROTECTED CRITICAL ASSET: {prot_detail}")
                return PolicyValidationResult(
                    is_valid=False,
                    verdict=PolicyVerdict.DENIED_PROTECTED_ASSET,
                    target=target,
                    violations=violations,
                    protected_asset_details=prot_detail,
                    validated_at=datetime.now(UTC),
                )

        # 4. Action Type Validation
        if action.action_type not in ActionType:
            violations.append(f"Unsupported action type: '{action.action_type}'")
            return PolicyValidationResult(
                is_valid=False,
                verdict=PolicyVerdict.DENIED_FAIL_CLOSED,
                target=target,
                violations=violations,
                validated_at=datetime.now(UTC),
            )

        # Passed all policy checks
        return PolicyValidationResult(
            is_valid=True,
            verdict=PolicyVerdict.ALLOWED,
            target=target,
            violations=[],
            validated_at=datetime.now(UTC),
        )
