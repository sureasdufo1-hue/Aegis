# 📐 03. 보안관제 시스템 상세설계 체계 (Detailed Design)

> **기준 일자:** 2026-09-28  
> **프로젝트 공식 명칭:** **AegisAI — AI for Security × Security for AI Integrated SOC Platform**  
> **현재 유효 기준선:** **v2.0 Low-Level Design (08_LOW_LEVEL_DESIGN.md)**  
> **레거시 참조:** v1.0 원본 PDF ([`보안관제_프로젝트_상세설계서(LLD)_v1.0.pdf`](./보안관제_프로젝트_상세설계서(LLD)_v1.0.pdf))

---

## 1. 상세설계 문서 계층 및 로드맵

```text
[ v2.0 통합 시스템 상위설계서 (HLD) ]
docs/02-architecture/07_HIGH_LEVEL_DESIGN.md (92개 챕터, 12대 다이어그램, 22개 컴포넌트)
      │
      ▼
[ v2.0 통합 시스템 상세설계서 (LLD) ]
docs/03-design/08_LOW_LEVEL_DESIGN.md (★ 126개 챕터, 18대 다이어그램, 48개 모듈)
      │
      ▼
[ v2.0 AI 보안 기능 평가 및 성능검증 계획서 ]
docs/05-testing/09_AI_EVALUATION_PLAN.md (160개 챕터, 3대 도메인, 17대 매트릭스)
      │
      ▼
[ v2.0 통합 구축 및 구현 계획서 ]
docs/04-deployment/10_IMPLEMENTATION_PLAN.md (★ 182개 챕터, 15대 트랙, 24대 매트릭스)
```

---

## 2. 핵심 상세설계 산출물 바로가기

| 문서 ID | 문서명 | 버전 / 성격 | 설명 및 링크 |
|---|---|:---:|---|
| `08_LOW_LEVEL_DESIGN` | **AegisAI 통합 시스템 상세설계서 (LLD)** | `v2.0 LLD Master` | [08_LOW_LEVEL_DESIGN.md](./08_LOW_LEVEL_DESIGN.md)<br>126개 챕터, 48개 모듈(MOD-*), 10대 API, Pydantic 스키마, 12개 시퀀스, 6개 DFD, 20대 구현 금지사항 |
| `LLD_V1.0_ORIGINAL` | **보안관제 프로젝트 상세설계서 (LLD v1.0 원본)** | `v1.0 Baseline` | [`보안관제_프로젝트_상세설계서(LLD)_v1.0.pdf`](./보안관제_프로젝트_상세설계서(LLD)_v1.0.pdf)<br>Hyper-V 3망 분리, Suricata/Snort 듀얼 IDS, Wazuh Docker 기본 상세 스펙 |

---

## 3. LLD v2.0 핵심 설계 요약 (Implementation Highlights)

```text
┌────────────────────────────────────────────────────────┐
│ 1. 48개 모듈 레지스트리 (MOD-SURI-001 ~ MOD-AUD-002)     │
│ 2. 10대 RESTful API 패밀리 (Pydantic v2 Schema 강제)    │
│ 3. AI Security Gateway 8단계 인라인 검사 파이프라인    │
│ 4. Presidio 6대 PII + 20대 Secret 가명화 토큰화       │
│ 5. 15분 슬라이딩 윈도우 결정론적 공격 체인 상관분석   │
│ 6. Ollama Qwen2.5 7B 로컬 격리 바인딩 (127.0.0.1)     │
│ 7. BGE-M3 + Elasticsearch kNN 하이브리드 RAG 검색      │
│ 8. 1-Click 암호 Nonce (900s) + Level 4 Dual-Control     │
│ 9. L3 Gateway nftables ipset 동적 차단 및 3,600s TTL   │
│ 10. WORM 불변 감사 로그 및 SHA-256 해시 체이닝        │
└────────────────────────────────────────────────────────┘
```
