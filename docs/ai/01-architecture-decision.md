# Architecture Decision Records (ADRs)

## ADR-001: AI Orchestrator Architecture

- **Status**: APPROVED
- **Context**: The SOC lab needs an AI investigation and triage layer on top of Suricata, Snort, and Wazuh. Options considered: (1) Heavyweight agentic framework (LangChain/LlamaIndex), (2) Lightweight native Python orchestrator.
- **Decision**: Adopt a **Lightweight Native Python Orchestrator** using Pydantic schemas, explicit tool dispatching, and bounded execution loops.
- **Rationale**:
  1. Full control over tool execution permissions, schema validation, and timeouts without opaque abstraction layers.
  2. Native integration with FastAPI (`dashboard/app.py`) and existing Pydantic v2 models.
  3. Strict 8K token budget compliance without uncontrolled prompt bloat.
  4. Zero heavy extra dependencies; transparent auditing and deterministic testability.

---

## ADR-002: LLM Provider Strategy & Model Tiering

- **Status**: APPROVED
- **Context**: Host is Windows 11 with 64GB RAM and Intel UHD Graphics P750 (no dedicated CUDA GPU). Ollama is not installed by default in the execution environment.
- **Decision**: Provide an extensible `LLMProvider` abstract interface with 3 concrete implementations:
  1. `MockLLMProvider`: Deterministic, grounded provider for zero-cost offline CI/CD, unit tests, and security regression checks.
  2. `OllamaProvider`: Native HTTP adapter to local/remote Ollama instance (`http://localhost:11434`), supporting `qwen2.5:7b` / `qwen2.5:14b` or user-specified model.
  3. `OpenAICompatibleProvider`: Generic adapter for OpenAI/Gemini REST endpoints, **disabled by default** to avoid untrusted external telemetry leakage.
- **Fail-safe Invariant**: If the LLM provider fails, times out, or is offline, the primary SOC pipeline (Suricata/Snort -> Wazuh -> Correlation -> Dashboard) continues operating normally without degradation.

---

## ADR-003: AI State & Evidence Storage Model

- **Status**: APPROVED
- **Context**: Where should AI-generated incident analyses, proposed actions, and approval audit logs be stored?
- **Decision**: Maintain a separate in-memory / JSON-backed persistent store (`analyzer/ai/approvals/repository.py`) decoupled from raw alert logs.
- **Rationale**:
  1. Raw alerts (`eve.json`, `alerts.json`, OpenSearch docs) remain immutable ground truth.
  2. AI analysis objects, hypotheses, and human approval decisions are distinct audit entities with their own lifecycle.

---

## ADR-004: Action Execution & Policy Validation Boundaries

- **Status**: APPROVED
- **Context**: Can the AI Orchestrator directly alter firewall rules or block IP addresses?
- **Decision**:
  1. Default mode: `AI_ACTIONS_ENABLED=false`, `AI_ACTION_MODE=dry-run`.
  2. **Zero Autonomous Execution**: The LLM can ONLY propose actions (`RecommendedAction`).
  3. **Deterministic Policy Validation**: An independent Python policy engine (`PolicyValidator`) verifies protected assets (Gateway, DNS, SIEM), syntax, and CIDR safety.
  4. **Human in the Loop (HITL)**: A human SOC analyst must explicitly click "Approve" or "Reject" via the FastAPI UI / REST API.
  5. **Bounded Execution**: Even when approved, only pre-registered dry-run or safe adapter scripts execute; no arbitrary shell commands are ever accepted from the LLM.
