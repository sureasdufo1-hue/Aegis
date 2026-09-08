# Phase LLM-2: 로컬 AI 플랫폼 배치 아키텍처 (Deployment Architecture & ADR)

| 문서 항목 | 내용 |
|---|---|
| 문서 ID | SOC-AI-LLM-ARC-002 |
| 작성 일시 | 2026-09-08 |
| 상태 | **사용자 승인 완료 (Approved)** |
| 아키텍처 결정 | **Windows Host Native Ollama 독립 플랫폼 배치** |
| 바인딩 주소 | `127.0.0.1:11434` (Strict Localhost Only) |

---

## 1. 아키텍처 결정 배경 (Context & Decision)

### 1.1 배치 대안 비교 분석

| 평가 기준 | 방안 1: Windows Host Native (채택) | 방안 2: WSL2 컨테이너/인스턴스 | 방안 3: 별도 신규 Hyper-V VM |
|---|---|---|---|
| **메모리 접근** | 64GB 물리 메모리 및 31.7GB 유휴 RAM 직접 접근 | WSL2 기본 8GB 메모리 제한 및 동적 반환 지연 | VM에 고정 16GB 메모리 사전 격리 할당 필요 |
| **CPU 성능 오버헤드** | 네이티브 AVX2/AVX-512 즉각 실행, 오버헤드 0% | 가상화 계층 경유로 3~8% CPU 연산 손실 | 하이퍼바이저 vCPU 스케줄링 오버헤드 발생 |
| **기존 SOC 영향** | Wazuh Docker(7.75GB 한도)와 자원 충돌 없음 | Docker WSL2 VM과 메모리 경합 발생 | 기존 Hyper-V 가상스위치 및 네트워크 재구성 필요 |
| **네트워크 보안** | 로컬 프로세스 루프백 통신만 허용 (간결함) | vEthernet(WSL) IP 라우팅 경로 필요 | 가상 브리지 및 서브넷 방화벽 정책 추가 필요 |
| **최종 판정** | **최적안 (사용자 승인 채택)** | 기각 (불필요한 가상화 계층) | 기각 (과도한 엔지니어링 및 자원 낭비) |

---

## 2. 자원 할당 및 예산 (Resource Budget)

### 2.1 호스트 자원 배분 계획 (총 64 GB RAM)
- **Windows OS 및 시스템 데몬**: ~6.0 GB
- **Docker Desktop & Wazuh SIEM 스택**: ~7.75 GB (실제 사용량 1.6 GB)
- **FastAPI SOC Console & Python 데몬**: ~0.5 GB
- **Ollama 런타임 및 Qwen3.5 9B (8K Context)**:
  - 모델 가중치 (Weights): 6.6 GB
  - KV Cache (8,192 tokens): ~2.5 GB
  - Compute Workspace & Buffer: ~1.4 GB
  - **합계 요구량**: **~10.5 GB**
- **안전 여유 메모리 (Safety Buffer)**: **약 21.0 GB 이상 유지** (Paging/OOM 원천 방지)

### 2.2 CPU 동시성 제약
- **동시 추론 수 상한**: `OLLAMA_NUM_PARALLEL=1`
- **동시 로딩 모델 상한**: `OLLAMA_MAX_LOADED_MODELS=1`
- **CPU 코어 집중**: 4코어 8스레드가 순차적으로 단일 조사 분석을 처리하여, 기존 Wazuh 및 네트워크 파이프라인의 스케줄링 간섭을 최소화.

---

## 3. 네트워크 및 프로세스 격리 (Network & Security Baseline)

```text
[외부 인터넷 / 공격자] ──── (접속 불가: 127.0.0.1 바인딩) ────┐
                                                                │
[SOC Dashboard Backend :8501] ─── (HTTP REST API) ───> [Ollama Native :11434]
     (FastAPI Python)                                      (Local-only 추론)
```

1. **로컬 전용 바인딩**: `OLLAMA_HOST=127.0.0.1:11434`
2. **원격 접근 및 클라우드 통신 비활성화**:
   - `OLLAMA_NO_CLOUD=1`
   - `OLLAMA_ORIGINS=""` (외부 웹 브라우저로부터의 CORS 요청 차단)
3. **Fail-Closed 안전장치**:
   - Ollama 런타임 장애/응답 지연 시, 임의의 클라우드 LLM으로 자동 전환되는 Fallback을 일체 두지 않음.
   - Live Provider 실패 시 명시적인 `UNAVAILABLE` 상태로 즉각 전환하여 관제 요원에게 장애 사실을 투명하게 고지.
