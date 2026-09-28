# 02_TO_BE_ARCHITECTURE — AegisAI 목표 시스템 아키텍처 설계서

**문서 ID:** `02_TO_BE_ARCHITECTURE`  
**상위 문서:** [`00_PROJECT_DEFINITION_V2`](../01-requirements/00_PROJECT_DEFINITION_V2.md), [`01_AS_IS_SOC_BASELINE`](../01-requirements/01_AS_IS_SOC_BASELINE.md)  
**하위 연계 문서:** `03_AI_THREAT_MODEL`, [`04_REQUIREMENTS_SPECIFICATION_V2`](../01-requirements/04_REQUIREMENTS_SPECIFICATION_V2.md)  
**기준일:** 2026-09-28  
**상태:** Approved TO-BE Baseline  
**작성자:** AegisAI 수석 보안 아키텍처팀 (Enterprise Security & AI Security Architecture)  

---

## 1. 문서 개요

### 1.1 목적
본 문서는 `01_AS_IS_SOC_BASELINE`에서 확정된 기존 SOC 핵심 자산(Suricata 8.0.6, Wazuh 4.14.7, Elasticsearch 8.19.20, EVE JSON, 다단계 킬체인 상관분석 엔진)을 100% 보존하면서, **AI for Security (보안관제 지능화)**와 **Security for AI (생성형 AI 자산 및 Agent 공격표면 방어)**를 유기적으로 결합한 차세대 통합 보안관제 플랫폼 **AegisAI v2.0**의 목표 시스템 아키텍처를 정의합니다.

### 1.2 범위
본 문서는 상세 API 파라미터나 특정 소스코드를 다루는 HLD/LLD가 아니며, 시스템의 **경계(Boundaries), 4개 논리 계층(4-Layers), 컴포넌트 간 책임 및 인터페이스, 보안 신뢰 경계(Trust Boundaries), 배치 토폴로지, 폐루프(Closed-loop) 텔레메트리 흐름 및 장애 격리(Fail-Safe) 메커니즘**을 확정하는 상위 아키텍처 기준선입니다.

### 1.3 상위 문서 및 관계
```text
00_PROJECT_DEFINITION_V2 (프로젝트 정의서)
        ↓
01_AS_IS_SOC_BASELINE (자산 분류 및 출발점 동결)
        ↓
02_TO_BE_ARCHITECTURE (목표 시스템 아키텍처)  ← [본 문서]
        ↓
03_AI_THREAT_MODEL (AI/LLM/Agent 위협 모델링)
        ↓
04_REQUIREMENTS_SPECIFICATION_V2 (상세 요구사항 정의서)
```

### 1.4 Architecture 핵심 원칙
1. **Existing SOC First (원천 인프라 보존)**: 검증된 시그니처/룰 기반 탐지 엔진(Suricata/Wazuh)을 LLM으로 대체하지 않으며, AI 계층 장애 시에도 L1 인프라는 100% 무손실 가동(**Graceful Degradation**).
2. **Defense in Depth (다계층 심층 방어)**: `시그니처 + 룰 + 결정론적 상관분석 + AI 상황분석 + 인간 승인`의 5단계 방어선 준수.
3. **Zero Trust for AI (AI 대상 무신뢰)**: 사용자 프롬프트뿐만 아니라 LLM 생성 응답, RAG 참조 문서, Agent Tool 호출 전수를 검증 대상으로 격리.
4. **Human-in-the-Loop (Level 4 Boundary)**: 모든 가용성 침해 가능 대응 조치는 분석가의 명시적 1-Click 승인을 받아야 집행.
5. **Closed-loop Security (폐루프 텔레메트리)**: Security for AI의 차단 데이터가 SIEM으로 유입되어 AI for Security의 분석 입력으로 순환.

---

## 2. AS-IS 입력 기준

`01_AS_IS_SOC_BASELINE`의 동결 결과를 기반으로 컴포넌트를 4대 범주로 명확히 분리하여 설계에 반영합니다.

```text
+-------------------+-------------------------------------------------------------+
| 분류 범주          | 컴포넌트 및 자산 목록                                       |
+-------------------+-------------------------------------------------------------+
| [KEEP] 원형 보존  | • [E] Suricata 8.0.6 (AF_PACKET 미러링 수집 및 EVE JSON 출력)|
|                   | • [E] Filebeat 8.19.20 (로그 포워딩 파이프라인)             |
|                   | • [E] Elasticsearch 8.19.20 (보안 데이터 레이크 저장소)     |
|                   | • [E] Wazuh 4.14.7 (HIDS 에이전트 및 호스트 보안 이벤트)    |
|                   | • [E] 기존 커스텀 룰셋 (Suricata SID, Wazuh Rule)           |
|                   | • [E] VMware SOC Attack/Defense 격리 랩 환경                |
+-------------------+-------------------------------------------------------------+
| [MODIFY/INTEGRATE]| • [M] Correlation Engine (단순 룰 매칭 ➔ 인시던트 군집화)   |
|   기능 확장       | • [M] Kibana Dashboard (전세계 위협 지도 + AI 보안 모니터링)|
|                   | • [M] N2SF-AIGate (기존 PII/Secret DLP ➔ AI Gateway M4/M5)  |
|                   | • [M] Security Knowledge RAG (정적 문서 ➔ 하이브리드 RAG M3)|
|                   | • [M] Security Event Pipeline (도메인 정규화 파이프라인 확장)|
+-------------------+-------------------------------------------------------------+
| [NEW] 신규 개발   | • [N] AI SOC Analyst (M2: Alert Triage, 타임라인, 위험도)   |
|                   | • [N] AI Security Gateway (M4: 고성능 리버스 프록시)        |
|                   | • [N] Prompt Injection & Jailbreak Defense (M6: OWASP 2026) |
|                   | • [N] Unified Security Event Schema (6대 도메인 ECS 기반)    |
|                   | • [N] Closed-loop Telemetry & HITL 승인 큐 (M7)             |
|                   | • [N] AI Evaluation Framework (정량 평가 스위트)            |
+-------------------+-------------------------------------------------------------+
| [NOT FROZEN]      | • 실제 물리 VLAN 10/20/30 및 공용 IP (현장 실측 전 임의 확정 금지)|
|   미확정/보류     | • AhnLab TrusGuard 방화벽 세션 및 NAT/VIP 세부 정책         |
|                   | • L3 SPAN 패킷 손실률 및 NTP UDP/123 시간 동기화            |
+-------------------+-------------------------------------------------------------+
```

---

## 3. Architecture Goals

AegisAI v2.0 아키텍처가 달성해야 하는 5대 목표:
1. **가시성 단일화 (Single Pane of Telemetry)**: 네트워크/호스트 공격뿐만 아니라 생성형 AI 대상 프롬프트 공격 및 데이터 유출을 동일한 SIEM 데이터 레이크에서 단일 이벤트 뷰로 관제.
2. **조사 생산성 극대화 (Triage Acceleration)**: 다중 경보 상관분석 및 AI 인시던트 요약을 통해 분석가의 Mean Time to Triage(MTTT)를 70% 이상 단축.
3. **인라인 AI 공격 방어 (Sub-150ms Inline Guard)**: 사내 LLM 요청 경로 상에서 인라인 검사를 수행하며 150ms 미만의 추가 오버헤드로 탈옥/PII 유출을 100% 차단.
4. **결정론적 안전 경계 (Deterministic Safety Boundary)**: LLM의 환각이나 오류로 인한 오차단/인프라 장애를 방지하는 엄격한 화이트리스트 정책 검증기 및 인간 승인 큐 유지.
5. **자립형 폐쇄망 운영 (Air-Gapped Sovereign AI)**: 온프레미스 로컬 추론 런타임(Ollama Qwen2.5)을 기반으로 민감한 기업 보안 로그의 외부 유출 원천 차단.

---

## 4. System Context

AegisAI 시스템은 외부 공격자, 내부 업무 사용자, 보안 관제 분석가, 사내 AI 애플리케이션 및 보호 대상 엔터프라이즈 인프라 간의 중심 접점에 위치합니다.

### Diagram 1: 전체 Context Architecture
```text
  +-------------------------------------------------------------------------------+
  |                             EXTERNAL / UNTRUSTED                              |
  |  +--------------------+                     +------------------------------+  |
  |  | External Attacker  |                     | Public AI / Cloud APIs       |  |
  |  +---------+----------+                     +--------------▲---------------+  |
  +------------│-----------------------------------------------│------------------+
               │ (Scans, Exploits, Injections)                 │ (Optional Egress)
  =============▼===============================================│===================
  [TB-01: Perimeter Boundary]                                  │
  =============▲===============================================│===================
  +------------│-----------------------------------------------│------------------+
  |            │             ENTERPRISE INTRANET               │                  |
  |  +---------▼----------+                     +--------------┴---------------+  |
  |  | Protected Assets   |                     | Internal AI Users / Apps     |  |
  |  | (DMZ Web, DB, Svr) |                     | (Chat, RAG Assistant, Agent) |  |
  |  +---------+----------+                     +--------------+---------------+  |
  |            │                                               │                  |
  |            │ Mirrored Packets                              │ Prompt Requests  |
  |            ▼                                               ▼                  |
  |    +---------------+                               +---------------+          |
  |    | L1: Sensor    |                               | L2: AI Sec GW |          |
  |    | (Suricata/HIDS|                               | (Prompt/DLP)  |          |
  |    +-------+-------+                               +-------+-------+          |
  |            │ EVE JSON                                      │ AI Telemetry     |
  |            ▼                                               ▼                  |
  |  +-----------------------------------------------------------------+          |
  |  |                     AegisAI Core Platform                       |          |
  |  |  +-----------------------------------------------------------+  |          |
  |  |  | L1: Elasticsearch 8.19 Security Lake                      |  |          |
  |  |  +-----------------------------+-----------------------------+  |          |
  |  |                                │ Unified Events                 |          |
  |  |  +-----------------------------▼-----------------------------+  |          |
  |  |  | L3: Deterministic Correlation Engine & AI SOC Analyst     |  |          |
  |  |  +-----------------------------+-----------------------------+  |          |
  |  |                                │ Incident & Recommendations     |          |
  |  |  +-----------------------------▼-----------------------------+  |          |
  |  |  | L4: Unified Dashboard & Human-in-the-Loop Approval Queue  |  |          |
  |  |  +-----------------------------+-----------------------------+  |          |
  |  +--------------------------------│--------------------------------+          |
  |                                   │ Approved Block Actions                    |
  |                                   ▼                                           |
  |                   +-------------------------------+                           |
  |                   | Containment Enforcement       |                           |
  |                   | (Firewall, Wazuh, AI GW Rule) |                           |
  |                   +-------------------------------+                           |
  +-------------------------------------------------------------------------------+
```
- **목적**: 시스템 외부 주체와 내부 보안 컴포넌트 간의 고수준 데이터 교환 및 통제 범위 도문화.
- **주요 Component**: 외부 공격자, 내부 업무 사용자, L1 수집 센서, L2 AI 게이트웨이, AegisAI 코어, 대응 집행기.
- **데이터 흐름**: 미러링 패킷/프롬프트 요청 ➔ 수집/검사 ➔ 중앙 데이터 레이크 ➔ 상관분석/AI 분석 ➔ 승인 ➔ 집행.
- **보안 의미**: 네트워크 침해와 AI 오용이 서로 다른 사일로가 아닌 하나의 중앙 관제 플랫폼으로 수렴됨을 증명.

---

## 5. 4-Layer Architecture

AegisAI는 기능적 결합도와 장애 전파 격리를 위해 **4계층 수직 분리 모델**을 채택합니다.

### Diagram 2: 4-Layer Architecture
```text
+---------------------------------------------------------------------------------+
| L4: Unified AI-SOC & Response                                                   |
| - [E] Kibana Unified Threat Map & SIEM Visualizer                               |
| - [N] FastAPI AI Investigation Workspace & Multi-Engine Stepper                 |
| - [N] Deterministic Policy Engine & 1-Click Human Approval Queue (HITL Level 4) |
+---------------------------------------------------------------------------------+
                                      ▲
                                      │ Incidents, Graph, Recommendations
+---------------------------------------------------------------------------------+
| L3: AI SOC Intelligence                                                         |
| - [M] Multi-Stage Kill Chain Correlation Engine (Deterministic Invariant)       |
| - [N] AI SOC Analyst (Alert Triage, Attack Timeline, Composite Risk Scoring)    |
| - [N] Dual Framework Mapping (MITRE ATT&CK v19.2 & MITRE ATLAS)                |
| - [M] Security Knowledge RAG (Hybrid BM25 + Dense Vector Engine)                |
+---------------------------------------------------------------------------------+
                                      ▲
                                      │ Unified Security Events (ECS Normalized)
+---------------------------------------------------------------------------------+
| L2: AI Security Enforcement (Security for AI)                                   |
| - [N] AI Security Gateway (High-Performance Reverse Proxy, Token Auth, Rate-Limit)|
| - [N] Prompt Attack Defense Engine (OWASP 2026: Direct/Indirect Injection Guard)|
| - [M] N2SF-AIGate AI DLP (PII 6-Pattern, Secret 20-Pattern, C/S/O Classification)|
| - [N] Context-Preserving Masking & Output Security Validator                    |
| - [N] Real-time AI Security Telemetry Emitter (event_domain: AI_SECURITY)      |
+---------------------------------------------------------------------------------+
                                      ▲
                                      │ Network / Host / Syslog Telemetry
+---------------------------------------------------------------------------------+
| L1: Existing SOC Core (Detection Foundation & System of Record)                 |
| - [E] Suricata 8.0.6 (AF_PACKET Multi-Threaded Passive NIDS, eve.json)          |
| - [E] Snort 3.12.2.0 (Offline PCAP Cross-Validation Engine)                     |
| - [E] Wazuh 4.14.7 (Endpoint HIDS Agents & Manager Telemetry)                   |
| - [E] Filebeat 8.19.20 (Secure Ingestion Shipping)                              |
| - [E] Elasticsearch 8.19.20 Cluster (Hot Data Streams, Index Templates)         |
| - [E] Network Firewalls & L3 SPAN Infrastructure                               |
+---------------------------------------------------------------------------------+
```
- **목적**: 기존 인프라(L1), AI 자산 보호(L2), AI 분석 지능(L3), 통합 운영/승인(L4) 계층의 수직적 책임 분리.
- **보안 의미**: 상위 계층(L2~L4)의 소프트웨어 오류나 모델 다운이 발생해도 L1의 침입 탐지 및 로그 저장은 완벽하게 격리되어 지속 작동(Fail-Safe).

### 5.1 L1 — Existing SOC Core
- **역할**: 패킷 가시성 확보, 시그니처 기반 실시간 침입 탐지, 호스트 시스템 콜 감사, 분산 색인 및 무결성 영구 보존.
- **불변 원칙**: L1은 L2~L4 컴포넌트에 대한 런타임 의존성을 일체 갖지 않음.

### 5.2 L2 — AI Security Enforcement
- **역할**: LLM 및 RAG 호출 트래픽의 인라인 중계, OWASP GenAI/Agentic 2026 위협 실시간 차단, 개인정보/시크릿 마스킹, `AI_SECURITY` 텔레메트리 방출.
- **성능 원칙**: 검사 오버헤드는 150ms 이내로 제한.

### 5.3 L3 — AI SOC Intelligence
- **역할**: 이종 도메인 이벤트 정규화, 결정론적 킬체인 상관분석, 후보 인시던트(Candidate Incident) 생성, 로컬 LLM 기반 심층 요약 및 하이브리드 RAG 대응안 추천.
- **분석 원칙**: 원시 Alert 수천 건을 LLM에 직접 입력하지 않고, 반드시 상관분석 엔진이 압축한 인시던트 단위로 추론.

### 5.4 L4 — Unified AI-SOC
- **역할**: 전통 보안 위협과 AI 보안 현황의 단일 화면 관제, 다크모드 전세계 위협 지도, 4단계 인터랙티브 조사 콘솔 및 인간 승인 기반 SOAR 대응 집행.

---

## 6. Existing SOC Integration

기존에 검증된 L1 파이프라인은 설정 변경 없이 원형 그대로 유지됩니다.

### Diagram 3: Existing SOC Architecture
```text
  [ Network Traffic ]          [ Host System Events ]
          │                              │
          ▼                              ▼
  +---------------+              +---------------+
  | L3 SPAN Port  |              | Wazuh Agent   |
  +-------+-------+              +-------+-------+
          │ (Zero-IP Promiscuous)        │
          ▼                              ▼
  +---------------+              +---------------+
  | Suricata 8.0  |              | Wazuh Manager |
  | (AF_PACKET)   |              +-------+-------+
  +-------+-------+                      │
          │ eve.json                     │ Wazuh Alerts
          ▼                              ▼
  +---------------+              +---------------+
  | Filebeat 8.19 |              | Filebeat /    |
  | Ingestion     |              | Custom Shipper|
  +-------+-------+              +-------+-------+
          │                              │
          └──────────────┬───────────────┘
                         ▼
             +-----------------------+
             | Elasticsearch 8.19    |
             | Data Streams          |
             +-----------+-----------+
                         │
                         ▼
             +-----------------------+
             | Kibana 8.19 Dashboards|
             +-----------------------+
```
- **연동 방식**: 기존 Suricata `eve.json`과 Wazuh 인덱서는 그대로 Elasticsearch에 색인되며, v2.0에서는 Logstash Ingest Pipeline에 경량 ECS 필터를 추가하여 공통 스키마(`soc-events-*`)로 섀도우 미러링합니다.

---

## 7. Security Data Architecture

모든 원시 보안 데이터는 수집 즉시 정규화 파이프라인을 거쳐 계층화된 스토리지 정책에 따라 저장됩니다.
- **수집 레이어**: Filebeat(EVE JSON), Syslog UDP 5514(방화벽), FluentBit/HTTP(AI 게이트웨이).
- **파싱 & 인리치먼트 레이어**: ECS 매핑, MaxMind GeoIP 위경도 좌표 주입, 신뢰도 스코어링.
- **스토리지 레이어**: Elasticsearch 8.19.20 Hot Data Stream (`soc-events-*`, `soc-incidents-*`, `soc-audit-*`).
- **보존 주기**:
  - Hot Storage (실시간 검색): 30일
  - Warm/Cold Storage (감사 보존): 365일 (불변 플래그 적용)

---

## 8. Unified Security Event Architecture

전통적 인프라 보안과 AI 보안을 단일 모델로 융합하기 위해 **ECS 기반 6대 도메인 공통 스키마**를 채택합니다.

### Diagram 6: Unified Security Event Flow
```text
  [Traditional Telemetry]                        [AI Telemetry]
  - Suricata (Network)                           - AI Gateway (Prompt Injection)
  - Wazuh (Host/Auth)                            - AI DLP (PII / Secret Leakage)
  - Firewall (Border Traffic)                    - RAG Security (Poisoning/ACL)
  - Web Server (App Logs)                        - Agentic Guard (Excessive Agency)
            │                                              │
            ▼                                              ▼
  +-------------------+                          +-------------------+
  | Ingest Pipeline A |                          | Ingest Pipeline B |
  +---------+---------+                          +---------+---------+
            │                                              │
            └──────────────────────┬───────────────────────┘
                                   ▼
              +-----------------------------------------+
              |      Unified Security Event Schema      |
              |                                         |
              |  • Identity: timestamp, event_id, trace |
              |  • Domain: 6 Security Domains           |
              |  • Entity: src, dst, user, asset, model |
              |  • Risk: severity, risk_score, conf     |
              |  • Detection: engine, rule_id, sid      |
              |  • Framework: ATT&CK / ATLAS ID         |
              |  • Decision: action, policy_id, reason  |
              +--------------------+--------------------+
                                   │
                                   ▼
              +-----------------------------------------+
              |   Elasticsearch Data Stream: soc-events |
              +-----------------------------------------+
```

### 6대 Event Domain 정의
1. `NETWORK_SECURITY`: 포트 스캔, DoS, 비콘, 프로토콜 이상 (Suricata/Snort)
2. `HOST_SECURITY`: 파일 무결성(FIM), 악성 프로세스, 루트킷 (Wazuh)
3. `WEB_SECURITY`: SQLi, XSS, Path Traversal, 웹셸 (Nginx/WAF)
4. `IDENTITY_SECURITY`: SSH 브루트포스, 비인가 계정 접근, 권한 상승 (Auth/IAM)
5. `AI_SECURITY`: 프롬프트 주입, 모델 탈옥, 시스템 프롬프트 탈취, 에이전트 남용 (AI Gateway)
6. `DATA_SECURITY`: 개인정보(PII) 유출, API 키/비밀번호 노출, RAG 비인가 접근 (AI DLP)

---

## 9. Incident Architecture

AegisAI는 수천 건의 파편화된 Alert를 관제 분석가에게 노출하지 않고, 문맥적으로 연결된 단일 **Incident** 객체로 변환하여 관리합니다.

```text
[ Raw Events ]  ➔  [ Detection Rules ]  ➔  [ Alerts ]  ➔  [ Correlation Engine ]  ➔  [ Incident ]
(100,000 EPS)       (1,000 EPS)             (100 EPS)       (15-min Window)            (1 Incident)
```

### Incident 핵심 구성 필드
- `incident_id`: 고유 식별자 (`INCIDENT-YYYYMMDD-UUID`)
- `title` & `summary`: 인시던트 핵심 요약 (AI SOC Analyst 생성)
- `risk_score` (0~100) & `severity`: 동적 산출된 위험도 등급
- `entities`: 공격자 IP, 피해 자산 호스트명, 관련 사용자 ID, 대상 AI 모델명
- `attack_stage`: 현재 킬체인 진행 단계 (Recon ➔ Weapon ➔ Exploit ➔ AI Attack ➔ Exfil)
- `timeline`: 밀리초 단위 이벤트 시계열 배열
- `mappings`: MITRE ATT&CK 기법 ID 및 MITRE ATLAS 기법 ID 목록
- `evidence_refs`: 연관된 원시 EVE JSON 로그 ID 및 PCAP SHA-256 해시
- `recommended_action`: 제안된 차단 스크립트 및 정책 변경안
- `approval_status`: `PENDING` ➔ `APPROVED` / `REJECTED` / `EXECUTED`

---

## 10. Correlation Architecture

기존의 검증된 다단계 킬체인 상관분석 엔진([`BL-CORR-001`](../01-requirements/01_AS_IS_SOC_BASELINE.md))을 LLM으로 대체하지 않고, **결정론적 1차 집계기(Deterministic Aggregator)**로 유지합니다.

```text
                                [ Unified Events ]
                                        │
                                        ▼
                  +-------------------------------------------+
                  | [M] Multi-Stage Kill Chain Engine         |
                  |                                           |
                  | • Grouping: src_ip, dst_ip, session_id    |
                  | • Sliding Window: 15 minutes              |
                  | • State Machine:                          |
                  |   Stage 1: Recon (Scan / Enum)            |
                  |   Stage 2: Initial Access (Brute/Web)     |
                  |   Stage 3: Lateral Movement / AI Probe    |
                  |   Stage 4: Execution / Injection          |
                  |   Stage 5: Exfiltration / Secret Leak     |
                  +---------------------+---------------------+
                                        │
                                        ▼
                           [ Candidate Incident ]
                                        │
                                        ▼
                  +-------------------------------------------+
                  | [N] AI SOC Analyst (Reasoning & Context)  |
                  +-------------------------------------------+
```
- **역할 분담**:
  - **상관분석 엔진 (결정론적)**: 이벤트 그룹화, 타임 윈도우 계산, 공격 단계 천이 판정 (오탐 없는 고속 처리).
  - **AI SOC Analyst (맥락적)**: 침해 인과관계 해석, 자연어 요약, 위험도 가중치 산출, 대응 조치 권고.

---

## 11. AI SOC Analyst

AI for Security 계층의 핵심 컴포넌트로서, 상관분석 엔진이 넘겨준 `Candidate Incident`를 심층 분석합니다.

### Diagram 4: AI for Security Architecture
```text
  +----------------------+
  |  Candidate Incident  |
  +----------+-----------+
             │
             ▼
  +-------------------------------------------------------------------------------+
  | [N] AI SOC Analyst Engine                                                     |
  |                                                                               |
  |  +--------------------+   +--------------------+   +-----------------------+  |
  |  | Alert Triage Unit  |   | Attack Timeline    |   | Dynamic Risk Scorer   |  |
  |  | (Noise Filtering)  |   | Sequencer          |   | (Composite Formula)   |  |
  |  +---------+----------+   +---------+----------+   +-----------+-----------+  |
  |            │                        │                          │              |
  |            └────────────────────────┼──────────────────────────┘              |
  |                                     ▼                                         |
  |                       +---------------------------+                           |
  |                       | Evidence & Graph Analyzer |                           |
  |                       +-------------+-------------+                           |
  +-------------------------------------│-----------------------------------------+
                                        │
                                        ▼
                          +---------------------------+
                          | [M] Security Knowledge RAG| ◄── (ATT&CK / Playbooks)
                          +-------------+-------------+
                                        │
                                        ▼
                          +---------------------------+
                          | Structured Incident Report|
                          | & Recommended Action      |
                          +---------------------------+
```
- **동적 위험도 산출 공식**:
  $$\text{Risk Score} = (\text{Base Severity} \times 0.30) + (\text{Asset Criticality} \times 0.25) + (\text{Kill Chain Stage} \times 0.25) + (\text{AI Confidence} \times 0.20)$$

---

## 12. Security Knowledge RAG

근거 없는 보안 권고(Hallucination)를 방지하기 위해 엄격한 **지식 검색 증강(RAG)** 파이프라인을 구축합니다.

### Diagram 7: Security RAG Architecture
```text
  [ Ingestion Pipeline ]                               [ Retrieval Pipeline ]
  +-------------------------------+                    +-------------------------------+
  | MITRE ATT&CK v19.2 Documents  |                    | AI Analyst Context Query      |
  | MITRE ATLAS AI Threat Matrix  |                    +---------------+---------------+
  | Suricata/Snort Rule Catalog   |                                    │
  | Incident Response Playbooks   |                                    ▼
  +---------------+---------------+                    +-------------------------------+
                  │                                    | Hybrid Retriever              |
                  ▼                                    | - BM25 Sparse Search (Exact)  |
  +-------------------------------+                    | - Dense Vector Search (Cosine)|
  | Document Ingestion Guard      |                    +---------------+---------------+
  | (Scanner: Injection / PII)    |                                    │ Reciprocal Rank Fusion
  +---------------+---------------+                                    ▼
                  │ Validated Markdown                 +-------------------------------+
                  ▼                                    | Re-Ranker & Threshold Filter  |
  +-------------------------------+                    | (Drop if Cosine Sim < 0.65)   |
  | Chunking & BGE-M3 Embedding   |                    +---------------+---------------+
  +---------------+---------------+                                    │ Top-3 Chunks
                  │                                                    ▼
                  ▼                                    +-------------------------------+
  +-------------------------------+                    | Grounded Context Injection    |
  | Vector Store (FAISS / ES kNN) |───────────────────►| [Source: playbooks/ir-03.md]  |
  +-------------------------------+                    +-------------------------------+
```
- **환각 방지 기준**: 유사도 점수 0.65 미만 시 허위 정보를 생성하지 않고 "근거 문서 미확인"으로 처리.

---

## 13. AI Security Gateway

Security for AI 계층의 관문으로서, 모든 사내 AI 프롬프트 트래픽을 인라인에서 인터셉트합니다.

### Diagram 8: AI Security Gateway
```text
  [ User / Application ]
            │
            ▼ (HTTP POST /v1/chat/completions)
  +-------------------------------------------------------------------------------+
  | [N] AI Security Gateway (Reverse Proxy Engine)                                |
  |                                                                               |
  |  +--------------------+   +--------------------+   +-----------------------+  |
  |  | Auth & Token Check |   | Rate Limiter /     |   | Prompt De-obfuscator  |  |
  |  | (API Key / JWT)    |   | Quota Guard        |   | (Base64/Hex/URL Decode|  |
  |  +---------+----------+   +---------+----------+   +-----------+-----------+  |
  |            │                        │                          │              |
  |            ▼                        ▼                          ▼              |
  |  +-------------------------------------------------------------------------+  |
  |  | Deterministic Policy Pipeline                                           |  |
  |  |  [Step 1] AI DLP Engine (PII 6-Pattern, Secret 20-Pattern Check)        |  |
  |  |  [Step 2] Prompt Injection Detector (Regex + DeBERTa Guard Model)       |  |
  |  |  [Step 3] Classification & RBAC Validator (Confidential / Secret / Open)|  |
  |  +-------------------------------------+-----------------------------------+  |
  |                                        │                                      |
  |             ┌──────────────────────────┴──────────────────────────┐           |
  |             ▼                                                     ▼           |
  |     [ VIOLATION: BLOCK ]                                  [ PASSED: FORWARD ] |
  |     - Return HTTP 403                                     - Route to LLM/RAG  |
  |     - Emit AI_SECURITY Log                                - Stream Validation |
  +-------------│-----------------------------------------------------│-----------+
                │                                                     ▼
                ▼                                            +-----------------+
    +-----------------------+                                | LLM / Ollama    |
    | Elasticsearch Cluster |◄── (Async Telemetry Emission)  +--------+--------+
    +-----------------------+                                         │ Output
                                                                      ▼
                                                             +-----------------+
                                                             | Output DLP/Scan |
                                                             +--------+--------+
                                                                      │ Safe Resp
                                                                      ▼
                                                             [ User / App ]
```

---

## 14. AI DLP

사내 기밀 및 개인정보의 AI 외부 유출을 원천 방지하는 룰 엔진입니다.
- **PII 탐지 (6종)**: 주민번호(체크섬), 전화번호, 이메일, 카드번호(Luhn), 계좌번호, 여권번호.
- **Secret 탐지 (20종)**: AWS/GCP/Azure 키, OpenAI 키, SSH 개인키, JWT, DB 커넥션 스트링.
- **5대 확정적 조치 정책**:
  1. `ALLOW`: 무해한 일반 프롬프트 통과.
  2. `MASK`: 개인정보를 `[PII_PHONE_1]` 등 형태 보존형 토큰으로 치환하여 LLM 전달.
  3. `WARN`: 위험 경고 배너와 함께 분석가 감사 로그 기록.
  4. `REQUIRE_APPROVAL`: 관리자 승인 큐 대기 (승인 전까지 LLM 전달 보류).
  5. `BLOCK`: 연결 즉시 차단 및 HTTP 403 Forbidden 반환.

---

## 15. RAG Security

RAG 데이터 저장소 및 검색 파이프라인에 대한 보안 통제:
1. **문서 수집 검증 (Ingestion Guard)**: 등록되는 모든 문서 내 제로폰트(Zero-font), 숨김 텍스트, 간접 프롬프트 주입 페이로드 사전 검사 및 서명 검증.
2. **검색 접근 제어 (Document ACL)**: 사용자 역할(General, Analyst, Admin)에 따라 검색 가능한 벡터 인덱스 파티셔닝.
3. **컨텍스트 격리**: 검색된 RAG 청크는 시스템 프롬프트와 엄격히 분리된 `<untrusted_rag_context>` 태그 내에 샌드박싱하여 LLM에 전달.

---

## 16. Agent Security

자율 에이전트(Agentic AI)의 비인가 도구 호출 및 권한 남용(OWASP Agentic 2026 ASI01) 방어:
1. **최소 권한 도구 등록부 (Tool Allowlist)**: 읽기 전용(Read-Only) 도구만 기본 허용.
2. **위험 명령어 차단**: 셸 실행 인자 내 `rm`, `mkfs`, `drop`, `chmod`, `sudo`, 파이프(`|`), 백틱(```) 포함 시 게이트웨이 레벨에서 실행 거부.
3. **도구 호출 예산 제한 (Execution Budget)**: 세션당 최대 도구 호출 횟수(기본 8회)를 초과할 경우 루프 강제 차단.

---

## 17. Unified AI-SOC

최상위 운영 계층(L4)에서는 Kibana와 경량 FastAPI 웹 콘솔의 장점을 결합한 듀얼 프론트엔드 전략을 채택합니다.
- **Kibana Enterprise View (대규모 분석가용)**: 전세계 위협 지도(Map Layer), 시계열 이벤트 차트, 도메인별 트래픽 분포.
- **FastAPI AI Workspace (인시던트 대응 및 승인용)**: 4단계 실시간 AI 침해조사 모달창, 공격 타임라인 시각화, 1-Click 인간 승인 큐.

---

## 18. Closed-loop Security

AegisAI의 가장 강력한 차별점인 **폐루프 선순환 방어 체계**입니다.

### Diagram 9: Closed-loop Security
```text
  [ Attacker / Prompt Injector ]
                │
                ▼ (OWASP LLM01: Prompt Injection Attempt)
  +-------------------------------+
  | L2: AI Security Gateway       |
  | Action: BLOCK (HTTP 403)      |
  +---------------+---------------+
                  │
                  ▼ (Real-time Telemetry: event_domain = AI_SECURITY)
  +-------------------------------+
  | L1: Elasticsearch Data Stream |
  +---------------+---------------+
                  │
                  ▼ (Cross-Domain Correlation Window)
  +-------------------------------+
  | L3: Correlation Engine        | ◄── (Correlated with Network Recon & Web SQLi)
  | Output: INCIDENT-20260928-001 |
  +---------------+---------------+
                  │
                  ▼
  +-------------------------------+
  | L3: AI SOC Analyst            | ──► [ MITRE ATT&CK: T1190 + ATLAS: AML.T0051 ]
  | Rec: Block IP at Perimeter    |
  +---------------+---------------+
                  │
                  ▼ (Proposal to Queue)
  +-------------------------------+
  | L4: Human-in-the-Loop Approval|
  | Analyst Action: [ APPROVE ]   |
  +---------------+---------------+
                  │
                  ▼ (Automated Execution)
  +---------------------------------------------------------------+
  | Containment Enforcement                                       |
  | 1) Perimeter Firewall: Block Attacker IP (nftables rule injected)|
  | 2) AI Security Gateway: Revoke User Token / Blacklist Source   |
  +---------------+-----------------------------------------------+
                  │
                  ▼
  +-------------------------------+
  | New Audit Telemetry Emitted   | ──► (Feedback to Elasticsearch for Re-test)
  +-------------------------------+
```

---

## 19. Human-in-the-loop Response

AegisAI의 자동화 대응은 **HITL Level 4 (Human-Approved Response)** 경계 내로 제한됩니다.

### Diagram 10: Human-in-the-loop Response
```text
  +---------------------------+
  | Candidate Containment     |
  | (Generated by AI Analyst) |
  +-------------+-------------+
                │
                ▼
  +-------------------------------------------------------------------------------+
  | Deterministic Policy Engine (Pre-Approval Safety Gate)                        |
  | - Protected Asset Collision Check (Never Block Gateways, SIEM, DNS, VIPs)     |
  | - Command Injection Syntax Sanity Check (Reject Metacharacters)               |
  | - TTL Expiration Check (Valid for 15 minutes only)                            |
  +-------------------------------------+-----------------------------------------+
                                        │
                                        ▼ (Safe Proposal)
  +-------------------------------------------------------------------------------+
  | Analyst Decision Workspace (Web UI Modal)                                     |
  | [ Target: 10.77.20.88 ]  [ Reason: SQLi + Prompt Injection Kill Chain ]       |
  | [ Action: nftables drop ] [ TTL: 4 Hours ]                                    |
  |                                                                               |
  |     [ APPROVE (Execute) ]       [ MODIFY (Edit TTL/IP) ]     [ REJECT (Drop) ]|
  +-------------│───────────────────────────────│─────────────────────────│-------+
                │ (Signed Token)                │                         │
                ▼                               ▼                         ▼
  +---------------------------+   +---------------------------+   +---------------+
  | Response Orchestrator     |   | Re-enter Policy Engine    |   | Log Reason to |
  | (Firewall/Wazuh Execution)|   +---------------------------+   | Audit Trail   |
  +---------------------------+                                   +---------------+
```

---

## 20. Trust Boundary

AegisAI 아키텍처는 시스템 내·외부의 10대 보안 신뢰 경계(Trust Boundary)를 명확히 식별하고 통제합니다.

### Diagram 11: Trust Boundary
```text
  [ External World ]
  ================== [ TB-01: Perimeter Boundary ] ==================
  [ DMZ Zone ]
  ================== [ TB-02: Web Application Boundary ] ============
  [ Internal Network ]
  ================== [ TB-03: Internal Trust Boundary ] =============
  [ Management Network ]
  ================== [ TB-04: SOC Admin Boundary ] ==================
  [ Security / Sensor Network ]
  ================== [ TB-05: SIEM Ingestion Boundary ] =============
  [ AI Security Gateway ]
  ================== [ TB-07: Inbound Prompt Boundary ] =============
  ================== [ TB-08: Model Execution Boundary ] ============
  [ LLM Inference Runtime ]
  ================== [ TB-09: Knowledge Storage Boundary ] ==========
  [ RAG Vector DB ]
  ================== [ TB-10: SOAR Execution Boundary ] =============
  [ Firewall / Switch OS ]
```

### Trust Boundary 통제 매트릭스
| Boundary ID | 경계 명칭 | 횡단 데이터 | 위협 및 위험 | 필수 보안 통제 (Controls) |
|---|---|---|---|---|
| **TB-01** | Perimeter Boundary | 외부 인바운드 트래픽 | DDoS, 무차별 스캔, 침투 | 경계 방화벽 차단 정책, L3 라우팅 격리 |
| **TB-02** | Web App Boundary | HTTP 요청/응답 | Web Exploit, 파라미터 변조 | WAF, 입력값 검증, DMZ 망분리 |
| **TB-03** | Internal Trust Boundary | 사내 사용자 트래픽 | 내부 횡적이동, 악성코드 | 서브넷 격리, 802.1Q VLAN, 접근제어 |
| **TB-04** | SOC Admin Boundary | 분석가 관리 트래픽 | 세션 탈취, 비인가 승인 | MFA, 전용 관리망(VLAN 10), RBAC |
| **TB-05** | SIEM Ingestion Boundary | EVE JSON, 텔레메트리 | 로그 변조, 위조 주입 | TLS 암호화, Beats 상호인증, DLQ |
| **TB-07** | Inbound Prompt Boundary | 사용자 프롬프트 | Prompt Injection, 탈옥, PII | AI Gateway 정규식/DLP, 토큰 인증 |
| **TB-08** | Model Execution Boundary | LLM 출력 스트림 | 악성 셸코드, 기밀 유출 | 출력 마스킹, 실행 권한 격리 |
| **TB-09** | Knowledge Storage Boundary | RAG 문서 청크 | Vector Poisoning, 비인가조회| RAG 수집 검증기, 문서 ACL, FAISS 격리|
| **TB-10** | SOAR Execution Boundary | 방화벽 차단 커맨드 | 오차단으로 인한 인프라 마비| 보호대역 충돌검사, 분석가 1-Click 승인|

---

## 21. Network / Zone Architecture

`01_AS_IS_SOC_BASELINE`의 망분리 원칙을 준수하여 논리적 영역(Zone)을 분리합니다.

```text
+---------------------------------------------------------------------------------+
| ZONE-EXTERNAL (인터넷 / 공격망)                                                 |
+---------------------------------------------------------------------------------+
                                       │
                                       ▼
+---------------------------------------------------------------------------------+
| 경계 방화벽 (AhnLab TrusGuard / Virtual Gateway)                                |
+---------------------------------------------------------------------------------+
            │                                  │                     │
            ▼                                  ▼                     ▼
+-----------------------+          +-----------------------+ +--------------------+
| ZONE-DMZ              |          | ZONE-INTERNAL         | | ZONE-MGMT          |
| (Web Servers, WAF)    |          | (User PCs, Dev Apps)  | | (Admin Console)    |
+-----------------------+          +-----------------------+ +--------------------+
            │                                  │                     │
            └─────────────────┬────────────────┘                     │
                              ▼                                      │
+-------------------------------------------------------------+      │
| ZONE-AI (생성형 AI 인프라 영역)                            |      │
| • AI Security Gateway (8080/TCP)                           |      │
| • Local LLM Inference Engine (Ollama 11434/TCP)             |      │
| • Security RAG Vector DB (FAISS / Local Vector Store)       |      │
+-----------------------------+-------------------------------+      │
                              │ AI Security Telemetry                │
                              ▼                                      │
+-------------------------------------------------------------+      │
| ZONE-SOC (통합 보안관제 및 모니터링 영역)                   |◄─────┘
| • Network Sensor (Suricata 8.0.6 - 무IP Promiscuous 캡처)   |
| • SIEM Cluster (Elasticsearch 9200, Logstash 5044, Kibana)  |
| • AegisAI Intelligence Engine (FastAPI 8501)                |
+-------------------------------------------------------------+
```

---

## 22. Deployment Architecture

논리적 아키텍처 컴포넌트를 실제 배포 가능한 단위로 매핑합니다.

### Diagram 12: Deployment Architecture
```text
  [ Host Node: soc-sensor ]               [ Host Node: soc-siem / Controller ]
  +--------------------------------+      +-----------------------------------------+
  | OS: Ubuntu 22.04 LTS           |      | OS: Ubuntu 22.04 LTS / Docker Engine    |
  |                                |      |                                         |
  | • [E] Suricata 8.0.6 (Host OS) |      | • [E] Elasticsearch 8.19 Container      |
  |   (NIC: ens33, AF_PACKET)      |      | • [E] Kibana 8.19 Container             |
  | • [E] Snort 3.12 (CLI Tools)   |      | • [E] Wazuh Manager/Indexer Container   |
  | • [E] Filebeat Shipper         |      | • [N] AI Security Gateway Container     |
  +----------------+---------------+      | • [M] Logstash ECS Pipeline Container   |
                   │                      | • [N] AegisAI FastAPI App (Port 8501)   |
                   │ EVE JSON Log         | • [N] Ollama LLM Service (Qwen2.5 7B)   |
                   └─────────────────────►| • [N] FAISS Vector DB Mount             |
                                          +-----------------------------------------+
```

### 컴포넌트 배포 명세표
| Component | 패키지/컨테이너 형태 | 권장 호스트 | 포트 / 인터페이스 | 의존성 |
|---|---|---|---|---|
| **Suricata 8.0** | Native Daemon | `soc-sensor` | `ens33` (Zero-IP) | L3 SPAN 미러링 |
| **Elasticsearch** | Docker Container | `soc-siem` | `9200/TCP` (내부) | 호스트 SSD 스토리지 |
| **Kibana** | Docker Container | `soc-siem` | `5601/TCP` (분석가) | Elasticsearch |
| **AI Gateway** | Docker Container | `soc-siem` | `8080/TCP` (앱/사용자) | Policy Engine, Redis |
| **FastAPI Core** | Python/Uvicorn | `soc-siem` | `8501/TCP` (웹 포털) | Elasticsearch, Ollama |
| **Ollama LLM** | Native Daemon | `soc-siem` | `11434/TCP` (내부) | GPU 또는 AVX2 CPU |
| **Vector DB** | Embedded FAISS | `soc-siem` | Local File IPC | Python 프로세스 |

---

## 23. Observability

AegisAI 시스템 자체의 헬스체크 및 성능 관제:
- **메트릭 수집**: AI Gateway 처리량(RPS), 추가 지연시간(p95, p99 Latency), 토큰 소비량, HTTP 상태코드.
- **AI 컴포넌트 헬스체크**:
  - `GET /health/gateway`: 게이트웨이 정상 동작 여부
  - `GET /health/llm`: Ollama 데몬 핑 및 모델 로드 상태
  - `GET /health/siem`: Elasticsearch 클러스터 헬스 (`green` / `yellow`)
- **알람 기준**: 게이트웨이 지연 > 250ms 지속 시 또는 LLM 추론 타임아웃 발생 시 경보 발령.

---

## 24. Audit Architecture

AI가 개입된 모든 보안 판단은 법적·규제적 책무성을 위해 **완전한 감사 체인(End-to-End Audit Chain)**으로 기록됩니다.
- **추적 식별자 연계**: `trace_id`를 요청 최초 진입점(게이트웨이)에서 발급하여 LLM 추론, RAG 조회, 인시던트 생성, 분석가 승인, 방화벽 차단 로그까지 100% 동일하게 전파.
- **감사 레코드 필수 필드**:
  ```json
  {
    "trace_id": "tr-20260928-8f9a1b",
    "timestamp": "2026-09-28T09:37:05.123Z",
    "prompt_raw_hash": "sha256:4a8b...",
    "prompt_masked": "사용자 [PII_PHONE_1] 차단 요청",
    "gateway_action": "MASK",
    "ai_reasoning": "SQLi 및 프롬프트 탈옥 킬체인 식별",
    "rag_citations": ["playbooks/ir-03.md#chunk2"],
    "analyst_id": "analyst_kim",
    "approval_action": "APPROVED",
    "executed_command": "nft add rule inet filter input ip saddr 10.77.20.88 drop"
  }
  ```

---

## 25. Fail-safe Architecture

AI 컴포넌트의 장애가 기존 SOC의 보안 기능을 마비시키지 않도록 **Graceful Degradation**을 보장합니다.

### Diagram 13: Failure / Fail-safe Architecture
```text
  [ Scenario A: AI Gateway Crash / Timeout ]
  - Traffic: User AI Prompts
  - Action: Fail-Closed (기밀 보호를 위해 비인가 AI 요청 차단)
  - Impact to Core SOC: ZERO (Suricata 패킷 캡처 및 룰 탐지 100% 정상 작동)

  [ Scenario B: Local LLM Engine (Ollama) Crash ]
  - Traffic: Incident Analysis Pipeline
  - Action: Graceful Degradation
    Candidate Incident ➔ [ AI Analyst Down ] ➔ Fallback to Static Rule Template
    - 화면 표출: "⚠️ AI 심층 분석 일시 지연 - 룰 기반 요약 대체"
    - 인시던트 목록 및 수동 방화벽 차단 기능은 100% 정상 제공
  - Impact to Core SOC: ZERO

  [ Scenario C: RAG Vector DB Search Failure ]
  - Action: Fallback to Raw ATT&CK Matrix Static JSON lookup
  - Hallucination Guard: "근거 플레이북 검색 실패 - 수동 절차 확인 요망" 표출
```

---

## 26. Security Controls

AegisAI 플랫폼 자체를 보호하기 위한 4대 보안 통제선:
1. **Identity & Access**: 분석가 웹 콘솔 로그인 시 강력한 패스워드 정책, 역할 기반 접근 제어(RBAC), 세션 타임아웃(30분).
2. **Network Security**: AI Gateway와 Ollama 간 통신은 `127.0.0.1` 루프백 바인딩 또는 격리된 Docker 브릿지 네트워크로만 허용 (외부 노출 차단).
3. **Data Security**: `.env` 파일 커밋 방지(Pre-commit Git Hook), 파일 권한 `chmod 600`, 메모리 상의 평문 민감정보 제로화.
4. **AI Application Security**: 프롬프트 인젝션 방어, 탈옥 방어, 모델 역추적 방어, Agent 권한 최소화.

---

## 27. Architecture Decision Records (ADR)

### ADR-001: 기존 Elastic Stack(8.19) 유지 여부
- **Context**: Elastic Stack 9.x 릴리스가 존재하나 기존 실습 랩은 8.19.20 기반으로 안정화됨.
- **Decision**: 기존 **Elasticsearch 8.19.20 유지** (`KEEP`).
- **Reason**: v2.0의 목적은 AI 통합이지 제품 메이저 마이그레이션이 아니며, 버전 변경 시 기존 Kibana 대시보드 호환성 파괴 위험.
- **Impact**: 검증된 EVE JSON 인덱싱 안정성 100% 보존.

### ADR-002: Wazuh와 Elasticsearch 통합 방식
- **Context**: Wazuh는 독립적인 Indexer를 내장하고 있어 Elasticsearch와의 물리 저장소 중복 문제 발생.
- **Decision**: 물리 저장소 분리 유지 + **논리적 상위 이벤트 통합** (`INTEGRATE`).
- **Reason**: Wazuh Manager의 내부 작동을 훼손하지 않고, Wazuh Alert를 Filebeat를 통해 Elasticsearch `soc-events-*`로 이중 전달(Dual-Ship).

### ADR-003: 기존 Correlation Engine 재사용
- **Context**: LLM에게 다단계 상관분석을 전담시킬 것인가, 기존 파이썬 엔진을 유지할 것인가.
- **Decision**: **기존 킬체인 상관분석 엔진 100% 재사용 및 확장** (`KEEP & MODIFY`).
- **Reason**: LLM은 비결정론적이며 대량 이벤트 처리 시 비용/지연 발생. 시간 윈도우 계산은 결정론적 코드가 수행하고 LLM은 해석만 담당.

### ADR-004: AI Security Gateway 배치 방식
- **Context**: 게이트웨이를 각 애플리케이션 내 라이브러리로 넣을 것인가, 중앙 리버스 프록시로 둘 것인가.
- **Decision**: **중앙 독립 리버스 프록시 (Option B)** 채택.
- **Reason**: 중앙 집중적 정책 집행, 일관된 감사 로그 수집, 애플리케이션 코드 수정 최소화.

### ADR-005: Local LLM vs External API 선정
- **Context**: 보안관제 인시던트 데이터에는 사내 IP, 취약점, 계정 정보가 포함됨.
- **Decision**: **온프레미스 Local LLM (Ollama Qwen2.5 7B) 단독 운영** (MVP 기준).
- **Reason**: 폐쇄망 운영 가능, 데이터 외부 유출 위험 0%, 비용 예측 가능.

### ADR-006: Security RAG Vector Store 선정
- **Context**: 대규모 분산 벡터 DB(Milvus/Pinecone) 도입 여부.
- **Decision**: **경량 인메모리 FAISS 및 Elasticsearch kNN 플러그인** 활용.
- **Reason**: 수천 개 수준의 보안 플레이북 청크 처리에 분산 DB는 과도한 오버엔지니어링.

### ADR-007: Unified Event 처리 방식
- **Context**: 6대 도메인 이벤트를 어떤 형식으로 통일할 것인가.
- **Decision**: **Elastic Common Schema (ECS) 기반 확장 JSON 모델** 채택.
- **Reason**: Elasticsearch와의 기본 호환성 극대화 및 필드 검색 표준화.

### ADR-008: Human-in-the-loop (HITL) 통제 경계
- **Context**: AI가 방화벽 차단을 전자동으로 집행할 수 있는가.
- **Decision**: **Level 4 (Human-Approved Response) 엄격 준수**.
- **Reason**: 오차단으로 인한 핵심 인프라 마비 방지. 분석가 승인 토큰 없이 커맨드 실행 불가.

### ADR-009: AI Telemetry 저장 방식
- **Context**: AI Gateway 차단 로그를 어디에 저장할 것인가.
- **Decision**: 중앙 Elasticsearch의 **`soc-events-*` 데이터 스트림에 동일하게 색인**.
- **Reason**: 네트워크 이벤트와 AI 이벤트를 동일 인덱스에서 교차 검색 및 상관분석 가능.

### ADR-010: Dashboard 구축 전략
- **Context**: Kibana 단독 운영 vs 신규 웹 프론트엔드 전면 개발.
- **Decision**: **하이브리드 전략 (Kibana 대규모 뷰 + FastAPI 경량 인터랙티브 콘솔)**.
- **Reason**: Kibana의 강력한 맵/시계열 시각화를 재사용하면서, AI 대화형 조사 및 1-Click 승인 UX를 FastAPI로 완벽 지원.

---

## 28. Component Matrix

| Component ID | Component 명칭 | 계층 | 상태 | 주요 책임 및 역할 | Data In | Data Out |
|---|---|:---:|:---:|---|---|---|
| **CMP-IDS-001** | Suricata NIDS | L1 | `[E]` | 실시간 네트워크 패킷 센싱 및 침입 탐지 | Mirrored Packets | eve.json |
| **CMP-IDS-002** | Snort 3 Engine | L1 | `[E]` | 오프라인 PCAP 교차 검증 및 룰 비교 | PCAP 파일 | alert_json |
| **CMP-HIDS-001**| Wazuh Manager | L1 | `[E]` | 엔드포인트 시스템 감사 및 계정 침해 탐지 | Agent Events | Wazuh Alerts |
| **CMP-SIEM-001**| Elasticsearch | L1 | `[E]` | 보안 빅데이터 분산 색인 및 스토리지 | Parsed JSON | Search Hits |
| **CMP-SHP-001** | Filebeat Shipper| L1 | `[E]` | 원시 로그 파일의 무손실 고속 전송 | Log Files | TCP Stream |
| **CMP-AIGW-001**| AI Security GW | L2 | `[N]` | 인라인 프롬프트 인터셉트, 인증, 정책 집행 | User Prompts | Safe Prompts / 403 |
| **CMP-DLP-001** | N2SF AI DLP | L2 | `[M]` | PII 및 Secret 탐지, 형태보존 마스킹 | Prompt Text | Masked Text / Telemetry|
| **CMP-ATK-001** | Prompt Defense | L2 | `[N]` | OWASP 2026 주입 공격 및 탈옥 탐지 | Prompt Text | Attack Decision |
| **CMP-CORR-001**| Correlation Eng | L3 | `[M]` | 15분 타임 윈도우 다단계 킬체인 상관분석 | Unified Events | Candidate Incident |
| **CMP-AISOC-001**| AI SOC Analyst | L3 | `[N]` | 인시던트 심층 요약, 타임라인, 위험도 채점 | Cand. Incident | Incident Report |
| **CMP-RAG-001** | Security RAG | L3 | `[M]` | ATT&CK/플레이북 하이브리드 지식 검색 | Query String | Citation Context |
| **CMP-LLM-001** | Ollama Engine | L3 | `[N]` | 온프레미스 Qwen2.5 7B 추론 서빙 | Prompt Chunks | Generated Text |
| **CMP-DASH-001**| Kibana Map Dash | L4 | `[M]` | 전세계 위협 지도 및 트래픽 현황판 표출 | ES Aggregations | Web Visuals |
| **CMP-UI-001**  | FastAPI Console | L4 | `[N]` | 4단계 AI 침해조사 워크스페이스 & 승인 큐 | Analyst Inputs | REST API / Commands |
| **CMP-SOAR-001**| HITL Orchestrator| L4 | `[N]` | 분석가 1-Click 승인 기반 방화벽/ACL 집행 | Approved Token | Firewall Rules |

---

## 29. Interface Matrix

| Source Component | Destination Component | 전달 데이터 | 인터페이스 규격 | 보안 통제 |
|---|---|---|---|---|
| Suricata 8.0 | Filebeat Shipper | 원시 EVE JSON 스트림 | Local File I/O | 파일 읽기 전용 권한 |
| Filebeat Shipper | Elasticsearch Cluster | 정규화 이벤트 | Elastic Bulk API / TLS | mTLS 및 API Key 인증 |
| Wazuh Manager | Elasticsearch Cluster | HIDS 보안 알림 | Filebeat Dual-Ship | 내부 통신 격리 |
| User Client | AI Security Gateway | 사용자 프롬프트 | HTTPS / REST API | Bearer Token / API Key |
| AI Security Gateway | Ollama LLM Engine | 검증된 프롬프트 | HTTP REST (11434/TCP) | Localhost 바인딩 |
| AI Security Gateway | Elasticsearch Cluster | `AI_SECURITY` 텔레메트리 | REST JSON Ingestion | 감사 인덱스 쓰기 전용 |
| Elasticsearch | Correlation Engine | 도메인별 보안 이벤트 | ES Scroll / Search API | 서비스 전용 읽기 계정 |
| Correlation Engine | AI SOC Analyst | Candidate Incident | Python In-Memory DTO | 프로세스 메모리 격리 |
| AI SOC Analyst | Security Knowledge RAG | 의미 검색 쿼리 | Vector Search / IPC | 인메모리 FAISS 인덱스 |
| AI SOC Analyst | FastAPI Web Console | 완성된 인시던트 리포트 | JSON over WebSocket/REST | 세션 인증 및 XSS 방어 |
| FastAPI Web Console | HITL Orchestrator | 승인된 차단 액션 | Signed Approval Token | 15분 만료 TTL 검증 |
| HITL Orchestrator | Border Firewall / Host | IP 차단 명령어 | SSH / nftables API | 화이트리스트 검증 |

---

## 30. Representative E2E Scenario

### Diagram 14: Representative E2E Sequence
```text
Attacker        Firewall/Sensor    AI Gateway       SIEM/Correlation   AI Analyst       Analyst (L4)
   │                   │               │                   │               │                 │
   │ (1) Network Scan  │               │                   │               │                 │
   ├──────────────────►│               │                   │               │                 │
   │                   │ (2) EVE: T1046│                   │               │                 │
   │                   ├───────────────┼──────────────────►│               │                 │
   │ (3) Web SQLi      │               │                   │               │                 │
   ├──────────────────►│               │                   │               │                 │
   │                   │ (4) EVE: T1190│                   │               │                 │
   │                   ├───────────────┼──────────────────►│               │                 │
   │ (5) Prompt Inject │               │                   │               │                 │
   │ (OWASP LLM01)     │               │                   │               │                 │
   ├───────────────────┼──────────────►│                   │               │                 │
   │                   │               │ (6) BLOCK (403)   │               │                 │
   │<──────────────────┼───────────────┤                   │               │                 │
   │                   │               │ (7) AI_SECURITY   │               │                 │
   │                   │               ├──────────────────►│               │                 │
   │                   │               │                   │ (8) Sliding   │                 │
   │                   │               │                   │     Window    │                 │
   │                   │               │                   │     Merge     │                 │
   │                   │               │                   ├──────────────►│                 │
   │                   │               │                   │               │ (9) RAG Lookup  │
   │                   │               │                   │               │ (ATT&CK+ATLAS)  │
   │                   │               │                   │               │ (10) Rec Action │
   │                   │               │                   │               ├────────────────►│
   │                   │               │                   │               │                 │ (11) Review
   │                   │               │                   │               │                 │      [APPROVE]
   │                   │ (12) Inject nftables Block Rule   │               │                 │
   │                   │◄──────────────────────────────────┴───────────────┴─────────────────┤
   │ (13) Blocked      │                                                                     │
   ├──X (Packet Dropped)                                                                     │
```
- **09:30 Recon**: 외부 공격자(`10.77.20.88`)가 Nmap 스텔스 스캔 수행 ➔ Suricata 감지 ➔ `NETWORK_SECURITY` (T1046)
- **09:32 Web Exploit**: DMZ Web 서버 대상 SQL Injection 시도 ➔ Suricata 감지 ➔ `WEB_SECURITY` (T1190)
- **09:37 AI Injection**: 사내 고객센터 LLM 앱에 탈옥 프롬프트 주입 ➔ AI Gateway 차단(403) ➔ `AI_SECURITY` (AML.T0051)
- **09:40 Incident Formation**: 상관분석 엔진이 15분 내 동일 IP 공격을 `INCIDENT-20260928-001`로 통합
- **09:40 AI Triage & RAG**: AI SOC Analyst가 ATT&CK/ATLAS 듀얼 매핑 및 플레이북 기반 방화벽 차단 스크립트 도출
- **09:41 HITL Enforcement**: 관제 분석가가 화면에서 [승인] 클릭 ➔ 방화벽에 `10.77.20.88` Drop 룰 즉시 주입 완료

---

## 31. MVP Architecture

프로젝트 1차 완료를 위한 최소 실행 가능 구조(MVP):
```text
  [ Traffic Ingestion ] ──► [ Suricata 8.0 ] ──► [ Filebeat ] ──► [ Elasticsearch 8.19 ]
                                                                          │
  [ Prompt Requests ]   ──► [ AI Security Gateway ] ──► (AI_SECURITY) ────┘
                                  │
                                  ▼ (ALLOW / MASK / BLOCK)
                             [ Ollama LLM ]
                                  │
                                  ▼
                     [ Correlation Engine ]
                                  │
                                  ▼
                     [ AI SOC Analyst + RAG ]
                                  │
                                  ▼
        [ Unified Threat Map & FastAPI 4-Step Approval Console ]
```

---

## 32. Advanced Architecture (Post-MVP)

MVP 완료 후 2단계 확장 로드맵:
- **다중 에이전트 협업 관제 (Multi-Agent SOC)**: 침해조사 에이전트, 악성코드 역분석 에이전트, 보고서 작성 에이전트 간 분업.
- **RAG Poisoning 실시간 샌드박스**: 수집 문서 동적 행위 분석 및 임베딩 드리프트 탐지.
- **머신러닝 이상 탐지 (ML Anomaly)**: 유저 행동 프로파일링(UEBA) 기반 이상 토큰 소비 탐지.
- **제한적 자율 대응 (Restricted Autonomous Level 5)**: 사전에 정의된 격리 랩 환경에 한해 무승인 즉시 격리 허용.

---

## 33. Performance & Scalability Consideration

- **AI Gateway 저지연 설계**: 정규식 및 로컬 가드레일 캐시를 활용하여 95%의 정상 요청을 50ms 이내에 중계.
- **상관분석 엔진 메모리 최적화**: 슬라이딩 윈도우(15분) 만료 이벤트를 주기적으로 메모리 해제하여 장기 실행 시 OOM 방지.
- **스케일아웃 전략**: 향후 관제 대상 확대 시 AI Gateway는 Stateless 컨테이너로 수평 확장(Scale-Out)하고, Elasticsearch 데이터 노드를 추가 증설.

---

## 34. Architecture Risks & Mitigations

| 위험 ID | 위험 명칭 | 발생 원인 | 영향도 | 아키텍처적 대응 방안 (Mitigation) | 잔여 위험 |
|---|---|---|:---:|---|---|
| **RSK-01** | LLM 환각 (Hallucination) | 모델의 임의 추론 성향 | High | 엄격한 RAG 기반 증적 강제 및 유사도 0.65 미만 시 생성 거부 | Low |
| **RSK-02** | 게이트웨이 병목 (Latency) | 복잡한 딥러닝 가드레일 | High | 경량 정규식 1차 필터링 ➔ 의심 트래픽만 비동기 정밀 모델 검사 | Medium |
| **RSK-03** | 오차단 (False Positive) | 엄격한 DLP 정책 오작동 | High | 핵심 인프라 화이트리스트 사전 검증 및 분석가 승인 필수화(HITL) | Low |
| **RSK-04** | AI 계층 다운 (Crash) | Ollama 메모리 부족 | Medium | Fail-Safe 아키텍처: L1 NIDS 및 룰 기반 관제로 즉시 자동 폴백 | Very Low |
| **RSK-05** | 간접 프롬프트 주입 | 외부 문서 내 숨겨진 주입 | High | RAG 수집 검증 샌드박스 및 XML 컨텍스트 태그 격리 | Medium |

---

## 35. Implementation Priority

```text
[Step 1] Existing SOC L1 Baseline 가용성 검증 및 동결
   ↓
[Step 2] Unified Security Event Schema (ECS 매핑) Logstash 파이프라인 구축
   ↓
[Step 3] AI Security Gateway (M4) & AI DLP (M5) 인라인 프록시 구현
   ↓
[Step 4] AI Gateway ➔ Elasticsearch 텔레메트리 방출 연동
   ↓
[Step 5] Correlation Engine (M1) 다중 도메인 인시던트 집계 로직 확장
   ↓
[Step 6] Security Knowledge RAG (M3) FAISS 인덱싱 및 검색기 구현
   ↓
[Step 7] AI SOC Analyst (M2) Ollama Qwen2.5 연동 침해 요약기 구현
   ↓
[Step 8] FastAPI 4단계 침해조사 워크스페이스 & HITL 1-Click 승인 큐 완성
   ↓
[Step 9] E2E Closed-loop 관제 검증 (정찰 ➔ 주입 ➔ 차단 피드백)
```

---

## 36. Architecture Constraints

1. **상용 클라우드 AI API 전송 금지**: 인시던트 데이터와 사내 프롬프트는 인터넷을 통해 외부(OpenAI, Anthropic 등)로 전송하지 않음.
2. **센서 NIC 무IP 원칙 준수**: `soc-sensor` 패킷 수집 인터페이스는 L3 IP를 할당하지 않음.
3. **단일 노드 리소스 제약**: SIEM 및 AI 추론 환경은 단일 고성능 워크스테이션(RAM 24GB~32GB) 내에서 구동 가능해야 함.

---

## 37. Open Issues (미확정 관리 항목)

| 이슈 ID | 항목 | 현재 상태 | 해결 계획 |
|---|---|---|---|
| **OPEN-ARCH-001** | 실제 VLAN 10/20/30 물리 IP | `NOT FROZEN` | 현장 배포 시 `ip addr` 실측 후 파라미터 매핑 확정 |
| **OPEN-ARCH-002** | TrusGuard 방화벽 Syslog 포트 | `PARTIAL` | UDP 5514 기본 설정 후 실 방화벽 정책 연동 테스트 |
| **OPEN-ARCH-003** | L3 SPAN 패킷 미러링 품질 | `REVALIDATE` | `tcpdump -eni ens33 -c 10` 수신 증적 확보로 최종 확정 |
| **OPEN-ARCH-004** | NTP 시간 동기화 | `REVALIDATE` | 인시던트 타임라인 정밀도를 위해 호스트 NTP 데몬 정상화 |

---

## 38. Final TO-BE Architecture

### A. 최종 통합 아키텍처 다이어그램
```text
===================================================================================================
                                      AegisAI v2.0 Platform
===================================================================================================

  [ INGESTION & SENSING ]
  +-------------------------------------+      +-------------------------------------+
  | L1: Suricata 8.0.6 (AF_PACKET) [E]  |      | L2: AI Security Gateway (8080)  [N] |
  | - Mirrored L3 SPAN Packets          |      | - Token Auth & Rate Limiting        |
  | - eve.json Event Streaming          |      | - OWASP 2026 Prompt Injection Guard |
  +------------------+------------------+      | - N2SF PII & Secret DLP Engine [M]  |
                     │                         +------------------+------------------+
                     │                                            │
                     │ NETWORK_SECURITY / WEB_SECURITY            │ AI_SECURITY / DATA_SECURITY
                     ▼                                            ▼
  =================================================================================================
  [ UNIFIED DATA LAKE ]
  +-----------------------------------------------------------------------------------------------+
  | L1: Elasticsearch 8.19.20 Security Data Lake [E]                                              |
  | - Data Streams: soc-events-*, soc-incidents-*, soc-audit-*                                    |
  | - Logstash ECS Pipeline & GeoIP Location Enrichment [M]                                       |
  +-----------------------------------------------+-----------------------------------------------+
                                                  │
                                                  ▼
  =================================================================================================
  [ CORRELATION & INTELLIGENCE ]
  +-----------------------------------------------------------------------------------------------+
  | L3: Deterministic Kill Chain Correlation Engine (15-min Sliding Window) [M]                   |
  | -> Multi-Domain Aggregation -> Generates Candidate Incident                                   |
  +-----------------------------------------------+-----------------------------------------------+
                                                  │
                                                  ▼
  +-----------------------------------------------------------------------------------------------+
  | L3: AI SOC Analyst Engine (Ollama Qwen2.5 7B) [N]                                             |
  | - Dynamic Risk Scorer (0-100) & Attack Timeline Sequencer                                     |
  | - Dual Framework: MITRE ATT&CK v19.2 + MITRE ATLAS Mapping                                    |
  | - Grounded by Security Knowledge RAG (FAISS Hybrid Search) [M]                                |
  +-----------------------------------------------+-----------------------------------------------+
                                                  │
                                                  ▼
  =================================================================================================
  [ UNIFIED OPERATIONS & HITL RESPONSE ]
  +-----------------------------------------------------------------------------------------------+
  | L4: Unified AI-SOC Operator Workspace                                                         |
  | - Kibana 8.19 Dark-mode Global Threat Map & Event Stream [M]                                  |
  | - FastAPI AI 4-Step Investigation Modal Console (:8501) [N]                                   |
  | - Human-in-the-Loop (HITL Level 4) Approval Queue [N]                                         |
  +-----------------------------------------------+-----------------------------------------------+
                                                  │
                                                  ▼ (Analyst 1-Click Approval)
  +-----------------------------------------------------------------------------------------------+
  | Closed-loop Containment Enforcement                                                           |
  | -> nftables Perimeter Drop / L3 ACL / AI Gateway Token Revocation                            |
  | -> Real-time Audit Trail Emitted back to Elasticsearch [N]                                    |
  +-----------------------------------------------------------------------------------------------+
===================================================================================================
```

### B. Architecture 핵심 정의
> **AegisAI는 기존 Suricata·Wazuh·Elasticsearch 기반 SOC의 탐지 능력을 100% 보존하면서 AI를 상위 분석·의사결정 지원 계층으로 추가하고, 동시에 AI 시스템 자체에서 발생하는 보안위협을 동일한 SOC Telemetry와 Incident 체계로 통합하는 Closed-loop AI Security Architecture를 구축한다.**

---

## 39. Next Artifact

다음 단계 산출물:
> **`03_AI_THREAT_MODEL — AegisAI AI/LLM/RAG/Agent 통합 위협모델 분석서`**

### Threat Model의 핵심 입력값 인계
본 아키텍처에서 확정된 다음 요소들이 `03_AI_THREAT_MODEL`의 직접적인 분석 대상 자산 및 공격표면으로 전달됩니다:
1. **자산 및 컴포넌트**: `AI Security Gateway`, `Ollama LLM 런타임`, `FAISS 벡터 DB`, `Elasticsearch 데이터 레이크`, `FastAPI 승인 콘솔`.
2. **진입점 (Entry Points)**: 사용자 프롬프트 엔드포인트(`:8080/v1/chat`), 분석가 승인 엔드포인트(`:8501/api/approve`), RAG 지식 수집 경로.
3. **신뢰 경계 (Trust Boundaries)**: `TB-01`(경계), `TB-07`(프롬프트 경계), `TB-08`(모델 실행 경계), `TB-09`(RAG 스토리지 경계), `TB-10`(SOAR 집행 경계).
4. **위협 프레임워크 기준**: **OWASP GenAI LLM Top 10 2026**, **OWASP Agentic Top 10 2026**, **MITRE ATLAS**, **NIST AI RMF 1.0**.
