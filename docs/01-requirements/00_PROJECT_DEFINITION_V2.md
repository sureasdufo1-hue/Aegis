# 보안관제 프로젝트 v2.0 프로젝트 정의서  
**문서 ID:** `00_PROJECT_DEFINITION_V2`  
**프로젝트 가칭:** **AegisAI — AI for Security × Security for AI Integrated SOC Platform**  
**기준일:** 2026-09-28  
**문서 상태:** v2.0 Baseline

> 본 문서는 기존 SOC를 폐기하지 않고 **v1.x Core SOC Baseline을 유지하면서 AI for Security와 Security for AI를 통합하는 상위 기준 문서**로 작성한다.

---

# 1. 문서 개요

## 1.1 작성 목적

본 문서는 기존 Suricata·Snort·Wazuh·Elastic Stack 기반 보안관제 환경을 **AI 기반 통합 보안관제 플랫폼**으로 발전시키기 위한 프로젝트의 목적, 범위, 설계원칙, 모듈, 단계, 성공기준 및 후속 산출물 체계를 정의한다.

핵심은 기존 SOC를 AI로 대체하는 것이 아니다.

```text
기존 Rule / Signature Detection
             +
      Correlation Engine
             +
        AI Analysis
             ↓
      Unified AI-SOC
```

AI는 **상위 분석·의사결정 지원 계층**으로 사용한다. 이는 `Rule-based Detection + Correlation + AI Analysis` 원칙을 그대로 따른다.

## 1.2 문서 범위

본 문서는 다음 후속 산출물의 최상위 기준선이다.

```text
00 Project Definition
        ↓
01 AS-IS SOC Baseline
        ↓
02 TO-BE Architecture
        ↓
03 AI Threat Model
        ↓
04 Requirements Specification
        ↓
05 Unified Security Event Schema
        ↓
06 AI Security Policy
        ↓
07 HLD
        ↓
08 LLD
        ↓
09 Evaluation Plan
        ↓
10 Implementation Plan
        ↓
11 Test Plan
        ↓
12 AI Red Team Scenarios
        ↓
13 Operation Playbook
        ↓
14 Final Evaluation Report
        ↓
15 Portfolio Report
```

## 1.3 대상 독자

- 프로젝트 개발자
- SOC Analyst
- 보안 관리자
- 네트워크·시스템 관리자
- AI/LLM 개발자
- AI Security Engineer
- 프로젝트 평가자 및 포트폴리오 검토자

---

# 2. 프로젝트 개요

## 2.1 프로젝트명

**AegisAI — AI for Security × Security for AI Integrated SOC Platform**

## 2.2 추진 배경

기존 SOC는 네트워크·호스트·웹·시스템 보안 이벤트를 탐지하고 SIEM에서 분석하는 구조이다.

그러나 생성형 AI의 도입으로 관제 대상이 다음과 같이 확장되고 있다.

```text
Traditional Security
Network / Host / Web / Identity
                +
AI Security
LLM / RAG / Agent / Vector DB / Tool
```

실제로 OWASP는 2026년 **GenAI LLM Top 10 2026**을 새로 발표했으며, 별도로 **Top 10 for Agentic Applications 2026**도 제공하고 있다. 2026판 LLM 지침은 실제 AI 보안 사고 자료와 최신 연구를 반영하고 MITRE ATLAS·NIST 등과의 매핑도 확대했다.

따라서 기존 SOC도 단순히 네트워크와 서버만 관제하는 구조에서 벗어나 **AI Application 자체를 새로운 보안자산 및 공격표면으로 취급할 필요가 있다.**

## 2.3 문제 정의

현재 구조에는 네 가지 핵심 한계가 존재한다.

| 문제 | v2.0 대응 |
|---|---|
| Alert가 개별적으로 발생 | Incident Correlation |
| 분석가가 직접 이벤트 해석 | AI SOC Analyst |
| AI Application 보안 가시성 부족 | AI Security Gateway |
| 전통 보안과 AI 보안 분리 | Unified AI-SOC |

## 2.4 프로젝트 목표

본 프로젝트의 목표는 다음 두 축을 통합하는 것이다.

### AI for Security

AI를 이용하여 다음 SOC 업무를 지원한다.

- Alert Triage
- 이벤트 상관분석
- Incident 생성
- Attack Timeline
- MITRE ATT&CK Mapping
- Risk Scoring
- 사고 요약
- Security RAG
- 대응 권고

### Security for AI

LLM·RAG·AI Agent에 대해 다음을 통제한다.

- Prompt Injection
- Sensitive Information Leakage
- Secret Leakage
- System Prompt Leakage
- RAG/Vector Security
- Data/Model Poisoning
- Unsafe Output
- Excessive Agency
- Resource Abuse
- Audit

이 두 축의 Security Telemetry를 중앙 SIEM으로 다시 수집하는 구조를 핵심으로 한다.

## 2.5 핵심 연구 질문

> **AI를 이용해 기존 SOC의 탐지·분석 효율을 높이면서, 동시에 그 AI 자체의 공격표면과 데이터 유출 위험을 어떻게 통제할 것인가?**

---

# 3. AS-IS — 기존 SOC

## 3.1 기존 구조

현재 프로젝트 자산을 v1.x Core SOC Baseline으로 정의한다.

```text
Network / Server / Web
          │
          ▼
 Suricata / Snort / Wazuh
          │
          ▼
       Filebeat
          │
          ▼
 Elasticsearch
          │
          ▼
 Kibana / Wazuh Dashboard
          │
          ▼
      SOC Analyst
```

## 3.2 구축 완료로 취급하는 기준선

| 영역 | 기준선 |
|---|---|
| Virtualization | VMware SOC Lab |
| Network | Gateway / Sensor / Attacker / Victim |
| NIDS | Suricata |
| 보조 IDS | Snort |
| Endpoint/SIEM | Wazuh |
| Pipeline | Filebeat |
| Data/Search | Elasticsearch |
| Visualization | Kibana |
| Network Event | EVE JSON |
| Detection | Custom Rule |
| Correlation | Kill Chain Correlation |

다만 **실제 운영망의 관리망·DMZ·DB망·로그망 구성과 VMware SOC Lab은 물리/논리 구조가 다를 수 있으므로**, `01_AS_IS_SOC_BASELINE`에서 실제 현재 토폴로지를 다시 동결한다.

## 3.3 버전 기준

2026-09-28 공식자료 확인 결과:

- Suricata 8.0.6은 2026년 7월 보안 릴리스이며 7.x는 EOL이다.
- Wazuh는 기존 프로젝트의 4.14.7보다 **4.14.8이 2026-09-23 출시**되어 현재 최신 4.14 계열 기준선이 한 단계 올라갔다. 따라서 기존 환경은 4.14.7 Baseline으로 기록하되 업그레이드 여부를 별도로 판단한다.
- Elastic은 9.x 계열이 존재하지만 기존 프로젝트의 8.19.x를 무조건 교체하지 않는다. 2026-09-02에는 8.19.21도 별도 유지·배포되고 있다.

즉 **v2.0 전환과 제품 Major Upgrade를 동시에 수행하지 않는다.**

---

# 4. TO-BE — AegisAI

## 4.1 목표 구조

```text
                        AegisAI
                           │
                 ┌─────────▼─────────┐
                 │ Unified AI-SOC    │
                 └─────────┬─────────┘
                           │
                 ┌─────────▼─────────┐
                 │ AI SOC Analyst    │
                 └─────────┬─────────┘
                           │
          ┌────────────────┴────────────────┐
          │                                 │
          ▼                                 ▼
   AI for Security                  Security for AI
          │                                 │
 Alert Triage                       AI Gateway
 Correlation                        Prompt Security
 ATT&CK Mapping                     AI DLP
 Risk Scoring                       Secret Detection
 Security RAG                       RAG Security
 Incident Summary                   Agent Security
 Response Recommendation            Output Validation
          │                                 │
          └────────────────┬────────────────┘
                           ▼
                  Security Data Layer
                    Elasticsearch
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
    Suricata             Wazuh          AI Telemetry
        │                  │                  │
        └──────────────────┼──────────────────┘
                           ▼
                  Response Orchestrator
                           │
                     Human Approval
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
          Firewall       Wazuh      AI Gateway
```

---

# 5. 설계 원칙

### ① Existing SOC First

AI 장애가 기존 SOC 장애로 전파되어서는 안 된다.

```text
AI Down

Suricata     → 정상
Wazuh        → 정상
Filebeat     → 정상
Elasticsearch→ 정상
Rule Alert   → 정상

AI Analysis  → Degraded
```

### ② Defense in Depth

단일 LLM 판단을 보안결정으로 사용하지 않는다.

```text
Signature
  +
Rule
  +
Policy
  +
Correlation
  +
AI
  +
Human
```

### ③ Human-in-the-loop

기본 대응은 다음과 같다.

```text
Detection
   ↓
AI Analysis
   ↓
Response Proposal
   ↓
Human Approval
   ↓
Enforcement
```

### ④ Explainability

모든 AI 판단은 최소한 다음을 기록한다.

`결과 / Risk Score / Confidence / Evidence / 관련 Event / Policy / ATT&CK·ATLAS / RAG Source / Approval`

### ⑤ Zero Trust for AI

AI의 입력뿐 아니라 **AI가 생성한 출력과 Agent Action도 검증 대상**이다.

### ⑥ Fail-Safe

AI가 실패하면 기존 Rule 기반 SOC로 자동적으로 기능이 축소되는 **Graceful Degradation**을 목표로 한다.

---

# 6. 시스템 범위

## 6.1 MVP

**반드시 구현할 범위**

- 기존 SOC 유지
- Unified Security Event
- AI Alert Triage
- Incident Correlation
- Incident Summary
- ATT&CK Mapping
- Security RAG
- AI Security Gateway
- Prompt Injection Detection
- PII Detection
- Secret Detection
- AI Security Telemetry
- Elasticsearch 연동
- Unified Dashboard

## 6.2 Advanced

- RAG Poisoning Detection
- Agent Security
- Automated Threat Hunting
- Behavioral Detection
- ML Anomaly Detection
- SOAR
- Automated Response
- Multi-Agent SOC

## 6.3 Out of Scope

- 완전자율 SOC
- 무승인 Firewall 변경
- 무승인 계정 삭제
- Foundation Model 자체 학습
- 상용 SOC 수준 HA
- 실제 외부 운영망 공격

---

# 7. 주요 Actor와 Use Case

| Actor | 주요 Use Case |
|---|---|
| SOC Analyst | Incident 조사·AI 분석 검토·대응 승인 |
| Security Administrator | 정책·Rule·Gateway 관리 |
| AI User | 승인된 AI Application 사용 |
| AI Administrator | RAG/Agent/Model 운영 |
| Red Team | 공격 시나리오 검증 |

---

# 8. 시스템 모듈

## M0 — Governance & Evaluation

**역할:** 프로젝트 전체의 보안 기준선.

- Threat Model
- Security Policy
- Risk Classification
- Dataset
- Evaluation
- Red Team
- Model Change Management

## M1 — Security Data Pipeline

```text
Collection
   ↓
Parsing
   ↓
Normalization
   ↓
Enrichment
   ↓
Storage
```

대상:

`Suricata / Snort / Wazuh / Firewall / Web / System / AI Gateway`

## M2 — AI SOC Analyst

```text
Alert
 ↓
Triage
 ↓
Correlation
 ↓
Incident
 ↓
Timeline
 ↓
ATT&CK Mapping
 ↓
Risk Score
 ↓
Summary
```

## M3 — Security Knowledge RAG

지식원:

- MITRE ATT&CK
- MITRE ATLAS
- CVE/CWE
- Detection Rule
- 내부 Playbook
- SOC Procedure
- Security Policy

## M4 — AI Security Gateway

```text
User
 ↓
Authentication
 ↓
Authorization
 ↓
Prompt Inspection
 ↓
Policy Engine
 ↓
DLP / AI Attack Detection
 ↓
LLM / RAG
 ↓
Output Validation
 ↓
User
```

## M5 — AI DLP

정책 결과:

```text
ALLOW
MASK
WARN
REQUIRE_APPROVAL
BLOCK
```

## M6 — AI Attack Defense

세부 Threat Model 작성 시 **LLM 2026 + Agentic 2026을 동시에 매핑**한다.

## M7 — Unified AI-SOC

```text
Traditional Security
Network
Host
Web
Identity
Malware
C2

        +

AI Security
Prompt
RAG
DLP
Agent
Data Leakage
Policy Violation

        ↓

Unified Incident
```

---

# 9. 핵심 데이터 흐름

```text
                  [Security Sources]

 Suricata ─┐
 Wazuh ────┤
 Firewall ─┤
 Web ──────┤
 AI GW ────┤
 RAG ──────┘
      │
      ▼
 Normalization
      │
      ▼
Unified Security Event
      │
      ▼
 Elasticsearch
      │
      ├─────────────► Dashboard
      │
      ▼
 Correlation Engine
      │
      ▼
 AI SOC Analyst
      │
      ▼
 Security RAG
      │
      ▼
 Response Recommendation
      │
      ▼
 Human Approval
      │
      ▼
 Response
      │
      └─────────────► New Telemetry
```

---

# 10. Unified Security Event 전략

최소 공통 필드 범주:

```text
Identity
timestamp
event_id
trace_id
incident_id

Classification
event_domain
event_category
event_type

Entity
source
destination
user
asset
application

Risk
severity
risk_score
confidence

Detection
detection_source
rule_id

Framework
framework
technique

Decision
evidence
action
action_status
policy

AI
ai_model
ai_application
rag_source

Workflow
analyst_status
created_at
updated_at
```

event_domain은 최소:

```text
NETWORK_SECURITY
HOST_SECURITY
WEB_SECURITY
IDENTITY_SECURITY
AI_SECURITY
DATA_SECURITY
```

로 구성한다.

---

# 11. AI Threat Model 개요

## 11.1 Traditional Surface

- Network
- Host
- Web
- Identity
- Database
- Security Infrastructure

## 11.2 AI Surface

- User Prompt
- System Prompt
- LLM
- RAG
- Embedding
- Vector DB
- Agent
- Tool
- API
- Model Output
- Gateway

## 11.3 2026 공식 기준선

| 기관 | 기준 | 프로젝트 활용 |
|---|---|---|
| OWASP | GenAI LLM Top 10 2026 | LLM/RAG 위협 |
| OWASP | Agentic Applications Top 10 2026 | Agent 위협 |
| NIST | AI RMF 1.0 + GenAI Profile | 위험관리 |
| MITRE | ATT&CK v19.2 | 기존 공격 TTP |
| MITRE | ATLAS | AI 공격 TTP |

---

# 12. 대표 E2E 시나리오

```text
09:30 Network Scan
        │
09:32 Web Enumeration
        │
09:34 Authentication Failure
        │
09:37 Prompt Injection
        │
09:38 RAG Sensitive Data Access
        │
09:39 AI Gateway BLOCK
        │
09:39 AI_SECURITY Event
        │
09:40 Elasticsearch
        │
09:40 Correlation Engine
        │
        ▼
INCIDENT-20260928-001
        │
        ├─ Network Evidence
        ├─ Host Evidence
        ├─ Identity Evidence
        └─ AI Security Evidence
        │
        ▼
AI SOC Analyst
        │
        ▼
ATT&CK + ATLAS Mapping
        │
        ▼
Security RAG
        │
        ▼
Response Recommendation
        │
        ▼
SOC Analyst Approval
        │
        ▼
Response
```

---

# 13. Closed-loop Security

```text
       ┌──── Security for AI ────┐
       │                         │
Prompt Injection                 │
       ↓                         │
AI Security Gateway              │
       ↓                         │
BLOCK                            │
       ↓                         │
AI Security Event                │
       │                         │
       └──────────┐              │
                  ▼              │
             Elasticsearch       │
                  │              │
                  ▼              │
          AI for Security        │
                  │              │
           AI SOC Analyst        │
                  │              │
             Correlation         │
                  │              │
              Incident           │
                  │              │
             Security RAG        │
                  │              │
       Response Recommendation   │
                  │              │
            Human Approval       │
                  │              │
              Response ──────────┘
```

> **Security for AI에서 발생한 보안 Telemetry를 AI for Security가 다시 분석하고, 대응 결과가 다시 새로운 Telemetry가 되는 순환구조**

---

# 14. Human-in-the-loop

```text
Level 0
Rule Detection

Level 1
AI Summary

Level 2
AI Correlation

Level 3
AI Recommendation

Level 4
Human-approved Response

──────── MVP Boundary ────────

Level 5
Restricted Autonomous Response
```

MVP에서는 Level 4를 최대 자동화 수준으로 한다.

---

# 15. 평가전략

## 15.1 Detection
- Precision / Recall / F1 / False Positive Rate / False Negative Rate

## 15.2 Performance
- Detection Latency / AI Analysis Latency / Gateway Latency / RAG Retrieval Latency

## 15.3 SOC Efficiency
- Mean Triage Time / Incident Analysis Time / Analyst Investigation Steps / Alert → Incident Reduction Ratio

## 15.4 AI Security
- Prompt Injection Detection Rate / PII Detection Rate / Secret Detection Rate / Normal Prompt FPR / RAG Attack Detection Rate

### 핵심 비교 실험

```text
Experiment A: Baseline SOC vs. AI-Augmented SOC
Experiment B: Unprotected LLM/RAG vs. AI Security Gateway vs. LLM/RAG
```

---

# 16. 프로젝트 단계

| Phase | 목표 | 핵심 완료조건 |
|---|---|---|
| P0 | SOC Baseline Freeze | 기존 SOC 기준선 확정 |
| P1 | Unified Event | 공통 Event 저장 성공 |
| P2 | AI SOC MVP | Alert → AI Analysis 성공 |
| P3 | Security RAG | 근거 기반 대응안 생성 |
| P4 | AI Gateway | AI 요청·응답 경유 |
| P5 | AI DLP | PII/Secret 정책 동작 |
| P6 | AI Attack Defense | Prompt 공격 탐지 |
| P7 | Unified Dashboard | IT+AI Event 통합 |
| P8 | Closed-loop | Cross-domain Correlation |
| P9 | HITL Response | 승인 기반 대응 |
| P10 | Red Team/Evaluation | 정량평가 |
| P11 | Documentation | 최종 포트폴리오 |

---

# 17. 성공기준

## Functional
- [ ] Network Security Event 수집
- [ ] Host Security Event 수집
- [ ] AI Security Event 수집
- [ ] Unified Schema 변환
- [ ] Incident 생성
- [ ] Security RAG 검색
- [ ] AI Gateway 정책 실행
- [ ] Unified Dashboard 구현

## Security
- [ ] Direct Prompt Injection Test
- [ ] Indirect Prompt Injection Test
- [ ] PII Leakage Test
- [ ] Secret Leakage Test
- [ ] Unauthorized RAG Access Test
- [ ] Output Validation Test
- [ ] Audit Trail 검증

## Reliability
AI가 중단되어도:
- [ ] Suricata 동작
- [ ] Wazuh 동작
- [ ] 로그 수집
- [ ] Elasticsearch 저장
- [ ] Rule Alert
가 정상이어야 한다.

---

# 18. 주요 위험 및 대응

| 위험 | 대응 |
|---|---|
| Hallucination | RAG + Evidence + Human Review |
| False Positive | Rule/AI Hybrid + Threshold |
| False Negative | 다계층 탐지 |
| Prompt Injection | Gateway + Policy |
| Indirect Injection | Context/Document Inspection |
| RAG Poisoning | Ingestion Security |
| Data Leakage | DLP |
| Excessive Agency | Least Privilege + Approval |
| AI Supply Chain | Model/Dependency Inventory |
| Model Drift | Versioned Evaluation |
| AI API 장애 | Fail-safe SOC |
| Latency | Async Analysis/Timeout |
| 비용 | Local/Selective LLM |
| 기존 SOC 영향 | AI Layer 분리 |

---

# 19. 기존 N2SF-AIGate 통합

```text
                   AegisAI
                      │
        ┌─────────────┴─────────────┐
        │                           │
 AI for Security              Security for AI
        │                           │
    AI SOC                     AI Gateway
                                    │
                              N2SF-AIGate
                                    │
                       ┌────────────┼────────────┐
                       ▼            ▼            ▼
                      PII         Secret       DLP
                       │            │            │
                       └────────────┼────────────┘
                                    ▼
                             Policy Engine
```

기존 N2SF-AIGate의 PII/Secret 탐지, C/S/O 등급, Allow/Mask/Approve/Block, RAG 근거, 감사로그 등은 M4/M5의 후보 자산으로 분류한다.

---

# 20. 산출물 체계

```text
00_PROJECT_DEFINITION_V2          ← 현재 문서
│
├─01_AS_IS_SOC_BASELINE
├─02_TO_BE_ARCHITECTURE
├─03_AI_THREAT_MODEL
├─04_REQUIREMENTS_SPECIFICATION_V2
├─05_UNIFIED_SECURITY_EVENT_SCHEMA
├─06_AI_SECURITY_POLICY
├─07_HIGH_LEVEL_DESIGN
├─08_LOW_LEVEL_DESIGN
├─09_AI_EVALUATION_PLAN
├─10_IMPLEMENTATION_PLAN
├─11_TEST_PLAN
├─12_AI_RED_TEAM_SCENARIOS
├─13_OPERATION_PLAYBOOK
├─14_FINAL_EVALUATION_REPORT
└─15_PORTFOLIO_REPORT
```

---

# 21. 기술 기준선

| 기준 | 현재 확인 |
|---|---|
| OWASP GenAI | **LLM Top 10 2026** |
| OWASP Agentic | **Top 10 for Agentic Applications 2026** |
| NIST | AI RMF 1.0 + NIST AI 600-1 GenAI Profile |
| MITRE ATT&CK | **v19.2** |
| MITRE ATLAS | AI Threat Knowledge Base |
| Suricata | 기존 8.0.6 Baseline 유지 가능 |
| Wazuh | 프로젝트 4.14.7 / 공식 최신 4.14.8 확인 |
| Elastic | 기존 8.19.x 유지 우선 |

---

# 22. MVP 완료조건

- [ ] 기존 SOC Baseline 기능 보존
- [ ] Network/Host/AI Security Event 통합
- [ ] Unified Event Schema 적용
- [ ] Elasticsearch 통합 저장
- [ ] AI Alert Triage 구현
- [ ] 다중 Alert → Incident Correlation 구현
- [ ] Incident Summary 구현
- [ ] ATT&CK Mapping 구현
- [ ] Security RAG 구현
- [ ] AI Security Gateway 구현
- [ ] Prompt Injection 탐지
- [ ] PII 탐지
- [ ] Secret 탐지
- [ ] ALLOW/MASK/WARN/APPROVE/BLOCK 정책
- [ ] AI Security Event → SIEM 전달
- [ ] Unified Dashboard
- [ ] Human Approval Workflow
- [ ] AI 장애 시 기존 SOC 정상 동작
- [ ] Red Team Scenario 검증
- [ ] Precision/Recall/F1/FPR 측정
- [ ] AI 적용 전·후 Triage Time 비교
- [ ] Gateway Latency 측정

---

# 23. 최종 구현 목표

> **기존 네트워크·호스트·웹 보안 이벤트와 LLM·RAG·AI Agent에서 발생하는 AI Security Event를 하나의 SIEM으로 통합하고, AI를 이용하여 사건을 분석·상관분석·설명하면서 동시에 AI Security Gateway가 AI 자체의 공격·오용·민감정보 유출을 통제하는 Closed-loop AI-SOC를 구현한다.**

---

# 24. Project Definition

> **AegisAI는 기존 Suricata·Wazuh·Elastic 기반 SOC를 보존하면서 AI for Security와 Security for AI를 결합한 통합 보안관제 플랫폼이다. 기존 네트워크·호스트·웹 공격뿐 아니라 Prompt Injection, 민감정보 유출, RAG 및 Agent 관련 위협을 새로운 Security Telemetry로 수집하고, 이를 기존 보안 이벤트와 상관분석하여 Incident 단위로 관리한다. AI SOC Analyst는 Alert Triage, Incident Correlation, ATT&CK/ATLAS Mapping, Risk Scoring, Security RAG 기반 대응 권고를 수행하고, AI Security Gateway는 AI 시스템의 입력·출력·데이터·권한을 통제한다. 대응은 Human-in-the-loop를 원칙으로 하며 AI 장애 시에도 기존 Rule 기반 SOC가 지속 동작하는 Fail-Safe 구조를 유지한다.**

## 프로젝트 핵심 메시지

> **AI가 보안을 수행하고, 보안이 다시 AI를 보호한다.**
