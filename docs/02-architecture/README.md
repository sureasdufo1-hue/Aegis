# 🏛️ 02. 보안관제 시스템 아키텍처 및 위협 모델 문서 체계

> **기준 일자:** 2026-09-28  
> **프로젝트 공식 명칭:** **AegisAI — AI for Security × Security for AI Integrated SOC Platform**  
> **현재 유효 기준선:** **v2.0 TO-BE Architecture & Threat Model (AegisAI)**

---

## 1. 아키텍처 문서 계층 및 로드맵

```text
[ v2.0 최상위 프로젝트 정의서 ]
docs/01-requirements/00_PROJECT_DEFINITION_V2.md
      │
      ▼
[ v2.0 AS-IS 기준선 분석서 ]
docs/01-requirements/01_AS_IS_SOC_BASELINE.md
      │
      ▼
[ v2.0 목표 시스템 아키텍처 설계서 ]
docs/02-architecture/02_TO_BE_ARCHITECTURE.md (★ 목표 아키텍처 기준선)
      │
      ▼
[ v2.0 AI/LLM/RAG/Agent 통합 위협모델 분석서 ]
docs/02-architecture/03_AI_THREAT_MODEL.md (★ 위협 모델 기준선)
      │
      ▼
[ v2.0 통합 요구사항 정의서 ]
docs/01-requirements/04_REQUIREMENTS_SPECIFICATION_V2.md (68개 챕터, 112개 요구사항)
      │
      ▼
[ v2.0 통합 보안 이벤트 스키마 및 정규화 명세서 ]
docs/02-architecture/05_SECURITY_EVENT_SCHEMA.md (80개 챕터, ECS 기반 8대 도메인 스키마 계약)
      │
      ▼
[ v2.0 AI 보안정책 및 통제기준서 ]
docs/02-architecture/06_AI_SECURITY_POLICY.md (96개 챕터, 10대 다이어그램, 12대 PDR, 수치 거버넌스)
      │
      ▼
[ v2.0 통합 시스템 상위설계서 (HLD) ]
docs/02-architecture/07_HIGH_LEVEL_DESIGN.md (★ 92개 챕터, 12대 다이어그램, 12대 ADR, 22개 컴포넌트)
```

---

## 2. 핵심 아키텍처 및 위협 모델 문서 바로가기

| 문서 ID | 문서명 | 버전 / 성격 | 설명 및 링크 |
|---|---|:---:|---|
| `02_TO_BE_ARCHITECTURE` | **AegisAI 목표 시스템 아키텍처 설계서** | `v2.0 TO-BE` | [02_TO_BE_ARCHITECTURE.md](./02_TO_BE_ARCHITECTURE.md)<br>4-Layer 아키텍처, 14개 구조 다이어그램, 10개 ADR, Trust Boundary, Closed-loop SOAR |
| `03_AI_THREAT_MODEL` | **AegisAI AI/LLM/RAG/Agent 통합 위협모델 분석서** | `v2.0 Threat Model` | [03_AI_THREAT_MODEL.md](./03_AI_THREAT_MODEL.md)<br>STRIDE 분석, OWASP 2026(LLM/Agent), 15대 자산, 10대 Entry Point, 위협-통제-탐지 매트릭스 |
| `05_SECURITY_EVENT_SCHEMA` | **AegisAI 통합 보안 이벤트 스키마 및 정규화 명세서** | `v2.0 Schema Master` | [05_SECURITY_EVENT_SCHEMA.md](./05_SECURITY_EVENT_SCHEMA.md)<br>80개 챕터, 10대 다이어그램, ECS+aegis.* 네임스페이스, 12대 JSON 예제, 10대 SDR, 전수 매트릭스 |
| `06_AI_SECURITY_POLICY` | **AegisAI AI 보안정책 및 통제기준서** | `v2.0 Policy Master` | [06_AI_SECURITY_POLICY.md](./06_AI_SECURITY_POLICY.md)<br>96개 챕터, 10대 다이어그램, 12대 PDR, HITL Dual-Control, 동적 TTL 3600s, 수치 거버넌스 |
| `07_HIGH_LEVEL_DESIGN` | **AegisAI 통합 시스템 상위설계서 (HLD)** | `v2.0 HLD Master` | [07_HIGH_LEVEL_DESIGN.md](./07_HIGH_LEVEL_DESIGN.md)<br>92개 챕터, 12대 다이어그램, 12대 ADR, 22개 컴포넌트 레지스트리, Closed-loop HLD 기준선 |
| `HLD_V1.0_ORIGINAL` | **보안관제 시스템 아키텍처 및 기본설계서 (HLD v1.0 원본)** | `v1.0 Baseline` | [`보안관제_프로젝트_시스템_아키텍처_및_기본설계서(HLD)_v1.0.pdf`](./보안관제_프로젝트_시스템_아키텍처_및_기본설계서(HLD)_v1.0.pdf)<br>Hyper-V/VMware 3망 분리, Suricata/Snort 듀얼 IDS, Wazuh Docker 기본 설계 |
| `DESIGN-ISSUE-001` | **M1·M2 통합 네트워크 전환 설계 이슈 분석서** | `Design Issue` | [DESIGN-ISSUE-001-M1M2-SOC-INTEGRATION.md](./DESIGN-ISSUE-001-M1M2-SOC-INTEGRATION.md)<br>Cisco L3 SPAN 및 TrusGuard 방화벽 물리/가상망 통합 시 고려사항 |
| `TLS_PROXY_ARCH` | **TLS 복호화 및 리버스 프록시 연동 아키텍처** | `Reference` | [TLS_DECRYPTION_AND_REVERSE_PROXY_ARCHITECTURE.md](./TLS_DECRYPTION_AND_REVERSE_PROXY_ARCHITECTURE.md)<br>인라인 프록시 및 SSL/TLS 미러링 기술 설계 |

---

## 3. v2.0 목표 아키텍처 4대 핵심 계층 (4-Layer Invariant)

```text
┌────────────────────────────────────────────────────────┐
│ L4  Unified AI-SOC / Human Approval (FastAPI/Kibana)   │
├────────────────────────────────────────────────────────┤
│ L3  AI SOC Analyst / Security RAG (Correlation/Triage) │
├────────────────────────────────────────────────────────┤
│ L2  AI Security Gateway / DLP (OWASP 2026 / Telemetry) │
├────────────────────────────────────────────────────────┤
│ L1  Existing SOC Core (Suricata / Wazuh / Elastic)     │
│     * Fail-Safe: L2~L4 장애 시에도 L1은 100% 무손실 유지*│
└────────────────────────────────────────────────────────┘
```
