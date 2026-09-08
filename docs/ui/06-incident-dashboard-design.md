# Correlated Incident Workspace & Investigation UI Design

## 1. Component Overview

The **Correlated Incidents Workspace** serves as the primary operational surface for Tier 1 and Tier 2 analysts triaging multi-stage cyber attacks.

Instead of displaying flat alert logs, the workspace organizes alerts into correlated attack chains, reconstructs the adversarial timeline, and provides both on-demand Korean interpretation and automated AI triage.

---

## 2. Incident Card Anatomy

```text
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│ [심각 (CRITICAL)]  INC-10.77.20.20-1787727348  공격자 IP: 10.77.20.20   대상: 10.77.30.20 │
│ 다단계 킬체인 공격 흐름이 상관분석에 의해 입증되었습니다.                                │
│ 최초 탐지: 2026-09-07 20:10:53 KST | 최근 활동: 2026-09-07 20:32:30 KST (총 4개 경보)    │
│                                                                                           │
│ [공격 진행 단계:] [⚡ 1단계: 정찰] ➔ [⚡ 2단계: 초기 침투] ➔ [⚡ 3단계: 명령제어]           │
│                                                                                           │
│                                              [📖 한국어 해석]  [🤖 AI 심층 조사]          │
└───────────────────────────────────────────────────────────────────────────────────────────┘
```

### Key Elements:
1. **Severity Badge**: Color-coded and text-labeled (`심각 (Critical)`).
2. **Entity Coordinates**: Clear visual separation of Attacker IP (`text-red-400 font-bold`) and victim destinations (`text-slate-400`).
3. **Temporal Provenance**: Formatted in local Korean Standard Time (KST) with full ISO UTC string in tooltip.
4. **Visual Attack Progression**: Horizontal sequence tags showing the exact progression through the MITRE killchain.

---

## 3. Visual Attack Timeline

The timeline is dynamically generated based on `Incident.attack_stages`:
- **Stage 1 (Recon)**: Cyan badge (`text-cyan-400 bg-cyan-950/30`)
- **Stage 2 (Exploitation)**: Orange badge (`text-orange-400 bg-orange-950/30`)
- **Stage 3 (C2 / Reverse Shell)**: Red badge (`text-red-400 bg-red-950/30`)

Connecting arrows (`➔`) explicitly demonstrate the escalating threat trajectory to the analyst.

---

## 4. AI Deep Investigation Report Panel

When the analyst triggers **`[🤖 AI 심층 조사]`**, the report unfolds inline beneath the incident card:

### 4.1 Attribution Header
Transparently states provider provenance:
- **Mock Baseline**: `모의 분석 기준선 (Mock Baseline - 실제 LLM 분석 아님)`
- **Local Ollama**: `Ollama / qwen2.5:7b`
- Displays exact wall-clock latency (ms) and tool invocations executed.

### 4.2 Epistemic Distinction Grid
- **확인된 객관적 사실 (Observed Facts)**: Verifiable event data (e.g. 4 alerts across 3 stages, specific URIs).
- **미확인 사항 (Unknowns)**: Items requiring secondary investigation (e.g. victim disk artifacts, active memory processes).

### 4.3 ATT&CK Mapping Badges
Each technique includes:
- Technique ID (`T1046`, `T1190`, `T1059.004`)
- Localized technique name (`네트워크 서비스 탐색`, `외부 공개 애플리케이션 악용`)
- Confidence score (`0.95`)
