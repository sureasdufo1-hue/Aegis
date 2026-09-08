# AI-Orchestrated SOC Copilot Requirements Specification

## 1. Executive Summary & Purpose

The purpose of this specification is to define the functional and non-functional requirements for extending the existing **SOC Detection & Monitoring Lab** (Suricata 8.x, Snort 3, Wazuh SIEM, Correlation Engine) into an **Evidence-Grounded AI Investigation & Orchestration Layer**.

The AI layer functions as a senior triage analyst and orchestration copilot. It does not replace the deterministic detection pipeline or bypass human decision authority. All recommendations are grounded in immutable evidence, verified by an independent deterministic policy engine, and subject to Human-in-the-Loop (HITL) approval prior to execution.

---

## 2. Architecture Invariants

1. **Detection Independence**: Suricata, Snort, and Wazuh remain the primary detection authorities. The AI layer is downstream from alert and correlation generation.
2. **Fail-Closed Availability**: If the AI orchestrator, LLM provider, or RAG retriever becomes unavailable, the core SOC pipeline (packet capture, alert generation, SIEM ingestion, rule-based correlation) continues operating without degradation.
3. **No Autonomous Containment**: The LLM provider is strictly prohibited from executing containment actions or modifying firewall rules directly.
4. **Mandatory Policy Validation**: Every proposed action must pass deterministic policy validation (protected asset collision checks, command injection guards, syntax verification) before reaching the human analyst.
5. **Human Authorization Gate**: Action execution requires explicit review and approval by an authenticated SOC analyst.
6. **Bounded Action Execution**: Initial production mode is constrained to `dry-run` and `ticket_only` execution.

---

## 3. Functional Requirements (FR)

| Requirement ID | Category | Description | Priority | Verification Method |
|---|---|---|---|---|
| **AI-FR-001** | Evidence Normalization | Normalize multi-engine alerts (Suricata EVE, Snort 3, SIEM logs) into structured `SecurityEvidence` objects with network coordinates, alert metadata, and trust levels. | P0 | Unit / Integration Test |
| **AI-FR-002** | Evidence Immutability | Treat raw alert logs and PCAP files as immutable ground truth; store AI triage states in decoupled storage (`approvals_store.json`). | P0 | Automated Test |
| **AI-FR-003** | Read-Only Tools | Provide bounded, read-only investigation tools for SIEM OpenSearch queries, threat intelligence indicators, and PCAP flow inspection. | P0 | Tool Registry Tests |
| **AI-FR-004** | Tool Bounds & Budget | Enforce a strict maximum call limit (default 6–8 calls per investigation session) to prevent infinite loops, tool abuse, and prompt bloat. | P0 | Abuse / Security Test |
| **AI-FR-005** | PCAP Integrity Guard | Verify PCAP files against SHA-256 hashes in `pcap_manifest.json` and block path traversal attempts (`../`) before reading sample files. | P0 | Security Test |
| **AI-FR-006** | Threat Intel Triage | Query internal Threat Intelligence feeds; explicitly forbid assuming an indicator is benign solely due to a cache miss. | P0 | Unit Test |
| **AI-FR-007** | RAG Playbook Grounding | Index markdown playbooks (`playbooks/*.md`) and detection docs (`docs/06-detection/`) with SHA-256 tracking and hybrid keyword retrieval. | P0 | RAG Test |
| **AI-FR-008** | Citation Metadata | Require all RAG-retrieved knowledge references to include document title, chunk identifier, and similarity score. | P1 | Schema Validation |
| **AI-FR-009** | Separation of Facts | Enforce schema-level separation between **Observed Facts**, **Hypotheses**, **Unknowns**, and **Recommended Actions**. | P0 | Pydantic Schema |
| **AI-FR-010** | ATT&CK Mapping | Map correlated multi-stage alerts to MITRE ATT&CK techniques with explicit confidence scores and supporting evidence IDs. | P1 | Schema / Integration |
| **AI-FR-011** | Policy Validation | Deterministically validate all proposed containment actions against protected infrastructure (Gateways, SIEM host, DNS, loopbacks). | P0 | Policy Engine Test |
| **AI-FR-012** | Command Injection Defense | Reject any target IP, CIDR, or identifier containing shell metacharacters (`;`, `&`, `\|`, `` ` ``, `$()`). | P0 | Security Injection Test |
| **AI-FR-013** | HITL Approval Lifecycle | Support full approval lifecycle (`PENDING` -> `APPROVED` / `REJECTED` / `EXPIRED`) with TOCTOU guards and TTL enforcement. | P0 | State Machine Test |
| **AI-FR-014** | Dry-Run Execution | In `DRY_RUN` mode, generate and log syntactically valid `nftables` / `iptables` rule syntax without applying host kernel modifications. | P0 | Execution Test |
| **AI-FR-015** | Dashboard Console | Expose REST endpoints and interactive UI cards on the FastAPI monitoring dashboard (`:8501`) for triage trigger, analysis view, and approval actions. | P0 | E2E API / UI Test |

---

## 4. Non-Functional Requirements (NFR)

| Requirement ID | Category | Description | Target Metric |
|---|---|---|---|
| **AI-NFR-001** | Performance | Investigation orchestration latency (RAG retrieval + tool enrichment + mock reasoning + policy check) | < 2,500 ms (Mock: < 200 ms) |
| **AI-NFR-002** | Token Efficiency | Prompt context budgeting for evidence + RAG chunks + system instructions | Strictly ≤ 8,192 tokens |
| **AI-NFR-003** | Resilience | System behavior when LLM provider or OpenSearch endpoint times out | Fallback to Mock / Graceful Degrade |
| **AI-NFR-004** | Security | Resistance to indirect prompt injection in alert payloads or HTTP URIs | Zero unvetted actions permitted |
| **AI-NFR-005** | Auditability | Persistent logging of all tool invocations, policy decisions, and human approvals | 100% auditable JSON records |
| **AI-NFR-006** | Privacy | Sensitive telemetry exposure | Zero unencrypted external telemetry; local-first processing |
| **AI-NFR-007** | Test Coverage | Automated test pass rate across AI evidence, tools, RAG, policy, security, and dashboard API | 100% PASS (≥ 45 tests) |
| **AI-NFR-008** | Invariant Safety | Protected asset blocking prevention rate | 100% blocked (Fail-Closed) |
