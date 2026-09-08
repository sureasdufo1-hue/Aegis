# UI/UX & Korean Interpretation Requirements Specification

## 1. Functional Requirements (UI-FR)

| Requirement ID | Category | Description | Priority | Verification |
|---|---|---|---|---|
| **UI-FR-001** | View Mode Switching | Provide a segmented control (`[원문 (EN)]`, `[한국어 (KO)]`, `[나란히 보기 (Split)]`) persistent across browser sessions via `localStorage`. | P0 | Browser / Unit Test |
| **UI-FR-002** | Deterministic Dictionary | Expose a REST endpoint (`/api/localization/dictionary`) delivering standardized Korean translations for severities, engines, attack stages, policy verdicts, and approval statuses. | P0 | API Test |
| **UI-FR-003** | Semantic Interpretation | Provide on-demand Korean interpretation (`POST /api/ai/interpret`) explaining attack mechanics, threat meaning, and concrete analyst checklists. | P0 | API Test |
| **UI-FR-004** | Interpretation Caching | Cache interpretation outputs in-memory using SHA-256 keys of signature/incident text to eliminate redundant processing and ensure sub-millisecond response. | P0 | Unit / Cache Test |
| **UI-FR-005** | Compromise Distinction | Every interpretation must explicitly state that a detection alert does not automatically equate to a confirmed compromise without response log verification. | P0 | Content Validation |
| **UI-FR-006** | Action Separation | Strictly separate the **`[한국어 해석]`** button (signature explanation) from the **`[🤖 AI 심층 조사]`** button (multi-tool RAG investigation and containment proposal). | P0 | UI / Functional Test |
| **UI-FR-007** | Provider Transparency | Dynamically inspect `/api/ai/health` and display whether the system is operating in `모의 분석 기준선 (Mock Baseline)` or `로컬 LLM (Ollama)`. | P0 | API / UI Test |
| **UI-FR-008** | Attack Timeline | Render a sequential, visual killchain timeline for correlated incidents with distinct badges for Recon, Initial Access, and C2 stages. | P0 | Visual / E2E Test |
| **UI-FR-009** | Evidence Inspector | Provide a modal inspector for raw alert data showing timestamps (KST/UTC), flow ID, community ID, HTTP URI, User-Agent, and raw JSON payloads. | P0 | Functional Test |
| **UI-FR-010** | Unambiguous Containment | Explicitly label containment buttons as `[모의 실행 승인 (Dry-Run)]` and `[반려]` to eliminate confusion with live kernel firewall modifications. | P0 | UI Test |
| **UI-FR-011** | Interactive Filtering | Support real-time search across IPs, SIDs, signatures, and categories, paired with severity filter buttons (`ALL`, `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`). | P1 | Functional Test |
| **UI-FR-012** | XSS Defense | Escape all dynamic log, alert, and AI strings using `escapeHTML()` prior to DOM insertion to prevent script injection. | P0 | Security Test |

---

## 2. Non-Functional Requirements (UI-NFR)

| Requirement ID | Category | Target Metric / Constraint |
|---|---|---|
| **UI-NFR-001** | Performance | View mode toggle execution time < 50ms; dictionary retrieval < 100ms. |
| **UI-NFR-002** | Accessibility | High contrast text ratios compliant with WCAG 2.2 AA (≥ 4.5:1 for normal text). |
| **UI-NFR-003** | Typography | Use Pretendard for Korean readability and JetBrains Mono for IPs, ports, SIDs, and timestamps. |
| **UI-NFR-004** | Responsiveness | Seamless multi-column desktop layout (≥ 1280px) and single-column stacked layout on tablet/mobile. |
| **UI-NFR-005** | Zero Dependency Bloat | Single-page FastAPI HTML response with CDN resources; zero external build steps or `node_modules` overhead. |
| **UI-NFR-006** | Evidence Immutability | Presentation layer localization must NEVER alter raw logs, EVE events, PCAP files, or Git hashes. |
