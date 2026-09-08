# AI-Orchestrated SOC Copilot Test Plan & Verification Strategy

## 1. Objectives & Quality Gates

The primary objective of the testing strategy is to guarantee that the AI layer enhances analyst triage capability without compromising the deterministic integrity, availability, or security of the underlying SOC lab.

### Critical Quality Gates:
- **GATE-AI-01 (Zero Regression)**: 100% pass rate on the 22 pre-existing SOC detection, parser, correlation, and Phase 31 tests.
- **GATE-AI-02 (Schema Fidelity)**: Strict validation of Pydantic models for evidence, analysis, and actions.
- **GATE-AI-03 (Security & Injection Resistance)**: Deterministic policy engine blocks 100% of protected asset collisions and command injection attempts.
- **GATE-AI-04 (HITL State Machine)**: Approval transitions strictly honor TOCTOU, expiration, and analyst attribution.
- **GATE-AI-05 (API & UI Integration)**: All FastAPI AI endpoints and dashboard components return HTTP 200 with valid schemas.

---

## 2. Test Suite Inventory

| Test Module | Scope | Test Cases | Target Component |
|---|---|---|---|
| `tests/test_ai_evidence.py` | Evidence normalization & untrusted payload handling | 2 | `analyzer/ai/schemas/evidence.py` |
| `tests/test_ai_tools.py` | Read-only tools, SIEM query bounds, PCAP hash checks, TI lookups | 5 | `analyzer/ai/tools/` |
| `tests/test_ai_rag.py` | Markdown chunking, SHA-256 tracking, playbook retrieval | 2 | `analyzer/ai/rag/` |
| `tests/test_ai_policy_approval.py` | Protected assets detection, approval state machine, dry-run execution | 4 | `analyzer/ai/policy/`, `analyzer/ai/approvals/` |
| `tests/test_ai_orchestrator.py` | End-to-end incident investigation orchestration pipeline | 1 | `analyzer/ai/orchestrator.py` |
| `tests/test_ai_security.py` | Prompt injection, arbitrary tool abuse, PCAP path traversal, fail-closed target | 4 | Security boundaries & Policy engine |
| `tests/test_dashboard_ai_api.py` | FastAPI endpoints: health, protected assets, triage, approve, reject | 7 | `dashboard/app.py` |
| **Baseline SOC Suites** | Parsers, detection tuning, correlation, Phase 31 E2E, Threat Intel | 22 | Core detection & monitoring lab |
| **Total Automated Tests** | | **47** | **100% Pass Rate Target** |

---

## 3. Key Test Scenarios & Acceptance Criteria

### 3.1 Security & Injection Tests (`tests/test_ai_security.py`)
1. **Indirect Prompt Injection in Containment Target**:
   - Input: Adversary embeds injection payload `10.77.20.20; rm -rf / ;` or targets protected gateway `10.77.10.1`.
   - Assertion: `PolicyValidator.validate_proposal(...)` rejects the proposal with `is_valid == False` and `verdict in [DENIED_SYNTAX_ERROR, DENIED_PROTECTED_ASSET]`.
2. **Arbitrary Tool Abuse**:
   - Input: Attacker attempts to invoke an unregistered tool (e.g. `run_bash_command`).
   - Assertion: `ToolRegistry.execute_tool(...)` returns `success == False` with an explicit authorization error.
3. **PCAP Path Traversal Guard**:
   - Input: Tool invocation attempts to read `../../../../etc/passwd` or an unlisted file.
   - Assertion: `PcapInspectionTool` detects path traversal and returns an error without opening the file.

### 3.2 HITL Approval & Policy Tests (`tests/test_ai_policy_approval.py`)
1. **Policy-Violating Proposal Cannot Be Approved**:
   - Attempt: SOC analyst (or automated script) attempts to approve a proposal targeting `10.77.10.1`.
   - Assertion: `ApprovalRepository.review_approval(...)` returns `(False, "Cannot approve action: Policy validation failed...")`.
2. **Dry-Run Rule Generation**:
   - Action: Approved proposal executed via `ActionExecutor(mode=ExecutionMode.DRY_RUN)`.
   - Assertion: Returns simulated `nftables` syntax without making live kernel modifications; status transitions to `EXECUTED`.

---

## 4. Execution Command

```powershell
pytest tests/ -v
```

Expected Outcome: **47 passed in ~1.1s**.
