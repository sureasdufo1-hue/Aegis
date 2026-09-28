# `01_AS_IS_SOC_BASELINE` — 기존 보안관제 시스템 기준선 분석서

**프로젝트:** AegisAI — AI for Security × Security for AI Integrated SOC Platform  
**문서 ID:** `01_AS_IS_SOC_BASELINE`  
**상위 문서:** [`00_PROJECT_DEFINITION_V2`](./00_PROJECT_DEFINITION_V2.md)  
**기준일:** 2026-09-28  
**문서 성격:** AS-IS / Baseline Freeze

본 문서는 새로운 구조를 설계하는 문서가 아니라 **현재 실제 구축·설정·검증된 환경을 증적 수준에 따라 분류하고 v2.0의 출발점을 동결하는 문서**다. 기준에 따라 `VERIFIED / IMPLEMENTED / PARTIAL / PLANNED / BLOCKED / DEPRECATED / UNKNOWN`을 구분하며, 증적이 부족한 사항은 임의로 보완하지 않는다.

---

## 1. Executive Baseline Summary

현재 프로젝트는 하나의 단일 환경이라기보다 **세 개의 논리적 환경**으로 분리해서 보는 것이 정확하다.

| 환경 | 목적 | 현재 판정 |
|---|---|---|
| **A. VMware SOC Lab** | IDS·공격 시뮬레이션·SIEM·상관분석 | **VERIFIED / 일부 REVALIDATION** |
| **B. 실제 Network/Server 환경** | VLAN·Firewall·DMZ·Web·DB·ELK | **PARTIAL / 구축 진행 중** |
| **C. AI Security 환경** | N2SF-AIGate·LLM·RAG·DLP | **PARTIAL / PLANNED 혼재** |

특히 VMware Lab과 실제 VLAN/DMZ 인프라를 하나의 네트워크로 합쳐 기록해서는 안 된다.

### Baseline Snapshot

| 영역 | 현재 확인된 구성 | 판정 | 증적 수준 | v2.0 |
|---|---|---|---|---|
| VMware SOC Lab | Gateway/Sensor/Attacker/Victim/SIEM | VERIFIED | High | KEEP |
| Suricata | 8.0.6 / AF_PACKET / EVE | VERIFIED | High | KEEP |
| Snort | 3.12.2 계열 기록 | IMPLEMENTED | Medium | REVALIDATE |
| Filebeat | 8.19.20 | VERIFIED | High | KEEP |
| Elasticsearch | 8.19.20 | VERIFIED | High | KEEP |
| Kibana | 8.19.20 | VERIFIED | High | KEEP |
| Wazuh | 4.14.7 | VERIFIED/PARTIAL | Medium | INTEGRATE |
| Custom Rules | Suricata/Wazuh | VERIFIED | High | KEEP |
| Correlation | 다단계 Kill Chain Analyzer | VERIFIED | High | KEEP & MODIFY |
| 실제 VLAN 환경 | 관리/내부/DMZ/DB/LOG | PARTIAL | Medium | REVALIDATE |
| Firewall/NAT | 정책 구축·수정 진행 | PARTIAL | Medium | HARDEN |
| NTP | 장애 이력 존재 | PARTIAL | Medium | REVALIDATE |
| SPAN | 설계·구성 대상 | PARTIAL | Low/Medium | REVALIDATE |
| AI Security | N2SF-AIGate 등 | PARTIAL | Medium | INTEGRATE |

---

# 2. Environment Classification

## 2.1 Environment A — VMware SOC Lab

현재 가장 높은 수준으로 검증된 환경이다.

```text
                    WAN / NAT
                       │
                 [soc-gateway]
                       │
                    TRANSIT
                       │
                 [soc-sensor]
                  /         \
               RED          BLUE
                │             │
        [soc-attacker]   [soc-victim]

                       │
                  EVE / Logs
                       │
                  [soc-siem]
                       │
              Elasticsearch/Kibana
```

기존 기록상 다음 단계가 PASS 이력을 가진다.

```text
NETWORK FOUNDATION
       ↓
SURICATA IDS BASELINE
       ↓
SIEM / EVE INGESTION
       ↓
REAL-TIME SIEM E2E
```

단, 이후 Hyper-V 기반 재구성은 별도 Phase이며 VMware 기준선과 혼동하지 않는다.

---

## 2.2 Environment B — 실제 Network/Server 구축

별도의 실제 인프라형 구축 환경이다.

확인되는 논리적 구성은 다음과 같다.

```text
                   External
                      │
                  Firewall
                      │
      ┌───────────────┼────────────────┐
      │               │                │
 Management         DMZ              Internal
 VLAN 10             │
      │          Web Server
 Admin PC             │
                      │ 3306
                      ▼
                  DB Network
                   VLAN 30
                      │
                  DB Server

                LOG / ELK
                    │
                 ELK Server
```

최근 프로젝트 기록에서 확인되는 후보 값은 다음과 같다.

| 대상 | 기록된 값 | 판정 |
|---|---|---|
| 관리자 PC | `192.168.10.2/24` | IMPLEMENTED / 재검증 필요 |
| 관리망 GW | `192.168.10.1` | IMPLEMENTED / 재검증 필요 |
| DB Server | `192.168.30.2/24` | IMPLEMENTED |
| DB Gateway | `192.168.30.1` | IMPLEMENTED |
| DB SSH | TCP 2222 | IMPLEMENTED |
| MySQL | TCP 3306 | IMPLEMENTED |
| DMZ Web | `172.16.10.10` 기록 | REVALIDATION REQUIRED |

이 값들은 **최종 Baseline Freeze 전에 실제 `ip addr`, 방화벽 Interface/Policy, Switch VLAN 출력으로 재검증해야 한다.**

---

# 3. VMware SOC Asset Baseline

| Asset | 역할 | 확인 상태 |
|---|---|---|
| `soc-gateway` | RED/BLUE/TRANSIT 라우팅 | VERIFIED |
| `soc-sensor` | Suricata IDS Sensor | VERIFIED |
| `soc-attacker` | 공격 발생 | VERIFIED |
| `soc-victim` | 공격 대상 | VERIFIED |
| `soc-siem` | Elastic/SIEM | VERIFIED |

### IP Conflict

과거 기록에서 SOC Lab IP가 시점별로 변경된 흔적이 있다.

예를 들어 Attacker에 대해 `10.77.20.50`과 `10.77.20.20` 기록이 모두 존재한다.

따라서 현재 문서에서는:

> **CONFLICT — 현장/최종 Snapshot 확인 필요**

로 처리한다.

Baseline Freeze 전 다음 명령 결과가 필요하다.

```bash
ip addr
ip route
```

각 VM의 현재 출력으로 최종 IP Table을 확정한다.

---

# 4. Suricata Baseline

## 4.1 확인된 구성

| 항목 | 기준선 |
|---|---|
| Version | **8.0.6 RELEASE** |
| Mode | IDS / Passive |
| Capture | AF_PACKET |
| Cluster Mode | `cluster_flow` |
| Primary visibility | RED |
| Secondary visibility | BLUE 관련 구성 기록 |
| Main Log | `/var/log/suricata/eve.json` |
| Rule Source | ET Open + Custom |
| Filebeat 연계 | VERIFIED |

기존 검증에서 RED 측 `ens37` 캡처, EVE JSON 생성, Filebeat ingestion이 확인된 기록이 있다.

## 4.2 Custom Rule

확인된 초기 SID에는 최소:

```text
1000001
1000002
```

가 있으며 이후 프로젝트에서는 커스텀 SID 범위가 확장된 기록이 있다.

따라서 전체 SID Inventory는 실제 `local.rules`를 다시 추출하여 확정한다.

### 판정

**VERIFIED — KEEP**

Suricata는 AegisAI에서도 기존 Network Detection Engine으로 유지한다.

---

# 5. Snort Baseline

기존 기록상 Snort 3 계열이 존재하며 `alert_json` 및 별도 SID 체계를 사용한 이력이 있다.

그러나 현재 운영 파이프라인에서 Suricata와 동일한 수준의 E2E 증적은 상대적으로 부족하다.

### 현재 판정

**IMPLEMENTED — REVALIDATION REQUIRED**

v2.0에서는 우선:

```text
Suricata = Primary Network Detection
Snort    = Secondary / Comparative Detection
```

후보로 두되 실제 설정을 확인한 뒤 확정한다.

---

# 6. Elastic Stack Baseline

## Elasticsearch

| 항목 | 기준선 |
|---|---|
| Version | 8.19.20 |
| Cluster Health | GREEN 확인 이력 |
| 역할 | Security Data Storage/Search |
| Suricata EVE | Indexed |
| 상태 | VERIFIED |

## Kibana

| 항목 | 기준선 |
|---|---|
| Version | 8.19.20 |
| 역할 | Dashboard / Search / Visualization |
| Dashboard | 구축 및 테스트 이력 |
| 상태 | VERIFIED / REVALIDATE |

## Filebeat

| 항목 | 기준선 |
|---|---|
| Version | 8.19.20 |
| Input | Suricata EVE |
| Source | `/var/log/suricata/eve.json` |
| Output | Elasticsearch |
| 상태 | VERIFIED |

확인된 기본 Pipeline은:

```text
Network Packet
      ↓
Suricata
      ↓
eve.json
      ↓
Filebeat
      ↓
Elasticsearch
      ↓
Kibana
```

이다.

---

# 7. Wazuh Baseline

| 항목 | 확인 내용 |
|---|---|
| Version | **4.14.7** |
| Deployment | Docker 기반 기록 |
| Manager | 존재 |
| Indexer | 존재 |
| Dashboard | 존재 |
| Custom Rule | 존재 |
| 대표 Rule ID | `100100`, `100101` 기록 |
| 상태 | VERIFIED / PARTIAL |

Wazuh는 Elastic Stack과 완전히 동일한 저장소라고 가정하지 않는다.

```text
Elastic Pipeline
Suricata → Filebeat → Elasticsearch → Kibana

Wazuh Pipeline
Agent / Event → Wazuh Manager → Wazuh Indexer → Dashboard
```

현재 v2.0에서는 두 계층의 데이터를 **논리적으로 Unified SOC에서 통합하는 방향**이 적절하지만, 실제 물리 저장소 통합 여부는 TO-BE에서 결정한다.

---

# 8. Detection & Correlation Baseline

## Rule Detection

현재까지 확인 가능한 탐지 계층:

```text
ET Open
   +
Suricata Custom Rule
   +
Wazuh Custom Rule
   +
Correlation Logic
```

## Kill Chain Correlation

기존 프로젝트에는 **다단계 Kill Chain Correlation Analyzer** 구현 및 테스트 이력이 있다.

확인 기록:

```text
pytest
13 / 13 PASS
```

따라서 Correlation Engine 자체는 단순 계획으로 분류하지 않는다.

### 판정

**VERIFIED — KEEP & MODIFY**

AegisAI에서는 이를 폐기하고 LLM으로 대체하지 않는다.

```text
Suricata / Wazuh
        ↓
Normalization
        ↓
Existing Correlation Engine
        ↓
Candidate Incident
        ↓
AI SOC Analyst
```

형태로 확장하는 것이 기준이다.

---

# 9. 기존 E2E Validation

현재 프로젝트 기록에서 다음 검증 이력이 존재한다.

| Test | 과거 결과 | 현재 판정 |
|---|---|---|
| Network Foundation | PASS | REVALIDATE |
| Suricata IDS Baseline | PASS | VERIFIED |
| EVE JSON Generation | PASS | VERIFIED |
| Filebeat Ingestion | PASS | VERIFIED |
| Elasticsearch Indexing | PASS | VERIFIED |
| Kibana Search | PASS | VERIFIED |
| Real-time SIEM E2E | PASS | VERIFIED |
| Custom Suricata Rule | PASS | VERIFIED |
| Wazuh Custom Rule | PASS 이력 | REVALIDATE |
| Correlation Analyzer | 13/13 PASS | VERIFIED |
| Hyper-V Phase 32 | BLOCKED | BLOCKED |

특히 Hyper-V Phase 32는 당시:

- Standard User / UAC elevation
- VMware VMnet과의 Route/Network Conflict

때문에 BLOCKED 상태였다.

따라서 Hyper-V 환경을 VMware 환경의 구축 완료 결과처럼 포함하지 않는다.

---

# 10. 실제 인프라 Network Baseline

현재 확인 가능한 논리적 구분:

```text
Management
Internal
DMZ
Database
LOG / ELK
External
```

다만 현재 이 환경은 VMware SOC Lab보다 증적 수준이 낮다.

### 현재 주요 이슈 기록

| 영역 | 상태 |
|---|---|
| 관리자 → DB SSH | Timeout 이력 |
| 관리망 ↔ DB망 Routing | 확인/설정 필요 이력 |
| Internal → DMZ HTTP | 정책/라우팅 문제 이력 |
| Web → Internet | SNAT/Outbound 문제 이력 |
| Web → NTP UDP/123 | 실패 이력 |
| VMware ELK Bridge | 구축 진행 이력 |
| Web → DB | 최종 검증 필요 |
| SPAN | 최종 검증 필요 |

따라서 현재 전체 실제 인프라를 `VERIFIED`로 판정해서는 안 된다.

### 종합 판정

**PARTIAL — REVALIDATION REQUIRED**

---

# 11. Firewall / NAT Baseline

현재까지 Firewall에서 다뤄진 기능:

- Inter-VLAN Policy
- Internal → DMZ
- Admin → DB
- Web → DB
- Outbound
- SNAT
- DNAT/VIP
- NTP UDP 123
- Logging

그러나 최근 프로젝트에서 NTP와 인터넷 통신 문제가 실제로 발생했기 때문에:

```text
Policy 존재
    ≠
E2E Communication Verified
```

이다.

최종 Baseline Freeze에는 반드시:

```text
Policy Hit
Session
Route
SNAT
DNAT
Return Traffic
```

증적을 요구한다.

---

# 12. NTP Baseline

NTP는 현재 **Critical Revalidation Item**으로 분류한다.

과거 기록에서:

```text
DNS Resolution     → 정상화 이력
NTP UDP/123        → 실패 이력
```

이 존재한다.

SOC에서는 여러 시스템의 이벤트를 시간 Window로 상관분석하므로 NTP 불일치는 AegisAI의 Incident Correlation 정확도에도 직접 영향을 줄 수 있다.

### 판정

**PARTIAL — REVALIDATION REQUIRED**

---

# 13. SPAN / Packet Visibility

SPAN/Mirroring은 실제 인프라의 Suricata 가시성을 결정하는 핵심 요소다.

현재 문서만으로 다음 전체 항목을 VERIFIED로 확정하기 어렵다.

```text
SPAN Source
SPAN Destination
Direction
VLAN
Sensor Interface
Packet Loss
```

### 판정

**PARTIAL / UNKNOWN**

최종적으로 다음 질문에 패킷 증적으로 답해야 한다.

> **Suricata Sensor가 관제 대상 VLAN의 필요한 트래픽을 실제로 보고 있는가?**

---

# 14. AI Security Baseline

현재 AI Security는 기존 SOC보다 성숙도가 낮으며 **계획과 기존 프로젝트 자산을 분리해야 한다.**

| 기능 | 현재 판정 | v2.0 |
|---|---|---|
| Local LLM | PARTIAL/기존 프로젝트 자산 | INTEGRATE |
| Security RAG | PARTIAL | INTEGRATE |
| PII Detection | PARTIAL | INTEGRATE |
| Secret Detection | PARTIAL | INTEGRATE |
| Data Classification | PARTIAL | INTEGRATE |
| DLP Policy | 설계 존재 | MODIFY |
| Prompt Injection Defense | PLANNED | NEW |
| AI Security Gateway | PARTIAL/설계 | NEW/INTEGRATE |
| AI SOC Analyst | PLANNED | NEW |
| Agent Security | PLANNED | NEW |

즉 N2SF-AIGate에서 설계한:

```text
PII
Secret
C/S/O Classification
ALLOW
MASK
APPROVAL
BLOCK
Audit Log
Local LLM / RAG
```

개념은 v2.0에서 재사용할 가치가 있지만 **AegisAI의 AI Security Gateway가 이미 완성되어 있다고 판정해서는 안 된다.**

---

# 15. Reuse Matrix

| Asset | Current | v2.0 Decision |
|---|---|---|
| VMware SOC Lab | VERIFIED | **KEEP** |
| Suricata | VERIFIED | **KEEP** |
| EVE JSON | VERIFIED | **KEEP** |
| Snort | IMPLEMENTED | **REVALIDATE** |
| Wazuh | VERIFIED/PARTIAL | **KEEP & INTEGRATE** |
| Filebeat | VERIFIED | **KEEP** |
| Elasticsearch | VERIFIED | **KEEP** |
| Kibana | VERIFIED | **KEEP & MODIFY** |
| Custom Rules | VERIFIED | **KEEP** |
| Correlation Engine | VERIFIED | **KEEP & MODIFY** |
| Actual Network | PARTIAL | **REVALIDATE** |
| Firewall | PARTIAL | **KEEP & HARDEN** |
| SPAN | PARTIAL | **REVALIDATE** |
| N2SF-AIGate | PARTIAL | **INTEGRATE** |
| AI SOC Analyst | PLANNED | **NEW** |
| Unified Event Schema | PLANNED | **NEW** |
| Security RAG | PARTIAL | **INTEGRATE/MODIFY** |
| AI Gateway | PARTIAL/PLANNED | **NEW/INTEGRATE** |

---

# 16. Gap Analysis

| 영역 | AS-IS | v2.0 필요 | Gap |
|---|---|---|---|
| Detection | Rule/Signature | 유지 | 낮음 |
| Correlation | Kill Chain Engine | Unified Incident | 중간 |
| AI Analysis | 없음/실험 | AI SOC Analyst | **높음** |
| Event Schema | 제품별 | Unified Schema | **높음** |
| Security RAG | 부분 자산 | SOC 연동 RAG | 높음 |
| Prompt Security | 미완성 | Gateway Detection | **높음** |
| DLP | 별도 프로젝트 | SOC 연동 | 높음 |
| AI Telemetry | 없음 | Elasticsearch 연계 | **높음** |
| Agent Security | 없음 | Policy/Approval | 높음 |
| Dashboard | Traditional SOC | Unified AI-SOC | 중간 |
| Response | 수동 중심 | HITL Workflow | 중간 |
| Evaluation | 개별 Test | 정량 AI 평가 | 높음 |

---

# 17. Critical Gap

AegisAI 구현 전에 해결 우선순위가 높은 항목은 다음과 같다.

1. **실제 인프라 Network Baseline 재검증** — VLAN/IP/Route/Firewall/NAT를 최종 확정한다.
2. **NTP 정상화** — SOC 전체 시간 기준을 통일한다.
3. **SPAN Visibility 검증** — 실제 패킷 가시성을 증명한다.
4. **Unified Security Event Schema 정의** — 기존 IDS/Wazuh와 AI Security Event의 공통 언어를 만든다.
5. **기존 Correlation Engine 인터페이스 정의** — AI가 기존 엔진을 대체하지 않고 결과를 소비하도록 한다.
6. **N2SF-AIGate 실제 구현 범위 동결** — 재사용 코드와 설계만 존재하는 기능을 분리한다.

---

# 18. PASS / BLOCKED Matrix

| 영역 | 판정 | 비고 |
|---|---|---|
| VMware Network Foundation | PASS / REVALIDATE | 기존 PASS |
| Suricata | PASS | 강한 기준선 |
| EVE JSON | PASS | 유지 |
| Filebeat | PASS | 유지 |
| Elasticsearch | PASS | 유지 |
| Kibana | PASS / REVALIDATE | Dashboard 재검토 |
| Wazuh | PASS / PARTIAL | 통합구조 확인 |
| Correlation | PASS | AI 연계 대상 |
| Hyper-V Phase 32 | **BLOCKED** | v2.0 필수 아님 |
| 실제 Routing | PARTIAL | 재검증 |
| Firewall | PARTIAL | 재검증 |
| NTP | **PARTIAL/BLOCKED 이력** | 우선 해결 |
| SPAN | PARTIAL | Packet Evidence 필요 |
| AI SOC | NOT TESTED | 신규 |
| AI Gateway | NOT TESTED/PARTIAL | 신규 통합 |

---

# 19. Baseline Freeze

현재 자료로 동결 가능한 범위는 다음과 같다.

| Baseline ID | Component | Baseline | Status |
|---|---|---|---|
| `BL-LAB-001` | VMware SOC Lab | Segmented SOC Lab | VERIFIED |
| `BL-IDS-001` | Suricata | 8.0.6 | VERIFIED |
| `BL-IDS-002` | Snort | 3.x | REVALIDATE |
| `BL-PIPE-001` | Filebeat | 8.19.20 | VERIFIED |
| `BL-ELK-001` | Elasticsearch | 8.19.20 | VERIFIED |
| `BL-ELK-002` | Kibana | 8.19.20 | VERIFIED |
| `BL-WAZUH-001` | Wazuh | 4.14.7 | VERIFIED/PARTIAL |
| `BL-CORR-001` | Correlation | Kill Chain Analyzer | VERIFIED |
| `BL-NET-001` | 실제 VLAN Network | — | **NOT FROZEN** |
| `BL-FW-001` | Firewall | — | **NOT FROZEN** |
| `BL-SPAN-001` | SPAN | — | **NOT FROZEN** |
| `BL-AI-001` | N2SF-AIGate | — | PARTIAL |
| `BL-AISOC-001` | AI SOC Analyst | — | PLANNED |

---

# 20. AS-IS 최종 판정

현재 프로젝트는 **전통적 SOC Core 영역은 이미 실습·포트폴리오 수준에서 상당한 E2E 검증이 이루어진 상태**로 볼 수 있다. 특히 Suricata → EVE JSON → Filebeat → Elasticsearch/Kibana와 커스텀 탐지 및 Kill Chain 상관분석은 AegisAI를 구축할 때 다시 만드는 것보다 재사용하는 것이 합리적이다.

반면 **최근 실제 VLAN·DMZ·DB·ELK 인프라는 아직 동일한 수준으로 동결할 수 없다.** Routing, Firewall/NAT, NTP, VMware Bridge, SPAN 등에서 구축·검증 과정의 이슈가 존재했으므로 현재 상태를 다시 측정해야 한다.

AI Security 영역은 N2SF-AIGate 등에서 활용 가능한 설계·구현 자산이 존재하지만 **AegisAI AI Security Gateway 또는 AI SOC가 완성된 상태는 아니다.** 따라서 v2.0에서 신규 통합 계층으로 다루는 것이 정확하다.

---

# 21. `02_TO_BE_ARCHITECTURE`로 넘길 고정 Constraint

다음 항목은 TO-BE 설계에서 원칙적으로 유지한다.

```text
[KEEP]

Suricata
EVE JSON
Filebeat
Elasticsearch
Kibana
Wazuh
Custom Detection Rules
Existing Correlation Engine
VMware SOC Attack/Defense Lab
```

다음은 수정·통합한다.

```text
[MODIFY / INTEGRATE]

Correlation → Unified Incident
Dashboard → Unified AI-SOC
N2SF-AIGate → AI Security Gateway
Security RAG → SOC Knowledge RAG
Traditional Event → Unified Security Event
```

다음은 신규 개발한다.

```text
[NEW]

AI SOC Analyst
Unified Security Event Schema
AI Security Telemetry
Prompt Injection Detection
AI Gateway Policy Engine
AI Incident Analysis
ATT&CK / ATLAS Mapping Layer
Human-in-the-loop Workflow
AI Evaluation Framework
```

단, 다음은 TO-BE 작성 전에 **최종 현장 확인값이 필요하다.**

```text
[NOT FROZEN]

실제 VLAN
실제 IP
Firewall Interface
Firewall Policy
NAT/VIP
Routing
SPAN
NTP
ELK 실제 서버 Network
```

---

# 22. 다음 산출물

다음 문서는:

> **`02_TO_BE_ARCHITECTURE — AegisAI 목표 시스템 아키텍처 설계서`**

이다.

다음 4개 계층을 중심으로 설계하는 것이 핵심이다.

```text
┌─────────────────────────────────────────┐
│ L4  Unified AI-SOC / Human Approval    │
├─────────────────────────────────────────┤
│ L3  AI SOC Analyst / Security RAG      │
├─────────────────────────────────────────┤
│ L2  AI Security Gateway / DLP          │
├─────────────────────────────────────────┤
│ L1  Existing SOC Core                  │
│     Suricata / Wazuh / Elastic         │
└─────────────────────────────────────────┘
```

즉 **L1은 최대한 건드리지 않고 L2~L4를 추가하는 구조**가 `02_TO_BE_ARCHITECTURE`의 핵심 설계 제약조건이다.
