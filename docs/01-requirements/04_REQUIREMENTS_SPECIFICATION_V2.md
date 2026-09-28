# AegisAI 차세대 통합 보안관제 플랫폼 요구사항 정의서 (v2.0)

**문서 ID:** `04_REQUIREMENTS_SPECIFICATION_V2`  
**상위 문서:** [`00_PROJECT_DEFINITION_V2`](./00_PROJECT_DEFINITION_V2.md) (AegisAI — AI for Security × Security for AI Integrated SOC Platform)  
**프로젝트명:** **AegisAI — 차세대 AI 통합 보안관제 및 AI 애플리케이션 방어 플랫폼**  
**문서 버전:** v2.0 Baseline  
**기준 일자:** 2026-09-28  
**상태:** Approved Baseline  
**작성/관리:** SOC 보안엔지니어링팀 & AI 보안 아키텍처팀  

---

## 1. 개요 및 문서 목적 (Executive Summary)

### 1.1 배경 및 목적
본 문서는 상위 프로젝트 정의서([`00_PROJECT_DEFINITION_V2`](./00_PROJECT_DEFINITION_V2.md))에 명시된 원칙과 프레임워크를 기반으로, 기존의 **Suricata 8.x · Snort 3 · Wazuh 4.x · Elastic Stack 8.x** 보안관제 인프라(v1.x Core SOC Baseline)를 보존하면서, **AI for Security (보안관제 업무의 지능형 자동화)**와 **Security for AI (생성형 AI 자산 및 Agent 공격표면 방어)**를 통합하는 차세대 SOC 플랫폼(**AegisAI v2.0**)의 전체 기능적·비기능적 요구사항을 상세히 정의합니다.

```text
+-----------------------------------------------------------------------------------+
|                                     AegisAI v2.0                                  |
|                                                                                   |
|    [ AI for Security ]                            [ Security for AI ]             |
|    - Multi-Engine Alert Triage                    - AI Security Gateway           |
|    - Cross-Domain Incident Correlation            - Direct/Indirect Prompt Defense|
|    - Attack Timeline Reconstruction               - PII & Secret DLP Engine       |
|    - Dual MITRE ATT&CK v19.2 & ATLAS Mapping      - RAG & Vector Poisoning Defense|
|    - Security Knowledge RAG                       - Agentic Excessive Agency Guard|
|    - Evidence-based Response Recommendation       - Output Validation & Telemetry |
+-----------------------------------------------------------------------------------+
                                          │
                         [ Unified Security Event Schema ]
                 (Network, Host, Web, Identity, AI, Data Security)
                                          │
                                          ▼
                      [ Elasticsearch 8.x Security Data Lake ]
                                          │
                     ┌────────────────────┴────────────────────┐
                     ▼                                         ▼
         [ Unified Threat Dashboard ]             [ Closed-loop HITL SOAR ]
           (Map, Alerts, AI-Telemetry)              (Human Approval Queue)
```

### 1.2 핵심 설계 불변 원칙 (Architecture Invariants)
1. **Existing SOC First (원천 인프라 최우선)**: AI 레이어의 장애 또는 다운타임이 발생하더라도 기존 NIDS(Suricata/Snort), HIDS(Wazuh), 수집 파이프라인(Filebeat/Logstash), 검색/색인 엔진(Elasticsearch) 및 룰 기반 경보 시스템은 100% 정상 작동해야 합니다 (**Graceful Degradation**).
2. **Defense in Depth (다계층 심층 방어)**: 단일 LLM의 판단만으로 보안 결정을 내리지 않으며, `시그니처(Signature) + 룰(Rule) + 정책(Policy) + 상관분석(Correlation) + AI 분석 + 인간 승인(Human Approval)`의 다계층 체계를 거칩니다.
3. **Human-in-the-Loop Level 4 Boundary (인간 승인 경계)**: 방화벽 차단, 계정 정지, 네트워크 격리 등 시스템 가용성에 영향을 미치는 모든 대응 조치는 보안 분석가의 명시적인 1-Click 승인을 받아야만 실행됩니다 (무승인 파괴적 자율 실행 불가).
4. **Explainability & Evidence Grounding (설명가능성 및 증적 기반)**: 모든 AI 분석 결과는 결과 요약, 위험도(Risk Score), 신뢰도(Confidence), 원시 증적(Raw Event/PCAP), ATT&CK/ATLAS 매핑, RAG 참조 문서(Source/Chunk)를 완전히 명시해야 합니다.
5. **Zero Trust for AI (AI 대상 무신뢰 원칙)**: AI의 입력(사용자 프롬프트, 외부 검색 데이터, RAG 주입 문서)뿐만 아니라 **AI가 생성한 출력(Model Output)과 AI Agent가 호출하는 도구(Tool Call)**도 엄격한 검증 및 격리 대상입니다.

### 1.3 2026 최신 기술 기준선 (Standards Baseline)
- **OWASP GenAI LLM Top 10 2026**: LLM01(Prompt Injection) ~ LLM10(Model Theft) 최신 취약점 방어
- **OWASP Top 10 for Agentic Applications 2026**: ASI01(Excessive Agency) ~ ASI10(Misaligned Goals) Agent 통제
- **NIST AI RMF 1.0 & NIST AI 600-1 (GenAI Profile)**: 위험 거버넌스 및 AI 안전성 통제
- **MITRE ATT&CK v19.2 (2026-04-28)**: 전통적 인프라 공격 TTP 공식 매핑
- **MITRE ATLAS**: LLM 및 AI 시스템 대상 최신 위협/공격 기법 매핑
- **Core Stacks**: Suricata 8.0.6, Snort 3.12.2.0 (libDAQ 3.0.27), Wazuh 4.14.7(기준)/4.14.8(추적), Elastic Stack 8.17.x/8.19.x, Ollama(Qwen2.5 7B/9B 온프레미스 LLM)

---

## 2. 요구사항 분류 및 식별자 체계 (Requirements Taxonomy)

| 분류 코드 | 요구사항 영역 | 관련 모듈 | 주요 내용 |
|---|---|---|---|
| **REQ-GEN** | 일반 및 아키텍처 원칙 | M0 (거버넌스) | SOC First, Fail-Safe, Zero Trust, HITL 경계 |
| **REQ-PIPE** | 데이터 수집 및 공통 스키마 | M1 (데이터 파이프라인) | 6대 도메인 텔레메트리, Unified Event Schema, 불변 감사로그 |
| **REQ-AIA** | AI SOC 분석가 | M2 (AI 분석 엔진) | 경보 분류(Triage), 다중 Alert 상관분석, 타임라인, 위험도 채점 |
| **REQ-RAG** | 보안 지식 RAG | M3 (지식 베이스) | ATT&CK v19.2, ATLAS, 내부 플레이북, 하이브리드 검색, 인용 |
| **REQ-GW** | AI 보안 게이트웨이 | M4 (보안 게이트웨이) | 리버스 프록시, 토큰 인증, 양방향 패킷 인터셉트, 정책 집행 |
| **REQ-DLP** | AI DLP 및 데이터 유출 방지 | M5 (AI DLP) | PII 6종 탐지, Secret 20종 탐지, 3등급 분류, 형태보존 마스킹 |
| **REQ-ATK** | AI 공격 방어 | M6 (AI 공격 방어) | Direct/Indirect Prompt Injection, 탈옥, RAG 오염, Agent 권한 통제 |
| **REQ-SOC** | 통합 콘솔 및 Closed-loop SOAR | M7 (통합 AI-SOC) | 단일 관제 화면, 4단계 AI 조사 UI, 인간 승인 큐, 폐루프 피드백 |
| **REQ-NFR** | 비기능 요구사항 | 공통 | 성능(지연시간), 가용성, 신뢰성, 보안성, 온프레미스 폐쇄망 |
| **REQ-VAL** | 검증 및 평가 요구사항 | M0 (평가 체계) | 탐지율 지표, A/B 벤치마크, 12개 레드팀 시나리오 검증 |

*우선순위 표기: `P0 (Must Have - 필수)`, `P1 (Should Have - 중요)`, `P2 (Could Have - 확장 권장)`*

---

## 3. 기능 요구사항 (Functional Requirements)

### 3.1 일반 및 아키텍처 원칙 요구사항 (REQ-GEN)

| 요구사항 ID | 요구사항 명칭 | 우선순위 | 상세 요구사항 내용 | 검증 기준 및 테스트 방법 |
|---|---|:---:|---|---|
| **REQ-GEN-01** | 기존 SOC 기준선 보존<br>(Existing SOC Preservation) | **P0** | • 기존 v1.x의 Suricata 8.0.6, Snort 3.12.2, Wazuh 4.14.7, Filebeat, Elasticsearch 8.x 파이프라인 구성을 원본 그대로 유지해야 함.<br>• AI 계층 추가로 인한 기존 패킷 수집 및 룰 탐지 파이프라인의 설정 변경이나 성능 저하가 없어야 함. | • `pytest tests/test_elk_infrastructure.py`<br>• Suricata 및 Wazuh 에이전트 서비스 연속 가동 확인 (PASS) |
| **REQ-GEN-02** | 장애 격리 및 Fail-Safe<br>(Fail-Safe & Degradation) | **P0** | • AI 게이트웨이, RAG 벡터 DB, 또는 Ollama LLM 데몬이 비정상 종료(Crash)되거나 타임아웃이 발생해도 기존 NIDS/HIDS 탐지 및 SIEM 인덱싱은 100% 정상 작동해야 함.<br>• AI 장애 시 UI는 `AI Analysis: Degraded` 상태를 표출하고 룰 기반 관제로 자동 전환(Graceful Degradation)되어야 함. | • Ollama 및 AI 백엔드 강제 종료(`kill -9`) 후 공격 트래픽 발생 시 Elasticsearch에 Suricata 알림 정상 색인 확인 |
| **REQ-GEN-03** | AI 대상 제로 트러스트<br>(Zero Trust for AI) | **P0** | • 사용자의 입력 프롬프트, 외부 검색 결과, RAG 인덱싱 문서, LLM 생성 출력, AI Agent의 Tool 호출 파라미터 전체를 잠재적 위협으로 간주하고 전수 검증해야 함.<br>• 모델 내부의 출력을 신뢰하여 직접 시스템 셸이나 DB 쿼리에 바인딩하는 것을 엄격히 금지함. | • 명령 주입 메타문자(`;`, `&&`, `\|`) 포함된 LLM 생성 텍스트의 OS 실행 차단 테스트 |
| **REQ-GEN-04** | 인간 승인 경계 통제<br>(HITL Level 4 Boundary) | **P0** | • 자동화 대응 수준을 Level 4(Human-Approved Response)로 제한함.<br>• AI는 대응안 제안(Recommendation)까지만 수행하며, 실제 방화벽 IP 차단, L3 ACL 변경, 계정 차단은 분석가의 명시적 승인 토큰이 확인되어야만 집행되어야 함. | • 분석가 승인 없이 백엔드 SOAR 스크립트 단독 호출 시 `403 Forbidden: Approval Required` 반환 검증 |

---

### 3.2 보안 데이터 파이프라인 및 통합 스키마 요구사항 (REQ-PIPE, 모듈 M1)

| 요구사항 ID | 요구사항 명칭 | 우선순위 | 상세 요구사항 내용 | 검증 기준 및 테스트 방법 |
|---|---|:---:|---|---|
| **REQ-PIPE-01** | 6대 보안 도메인 수집<br>(Multi-Domain Telemetry) | **P0** | • 다음 6대 영역의 보안 이벤트를 단일 파이프라인으로 수집해야 함:<br>  1) `NETWORK_SECURITY` (Suricata EVE, Snort 3 Alert)<br>  2) `HOST_SECURITY` (Wazuh Agent 엔드포인트 이벤트)<br>  3) `WEB_SECURITY` (Nginx/Apache 액세스 및 웹 공격 로그)<br>  4) `IDENTITY_SECURITY` (SSH, VPN, Auth 로그인 실패 로그)<br>  5) `AI_SECURITY` (AI Gateway 프롬프트 주입/차단 로그)<br>  6) `DATA_SECURITY` (AI DLP 개인정보/Secret 유출 차단 로그) | • 6개 도메인 샘플 로그 인제스천 후 Elasticsearch 필터 쿼리로 도메인별 정상 색인 확인 |
| **REQ-PIPE-02** | 공통 보안 이벤트 스키마<br>(Unified Event Schema) | **P0** | • Elastic Common Schema(ECS)를 기반으로 9대 공통 필드 범주를 표준화해야 함:<br>  - **Identity**: `timestamp`, `event_id`, `trace_id`, `incident_id`<br>  - **Classification**: `event_domain`, `event_category`, `event_type`<br>  - **Entity**: `source`, `destination`, `user`, `asset`, `application`<br>  - **Risk**: `severity`, `risk_score`, `confidence`<br>  - **Detection**: `detection_source`, `rule_id`<br>  - **Framework**: `framework`, `technique` (ATT&CK / ATLAS)<br>  - **Decision**: `evidence`, `action`, `action_status`, `policy`<br>  - **AI**: `ai_model`, `ai_application`, `rag_source`<br>  - **Workflow**: `analyst_status`, `created_at`, `updated_at` | • Pydantic 모델 검증 스크립트 통과<br>• 누락 필드 발생 시 Logstash Dead Letter Queue(DLQ) 또는 파싱 에러 격리 확인 |
| **REQ-PIPE-03** | 실시간 스트리밍 인덱싱<br>(Real-time Ingestion) | **P0** | • Logstash 및 Elasticsearch Ingest Pipeline을 통해 정규화된 이벤트를 `soc-events-*` 및 `soc-incidents-*` 데이터 스트림에 1초 이내 실시간 색인해야 함.<br>• 위경도(GeoPoint) 인리치먼트를 적용하여 발원 IP의 지도 시각화 필드(`source.geo.location`)를 자동 생성해야 함. | • 1,000건 이벤트 인제스천 부하 테스트 시 지연시간 < 500ms 유지 확인 |
| **REQ-PIPE-04** | 원시 증적 불변성 보장<br>(Immutable Audit Trail) | **P0** | • 분석에 사용된 원시 로그(EVE JSON, PCAP 파일)는 읽기 전용으로 보존되어야 하며, SHA-256 해시를 생성하여 매니페스트에 영구 기록해야 함.<br>• AI 분석 메타데이터와 원본 패킷 데이터 간의 위변조 방지 연결 고리를 제공해야 함. | • `pcap_manifest.json` 해시 대조 스크립트 실행 및 불일치 감지 테스트 통과 |

---

### 3.3 AI SOC Analyst 요구사항 (REQ-AIA, 모듈 M2 - AI for Security)

| 요구사항 ID | 요구사항 명칭 | 우선순위 | 상세 요구사항 내용 | 검증 기준 및 테스트 방법 |
|---|---|:---:|---|---|
| **REQ-AIA-01** | 다중 엔진 경보 트라이아지<br>(Multi-Engine Alert Triage) | **P0** | • Suricata, Snort, Wazuh, AI Gateway에서 유입되는 수백 건의 개별 Alert 중 노이즈와 단순 스캔을 필터링하고 실제 위협 가능성이 높은 핵심 경보를 자동 선별해야 함.<br>• 신뢰도(Confidence: 0.0~1.0)와 심각도(Severity: LOW, MED, HIGH, CRIT)를 1차 판정해야 함. | • 시뮬레이션 경보 100건 주입 시 단순 노이즈 80% 이상 자동 분류 및 Triage 성공률 95% 이상 |
| **REQ-AIA-02** | 도메인 간 인시던트 상관분석<br>(Cross-Domain Correlation) | **P0** | • 시간 윈도우(기본 15분) 내 동일 공격자 IP, 대상 서버, 사용자 세션을 공유하는 이종 도메인 이벤트들을 단일 `INCIDENT-YYYYMMDD-xxx`로 자동 군집화해야 함.<br>• (예: 네트워크 스캔 ➔ 웹 SQLi ➔ DB 접근 ➔ LLM 프롬프트 주입을 1개 인시던트로 통합) | • 복합 공격 시나리오(IR-06) 주입 시 5개 개별 Alert가 1개의 Incident ID로 병합되는지 검증 |
| **REQ-AIA-03** | 공격 타임라인 재구성<br>(Attack Timeline Reconstruction) | **P0** | • 인시던트에 포함된 모든 이벤트를 밀리초(ms) 단위의 시간 순서로 정렬하고, 공격 단계(Recon ➔ Weaponization ➔ Delivery ➔ Exploitation ➔ Actions on Objectives)를 시각적 타임라인으로 구조화해야 함. | • 인시던트 상세 페이지에서 단계별 시계열 이벤트 플로우 JSON 및 시각화 UI 렌더링 확인 |
| **REQ-AIA-04** | ATT&CK 및 ATLAS 듀얼 매핑<br>(Dual Framework Mapping) | **P0** | • 인프라 침해 행위는 **MITRE ATT&CK v19.2**(예: T1046, T1190, T1059)로 매핑하고, AI 공격 행위는 **MITRE ATLAS**(예: AML.T0051 LLM Prompt Injection, AML.T0054 LLM Jailbreak)로 동시 매핑해야 함.<br>• 각 기법 매핑에 대한 판단 근거와 신뢰도 점수를 첨부해야 함. | • E2E 복합 시나리오 인시던트 생성 시 ATT&CK ID와 ATLAS ID가 동시 추출되는지 검증 |
| **REQ-AIA-05** | 복합 위험도 동적 스코어링<br>(Composite Risk Scoring) | **P0** | • 다음 수식을 기반으로 0~100점의 인시던트 위험도를 동적으로 산출해야 함:<br>  `Risk = (기본 심각도 × 0.3) + (자산 중요도 × 0.25) + (킬체인 진척도 × 0.25) + (AI 신뢰도 × 0.20)`<br>• 점수에 따라 `CRITICAL(≥85)`, `HIGH(≥70)`, `MEDIUM(≥50)`, `LOW(<50)` 레이블 자동 부여. | • 점수 계산기 단위 테스트(10개 케이스) 및 경계값 검증 완료 |
| **REQ-AIA-06** | 구조화된 인시던트 요약<br>(Incident Summary Generation) | **P0** | • 관제 분석가가 10초 내에 상황을 파악할 수 있도록 육하원칙(공격자, 대상 자산, 최초 침투 경로, 현재 상태, 유출/피해 규모)에 기반한 3줄 요약 및 상세 브리핑을 한글 마크다운으로 자동 생성해야 함. | • 생성된 요약문 내 핵심 사실(IP, 공격 기법, 피해 자산)의 정확도 95% 이상 평가 |
| **REQ-AIA-07** | 상황 인지형 대응 권고<br>(Response Recommendation) | **P0** | • 침해 유형에 맞춘 구체적인 기술적 대응 방안을 제시해야 함:<br>  - L3/방화벽 IP 차단 규칙 (`nftables add rule ...` / Cisco ACL 문법)<br>  - Wazuh 에이전트 활성 격리 (`active-response`)<br>  - AI Gateway 정책 갱신 (해당 사용자 토큰 정지 및 프롬프트 차단 룰 추가) | • 추천된 스크립트의 문법 유효성(Syntax Validity) 100% 검증 통과 |

---

### 3.4 보안 지식 RAG 요구사항 (REQ-RAG, 모듈 M3 - AI for Security)

| 요구사항 ID | 요구사항 명칭 | 우선순위 | 상세 요구사항 내용 | 검증 기준 및 테스트 방법 |
|---|---|:---:|---|---|
| **REQ-RAG-01** | 다중 지식원 인덱싱<br>(Multimodal Knowledge Base) | **P0** | • 다음 5개 영역의 보안 지식 문서를 벡터화하여 인덱싱해야 함:<br>  1) MITRE ATT&CK v19.2 매트릭스 기술 정의<br>  2) MITRE ATLAS 지식베이스<br>  3) Suricata/Snort 시그니처 룰 카탈로그 및 룰북 (`02_SOC_COMMON_RULEBOOK.md`)<br>  4) 사고 대응 절차서 (`docs/reports/scenarios/*.md`)<br>  5) 내부 방화벽 및 인프라 정책 가이드라인 | • 벡터 저장소(FAISS / Elasticsearch kNN) 색인 청크 수 1,000건 이상 및 로딩 확인 |
| **REQ-RAG-02** | 하이브리드 검색 엔진<br>(Hybrid Retrieval Engine) | **P0** | • 고유명사(CVE 번호, SID, IP, 포트, 함수명) 정확도를 위한 **BM25 키워드 검색**과 맥락 분석을 위한 **Dense Vector 의미 기반 검색**을 결합(Reciprocal Rank Fusion)하여 검색 성능을 극대화해야 함. | • "SQL Injection bypass SID 9010001" 질의 시 해당 룰 청크가 Top-3 내 검색되는지 평가 (Recall@3 ≥ 0.90) |
| **REQ-RAG-03** | 엄격한 인용 및 출처 명시<br>(Strict Source Citation) | **P0** | • AI가 생성하는 모든 권고안과 분석 의견은 참조한 지식 문서의 `파일명`, `청크 ID`, `유사도 점수(Similarity Score)`를 명시해야 함.<br>• 출처가 없는 임의의 지식 주장을 원천 차단함. | • 생성 결과 스키마 검증: `sources` 배열 내 최소 1개 이상의 유효한 로컬 파일 링크 포함 확인 |
| **REQ-RAG-04** | 환각 방지 가드레일<br>(Anti-Hallucination Guardrail) | **P0** | • RAG 검색 결과 유사도 점수가 임계치(기본 cosine similarity < 0.65) 미만일 경우, 모르는 내용을 허위 생성하지 않고 "관련 지식베이스 미확인으로 추가 분석 필요" 상태를 반환해야 함. | • 임의의 가상 SID(예: SID 9999999) 질의 시 허위 정보 생성 거부 및 미확인 반환 검증 |

---

### 3.5 AI 보안 게이트웨이 요구사항 (REQ-GW, 모듈 M4 - Security for AI)

| 요구사항 ID | 요구사항 명칭 | 우선순위 | 상세 요구사항 내용 | 검증 기준 및 테스트 방법 |
|---|---|:---:|---|---|
| **REQ-GW-01** | 고성능 인라인 리버스 프록시<br>(Inline Reverse Proxy) | **P0** | • 사용자 및 내부 시스템이 사내/외부 LLM(Ollama, OpenAI, Claude 등)을 호출할 때 반드시 거쳐야 하는 보안 중계 게이트웨이로 동작해야 함.<br>• 프록시 경유에 따른 추가 지연시간(Latency Overhead)은 150ms 이내여야 함. | • 게이트웨이 경유 전/후 100회 요청 Latency 비교 측정 (평균 오버헤드 < 150ms 통과) |
| **REQ-GW-02** | 사용자 인증 및 RBAC 통제<br>(Authentication & RBAC) | **P0** | • API Key 및 JWT 기반 인증을 수행하고, 사용자 역할(Role: General, Analyst, Admin)에 따라 접근 가능한 LLM 모델, 토큰 한도, 허용 도구를 차등 제어해야 함. | • 유효하지 않은 API Key 요청 시 `401 Unauthorized` 즉시 차단 검증 |
| **REQ-GW-03** | 양방향 패킷 인터셉트<br>(Bidirectional Inspection) | **P0** | • **Inbound (요청)**: 사용자 입력 프롬프트, 첨부 파일, 시스템 프롬프트 전수 검사.<br>• **Outbound (응답)**: LLM 생성 텍스트, 스트리밍 청크, Agent의 Tool Call 인자 전수 검사. | • 입력 인젝션 차단 및 출력 민감정보 노출 차단 테스트 각각 100% 통과 |
| **REQ-GW-04** | 확정적 정책 집행 엔진<br>(Deterministic Policy Engine) | **P0** | • 검사 결과에 따라 다음 5대 표준 정책 조치를 즉시 집행해야 함:<br>  1) `ALLOW`: 정상 처리 및 통과<br>  2) `MASK`: 개인정보/민감정보 마스킹 후 전달<br>  3) `WARN`: 사용자에게 경고 통지 후 전달<br>  4) `REQUIRE_APPROVAL`: 관리자 승인 대기 큐로 전송<br>  5) `BLOCK`: 즉시 차단 및 403 에러 반환 | • 5개 정책 상태별 시뮬레이션 패킷 주입 후 기대 동작 및 HTTP 상태 코드 일치 검증 |
| **REQ-GW-05** | AI 보안 텔레메트리 방출<br>(AI Security Telemetry) | **P0** | • 모든 요청/응답 검사 결과(허용/차단 여부, 탐지된 위험 유형, 정책 ID, 토큰 수, 레이턴시)를 `event_domain: AI_SECURITY` 포맷의 JSON 로그로 생성하여 Elasticsearch로 실시간 전송해야 함. | • 게이트웨이 차단 발생 시 Logstash ➔ Elasticsearch `soc-events-*` 색인 0.5초 내 반영 확인 |

---

### 3.6 AI DLP 및 데이터 유출 통제 요구사항 (REQ-DLP, 모듈 M5 - Security for AI)

| 요구사항 ID | 요구사항 명칭 | 우선순위 | 상세 요구사항 내용 | 검증 기준 및 테스트 방법 |
|---|---|:---:|---|---|
| **REQ-DLP-01** | 6대 개인정보(PII) 실시간 탐지<br>(PII Leakage Detection) | **P0** | • 프롬프트 내 포함된 다음 6대 개인식별정보를 정규식 및 맥락 분석으로 100% 실시간 탐지해야 함:<br>  1) 주민등록번호 / 외국인등록번호 (체크섬 검증 포함)<br>  2) 휴대폰 / 전화번호<br>  3) 이메일 주소<br>  4) 신용카드 번호 (Luhn 알고리즘 검증)<br>  5) 은행 계좌번호<br>  6) 여권번호 / 운전면허번호 | • PII 테스트 데이터셋 50건 주입 시 탐지율(Recall) ≥ 98%, 정상 텍스트 오탐율(FPR) ≤ 2% |
| **REQ-DLP-02** | 20종 시크릿 자격증명 탐지<br>(Secret & Key Detection) | **P0** | • 소스코드나 설정 파일 유출을 방지하기 위해 다음 20종 자격증명을 탐지해야 함:<br>  - AWS Access Key / Secret Key, GCP Service Account Key, Azure SAS Token<br>  - OpenAI / Anthropic / HuggingFace API Key<br>  - RSA/DSA Private Key (`-----BEGIN RSA PRIVATE KEY-----`)<br>  - JWT Token, GitHub Personal Access Token, Slack Webhook URL<br>  - 데이터베이스 접속 패스워드 스트링 (JDBC URL 등) | • 자격증명 패턴 30종 주입 테스트 시 100% 차단(BLOCK) 또는 마스킹 검증 |
| **REQ-DLP-03** | 3등급 데이터 기밀성 분류<br>(Data Classification) | **P1** | • 조직 데이터 정책에 따라 문서를 3등급으로 분류해야 함:<br>  - `Confidential (기밀)`: 외부 전송 절대 불가 (BLOCK)<br>  - `Secret (사내비)`: 승인 후 전송 또는 마스킹 전송 (REQUIRE_APPROVAL / MASK)<br>  - `Open (공개)`: 자유로운 전송 허용 (ALLOW) | • 등급별 라벨이 부여된 문서 주입 시 정책 엔진의 차등 제어 동작 검증 |
| **REQ-DLP-04** | 형태 보존형 가명화 마스킹<br>(Context-Preserving Masking) | **P0** | • `MASK` 정책 집행 시 LLM이 문맥을 이해할 수 있도록 형태 보존형 토큰으로 치환하여 전달해야 함:<br>  (예: `010-1234-5678` ➔ `[PII_PHONE_1]`, `test@corp.com` ➔ `[PII_EMAIL_1]`)<br>• LLM 응답 수신 시 역마스킹(De-masking)을 거쳐 원래 사용자에게 복원 표출 가능해야 함. | • 치환 전/후 프롬프트 비교 검증 및 LLM 응답 내 원본 민감정보 비노출 확인 |

---

### 3.7 AI 공격 방어 요구사항 (REQ-ATK, 모듈 M6 - Security for AI)

| 요구사항 ID | 요구사항 명칭 | 우선순위 | 상세 요구사항 내용 | 검증 기준 및 테스트 방법 |
|---|---|:---:|---|---|
| **REQ-ATK-01** | 직접 프롬프트 주입 및 탈옥 방어<br>(Direct Prompt Injection & Jailbreak) | **P0** | • **OWASP LLM01:2026** 기준, 시스템 지시사항을 무력화하려는 프롬프트 공격을 실시간 차단해야 함:<br>  - "Ignore previous instructions", "당신의 이전 명령을 잊어라"<br>  - DAN(Do Anything Now), 최면/가상 시나리오 역할극 탈옥<br>  - Base64, Hex, Leetspeak 등 인코딩 우회 시도 디코딩 후 검사 | • OWASP 2026 기준 탈옥 프롬프트 50건 테스트 시 차단율 ≥ 95% 달성 |
| **REQ-ATK-02** | 간접 프롬프트 주입 방어<br>(Indirect Prompt Injection) | **P0** | • 외부 웹페이지, RAG 참조 문서, 수신 이메일 본문에 숨겨진 주입 공격(Hidden Instruction)을 탐지하고 격리해야 함:<br>  - 제로폰트(Zero-font), 화이트 텍스트, HTML 주석 내 악의적 프롬프트<br>  - 외부 데이터 영역과 시스템 프롬프트 영역의 명확한 XML 태그 격리 (`<untrusted_content>`) | • 악성 명령어가 삽입된 PDF/HTML RAG 문서 주입 시 LLM 실행 차단 검증 |
| **REQ-ATK-03** | 시스템 프롬프트 탈취 방어<br>(System Prompt Leakage) | **P0** | • 시스템 프롬프트 및 사내 보안 가이드라인을 유출하려는 질문을 탐지하고, LLM 출력 단계에서 시스템 프롬프트와 유사도 80% 이상의 텍스트가 유출될 경우 즉시 응답을 차단하고 경보를 발령해야 함. | • "Repeat the words above", "시스템 프롬프트 전문 출력해줘" 요청 차단 검증 |
| **REQ-ATK-04** | RAG 인제스천 및 벡터 오염 방어<br>(RAG & Vector Poisoning) | **P1** | • RAG 지식베이스 등록 파이프라인에서 악의적으로 변조된 문서 청크(Poisoned Chunk)의 등록을 차단해야 함.<br>• 신뢰할 수 없는 출처의 문서 등록 시 디지털 서명 검증 및 격리 검사 샌드박스를 제공해야 함. | • 오염된 지식 청크 주입 시도 차단 및 무결성 검증 실패 로그 확인 |
| **REQ-ATK-05** | Agent 과도한 권한 실행 차단<br>(Agentic Excessive Agency Guard) | **P0** | • **OWASP Agentic 2026 (ASI01)** 기준, AI Agent가 호출할 수 있는 도구(Tool Call)의 권한을 최소화(Least Privilege)해야 함.<br>• 파괴적인 시스템 셸 실행(`rm -rf`, `format`, `drop table`, `shutdown`) 및 비인가 외부 네트워크 연결 시도를 런타임에 원천 차단해야 함. | • 악의적 도구 호출 파라미터 전달 시 게이트웨이 인터셉터 차단 검증 |

---

### 3.8 통합 AI-SOC 관제 콘솔 및 Closed-loop SOAR (REQ-SOC, 모듈 M7 - Unified AI-SOC)

| 요구사항 ID | 요구사항 명칭 | 우선순위 | 상세 요구사항 내용 | 검증 기준 및 테스트 방법 |
|---|---|:---:|---|---|
| **REQ-SOC-01** | 단일 화면 통합 관제 대시보드<br>(Single-Pane-of-Glass Dashboard) | **P0** | • Kibana 및 FastAPI 기반 웹 콘솔에서 전통적 보안(네트워크 지도, 방화벽 차단 통계, IDS 경보)과 AI 보안(AI 게이트웨이 차단, 프롬프트 주입 발생지, PII 유출 현황)을 단일 다크모드 화면에 실시간 표출해야 함. | • 브라우저 접속(`:5602`, `:8501`) 후 IT 보안 위협 지도와 AI 보안 위젯 동시 렌더링 확인 |
| **REQ-SOC-02** | 4단계 AI 인터랙티브 조사 콘솔<br>(4-Step AI Investigation Console) | **P0** | • 분석가가 인시던트 목록에서 [AI 심층 조사] 클릭 시, 4단계 순차 파이프라인을 시각화하고 결과를 제공해야 함:<br>  1) 증적 추출 (EVE 로그, PCAP, IP 이력 조회)<br>  2) RAG 지식 조회 (ATT&CK 매핑, 대응 절차서 검색)<br>  3) 다계층 위험도 분석 (침해 인과관계 및 공격 타임라인 재구성)<br>  4) 대응안 도출 (방화벽/ACL 차단 명령어 및 승인 큐 생성)<br>• 각 단계 완료 시 `✅ 완료` 배지가 동적으로 갱신되어야 함. | • 인시던트 조사 실행 후 4단계 배지 순차 전환 및 최종 권고안 화면 출력 확인 |
| **REQ-SOC-03** | 1-Click 인간 승인 큐<br>(Human Approval Queue) | **P0** | • AI가 생성한 대응 권고안(예: 악성 IP `10.77.20.88` 방화벽 차단)을 승인 큐에 등록하고, 분석가가 [승인] 클릭 시에만 실제 보안 장비 API 또는 스크립트로 전달해야 함.<br>• [반려] 클릭 시 사유를 입력받아 AI 피드백 튜닝 데이터로 저장해야 함. | • 승인 버튼 클릭 시 실제 `nftables` 룰 주입 성공 및 반려 시 미주입 확인 |
| **REQ-SOC-04** | 폐루프 보안 피드백<br>(Closed-loop Telemetry Feedback) | **P0** | • **AegisAI 핵심 메커니즘**: Security for AI(게이트웨이)에서 탐지된 차단 이벤트가 SIEM으로 수집되어 AI for Security(인시던트 분석가)의 상관분석 데이터로 활용되고, 인간 승인을 통해 방화벽 및 게이트웨이 정책이 강화되는 폐루프(Closed-loop)를 완성해야 함. | • 프롬프트 주입 발생 ➔ 통합 인시던트 생성 ➔ 공격자 IP 자동 차단 권고 ➔ 승인 ➔ 네트워크 차단 집행 완료 E2E 검증 |

---

## 4. 비기능 요구사항 (Non-Functional Requirements - REQ-NFR)

### 4.1 성능 요구사항 (Performance)
- **REQ-NFR-01 (게이트웨이 오버헤드)**: AI Security Gateway의 인라인 프롬프트/응답 검사로 인한 추가 왕복 지연시간은 평균 150ms 이하여야 함 (로컬 검사 기준).
- **REQ-NFR-02 (AI 사고 분석 지연)**: 인시던트 1건에 대한 AI 심층 조사(증적 추출, RAG 검색, 로컬 Qwen2.5 LLM 추론)는 5,000ms(5초) 이내에 완료되어야 함.
- **REQ-NFR-03 (파이프라인 처리량)**: 중앙 수집 및 인덱싱 파이프라인은 최소 1,000 EPS(Events Per Second) 이상의 트래픽을 데이터 유실 없이 안정적으로 처리해야 함.

### 4.2 안정성 및 복원력 요구사항 (Reliability & Resilience)
- **REQ-NFR-04 (Core SOC 가용성 100%)**: AI 컴포넌트(게이트웨이, LLM 서버, RAG 벡터 DB) 장애가 발생해도 Suricata, Wazuh, Filebeat, Elasticsearch의 패킷 센싱 및 룰 탐지 가용성은 99.9% 이상 유지되어야 함.
- **REQ-NFR-05 (안전한 장애 복구 - Graceful Degradation)**: Ollama 데몬 다운 시 FastAPI 콘솔은 사전 캐싱된 룰 기반 템플릿 요약으로 즉각 대체 동작해야 함.

### 4.3 보안성 및 프라이버시 요구사항 (Security & Privacy)
- **REQ-NFR-06 (온프레미스 폐쇄망 보장)**: 모든 AI 추론 및 RAG 지식 검색은 인터넷 연결이 차단된 로컬 폐쇄망(Local Ollama Engine) 내에서 수행되어야 하며, 사내 보안 텔레메트리가 외부 클라우드로 유출되어서는 안 됨.
- **REQ-NFR-07 (자격증명 보호)**: `.env`, API Key, DB 비밀번호, SSH 개인키는 Git 저장소 커밋을 엄격히 금지하며(Pre-commit Guard), OS 환경 변수 또는 권한 600 파일로만 격리 관리해야 함.

### 4.4 감사성 및 추적성 요구사항 (Auditability)
- **REQ-NFR-08 (100% 불변 감사로그)**: AI 프롬프트 원문(마스킹 전/후), 차단 사유, 분석가의 승인/반려 내역, 집행된 방화벽 명령어 전체를 위변조 불가능한 감사 인덱스(`soc-audit-*`)에 1년간 보존해야 함.

---

## 5. 검증 및 평가 요구사항 (Verification & Evaluation - REQ-VAL)

### 5.1 정량적 성능 지표 (Quantitative Evaluation Metrics)

| 평가 영역 | 세부 지표 | 목표 기준치 (Target) | 측정 방법 |
|---|---|:---:|---|
| **위협 탐지 정확도** | Precision (정밀도) | **≥ 90.0%** | 레이블링된 1,000건 테스트셋 검증 |
| | Recall (재현율) | **≥ 92.0%** | 미탐(FN) 최소화 평가 |
| | F1-Score | **≥ 91.0%** | 복합 조화평균 산출 |
| | False Positive Rate (오탐율) | **≤ 3.0%** | 정상 업무 트래픽 5,000건 통과 시험 |
| **SOC 운영 효율성** | Mean Time to Triage (MTTT) | **70% 이상 단축** | 기존 15분 ➔ AI 지원 시 3분 이내 |
| | Alert-to-Incident 압축률 | **≥ 5 : 1** | 500개 Alert ➔ 100개 이하 Incident 압축 |
| | 분석가 수동 조사 스텝 감소 | **60% 이상 감소** | 수동 쿼리 작성 횟수 대조 |
| **AI 공격 방어력** | Prompt Injection 탐지율 | **≥ 95.0%** | OWASP 2026 테스트 프롬프트 100건 주입 |
| | PII / Secret 차단 성공률 | **≥ 98.0%** | 50건 민감정보 데이터셋 주입 시험 |
| | 정상 질의 오차단율 (FPR) | **≤ 2.0%** | 일반 업무 프롬프트 500건 통과 시험 |

### 5.2 A/B 비교 벤치마크 실험 계획 (A/B Benchmark Experiments)

```text
[ Experiment A: SOC 관제 효율 비교 ]
- Baseline SOC (룰 단독 관제)  vs.  AegisAI (AI 증강 관제)
  -> 동일한 6단계 킬체인 공격 주입 후 인지 시간, 분석 리포트 완성 시간, 대응 소요시간 정량 비교

[ Experiment B: AI 보안 게이트웨이 방어력 비교 ]
- Unprotected LLM (보호 없는 LLM)  vs.  AegisAI Gateway + LLM
  -> 탈옥 프롬프트, PII 주입, Secret 탈취, 간접 인젝션 시도 시 유출 및 실행 성공률 대조
```

### 5.3 12대 레드팀 시나리오 검증 매핑 (Red Team Verification)
1. **SCN-01 (Network Recon)**: Nmap 스텔스 포트 스캔 및 서비스 식별
2. **SCN-02 (Auth Bruteforce)**: SSH/FTP 무차별 대입 및 자격증명 스터핑
3. **SCN-03 (Web Exploitation)**: SQLi, XSS, Path Traversal, Log4j RCE
4. **SCN-04 (C2 Communication)**: Reverse Shell 세션 형성 및 비콘 트래픽
5. **SCN-05 (Data Exfiltration)**: DNS 터널링 및 대용량 DB 덤프 외부 전송
6. **SCN-06 (Direct Prompt Injection)**: DAN 최면 및 시스템 프롬프트 무력화
7. **SCN-07 (Indirect Prompt Injection)**: 악성 외부 문서 기반 주입 공격
8. **SCN-08 (System Prompt Leakage)**: 역할극을 통한 시스템 설정 유출 시도
9. **SCN-09 (PII Bulk Extraction)**: 대량 고객 정보 질의 및 외부 전송 시도
10. **SCN-10 (Secret Credential Leak)**: 사내 AWS/API 키 요청 및 코드 유출
11. **SCN-11 (RAG Ingestion Poisoning)**: 오염된 문서 주입을 통한 허위 응답 유도
12. **SCN-12 (Multistage E2E Attack)**: 정찰 ➔ 웹 침투 ➔ 내부 이동 ➔ LLM 탈옥 ➔ 유출 복합 킬체인

---

## 6. 요구사항 추적성 매트릭스 (Requirements Traceability Matrix)

| 요구사항 ID | 관련 모듈 | 대응 원칙 및 상위 목표 | 검증 게이트 (Quality Gate) |
|---|:---:|---|:---:|
| **REQ-GEN-01~04** | M0 | Existing SOC First, Fail-Safe, HITL | `GATE-HOST-01`, `GATE-NET-01` |
| **REQ-PIPE-01~04** | M1 | 6대 도메인 텔레메트리, Unified Event Schema | `GATE-PIPE-01`, `GATE-SIEM-01` |
| **REQ-AIA-01~07** | M2 | Alert Triage, Incident Correlation, ATT&CK | `GATE-AI-01`, `GATE-ANALYSIS-01` |
| **REQ-RAG-01~04** | M3 | 지식베이스 하이브리드 검색, 환각 방지 | `GATE-RAG-01` |
| **REQ-GW-01~05** | M4 | 리버스 프록시, 정책 엔진, 실시간 텔레메트리 | `GATE-GW-01` |
| **REQ-DLP-01~04** | M5 | PII/Secret 탐지, 5대 조치, 가명화 마스킹 | `GATE-DLP-01` |
| **REQ-ATK-01~05** | M6 | OWASP LLM/Agentic 2026 주입 공격 방어 | `GATE-ATK-01` |
| **REQ-SOC-01~04** | M7 | 통합 대시보드, 1-Click 승인 큐, Closed-loop | `GATE-SOAR-01`, `GATE-E2E-01` |
| **REQ-NFR-01~08** | 공통 | 성능(오버헤드 <150ms), 폐쇄망 보안, 무중단 | `GATE-NFR-01` |
| **REQ-VAL-01~03** | M0 | 정량 벤치마크, A/B 실험, 12개 레드팀 검증 | `GATE-PORTFOLIO-01` |

---

## 7. 승인 및 변경 이력 (Document Control)

| 버전 | 일자 | 주요 개정 및 등록 내용 | 승인자 |
|---|---|---|---|
| **v1.0** | 2026-08-24 | 기존 Suricata/Snort/Wazuh/ELK 랩 기반 요구사항 정의 (v1.0 Baseline) | SOC 랩 엔지니어 |
| **v2.0** | 2026-09-28 | **AegisAI v2.0 통합 요구사항 정의서 전면 제정**: <br>• AI for Security (Triage, Correlation, RAG, ATT&CK/ATLAS) 요구사항 추가<br>• Security for AI (AI Gateway, PII/Secret DLP, OWASP 2026 Prompt/Agent 방어) 요구사항 추가<br>• 6대 도메인 Unified Security Event Schema 및 Closed-loop SOAR 반영<br>• 44개 상세 요구사항(REQ-GEN, PIPE, AIA, RAG, GW, DLP, ATK, SOC, NFR, VAL) 확정 | AI-SOC 총괄 아키텍트 |
