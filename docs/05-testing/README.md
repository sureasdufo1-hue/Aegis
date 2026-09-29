# 🧪 05. 보안관제 및 AI 통합 평가·검증 체계 (Testing & AI Evaluation)

> **기준 일자:** 2026-09-28  
> **프로젝트 공식 명칭:** **AegisAI — AI for Security × Security for AI Integrated SOC Platform**  
> **현재 유효 기준선:** **v2.0 AI Evaluation Plan (09_AI_EVALUATION_PLAN.md)**  
> **레거시 참조:** v1.0 SOC Lab 종합 테스트 및 검증 계획서 (Implementation Plan Section 45)  
> **적용 규정:** AGENTS.md Section 8 (Phase & Gate Policy), Section 17 (Testing Rules), Section 18 (Evidence Rules)

---

## 1. 평가 및 테스트 문서 계층 및 로드맵

```text
[ v2.0 통합 시스템 상세설계서 (LLD) ]
docs/03-design/08_LOW_LEVEL_DESIGN.md (126개 챕터, 48개 모듈, 10대 API)
      │
      ▼
[ v2.0 AI 보안 기능 평가 및 성능검증 계획서 ]
docs/05-testing/09_AI_EVALUATION_PLAN.md (★ 160개 챕터, 3대 평가 도메인, 17대 매트릭스)
      │
      ├──────────────────────────────┬──────────────────────────────┐
      ▼                              ▼                              ▼
[ v2.0 통합 구현 계획서 ]     [ v2.0 통합 시험 계획서 ]    [ v2.0 AI 레드팀 시나리오 ]
docs/04-deployment/          11_TEST_PLAN.md              12_AI_RED_TEAM_SCENARIOS.md
10_IMPLEMENTATION_PLAN.md    (★ 175개 챕터, 24대 매트릭스) (★ 180개 챕터, 24대 매트릭스)
(182개 챕터, 24대 매트릭스)
```

---

## 2. 핵심 평가 및 테스트 산출물 바로가기

| 문서 ID | 문서명 | 버전 / 성격 | 설명 및 링크 |
|---|---|:---:|---|
| `09_AI_EVALUATION_PLAN` | **AegisAI AI 보안 기능 평가 및 성능검증 계획서** | `v2.0 Eval Master` | [09_AI_EVALUATION_PLAN.md](./09_AI_EVALUATION_PLAN.md)<br>160개 챕터, 3대 도메인, 10대 평가대상(`EVT-*`), 6대 데이터셋(`DS-*`), 14대 메트릭(`MET-*`), 7대 무관용 결함(`CRIT-FAIL-*`), 6대 MVP 시나리오, 17대 매트릭스(A~Q) |
| `11_TEST_PLAN` | **AegisAI 통합 시스템 시험 및 검증 계획서** | `v2.0 Test Master` | [11_TEST_PLAN.md](./11_TEST_PLAN.md)<br>175개 챕터, 35개 핵심 TC, 14대 다이어그램, 7대 무관용 결함 CI 게이트, 6대 E2E 시나리오, 24대 매트릭스(A~X) |
| `12_AI_RED_TEAM_SCENARIOS` | **AegisAI AI 보안 레드팀 공격 시나리오 및 적대적 검증 계획서** | `v2.0 Red Team Master` | [12_AI_RED_TEAM_SCENARIOS.md](./12_AI_RED_TEAM_SCENARIOS.md)<br>180개 챕터, 51개 세부 공격 시나리오, 7대 심층 시나리오, 16대 다이어그램, 24대 필수 매트릭스(A~X) |
| `E2E_VAL_REPORT_V1.0` | **Phase 31 E2E 통합 검증 보고서** | `v1.0 Baseline` | [PHASE31_E2E_VALIDATION_REPORT.md](./PHASE31_E2E_VALIDATION_REPORT.md)<br>전통적 SOC Lab 31개 페이즈 및 14대 게이트 실측 증적 요약 |

---

## 3. v2.0 AI 평가 체계 핵심 요약 (Evaluation Highlights)

```text
┌────────────────────────────────────────────────────────────────────────┐
│ 1. 3대 평가 도메인:                                                    │
│    - Domain A: AI for Security (탐지/요약/RAG 지원)                   │
│    - Domain B: Security for AI (Gateway 차단/DLP/Agent 격리)           │
│    - Domain C: Closed-loop Integrated SOC (HITL Nonce/SOAR/생존성)     │
│ 2. 7대 무관용 보안 결함 (Zero Tolerance / Gate Fail):                  │
│    - 비인가 RAG 인출, 임의 쉘 실행, 자기 승인, Nonce 재사용,            │
│      보호 자산 차단, 원문 시크릿 로깅, 무승인 Level 4 자동 집행        │
│ 3. 6대 MVP 평가 시나리오:                                              │
│    - Scen 1: Traditional SOC ➔ AI SOC 파이프라인                     │
│    - Scen 2: Prompt Injection ➔ AI Gateway 인라인 방어                │
│    - Scen 3: PII & Secret Leakage ➔ AI DLP 마스킹                     │
│    - Scen 4: Unauthorized RAG Access ➔ 권한 격리                     │
│    - Scen 5: High-Risk Response ➔ HITL Nonce & TTL 롤백                │
│    - Scen 6: AI 장애 시 Core SOC 지속성 및 무손실 가동                 │
│ 4. 1대 복합 교차 도메인 시나리오:                                      │
│    - Nmap 정찰 + Web 취약점 ➔ Prompt 탈옥 ➔ RAG 인출 시도 ➔ 15분 상관분석│
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. 레거시 v1.0 테스트 케이스 매트릭스 (Traditional SOC Baseline)

| Test ID | 대상 단계 | 요구사항 ID | 검증 항목 | 검증 방식 | 성공 기준 (Pass Criteria) | 증적 (Evidence) |
|---|---|---|---|---|---|---|
| **TC-HOST-001** | Phase 0 | `REQ-HOST-01` | 호스트 가상화/리소스 검증 | `verify_host_readiness.ps1` | Hyper-V 활성, WSL2 >= 2.1.5, Docker 정상, RAM >= 32GB | `EV-HOST-001` |
| **TC-REPO-001** | Phase 1 | `REQ-REPO-01` | 레포지토리 구조 및 보안 설정 | 디렉토리 트리 검사 & Pytest | 27개 표준 디렉토리 생성, 시크릿 ignore, 10/10 pytest 통과 | `EV-REPO-001` |
| **TC-NET-001** | Phase 2 | `REQ-NET-01` | 3개 가상 스위치 및 호스트 IP | `Get-VMSwitch`, `Get-NetIPAddress` | `soc-vsw-*` 3종 생성, `10.77.10.10/24` 바인딩 | `EV-NET-INFRA-001` |
| **TC-VM-001** | Phase 3 | `REQ-VM-01` | 4대 VM 생성 및 어댑터 매핑 | `Get-VM`, `Get-VMNetworkAdapter` | 4개 Gen 2 VM 생성, 총 7개 NIC 지정 스위치 연결 | `EV-VM-001` |
| **TC-ROUTE-001** | Phase 5 | `REQ-NET-01` | 게이트웨이 라우팅 & 호스트 경로 | `Get-NetRoute`, `ping` | 호스트 ➔ `10.77.30.0/24 via 10.77.10.1` 라우팅 등록 | `EV-NET-INFRA-001` |
| **TC-FW-001** | Phase 6 | `REQ-NET-01` | 게이트웨이 망분리 방화벽 격리 | nftables 룰셋 검증 (`nft -c -f`) | 공격망 ➔ 관리망 차단, 공격망 ➔ 희생망 허용 | `EV-FW-001` |
| **TC-MIRROR-001**| Phase 7 | `REQ-NET-02` | Hyper-V 포트 미러링 모드 | `Get-VMNetworkAdapter` | 희생 서버: `Source`, 센서 모니터링 NIC: `Destination` | `EV-MIRROR-CONFIG-001`|
| **TC-SURI-001** | Phase 10 | `REQ-IDS-01` | Suricata 8.x 설정 및 룰 로드 | `suricata -T -c suricata.yaml` | 설정 구문 오류 0건, 9000~9030 커스텀 룰셋 로드 | `EV-SURI-001` |
| **TC-SNORT-001**| Phase 14 | `REQ-IDS-02` | Snort 3 오프라인 PCAP 검증 | `snort -T -c snort.lua` | Snort 3 검증 모드 정상, 9100 커스텀 룰셋 로드 | `EV-SNORT-001` |
| **TC-SIEM-001** | Phase 19 | `REQ-SIEM-01`| Wazuh EVE JSON 로그 수집 파이프라인 | `local_rules.xml` 디코딩 검증 | Suricata `eve.json` ➔ Wazuh Alert 디코딩/인덱싱 성공 | `EV-WAZUH-001` |
| **TC-ANALYSIS-001**| Phase 22 | `REQ-SOC-01`| 다단계 킬체인 상관분석 엔진 | `python -m analyzer.main` | 정찰 ➔ 초기 침투 ➔ C2 3단계 공격 단일 Incident 그룹화 | `EV-ANALYSIS-001` |
| **TC-TUNE-001** | Phase 25 | `REQ-SOC-02`| 오탐(False Positive) 룰 튜닝 | Before/After 트래픽 검증 | 정상 트래픽 오탐 제거 + 공격 트래픽 탐지 유지 동시 만족 | `EV-TUNE-001` |
