# AI-Orchestrated SOC Copilot Implementation Plan

## 1. Implementation Strategy & Milestones

The expansion of the SOC Detection Lab into an AI-orchestrated copilot was executed in 11 strictly phased milestones. Each milestone maintained the **Zero Regression** invariant against the existing 22/22 baseline test suite.

---

## 2. Milestone Breakdown & Deliverables

```text
Phase AI-0: Host Assessment & Architecture Decision Records (ADRs)
      │
      ▼
Phase AI-1: Data Contracts & Pydantic Schemas
      │
      ▼
Phase AI-2: Read-Only Tool Development & Sandbox Guards
      │
      ▼
Phase AI-3: RAG Knowledge Store & Playbook Provenance Indexing
      │
      ▼
Phase AI-4: LLM Provider Layer (Mock Baseline + Local Ollama)
      │
      ▼
Phase AI-5: Deterministic Policy Engine & Infrastructure Whitelist
      │
      ▼
Phase AI-6: HITL Approval Repository & Bounded Action Executor
      │
      ▼
Phase AI-7: AI Investigation Orchestrator Pipeline
      │
      ▼
Phase AI-8: Adversarial & Injection Security Testing
      │
      ▼
Phase AI-9: Dashboard REST API & Real-Time Web Console
      │
      ▼
Phase AI-10: Live End-to-End Lab Validation & Verification
```

---

## 3. Detailed Milestone Status

| Phase | Scope & Deliverables | Verification Artifact | Status |
|---|---|---|---|
| **Phase AI-0** | Host resource survey, GPU/RAM inventory, ADR-001 through ADR-004. | `docs/ai/00-current-baseline-assessment.md`<br>`docs/ai/01-architecture-decision.md` | **PASS** |
| **Phase AI-1** | Evidence, Analysis, Action schemas with Pydantic v2. | `analyzer/ai/schemas/` (evidence, analysis, actions)<br>`tests/test_ai_evidence.py` | **PASS** |
| **Phase AI-2** | SIEM OpenSearch tool, Threat Intel tool, PCAP tool, ToolRegistry. | `analyzer/ai/tools/`<br>`tests/test_ai_tools.py` | **PASS** |
| **Phase AI-3** | Markdown chunking, SHA-256 indexing, hybrid retriever. | `analyzer/ai/rag/`<br>`tests/test_ai_rag.py` | **PASS** |
| **Phase AI-4** | `BaseLLMProvider`, `MockLLMProvider`, `OllamaProvider`. | `analyzer/ai/providers/` | **PASS** |
| **Phase AI-5** | Protected asset whitelist, syntax validation, fail-closed policy. | `analyzer/ai/policy/`<br>`tests/test_ai_policy_approval.py` | **PASS** |
| **Phase AI-6** | `ApprovalRepository` (TOCTOU, JSON store), `ActionExecutor` (Dry-run). | `analyzer/ai/approvals/`<br>`analyzer/ai/actions/` | **PASS** |
| **Phase AI-7** | `AIOrchestrator` combining evidence, tools, RAG, LLM, policy, approvals. | `analyzer/ai/orchestrator.py`<br>`tests/test_ai_orchestrator.py` | **PASS** |
| **Phase AI-8** | Indirect prompt injection, path traversal, tool abuse, empty target tests. | `tests/test_ai_security.py` | **PASS** |
| **Phase AI-9** | FastAPI endpoints (`/api/ai/*`, `/api/action-proposals/*`), interactive UI. | `dashboard/app.py`<br>`tests/test_dashboard_ai_api.py` | **PASS** |
| **Phase AI-10**| Live incident triage, HITL approve/reject cycle on port 8501. | Live curl/REST outputs, full documentation in `docs/ai/` | **PASS** |

---

## 4. Invariant Preservation Checklist

- [x] All 22 original SOC tests continue to pass without modification.
- [x] Suricata and Snort rule engines remain primary detection sources.
- [x] Wazuh SIEM continues ingesting `eve.json` independently of AI layer.
- [x] Zero unapproved live firewall modifications (dry-run mode enforced).
- [x] Zero protected asset blockages allowed by policy engine.
- [x] Zero API keys or sensitive secrets committed to Git repository.
