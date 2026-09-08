# Information Architecture & User Journey Design

## 1. Information Architecture (IA) Overview

The SOC console information hierarchy organizes operational data from high-level situational awareness to granular packet forensic evidence.

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. GLOBAL NAVIGATION & CONTROL BAR                                          │
│    • Brand & Live Indicator        • LLM Provider Status Badge              │
│    • View Mode Segmented Control   • Refresh Trigger & API Docs Link        │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. OPERATIONAL KPI METRICS (5 Key Indicators)                               │
│    [Total Alerts] [Critical] [High & Med] [Correlated Incidents] [HITL Queue]│
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. ANALYTICAL VISUALIZATION & THREAT ACTORS                                 │
│    [Attack Categories Doughnut] [Engine Share Pie] [Top 5 Attacker IPs]     │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4. CORRELATED INCIDENTS & AI INVESTIGATION WORKSPACE                        │
│    • Multi-Stage Attack Chains     • Step-by-Step Attack Timeline           │
│    • Korean Interpretation Button  • AI Deep Investigation Trigger          │
│    • Expandable AI Triage Report (Observed Facts vs Hypotheses vs Unknowns) │
├─────────────────────────────────────────────────────────────────────────────┤
│ 5. HITL CONTAINMENT PROPOSALS QUEUE (Human Authorization Gate)              │
│    • Approval ID & Target          • Deterministic Policy Validation Status │
│    • Rule Syntax Preview           • Action Buttons: [모의 실행 승인] / [반려]  │
├─────────────────────────────────────────────────────────────────────────────┤
│ 6. REAL-TIME ALERT STREAM & FORENSIC INSPECTOR                              │
│    • Search & Severity Filter Bar  • Normalized Live Stream (KST/UTC)       │
│    • Inline Signature Translation  • Evidence & Payload Inspector Modal     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Primary Analyst User Journeys

### User Journey 1: Incident Assessment & Korean Interpretation
1. Analyst opens dashboard; checks **Correlated Incidents** card (`INC-10.77.20.20`).
2. Reads the visual attack timeline: `1단계: 정찰 (Recon)` ➔ `2단계: 초기 침투 (Initial Access)` ➔ `3단계: 명령제어 (C2)`.
3. Clicks **`📖 한국어 해석`**:
   - Modal pops up explaining the attack mechanics in plain Korean.
   - Clarifies compromise status: *"경보 발생 상태 (공격의 실제 침해 성공 여부는 웹 서버 응답 코드 추가 검증 필요)"*.
   - Displays analyst checklist (checking `/var/log/auth.log` or victim process list).

### User Journey 2: AI Investigation & Grounded Triage
1. Analyst clicks **`🤖 AI 심층 조사`** on the incident card.
2. The orchestrator queries threat intelligence, retrieves RAG playbooks, and runs model triage.
3. The report expands inline, strictly separating:
   - **확인된 객관적 사실 (Observed Facts)**: Verifiable flow IDs, timestamps, and URIs.
   - **미확인 사항 (Unknowns)**: Items requiring disk/memory forensics.
   - **ATT&CK 매핑**: `T1046`, `T1190`, `T1059.004` with Korean descriptions and confidence scores.

### User Journey 3: Human-in-the-Loop Containment Review & Dry-Run Execution
1. The AI orchestrator proposes `BLOCK_IP 10.77.20.20`.
2. The deterministic `PolicyValidator` checks against protected infrastructure (`protected_assets.py`) and returns `✅ ALLOW (정책 통과)`.
3. The proposal appears in the **HITL Containment Proposals Queue** with status `PENDING`.
4. The analyst reviews the generated `nftables` rule preview.
5. The analyst clicks **`✅ 모의 실행 승인 (Dry-Run)`**:
   - An explanatory confirmation prompt warns that this is a safe simulation without kernel modification.
   - The executor simulates rule execution, stores the audit trail in `logs/approvals_store.json`, and updates the status badge to `EXECUTED`.
