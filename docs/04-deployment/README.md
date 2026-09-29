# 🚀 04. 보안관제 시스템 구축 및 배포 계획 체계 (Implementation & Deployment)

> **기준 일자:** 2026-09-29  
> **프로젝트 공식 명칭:** **AegisAI — AI for Security × Security for AI Integrated SOC Platform**  
> **현재 유효 기준선:** **v2.0 Implementation Plan (10_IMPLEMENTATION_PLAN.md)**  
> **레거시 참조:** v1.0 SOC Detection & Monitoring Lab Implementation Plan ([`SOC_Detection__Monitoring_Lab_Implementation_Plan_v1.0.pdf`](./SOC_Detection__Monitoring_Lab_Implementation_Plan_v1.0.pdf))  
> **적용 규정:** AGENTS.md Section 7 (Critical Implementation Order), Section 8 (Phase & Gate Policy)

---

## 1. 구현 및 배포 문서 계층 및 로드맵

```text
[ v2.0 AI 보안 기능 평가 및 성능검증 계획서 ]
docs/05-testing/09_AI_EVALUATION_PLAN.md (160개 챕터, 3대 도메인, 17대 매트릭스)
      │
      ▼
[ v2.0 통합 구축 및 구현 계획서 ]
docs/04-deployment/10_IMPLEMENTATION_PLAN.md (★ 182개 챕터, 15대 트랙, 24대 매트릭스)
      │
      ├──────────────────────────────┬──────────────────────────────┐
      ▼                              ▼                              ▼
[ v2.0 통합 시험 계획서 ]    [ v2.0 AI 레드팀 시나리오 ]    [ v2.0 운영 플레이북 ]
../05-testing/               ../05-testing/                13_OPERATION_PLAYBOOK.md
11_TEST_PLAN.md              12_AI_RED_TEAM_SCENARIOS.md   (예정)
(★ 175개 챕터, 24대 매트릭스) (★ 180개 챕터, 24대 매트릭스)
```

---

## 2. 핵심 구현 산출물 바로가기

| 문서 ID | 문서명 | 버전 / 성격 | 설명 및 링크 |
|---|---|:---:|---|
| `10_IMPLEMENTATION_PLAN` | **AegisAI 통합 구축 및 구현 계획서** | `v2.0 Master` | [10_IMPLEMENTATION_PLAN.md](./10_IMPLEMENTATION_PLAN.md)<br>182개 챕터, 15대 구현 트랙, 16대 Work Package, 9대 스프린트(Sprint 0~8), 8대 품질 게이트(G0~G7), 12대 다이어그램, 24대 매트릭스(A~X) |
| `IMP_V1.0_ORIGINAL` | **SOC Detection & Monitoring Lab 구현 계획서** | `v1.0 Baseline` | [`SOC_Detection__Monitoring_Lab_Implementation_Plan_v1.0.pdf`](./SOC_Detection__Monitoring_Lab_Implementation_Plan_v1.0.pdf)<br>Hyper-V 30단계 구축 계획, 패킷 미러링 가시성 우선 원칙, 게이트웨이 라우팅 |

---

## 3. v2.0 마스터 구현 체계 핵심 요약 (Implementation Highlights)

```text
┌────────────────────────────────────────────────────────────────────────┐
│ 1. 15대 구현 트랙 (TRACK-0 ~ TRACK-14):                                │
│    - T0: Baseline Freeze / T1: Core SOC 불변 보존                      │
│    - T2: 05 스키마 파이프라인 / T3: AI Security Gateway                │
│    - T4: Prompt Security (MOD-PDEF) / T5: AI DLP (MOD-DLP)             │
│    - T6: Security RAG (BGE-M3 + ES kNN) / T7: AI SOC Analyst (7B)      │
│    - T8: 15분 상관분석 / T9: OPA Policy & HITL Nonce                  │
│    - T10: 방화벽 액추에이터 & TTL 롤백 / T11: 에이전트 도구 격리       │
│    - T12: Unified Analyst UI / T13: MOD-TEST 평가 인프라               │
│    - T14: DevSecOps & 증적 패키징                                      │
│ 2. 8단계 최장 선행 Critical Path (총 31일 공수):                       │
│    - Base ➔ Schema ➔ Gateway ➔ Prompt/DLP ➔ Policy ➔ HITL ➔ RSP ➔ Eval │
│ 3. 7대 무관용 보안 결함 (Zero Tolerance CI Gate):                      │
│    - 비인가 RAG 인출, 임의 쉘 실행, 자기 승인, Nonce 재사용,            │
│      보호 자산 차단, 원문 시크릿 로깅, 무승인 Level 4 자동 집행        │
│ 4. 2개 인프라 환경 엄격 분리:                                          │
│    - VMware SOC Lab (가상 격리망) vs 실제 VLAN/DMZ 물리망 분리         │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. 레거시 v1.0 30단계 구축 단계 및 품질 게이트 (Historical Reference)

```text
[Phase 0~8: 인프라 & 패킷 가시성]
  Phase 0: Host Readiness ➔ GATE-HOST-01
  Phase 1: Repository Baseline
  Phase 2: Hyper-V Virtual Network
  Phase 3: VM Provisioning
  Phase 4: IP Address Configuration ➔ GATE-NET-01
  Phase 5: Gateway Routing
  Phase 6: Gateway Firewall ➔ GATE-FW-01
  Phase 7: Port Mirroring ➔ GATE-MIRROR-01
  Phase 8: Packet Visibility Validation (tcpdump) ➔ GATE-NET-01 [CRITICAL]
        │
        ▼
[Phase 9~14: 듀얼 IDS 배포 & 룰셋 검증]
  Phase 9: Suricata Deployment
  Phase 10: Suricata Configuration ➔ GATE-SURI-01
  Phase 11: Detection Validation ➔ GATE-DETECT-01
  Phase 12: PCAP Evidence Generation ➔ GATE-PCAP-01
  Phase 13: Snort Deployment ➔ GATE-SNORT-01
  Phase 14: Snort Offline PCAP Validation
        │
        ▼
[Phase 15~20: Wazuh SIEM 통합 & 대시보드]
  Phase 15: Wazuh Host Readiness
  Phase 16: Wazuh Deployment ➔ GATE-WAZUH-01
  Phase 17: Sensor Wazuh Agent
  Phase 18: Victim Wazuh Agent
  Phase 19: Suricata-Wazuh Integration ➔ GATE-SIEM-01
  Phase 20: Dashboard Validation
        │
        ▼
[Phase 21~30: 관제 분석, 튜닝, 증적 및 릴리즈]
  Phase 21: Attack Scenario Execution
  Phase 22: SOC Investigation ➔ GATE-ANALYSIS-01
  Phase 23: MITRE ATT&CK Mapping
  Phase 24: False Positive Analysis
  Phase 25: Detection Tuning ➔ GATE-TUNE-01
  Phase 26: Re-test Verification
  Phase 27: End-to-End Validation ➔ GATE-E2E-01
  Phase 28: Evidence Packaging
  Phase 29: Portfolio Documentation ➔ GATE-PORTFOLIO-01
  Phase 30: Final Release Gate ➔ GATE-FINAL-01
```
