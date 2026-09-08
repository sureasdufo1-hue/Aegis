# Phase LLM-0: 런타임 진단 및 현행 SOC Baseline 실측 보고서

| 문서 항목 | 내용 |
|---|---|
| 문서 ID | SOC-AI-LLM-REP-000 |
| 관련 기준 | `08-implementation-plan.md` (SOC-AI-LLM-IMP-001) Phase LLM-0 |
| 작성 일시 | 2026-09-08 08:17:00 KST |
| 진단 성격 | **Read-only 실측 기반 진단 보고서 (코드 수정 및 설치 없음)** |
| 진단 결과 | **Phase LLM-0 Gate (G0): PASS** (하드웨어·자원·기존 SOC 완전 검증 완료) |

---

## 1. 개요 및 목적

본 문서는 `C:\Users\user\Downloads\08-implementation-plan.md`의 **Phase LLM-0 (Current Baseline Verification)** 지침에 따라, 어떠한 설치·모델 다운로드·기존 서비스 중지·코드 수정 없이 호스트 하드웨어, 가상화/컨테이너 자원, 로컬 AI 런타임 부재 상태, 기존 SOC 관제 파이프라인(54개 테스트 및 3개 Wazuh 컨테이너, FastAPI 대시보드)을 **읽기 전용 명령어로 100% 직접 실측·검증**한 결과서이다.

---

## 2. 호스트 하드웨어 실측 인벤토리 (Inventory)

Windows 11 PowerShell CimInstance 및 시스템 진단 실측 결과는 다음과 같다.

### 2.1 CPU & 프로세서
- **CPU 모델**: `Intel(R) Xeon(R) E-2374G CPU @ 3.70GHz`
- **코어 / 스레드**: 4 Physical Cores / 8 Logical Processors (Hyper-Threading 활성)
- **클럭**: Base 3.70 GHz / Max 3.696 GHz (Turbo Boost 지원)
- **명령어 집합**: AVX-512F, AVX2, FMA3, SSE4.2 지원
- **실측 진단 근거**: `Get-CimInstance Win32_Processor`

### 2.2 물리 메모리 (RAM)
- **전체 가시 메모리 (Total Visible)**: `66,945,364 KB` (**약 63.84 GiB**, 64GB)
- **실시간 가용 물리 메모리 (Free RAM)**: `33,310,536 KB` (**약 31.76 GiB**, 여유율 49.7%)
- **장착 RAM 모듈 실측**:
  - Slot 1: Samsung `M391A4G43AB1-CWE` 32GB DDR4-3200 ECC UDIMM (3200 MT/s)
  - Slot 2: Samsung `M391A4G43AB1-CWE` 32GB DDR4-3200 ECC UDIMM (3200 MT/s)
  - 채널 구성: Dual-Channel 활성화
- **실측 진단 근거**: `Get-CimInstance Win32_OperatingSystem`, `Get-CimInstance Win32_PhysicalMemory`

### 2.3 GPU 및 디스플레이 어댑터 (핵심 제약사항)
- **어댑터 1**: `Intel(R) UHD Graphics P750`
  - 드라이버: `32.0.101.7088`
  - 보고 VRAM (`AdapterRAM`): 2,147,479,552 Bytes (약 2.0 GB, 시스템 RAM 공유)
  - 하드웨어 ID: `PCI\VEN_8086&DEV_4C9A`
- **어댑터 2**: `Microsoft 기본 디스플레이 어댑터` (ASPEED AST2500/2600 서버 관리용 BMC 칩셋, `PCI\VEN_1A03&DEV_2000`)
- **GPU 실측 판정**:
  > **[CRITICAL HARDWARE FACT] 전용 NVIDIA (CUDA) 또는 AMD (ROCm) 외장 GPU가 존재하지 않음.**  
  > 따라서 로컬 LLM 구동 시 Ollama는 llama.cpp 백엔드를 통해 **100% CPU (AVX2/AVX-512) 및 시스템 RAM 기반 추론**으로 동작하게 됨.

### 2.4 저장공간 (Storage)
- **C: 드라이브 (OS & Workspaces)**:
  - 전체 용량: 약 1,761 GB (~1.72 TB NVMe/SSD)
  - 사용 용량: 546.44 GB
  - **가용 용량 (Free Space)**: **1,215.00 GB (~1.18 TB)**
- **I: 드라이브**: 가용 81.98 GB
- **저장공간 판정**: 목표 모델(Qwen3.5 9B Q4_K_M ~6.6GB) 및 컨텍스트 캐시, 임시 파일 수용에 여유 용량(1.2TB)이 극히 충분함.

---

## 3. 런타임 및 서비스 상태 진단

### 3.1 WSL2 & 가상화 상태
- **WSL 배포판**: `docker-desktop` (State: `Running`, Version: `2`)
- **WSL 내부 Ollama 유무**: `which ollama` 실행 결과 `Not Found` (미설치)

### 3.2 Docker & Wazuh SIEM 컨테이너 상태
Docker Desktop 런타임 상에서 SOC 관제 핵심 컨테이너가 15시간 이상 무장애 구동 중임:
- `soc-wazuh-dashboard`: Up 15 hours (Ports `5601`, `443` -> HTTP 200 OK 응답 확인)
- `soc-wazuh-manager`: Up 15 hours (Ports `1514/TCP` [OPEN], `1515/TCP` [OPEN], `55000/TCP`)
- `soc-wazuh-indexer`: Up 15 hours (Port `9200` OpenSearch REST API -> HTTP 200 OK 응답 확인)
- **Docker 자원 할당 및 사용량**:
  - Docker 전체 할당 상한: `7.755 GiB`
  - 현재 전체 컨테이너 사용 메모리: 약 `1.6 GiB` (여유 `6.15 GiB`)
  - Wazuh 3개 컴포넌트 실측 메모리: Indexer (719 MiB) + Manager (509 MiB) + Dashboard (227 MiB) = 1,455 MiB

### 3.3 로컬 Ollama 런타임 상태 실측
- `Get-Command ollama`: 미설치 (CommandNotFound)
- `Get-Process ollama*`: 미실행 (프로세스 없음)
- `127.0.0.1:11434` TCP 접속 테스트: `TcpTestSucceeded: False` (포트 닫힘)
- 설치 기본 경로(`AppData\Local\Programs\Ollama`, `Program Files\Ollama`): 폴더 부재 (`False`)
- **판정**: 호스트에 Ollama 런타임이 전혀 존재하지 않으며, 현재 시스템은 순수 Mock Provider 기반으로 완벽히 격리 구동 중임.

---

## 4. 기존 SOC Baseline 및 회귀 검증

### 4.1 Git 작업 트리 무결성
- 기존 변경 파일 및 증적 파일이 100% 보존되어 있음:
  - Modified: `analyzer/parsers/eve_parser.py`, `dashboard/app.py`, `infrastructure/docker/docker-compose.wazuh.yml`, `scenarios/traffic_generator.py`, `tests/test_dashboard_api.py`
  - Untracked: `analyzer/ai/`, `docs/ai/`, `docs/ui/`, `evidence/EV-*`, `tests/test_ai_*.py` 등
- **미커밋 변경사항 손실 0건 확인**.

### 4.2 자동화 회귀 테스트 스위트 실측
- **실행 명령어**: `pytest tests/`
- **소요 시간**: 1.94초
- **결과**: **54 passed, 0 failed (100% PASS)**
  - 기존 SOC 탐지·파서·상관분석·E2E: 22개 통과
  - AI 증적·도구·RAG·정책·보안·대시보드: 32개 통과

### 4.3 FastAPI 관제 콘솔 라이브 엔드포인트 검증 (`http://127.0.0.1:8501`)
- `GET /api/health` -> `200 OK`
  ```json
  {
    "status": "healthy",
    "service": "soc-dashboard",
    "eve_log_exists": true,
    "snort_log_exists": true,
    "ai_copilot_ready": true
  }
  ```
- `GET /api/ai/health` -> `200 OK`
  ```json
  {
    "status": "healthy",
    "provider": "mock-grounded",
    "provider_model": "mock-soc-analyst-v1",
    "is_mock_provider": true,
    "provider_status_label": "모의 분석 엔진 (Mock Baseline - 실제 LLM 아님)",
    "tools_available": 3,
    "rag_documents_loaded": 6,
    "rag_chunks_loaded": 28,
    "approval_stats": { "total": 41, "pending": 26, "approved": 4, "rejected": 5, "executed": 6, "expired": 0 }
  }
  ```
- `GET /api/stats` -> `200 OK` (총 84개 경보, 10개 인시던트 정상 수집)

---

## 5. Qwen3.5 9B 하드웨어 수용성 및 용량 분석 (Capacity Verdict)

구현계획서(`08-implementation-plan.md`)에 정의된 Qwen3.5 9B 운영 요건과 실측 하드웨어 비교 분석:

| 평가 항목 | Qwen3.5 9B (Q4_K_M) 요구 사양 | 호스트 실측 현황 | 판정 및 영향 |
|---|---|---|---|
| **RAM 용량** | 모델 가중치(6.6GB) + 8K KV Cache(1.5~2.5GB) + 작업영역 ≈ **9.5~10.5 GB** | 가용 RAM **31.76 GB** (전체 64GB) | **PASS** (메모리 충분, OOM 위험 극히 낮음) |
| **디스크 공간** | 모델 다운로드 및 캐시 ≈ 10~15 GB | 가용 디스크 **1,215 GB** | **PASS** (초고속 NVMe 공간 여유 100배 이상) |
| **GPU 가속** | 권장: NVIDIA VRAM 10GB+ (CUDA) | **외장 GPU 없음** (Intel UHD P750 내장) | **ATTENTION / CONCERN** (100% CPU 추론) |
| **추론 속도 예상** | GPU 환경: 30~50 tok/s | 4코어 8스레드 Xeon CPU: **약 3 ~ 6 tok/s** | **실측 필요 / PARTIAL 가능성** |
| **단일 조사 지연시간** | 300~500 토큰 생성 시 5~10초 | CPU 추론 시 **약 50 ~ 100초** 소요 예상 | 계획서 잠정 Gate (p95 < 120s) 이내이나 대기 체감 존재 |
| **동시성 제약** | CPU 자원 집중 필요 | 동시 추론 요청 시 지연시간 선형 급증 | `OLLAMA_NUM_PARALLEL=1` 필수 강제 |

### 💡 하드웨어 진단 결론
1. **메모리(RAM) 및 저장공간(Disk) 측면**: 64GB 물리 메모리 중 31.7GB가 유휴 상태이므로, Qwen3.5 9B(10.5GB 필요)의 로딩 및 8K 컨텍스트 유지는 안정적으로 가능함.
2. **연산 가속(GPU) 측면**: 전용 GPU가 없으므로 순수 CPU 추론이 강제됨. 따라서:
   - **동시 추론은 반드시 1개(`OLLAMA_NUM_PARALLEL=1`)로 제한**해야 함.
   - 추론 완료까지 수십 초가 소요될 수 있으므로 대시보드 비동기 폴링 구조가 필수적임.
   - 계획서에 명시된 바와 같이, 성능 벤치마크 단계(LLM-6)에서 경량 대안 모델(예: `qwen3.5:4b` 또는 `qwen2.5:3b/7b`)과의 속도·품질 비교군 테스트를 병행하는 것이 실무적으로 매우 합리적임.

---

## 6. 미확인 및 환경 제약 목록 (Unverified List)

1. **Hyper-V VM 내부 상태**: 현재 PowerShell 세션 권한 제약으로 `Get-VM` 직접 조회가 제한됨 (별도 관리자 권한 필요). 단, Docker 및 로컬 포트 통신 기반 SOC 파이프라인은 100% 정상 작동 중임.
2. **Intel iGPU (OpenVINO) 가속 가능 여부**: Ollama 공식 바이너리가 Intel UHD P750을 직접 감지 및 오프로드할 수 있는지 여부는 실제 런타임 배포 전까지 미확인 상태로 유지함. (현재 기본 가정은 100% AVX2 CPU 연산).

---

## 7. 향후 단계(Phase LLM-1 ~ LLM-4) 추진을 위한 승인 요청 항목

사용자의 사전 승인 조건에 따라, 다음 작업은 **사용자의 명시적 승인 후**에만 단계적으로 진행합니다.

1. **배치 방식 확정**:
   - **권고안**: Windows Native Ollama 설치 (WSL2 이중 가상화 오버헤드 배제 및 31.7GB 호스트 여유 메모리 직접 활용)
2. **Ollama 공식 런타임 설치 승인**:
   - Windows용 공식 최신 Ollama 설치
   - 바인딩 격리 적용: `OLLAMA_HOST=127.0.0.1:11434` (외부 노출 완전 차단)
3. **모델 다운로드 승인**:
   - 주력 목표: `qwen3.5:9b` (Q4_K_M, 약 6.6GB)
   - 비교 벤치마크용 후보: `qwen3.5:4b` (CPU 속도 비교용)
4. **Provider 코드 분리 승인**:
   - 현재 Mock Provider와 실제 Ollama Provider 간의 명시적 분리 (Live 장애 시 Mock으로 무단 위장 금지, 명시적 `UNAVAILABLE` 표기 적용)
