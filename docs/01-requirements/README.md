# 📋 01. 보안관제 프로젝트 요구사항 정의서 관리 체계

> **기준 일자:** 2026-09-28  
> **프로젝트 공식 명칭:** **AegisAI — AI for Security × Security for AI Integrated SOC Platform**  
> **현재 유효 기준선:** **v2.0 Baseline (AegisAI)**

---

## 1. 문서 체계 및 버전 이력 (Document Hierarchy)

본 저장소의 요구사항 문서는 실습망 구축 단계(v1.0)에서 엔터프라이즈 AI 통합 보안관제 플랫폼(v2.0)으로 체계적으로 확장되었습니다.

```text
[ v2.0 최상위 프로젝트 정의서 ]
docs/01-requirements/00_PROJECT_DEFINITION_V2.md
      │
      ▼
[ v2.0 통합 요구사항 정의서 ]
docs/01-requirements/04_REQUIREMENTS_SPECIFICATION_V2.md (현재 기준선)
      │
      ├── [기존 v1.x Core SOC 인프라 보존 (NIDS, HIDS, SIEM, Rulebook)]
      │     └── 보안관제_포트폴리오_프로젝트_요구사항_정의서_v1.0.pdf
      │
      ├── [AI for Security (AI 기반 경보 분류, 인시던트 상관분석, RAG, ATT&CK)]
      │
      └── [Security for AI (AI 보안 게이트웨이, PII/Secret DLP, OWASP 2026 방어)]
```

---

## 2. 요구사항 문서 바로가기

| 문서 ID | 문서명 | 버전 | 설명 및 링크 |
|---|---|:---:|---|
| `00_PROJECT_DEFINITION_V2` | **보안관제 프로젝트 v2.0 프로젝트 정의서** | `v2.0` | [00_PROJECT_DEFINITION_V2.md](./00_PROJECT_DEFINITION_V2.md)<br>AegisAI 비전, 핵심 원칙, 2026 표준 기준선, 전체 산출물 로드맵 |
| `04_REQUIREMENTS_SPECIFICATION_V2` | **AegisAI 차세대 통합 보안관제 플랫폼 요구사항 정의서** | `v2.0` | [04_REQUIREMENTS_SPECIFICATION_V2.md](./04_REQUIREMENTS_SPECIFICATION_V2.md)<br>44개 세부 기능/비기능 요구사항(REQ-GEN, PIPE, AIA, RAG, GW, DLP, ATK, SOC, NFR, VAL) |
| `REQ_V1.0_ORIGINAL` | **보안관제 포트폴리오 프로젝트 요구사항 정의서 (v1.0 원본)** | `v1.0` | [`보안관제_포트폴리오_프로젝트_요구사항_정의서_v1.0.pdf`](./보안관제_포트폴리오_프로젝트_요구사항_정의서_v1.0.pdf)<br>기존 3망 분리, 포트 미러링, Suricata/Snort 듀얼 IDS, Wazuh SIEM 랩 기준선 |

---

## 3. v1.0 ➔ v2.0 주요 확장 및 변경점 비교

| 영역 | v1.0 Core SOC Baseline | v2.0 AegisAI Integrated SOC Platform |
|---|---|---|
| **관제 대상 범위** | 네트워크 트래픽, 리눅스/윈도우 호스트, 웹 서버 | 전통적 인프라 + **LLM, RAG, Vector DB, AI Agent, AI Tool** |
| **경보 처리 방식** | 개별 Alert 발생 및 분석가 수동 분석 | **AI SOC Analyst 기반 Alert Triage 및 다중 Alert 상관분석** |
| **인시던트 관리** | 탐지 룰 단위 개별 이벤트 로그 | 복합 킬체인 기반 단일 **`INCIDENT-YYYYMMDD-xxx` 자동 생성** |
| **보안 지식 연계** | 정적 매뉴얼 및 분석가 경험 의존 | **Security Knowledge RAG** (ATT&CK v19.2, ATLAS, 내부 플레이북 실시간 참조) |
| **AI 자산 방어** | 미포함 (N/A) | **AI Security Gateway, PII/Secret DLP, OWASP 2026 프롬프트 주입/탈옥 방어** |
| **위협 프레임워크** | MITRE ATT&CK 단독 매핑 | **MITRE ATT&CK v19.2 + MITRE ATLAS 듀얼 매핑** |
| **보안 메커니즘** | 단방향 탐지 및 수동 차단 | **Closed-loop Security** (AI 텔레메트리 ➔ SIEM 상관분석 ➔ 1-Click HITL 차단) |
| **데이터 스키마** | Suricata EVE JSON / Wazuh JSON | **Unified Security Event Schema (6대 보안 도메인 ECS 정규화)** |

---

## 4. 핵심 준수 원칙

1. **Existing SOC First**: AI 컴포넌트의 장애가 발생하더라도 기존 v1.0의 Suricata, Wazuh, ELK 탐지/색인 파이프라인은 100% 정상 가동되어야 합니다 (Graceful Degradation).
2. **Zero Trust for AI**: AI의 프롬프트 입력뿐만 아니라 LLM 생성 출력과 Agent Action 전체를 검증 및 격리합니다.
3. **Human-in-the-Loop (Level 4)**: 모든 능동적 차단 조치는 보안 분석가의 명시적인 1-Click 승인을 거쳐야만 집행됩니다.
