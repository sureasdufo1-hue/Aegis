# AI-ORCHESTRATED SOC COPILOT
## 로컬 LLM 운영 관리 및 비상 롤백 런북 (Operations & Rollback Runbook)

| 문서 항목 | 내용 |
|---|---|
| 문서 ID | SOC-AI-RUNBOOK-001 |
| 버전 / 상태 | v1.0 Final / **운영 배포 승인 (Operational)** |
| 대상 시스템 | SOC Detection & Monitoring Lab / AI-Orchestrated SOC Copilot |
| 대상 컴포넌트 | Local Ollama Runtime (`127.0.0.1:11434`), AI Provider Engine, FastAPI Console |
| 대상 모델 | `qwen3.5:9b`, `qwen3.5:4b`, `mock-grounded` (Fallback Baseline) |
| 작성 일시 | 2026-09-08 |
| 운영 책임자 | SOC 관제 운영팀 및 AI Security Engineering Team |

---

## 목차

- [1. 운영 개요 및 아키텍처 원칙](#1-운영-개요-및-아키텍처-원칙)
- [2. 표준 운영 절차 (Standard Operating Procedures)](#2-표준-운영-절차-standard-operating-procedures)
  - [2.1 RUN-OPS-001: Ollama 데몬 기동 및 무결성(Model-Lock) 검증](#21-run-ops-001-ollama-데몬-기동-및-무결성model-lock-검증)
  - [2.2 RUN-OPS-002: 실시간 프로바이더 동적 전환 (API 및 콘솔 연계)](#22-run-ops-002-실시간-프로바이더-동적-전환-api-및-콘솔-연계)
  - [2.3 RUN-OPS-003: 정기 헬스체크 및 추론 메트릭 모니터링](#23-run-ops-003-정기-헬스체크-및-추론-메트릭-모니터링)
- [3. 장애 대응 및 자동 복구 절차 (Incident Response & Auto-Recovery)](#3-장애-대응-및-자동-복구-절차-incident-response--auto-recovery)
  - [3.1 RUN-FAIL-001: Ollama 데몬 크래시 및 비정상 응답 감지 시 자동 재기동](#31-run-fail-001-ollama-데몬-크래시-및-비정상-응답-감지-시-자동-재기동)
  - [3.2 RUN-FAIL-002: 추론 타임아웃(Timeout) 및 CPU 과열 방지 통제](#32-run-fail-002-추론-타임아웃timeout-및-cpu-과열-방지-통제)
  - [3.3 RUN-FAIL-003: Pydantic 스키마 파싱 실패 및 방어적 격리](#33-run-fail-003-pydantic-스키마-파싱-실패-및-방어적-격리)
- [4. 긴급 1초 비상 롤백 절차 (Emergency 1-Second Rollback)](#4-긴급-1초-비상-롤백-절차-emergency-1-second-rollback)
  - [4.1 RUN-ROLL-001: Mock Baseline 즉시 전환 및 관제 무중단 유지](#41-run-roll-001-mock-baseline-즉시-전환-및-관제-무중단-유지)
  - [4.2 RUN-ROLL-002: 가중치 롤백 및 다운그레이드 절차 (9B → 4B)](#42-run-roll-002-가중치-롤백-및-다운그레이드-절차-9b--4b)
- [5. 장애 복구 후 검증 및 감사 기록 (Post-Recovery Audit)](#5-장애-복구-후-검증-및-감사-기록-post-recovery-audit)

---

## 1. 운영 개요 및 아키텍처 원칙

본 런북은 **AI-Orchestrated SOC Copilot**의 로컬 LLM 런타임(Ollama Native), 관제 대시보드(Port 8501), 그리고 백엔드 추론 엔진의 일상 운영과 장애 시 비상 복구 절차를 규정한다.

### 1.1 핵심 운영 원칙 (Operational Invariants)
1. **Strict Local-only 통제**: Ollama 데몬은 오직 `127.0.0.1:11434`에만 바인딩되며, 클라우드 원격 통신(`OLLAMA_NO_CLOUD=1`) 및 외부 인터페이스 노출이 절대 금지된다.
2. **단일 동시성 통제 (Concurrency Invariant)**: Xeon 4코어 CPU 환경의 과열 및 병목을 방지하기 위해 `OLLAMA_NUM_PARALLEL=1`로 단일 추론 스레드만 허용한다.
3. **Fail-Closed & Fallback 보장**: LLM 추론 지연, 프로세스 크래시, 포맷 오류 발생 시 관제 전체가 중단되지 않고 1초 이내에 결정론적 `Mock Baseline`으로 안전하게 전환된다.
4. **증적 및 무결성 보존**: 모든 모델 가중치는 `docs/ai/model-lock.json`의 64자리 SHA-256 해시값과 100% 일치해야만 로딩이 허용된다.

---

## 2. 표준 운영 절차 (Standard Operating Procedures)

### 2.1 RUN-OPS-001: Ollama 데몬 기동 및 무결성(Model-Lock) 검증

| 절차 코드 | RUN-OPS-001 | 중요도 | P0 (필수 운영 절차) |
|---|---|---|---|
| **목적** | 격리된 로컬 환경에서 Ollama 데몬을 기동하고, 승인된 모델 해시 무결성을 검증 |
| **선행 조건** | Windows Host 관리자 권한, Docker Wazuh 정상 동작 확인 |
| **담당자** | SOC AI 시스템 관리자 / Tier 2 분석가 |

#### 실행 절차
```powershell
# 1. 작업 디렉터리 이동
cd C:\Users\user\Documents\ChatGPT\Suricata-Snort-SOC-Lab

# 2. Ollama 데몬 백그라운드 기동 스크립트 실행
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start_ollama_local.ps1

# 3. 로컬 11434 포트 리스닝 확인
Test-NetConnection -ComputerName 127.0.0.1 -Port 11434

# 4. 모델 무결성 락 검증
python -c "
import json, urllib.request
with open('docs/ai/model-lock.json', encoding='utf-8') as f:
    locks = json.load(f)
req = urllib.request.urlopen('http://127.0.0.1:11434/api/tags')
res = json.loads(req.read())
for m in res['models']:
    name = m['name']
    digest = m['digest']
    if name in locks['models']:
        expected = locks['models'][name]['digest']
        status = 'MATCH' if digest.startswith(expected) else 'MISMATCH'
        print(f'Model [{name}]: {status} ({digest[:16]}...)')
"
```

---

### 2.2 RUN-OPS-002: 실시간 프로바이더 동적 전환 (API 및 콘솔 연계)

| 절차 코드 | RUN-OPS-002 | 중요도 | P1 (상시 운영 절차) |
|---|---|---|---|
| **목적** | 시스템 재기동 없이 REST API 및 대시보드를 통해 추론 모델(9B, 4B, Mock)을 실시간 전환 |
| **적용 시점** | 긴급 정밀 분석 필요 시(9B 전환), 주간 대량 경보 트리아지 시(4B 전환), 비상 롤백 시(Mock) |

#### 실행 절차
```bash
# Case 1: 고속 일상 관제 모드 (Qwen3.5 4B) 전환
curl -X POST http://127.0.0.1:8501/api/ai/provider/select \
     -H "Content-Type: application/json" \
     -d '{"provider_type": "real", "model_name": "qwen3.5:4b"}'

# Case 2: 심층 인과관계 정밀 분석 모드 (Qwen3.5 9B) 전환
curl -X POST http://127.0.0.1:8501/api/ai/provider/select \
     -H "Content-Type: application/json" \
     -d '{"provider_type": "real", "model_name": "qwen3.5:9b"}'

# Case 3: 안전망 모의 기준선 (Mock) 즉시 전환
curl -X POST http://127.0.0.1:8501/api/ai/provider/select \
     -H "Content-Type: application/json" \
     -d '{"provider_type": "mock"}'
```

---

### 2.3 RUN-OPS-003: 정기 헬스체크 및 추론 메트릭 모니터링

| 절차 코드 | RUN-OPS-003 | 중요도 | P2 (일상 점검) |
|---|---|---|---|
| **목적** | AI 프로바이더 헬스체크, 최근 토큰 소비량, 추론 소요 시간 모니터링 |

```bash
# 프로바이더 상태 및 메트릭 조회
curl -s http://127.0.0.1:8501/api/ai/provider/status | python -m json.tool
```

---

## 3. 장애 대응 및 자동 복구 절차 (Incident Response & Auto-Recovery)

### 3.1 RUN-FAIL-001: Ollama 데몬 크래시 및 비정상 응답 감지 시 자동 재기동

| 절차 코드 | RUN-FAIL-001 | 목표 복구 시간 (RTO) | 30초 이내 |
|---|---|---|---|
| **장애 징후** | `127.0.0.1:11434` 연결 거부(Connection Refused), 조사 요청 시 HTTP 500/503 발생 |
| **원인 분석** | 프로세스 예기치 않은 종료, 일시적 CPU 소진, 메모리 부족 |

#### 복구 절차
```powershell
# 1. 잔여 고아 ollama 프로세스 강제 종료
Get-Process -Name "ollama" -ErrorAction SilentlyContinue | Stop-Process -Force

# 2. 임시 캐시 확인 및 데몬 재기동
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start_ollama_local.ps1

# 3. 5초 대기 후 헬스체크
Start-Sleep -Seconds 5
Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -Method Get

# 4. 관제 대시보드 상태 재확인
Invoke-RestMethod -Uri "http://127.0.0.1:8501/api/ai/provider/status" -Method Get
```

---

### 3.2 RUN-FAIL-002: 추론 타임아웃(Timeout) 및 CPU 과열 방지 통제

| 절차 코드 | RUN-FAIL-002 | 통제 기준 | 단일 추론 240초 초과 시 강제 차단 |
|---|---|---|---|
| **장애 징후** | 단일 침해사고 분석 요청이 4분(240초) 이상 지연되며 CPU 점유율이 90% 이상 지속 |
| **안전 대책** | `OllamaProvider` 내부 타임아웃(240초) 발동 및 자동 Mock Fallback |

```text
[타임아웃 감지 시 처리 로직]
1. Python httpx/urllib 240초 타임아웃 예외(TimeoutException) 발생
2. 시스템 로그에 WARN [AI_TIMEOUT_EXCEEDED] 기록
3. 즉시 is_mock=True, fallback_reason="INFERENCE_TIMEOUT" 플래그를 포함한 기본 안전 응답 반환
4. 관제 요원 UI에 "추론 시간 초과로 기본 규칙 분석 결과가 제공되었습니다" 경고 배너 표출
```

---

### 3.3 RUN-FAIL-003: Pydantic 스키마 파싱 실패 및 방어적 격리

| 절차 코드 | RUN-FAIL-003 | 대응 방식 | 방어적 정규화(Defensive Normalization) |
|---|---|---|---|
| **장애 징후** | LLM이 불완전한 JSON 반환 또는 필수 필드 누락 |
| **방어 로직** | `OllamaProvider._normalize_payload()`가 자동 개입하여 누락된 키(citations, techniques)를 안전 기본값으로 보정 |

---

## 4. 긴급 1초 비상 롤백 절차 (Emergency 1-Second Rollback)

### 4.1 RUN-ROLL-001: Mock Baseline 즉시 전환 및 관제 무중단 유지

| 절차 코드 | RUN-ROLL-001 | 목표 롤백 시간 | **1.0초 이내 (즉각 전환)** |
|---|---|---|---|
| **발동 기준** | • LLM 연속 2회 이상 타임아웃 발생 시<br>• 미검증 신종 공격으로 인한 비정상 환각 의심 시<br>• 호스트 서버 리소스 긴급 확보 필요 시 |

#### 단일 명령 롤백
```bash
# 1초 긴급 롤백 명령 실행
curl -X POST http://127.0.0.1:8501/api/ai/provider/select \
     -H "Content-Type: application/json" \
     -d '{"provider_type": "mock"}'
```

```text
[롤백 성공 확인 지표]
{
  "status": "success",
  "selected_provider": "mock",
  "selected_model": "mock-grounded",
  "is_mock": true,
  "message": "AI provider successfully updated to mock (mock-grounded)"
}
```

---

### 4.2 RUN-ROLL-002: 가중치 롤백 및 다운그레이드 절차 (9B → 4B)

```bash
# 9B 부하 과다 시 4B로 즉시 다운그레이드
curl -X POST http://127.0.0.1:8501/api/ai/provider/select \
     -H "Content-Type: application/json" \
     -d '{"provider_type": "real", "model_name": "qwen3.5:4b"}'
```

---

## 5. 장애 복구 후 검증 및 감사 기록 (Post-Recovery Audit)

장애 조치 및 롤백이 완료된 후에는 다음 검증을 수행하여 시스템 무결성을 확인한다.

```powershell
# 1. 자동화 회귀 테스트 전체 60개 수행
pytest tests/

# 2. 실모델 E2E 파이프라인 무결성 검증
python scripts/verify_real_llm_e2e.py

# 3. 관제 감사 로그 기록 확인
Get-Content -Path "logs/dashboard.log" -Tail 30
```

| 검증 단계 | 합격 기준 | 확인 방법 |
|---|---|---|
| 단위 및 통합 테스트 | 60 / 60 통과 (100%) | `pytest tests/` 녹색 출력 |
| E2E 분석 파이프라인 | `is_mock: false`, 정책 검증 통과 | `verify_real_llm_e2e.py` 성공 |
| 관제 대시보드 | UI 렌더링 정상, 응답 200 OK | `http://127.0.0.1:8501` 접속 확인 |
| 데몬 자원 상태 | RAM 30GB 이상 유휴, CPU 안정 | `Get-Process ollama` 확인 |
