# SOC Detection & Monitoring Lab
# 보고서 및 룰북 전체 통합 레지스터 (Report & Rulebook Register)

> **문서 식별 번호**: `REG-SOC-2026-001`  
> **최종 개정일시**: `2026-09-08 14:40:00 KST`  
> **관제 책임자**: SOC 관제센터장 & 수석 침해사고 분석가 (Lead Incident Commander)  
> **적용 표준**: NIST SP 800-61 Rev.3 (2025.04 확정본), NIST CSF 2.0, MITRE ATT&CK v19.2 (2026.08)  
> **프로젝트 기준선**: Suricata 8.0.6 · Snort 3.12.2.0 · Wazuh 4.14.7 · AI-Orchestrated SOC Copilot (Qwen3.5 9B/4B)  

---

## 1. 개요 및 3계층 보고서 통합 체계

본 레지스터는 **SOC Detection & Monitoring Lab**에서 실제 검증된 탐지 규칙, 센서 텔레메트리, 다단계 상관분석, AI 침해사고 조사 및 정책 승인 기록을 기반으로 구축된 3계층 통합 관제 보고서 체계의 전체 색인 및 추적성을 관리합니다.

```text
[계층 1. 침해유형별 탐지·대응 룰북 (Detection & Response Rulebooks)]
  - 무엇을 탐지하고 어떻게 조사·대응·복구할 것인가?
  - 7대 핵심 침해유형별 탐지 조건, 룰 시그니처, 패킷 분석, 대응 절차 및 튜닝 방법
                ↓
[계층 2. 침해사고별 분석·처리 결과보고서 (Incident Analysis & Response Reports)]
  - 실제로 무엇이 발생했고, 어떤 증적으로 판정 및 완화 조치되었는가?
  - 실측 E2E 다단계 침해사고, 웹 공격 집중 침해, 내부 인프라 오차단 방지 실사례
                ↓
[계층 3. 종합관제 운영·성과 보고서 (Comprehensive SOC Operations Report)]
  - 전체적으로 무엇을 탐지했고 얼마나 효과적·안전하게 대응하였는가?
  - 84건 실시간 경보, 듀얼 엔진 성능, 다단계 상관분석 성과, AI Copilot 및 HITL 승인 통제 지표
```

---

## 2. 전체 문서 목록 및 아티팩트 매핑

### 2.1 메인 보고서 및 룰북 (Tier 1 & Tier 3)

| 문서 코드 | 문서 파일명 및 경로 | 문서 분류 | 주요 내용 | 상태 |
|---|---|---|---|:---:|
| **DOC-REP-01** | [`01_SOC_COMPREHENSIVE_REPORT.md`](01_SOC_COMPREHENSIVE_REPORT.md) | 종합관제 보고서 | 관제 총평, 탐지 통계(84건), 듀얼 엔진 비교, AI Copilot 성과, HITL 거버넌스 | `VERIFIED` |
| **DOC-RUL-02** | [`02_SOC_COMMON_RULEBOOK.md`](02_SOC_COMMON_RULEBOOK.md) | 공통 대응 룰북 | 관제 아키텍처, 6대 역할, 사고 등급(P1~P4), NIST 800-61 대응 절차, 포렌식 원칙 | `VERIFIED` |

### 2.2 침해유형별 세부 탐지·대응 룰북 (Tier 1 Scenarios)

| 시나리오 코드 | 파일명 및 경로 | 대상 공격 유형 | 연계 규칙 및 기법 | RAG 플레이북 | 상태 |
|---|---|---|---|---|:---:|
| **IR-01** | [`scenarios/IR-01_NETWORK_RECON.md`](scenarios/IR-01_NETWORK_RECON.md) | 네트워크 스캔 및 은닉 정찰 | SID `9000001~9000008` (Nmap NULL/XMAS/FIN)<br>MITRE `T1595`, `T1046` | `01_port_scan_investigation.md` | `VERIFIED` |
| **IR-02** | [`scenarios/IR-02_AUTH_BRUTEFORCE.md`](scenarios/IR-02_AUTH_BRUTEFORCE.md) | SSH 및 웹 인증 무차별 대입 | SID `9020001~9020002` (High Frequency Auth)<br>MITRE `T1110`, `T1110.001` | `05_ssh_brute_force_investigation.md` | `VERIFIED` |
| **IR-03** | [`scenarios/IR-03_WEB_APPLICATION_ATTACKS.md`](scenarios/IR-03_WEB_APPLICATION_ATTACKS.md) | 웹 애플리케이션 침해 (SQLi/RCE) | SID `9010001~9010007` (UNION SELECT, Log4j)<br>MITRE `T1190`, `T1059` | `03_web_attack_investigation.md` | `VERIFIED` |
| **IR-04** | [`scenarios/IR-04_MALWARE_C2_REVERSESHELL.md`](scenarios/IR-04_MALWARE_C2_REVERSESHELL.md) | 악성코드 C2 및 역방향 셸 | SID `9030001~9030010` (TCP 4444, `/bin/sh`)<br>MITRE `T1071`, `T1059` | `04_malware_c2_investigation.md` | `VERIFIED` |
| **IR-05** | [`scenarios/IR-05_DOS_NETWORK_FLOOD.md`](scenarios/IR-05_DOS_NETWORK_FLOOD.md) | 서비스 거부 및 패킷 플러딩 | SID `9000008`, `9100002` (ICMP/SYN Flood)<br>MITRE `T1498`, `T1498.001` | `02_dos_flood_investigation.md` | `VERIFIED` |
| **IR-06** | [`scenarios/IR-06_MULTISTAGE_KILLCHAIN.md`](scenarios/IR-06_MULTISTAGE_KILLCHAIN.md) | 다단계 킬체인 상관분석 | CorrelationEngine 3단계 연계<br>MITRE `T1595` ➔ `T1190` ➔ `T1059` | 다단계 복합 플레이북 | `VERIFIED` |
| **IR-07** | [`scenarios/IR-07_FALSE_POSITIVE_TUNING.md`](scenarios/IR-07_FALSE_POSITIVE_TUNING.md) | 오탐 분석 및 탐지 튜닝 루프 | SID `9010001 rev:1` ➔ `rev:2`<br>정상 트래픽 FP 제거 & 공격 유지 | 튜닝 라이프사이클 | `VERIFIED` |

### 2.3 침해사고별 상세 분석·처리 결과보고서 (Tier 2 Incidents)

| 사고 식별 번호 | 파일명 및 경로 | 사고 명칭 | 침해 등급 | 공격자 / 피해 대상 | 최종 판정 |
|---|---|---|:---:|---|:---:|
| **INC-10.77.20.20-1787727443** | [`incidents/INC-10.77.20.20-1787727443.md`](incidents/INC-10.77.20.20-1787727443.md) | 정찰·웹취약점·C2 복합 침해사고 | **P1 (CRITICAL)** | `10.77.20.20` ➔ `10.77.30.20` | **TRUE_POSITIVE** (완전 격리 성공) |
| **INC-10.77.20.88-1788772741** | [`incidents/INC-10.77.20.88-1788772741.md`](incidents/INC-10.77.20.88-1788772741.md) | 웹 SQLi 및 데이터베이스 탈취 시도 | **P2 (HIGH)** | `10.77.20.88` ➔ `10.77.30.20:80` | **TRUE_POSITIVE** (인바운드 차단 승인) |
| **INC-10.77.10.1-1788772755** | [`incidents/INC-10.77.10.1-1788772755.md`](incidents/INC-10.77.10.1-1788772755.md) | 게이트웨이 보호 인프라 오차단 방지 | **P3 (MEDIUM)** | `10.77.10.1` (핵심 라우팅 GW) | **POLICY_REJECTED** (오차단 0건 방어) |

### 2.4 증적 및 추적성 부록 (Tier 3 Appendices)

| 부록 코드 | 파일명 및 경로 | 부록 명칭 | 주요 수록 내용 |
|---|---|---|---|
| **APP-EVI** | [`evidence/EVIDENCE_REGISTER.md`](evidence/EVIDENCE_REGISTER.md) | 전체 보안 증적 레지스터 | `EV-HOST-001` ~ `EV-E2E-002`, `EV-UI-001` ~ `EV-TEST-001` 메타데이터 전수 |
| **APP-RUL** | [`appendices/RULE_CATALOG.md`](appendices/RULE_CATALOG.md) | 탐지 규칙 카탈로그 | Suricata(9000000번대) & Snort(9100000번대) 전체 룰 문법 및 분류표 |
| **APP-MIT** | [`appendices/MITRE_COVERAGE.md`](appendices/MITRE_COVERAGE.md) | MITRE ATT&CK 커버리지 | v19.2 공식 전술 5개, 기법 12개 매핑 현황 및 D3FEND 연계성 |
| **APP-TST** | [`appendices/TEST_MATRIX.md`](appendices/TEST_MATRIX.md) | 자동화 테스트 매트릭스 | 64개 Pytest 자동화 회귀 테스트 전수 결과 및 게이트 검증표 |
| **APP-KPI** | [`appendices/KPI_DEFINITIONS.md`](appendices/KPI_DEFINITIONS.md) | 관제 핵심 성과 지표(KPI) | MTTD, MTTR, FP율, Precision, Recall, Token 대역폭 정의식 |
| **APP-GLO** | [`appendices/GLOSSARY.md`](appendices/GLOSSARY.md) | 보안관제 전문 용어집 | DICOM, SIEM, AF_PACKET, RAG, HITL, Dry-Run 등 40개 핵심 용어 |

---

## 3. 오프라인 산출물 및 배포본

- **공식 워드 통합 보고서 (.docx)**:
  - 파일 경로: `C:\Users\user\Downloads\SOC_침해유형별_탐지대응룰북_및_종합관제보고서_최종본.docx`
  - 저장소 사본: `docs/reports/SOC_침해유형별_탐지대응룰북_및_종합관제보고서_최종본.docx`
  - 규격: 51pt 여백, 표지, 목차, 4열 메타데이터 표, 음영 서식(`404040`/`D9D9D9`), Consolas 코드박스, 7대 주석 스크린샷 증적 삽입 완료.
