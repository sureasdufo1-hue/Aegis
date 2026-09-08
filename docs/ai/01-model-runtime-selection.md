# Phase LLM-1: 모델 및 런타임 선정 결정서 (Model & Runtime Selection)

| 문서 항목 | 내용 |
|---|---|
| 문서 ID | SOC-AI-LLM-SEL-001 |
| 작성 일시 | 2026-09-08 |
| 상태 | **사용자 승인 완료 (Approved)** |
| 대상 모델 | `Qwen/Qwen3.5-9B` (Ollama 배포 태그: `qwen3.5:9b` / `qwen3.5:9b-q4_K_M`) |
| 비교/대체 모델 | `Qwen/Qwen3.5-4B` (`qwen3.5:4b`), `qwen2.5:7b` (기존 어댑터 호환) |
| 선정 런타임 | Ollama Windows Native (최신 안정 공식 릴리스 v0.33.x+) |

---

## 1. 모델 선정 사유 및 기술 규격

### 1.1 주력 모델: Qwen3.5 9B (Q4_K_M)
- **제조사 / 아키텍처**: Alibaba Cloud Qwen 팀 / Post-trained Dense Transformer
- **파라미터 크기**: 9.65B 파라미터
- **양자화 형식**: `Q4_K_M` (가중치 파일 크기 약 6.6 GB)
- **라이선스**: **Apache License 2.0** (상업적/연구/실험 목적 자유로운 배포 및 사용 가능)
- **선정 이유**:
  1. **보안관제 추론 역량**: 보안 로그, 네트워크 프로토콜, MITRE ATT&CK 기법 해석 및 한국어 자연어 해석에서 7B 이하 모델 대비 뛰어난 맥락 유지력과 논리적 추론 능력을 제공.
  2. **구조화된 출력(JSON Schema / Structured Output)**: Pydantic 모델 기반의 `AIIncidentAnalysis` JSON Schema 준수율이 높음.
  3. **Tool Calling / 함수 호출 지원**: SIEM 경보 조회, Threat Intel 매칭, PCAP 패킷 검사 등 읽기 전용 SOC 도구와의 상호작용 지원.
  4. **메모리 적합성**: 호스트 가용 물리 메모리(31.76 GB) 대비 가중치(6.6GB) + 8K KV Cache(약 2.5GB) 탑재 시 10.5GB 미만으로 OOM 위험 없음.

### 1.2 보조/비교 모델 (Benchmark & Rollback)
- **Qwen3.5 4B (`qwen3.5:4b`)**:
  - 목적: 외장 GPU 부재(Intel UHD 내장 GPU) 환경에서 CPU 추론 속도(tok/s) 및 지연 시간 비교용.
  - 가중치 크기 약 2.7 GB, 8K 컨텍스트에서도 초당 10~15 토큰 이상의 빠른 반응성 기대.
- **기존 Qwen2.5 7B (`qwen2.5:7b`)**:
  - 기존 `ollama_provider.py`의 기본 참조 모델이자 롤백 후보.

---

## 2. 런타임 선정 및 버전 고정 정책

### 2.1 런타임: Ollama (Windows Native)
- **선정 이유**:
  - 단일 실행 바이너리로 구성되어 Docker/WSL2의 이중 가상화 오버헤드 없이 호스트의 64GB ECC 물리 메모리를 100% 직접 할당 가능.
  - REST API (`/api/chat`, `/api/tags`, `/api/show`, `/api/ps`)를 표준 제공하여 기존 FastAPI 백엔드와의 즉시 연동 가능.
  - 엄격한 로컬 루프백(`127.0.0.1:11434`) 바인딩 지원.

### 2.2 Model Lock & Digest 불변성 정책
1. 모델 다운로드 즉시 `ollama show --modelfile` 및 REST API 응답으로부터 **전체 64자 SHA-256 Digest**를 추출하여 `docs/ai/model-lock.json`에 기록·고정함.
2. 동일 태그명이라도 원격 리포지토리에서 가중치가 갱신되어 Digest가 달라진 경우, 사전 테스트 없이 자동 갱신되는 것을 차단함.

---

## 3. 라이선스 및 데이터 프라이버시 원칙

- **라이선스 무결성**: Apache 2.0 라이선스 조건을 준수하며 소스코드 및 문서에 고지.
- **외부 반출 금지 (Local-Only Invariant)**:
  - `OLLAMA_NO_CLOUD=1` 환경변수를 설정하여 외부 원격 분석 또는 클라우드 텔레메트리를 전면 차단.
  - 추론 시 사용되는 증적 로그(IP, 포트, 페이로드)는 호스트 루프백 외부로 일체 송출되지 않음.
