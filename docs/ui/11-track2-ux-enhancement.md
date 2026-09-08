# SOC 관제 실무 UX 개선: 원클릭 AI 프로바이더 셀렉터 및 조사 진행상태/경과 타이머 모달 (Track 2)

| 문서 항목 | 내용 |
|---|---|
| 문서 ID | SOC-UI-TRACK2-001 |
| 버전 / 상태 | v1.0 Final / **배포 완료 및 검증 완료 (Verified)** |
| 대상 시스템 | SOC Detection & Monitoring Lab / AI-Orchestrated SOC Copilot |
| 대상 화면 | 웹 관제 콘솔 (`http://127.0.0.1:8501`) 상단 헤더 및 복합 침해사고 조사 인터랙션 |
| 관련 요구사항 | 트랙 2: [관제 실무 UX] 웹 콘솔 상호작용 강화 및 프로바이더 전환기 탑재 |
| 작성 일시 | 2026-09-08 |
| 담당자 | Enterprise SOC UX/Frontend & AI Security Engineering Team |

---

## 1. 추진 목적 및 배경

본 개선 작업(트랙 2)은 로컬 LLM 환경(Intel Xeon 4코어 AVX2 CPU 전용)의 특성상 발생하는 **추론 대기시간(4B 모델 약 120초, 9B 모델 약 180초, Mock 모델 0초)을 관제 요원이 직관적으로 인지하고 제어할 수 있도록 실무형 UX를 고도화**하는 것을 목표로 한다.

기존 콘솔은 백엔드에 `/api/ai/provider/select` API가 존재함에도 화면에서 즉시 모델을 교체할 수 없고, "AI 심층 조사" 클릭 시 단순 스피너 텍스트만 표시되어 장시간 대기 시 화면 멈춤(Hang)으로 오인할 위험이 있었다. 이를 해결하기 위해 다음 2대 핵심 기능을 구현하였다.

---

## 2. 주요 구현 기능 상세

### 2.1 상단 헤더 원클릭 AI 프로바이더 셀렉터 (Provider Selector UI)

대시보드 상단 헤더의 실시간 상태 영역에 **즉각적인 드롭다운 셀렉터와 상태 뱃지**를 일체형으로 배치하였다.

```html
<!-- Interactive AI Engine Selector & Status Badge -->
<div class="flex items-center gap-2 bg-slate-800/90 border border-slate-700/80 rounded-lg px-2.5 py-1 text-xs">
    <label for="provider-select" class="text-slate-400 font-medium flex items-center gap-1.5 whitespace-nowrap">
        <span class="text-indigo-400">🤖</span>
        <span>AI 엔진:</span>
    </label>
    <select id="provider-select" onchange="switchAiProvider(this.value)" class="bg-slate-900 border border-slate-700 rounded-md px-2 py-1 text-xs font-mono font-semibold text-white focus:outline-none focus:border-cyan-500 cursor-pointer transition">
        <option value="mock">⚡ 모의 엔진 (Mock Baseline · 0s)</option>
        <option value="qwen3.5:4b">🚀 Qwen3.5 4B (고속 분석 · ~120s)</option>
        <option value="qwen3.5:9b">🧠 Qwen3.5 9B (정밀 분석 · ~180s)</option>
    </select>
    <div id="provider-badge" class="...">
        <span id="provider-status-dot" class="w-2 h-2 rounded-full ..."></span>
        <span id="provider-status-text">...</span>
    </div>
</div>
```

- **실시간 비동기 전환**: 드롭다운 선택 시 화면 깜빡임이나 재로딩 없이 `POST /api/ai/provider/select`가 즉각 호출되어 1초 이내에 오케스트레이터의 활성 프로바이더를 교체함.
- **양방향 상태 동기화**: `refreshData()` 주기(3초)마다 서버의 실제 프로바이더(`GET /api/ai/health`)를 조회하여 드롭다운 선택값과 뱃지 색상(Mock: Amber, 4B: Cyan, 9B: Purple)을 자동 일치시킴.
- **토스트 피드백**: 모델 전환 완료 시 우측 상단에 플로팅 알림 카드가 표출되어 분석관에게 시각적 확인을 제공함.

---

### 2.2 AI 심층 조사 진행 상태 프로그레스 / 경과 타이머 모달 (Stopwatch & Stepper Modal)

"AI 심층 조사" 버튼 클릭 시 관제 요원에게 시스템이 정상 동작 중임을 확신시키는 **전용 진행상태 모달**이 즉시 전면에 렌더링된다.

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🤖 AI 심층 침해사고 조사 파이프라인                               [▼ 최소화] │
│ 사고 ID: INC-20260908-001 | 공격자: 10.77.20.20                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  경과 시간 (Elapsed Timer)                       활성 추론 엔진              │
│  01:23.4                                        Qwen3.5 4B (고속 분석)      │
│                                                                             │
│  [===========================>                    ] 65%                     │
│  3단계: 로컬 LLM 추론 연산 중 (83s 경과 · CPU 연산)...                        │
│  ⚡ Intel Xeon 4C/8T AVX2 CPU 전용 연산 (Strict Localhost 127.0.0.1:11434)  │
├─────────────────────────────────────────────────────────────────────────────┤
│ 📋 단계별 분석 파이프라인 상태:                                             │
│  ✅ 1단계. 보안 증적 수집 및 읽기 도구 실행 (완료)                          │
│  ✅ 2단계. RAG 보안 플레이북 검색 및 컨텍스트 바운딩 (완료)                  │
│  🌀 3단계. 로컬 LLM 인과관계 추론 및 구조화 생성 (연산 진행 중)              │
│  ⏳ 4단계. 독립 정책 검증(PolicyValidator) 및 인간 승인 큐 등록 (대기 중)    │
├─────────────────────────────────────────────────────────────────────────────┤
│ * 창을 최소화해도 백그라운드 조사는 계속 진행됩니다.       [백그라운드로 계속] │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 핵심 기능 요소
1. **정밀 디지털 스톱워치 (Digital Stopwatch)**:
   - 60ms 간격으로 경과 시간(`MM:SS.s`)을 대형 폰트로 실시간 갱신하여 시스템 무응답(Freeze) 의심을 완전히 해소함.
2. **동적 4단계 파이프라인 스테퍼 (Visual Stepper)**:
   - 1단계: Suricata/Snort 로그 및 Threat Intel 조회 (0~3초)
   - 2단계: RAG 플레이북 검색 및 800자 컨텍스트 바운딩 (3~11초)
   - 3단계: 로컬 LLM AVX2 CPU 연산 및 Pydantic Structured JSON 생성 (11초~완료)
   - 4단계: 정책 검증 통과 및 인간 승인 대기열(HITL) 등록
3. **백그라운드 최소화 플로팅 필 (Minimized Pill)**:
   - 분석관이 조사 중 다른 알림 로그를 열람할 수 있도록 우측 하단에 타이머가 작동하는 소형 플로팅 뱃지(`inv-minimized-pill`)로 전환 가능.
4. **원클릭 결과 이동 (Smooth Focus & Highlight)**:
   - 조사가 완료되면 모달에 `[✅ 결과 확인하기]` 버튼이 나타나며, 클릭 시 분석 결과 영역으로 부드럽게 스크롤(Smooth Scroll)되고 청록색 링으로 강조 표시됨.

---

## 3. 검증 결과 및 증적

### 3.1 자동화 테스트 추가 및 통과 (`tests/test_dashboard_track2_ux.py`)
- `test_track2_provider_selector_in_html`: 상단 헤더 셀렉터 및 옵션 요소 검증 완료
- `test_track2_investigation_progress_modal_in_html`: 타이머, 프로그레스바, 4단계 스테퍼, 플로팅 필 검증 완료
- `test_track2_provider_select_aliases`: API의 `provider_type`, `model_name` 호환성 검증 완료

```text
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-9.1.1, pluggy-1.6.0
collected 63 items

tests\test_ai_evidence.py ..                                             [  3%]
tests\test_ai_ollama_provider.py .....                                   [ 11%]
tests\test_ai_orchestrator.py .                                          [ 12%]
tests\test_ai_policy_approval.py ....                                    [ 19%]
tests\test_ai_rag.py ..                                                  [ 22%]
tests\test_ai_security.py ....                                           [ 28%]
tests\test_ai_tools.py .....                                             [ 36%]
tests\test_correlation.py .                                              [ 38%]
tests\test_dashboard_ai_api.py ........                                  [ 50%]
tests\test_dashboard_api.py .....                                        [ 58%]
tests\test_dashboard_track2_ux.py ...                                    [ 63%]
tests\test_dashboard_ui_localization.py .......                          [ 74%]
tests\test_detection_tuning.py ..                                        [ 77%]
tests\test_parsers.py ..                                                 [ 80%]
tests\test_pcap_manifest.py .                                            [ 82%]
tests\test_phase31_e2e.py ........                                       [ 95%]
tests\test_threat_intel.py ...                                           [100%]

======================== 63 passed, 1 warning in 3.17s ========================
```

### 3.2 런타임 서비스 상태
- FastAPI Uvicorn 서비스: `http://0.0.0.0:8501` (PID 34756, 정상 가동 중)
- Ollama Localhost 런타임: `127.0.0.1:11434` (Strict Local-only 정상 가동 중)
