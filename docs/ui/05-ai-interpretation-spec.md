# AI Semantic Interpretation Service Specification

## 1. Scope & Operational Purpose

While deterministic dictionaries provide static label translation, complex security alerts require **context-aware semantic interpretation**.

The **Security Event Interpreter** (`analyzer/ai/localization/interpreter.py`) bridges this gap by translating technical IDS/IPS signatures and multi-stage incidents into practical Korean explanations with forensic investigation checklists.

---

## 2. Distinction: "한국어 해석" vs. "AI 심층 조사"

| Dimension | 한국어 해석 (Semantic Interpretation) | AI 심층 조사 (Deep Investigation) |
|---|---|---|
| **Trigger** | `[📖 한국어 해석]` button on Alert or Incident | `[🤖 AI 심층 조사]` button on Incident |
| **API Endpoint** | `POST /api/ai/interpret` | `POST /api/incidents/{id}/ai-investigate` |
| **Execution Scope** | Signature mechanics, threat meaning, compromise verification guide | RAG playbook retrieval, Threat Intel query, OpenSearch SIEM history, LLM reasoning |
| **Latency** | < 5 ms (Instant cached response) | ~35 ms (Mock) / ~2.5–6s (Ollama) |
| **Action Generation**| None (Educational & analytical explanation only) | Proposes policy-checked containment actions (`ProposedAction`) |

---

## 3. Data Contract (`POST /api/ai/interpret`)

### 3.1 Request Payload
```json
{
  "target_type": "alert",
  "signature": "SOC-ATTACK: Web SQL Injection - UNION SELECT Pattern Detected",
  "category": "Web Application Attack",
  "severity": "HIGH",
  "mitre_id": "T1190"
}
```

### 3.2 Response Schema
```json
{
  "source_signature": "SOC-ATTACK: Web SQL Injection - UNION SELECT Pattern Detected",
  "korean_title": "웹 애플리케이션 SQL 인젝션 공격 시도 탐지",
  "plain_korean_summary": "[높음] 웹 애플리케이션 SQL 인젝션 공격 시도 탐지",
  "security_meaning": "HTTP 파라미터에 'UNION SELECT' 구문을 삽입하여 데이터베이스 내부 정보를 비인가 조회하려는 공격입니다.",
  "compromise_status": "경보 발생 상태 (공격의 침해 성공 여부는 응답 로그 추가 검증 필요)",
  "recommended_checks": [
    "웹 서버의 실제 HTTP 응답 코드(200 OK vs 500/403)와 응답 데이터 크기를 확인하여 실제 데이터베이스 질의 성공 여부를 검증하십시오.",
    "관련 ATT&CK 기법: T1190 (외부 공개 애플리케이션 취약점 악용) - 인터넷에 공개된 웹 서버나 서비스의 취약점(SQLi, RCE)을 이용하여 내부로 침투하는 기법"
  ],
  "severity_ko": "높음",
  "severity_desc": "공격 시도 및 활성 취약점 악용 시도 (SQL 인젝션, 무차별 대입 등)",
  "generated_at": "2026-09-07T11:46:58.123456Z"
}
```

---

## 4. Compromise Status Philosophy

A core requirement is preventing false panics. An IDS signature alert confirms that an adversary transmitted a malicious pattern, but does not confirm that the target was compromised.

The interpretation engine enforces this principle:
> **"경보 발생 상태 (공격의 침해 성공 여부는 응답 로그 추가 검증 필요)"**

The analyst is instructed to inspect server response codes (HTTP 200 vs 403/500), response body sizes, and target host process activity before declaring an incident confirmed.

---

## 5. In-Memory SHA-256 Caching Engine

```python
class InterpretationCache:
    def _generate_cache_key(self, raw_text: str, context_type: str) -> str:
        content = f"{context_type}::{raw_text.strip()}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
```
- Deduplicates repeated alerts across live streams.
- Bounded LRU-style eviction (max 500 entries) prevents memory leaks.
