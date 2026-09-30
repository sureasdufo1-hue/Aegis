# [AegisAI UI/UX 마스터 프롬프트]
# 천상적 스카이 글래스모피즘(Celestial Sky Glassmorphism) SOC 콘솔 리디자인 프롬프트 명세서

> **문서 코드:** `PRMT-UIUX-SKY-001` (v1.0.0)  
> **기준 배경 이미지:** `C:\Users\user\Downloads\Codex 이미지 2026년 9월 30일 오후 02_25_43.png` (`dashboard/static/sky_bg.png`)  
> **프로젝트 대주제:** **「AI for Security + Security for AI」 AegisAI Unified SOC Platform**  
> **적용 기술 스택:** HTML5, Tailwind CSS, Vanilla JS / Vue / React, Chart.js, D3.js Geo Map

---

## 1. 프롬프트 개요 및 사용 목적

본 문서는 **기존의 무겁고 어두운 블랙 일색의 사이버 다크(Cyber Dark) SOC 대시보드를 탈피**하고, 제공된 청명한 낮 하늘과 부드러운 뭉게구름 이미지에 완벽히 조화되는 **'천상적 스카이 글래스모피즘(Celestial Sky Glassmorphism)'** 스타일로 UI 전체를 리디자인하기 위한 **AI 생성 및 엔지니어링 프롬프트**입니다.

이 프롬프트는 ChatGPT, Claude, Cursor, v0, Bolt.new 등의 AI 코딩 어시스턴트나 UI/UX 디자이너에게 그대로 전달하여 고품질의 대시보드 코드를 생성하도록 설계되었습니다.

---

## 2. 복사하여 바로 사용하는 마스터 프롬프트 (Copy-and-Paste Master Prompt)

```markdown
# Role & Expertise
당신은 최고 수준의 엔터프라이즈 **Security UI/UX 디자이너 겸 시니어 프론트엔드 엔지니어**다.
기존의 획일적인 Matrix 스타일의 칙칙한 검은색(#000000) 관제 화면을 완전히 탈피하여,
제공된 **맑고 광활한 푸른 하늘과 뭉게구름 배경 이미지**를 기반으로 한 독창적이고 고급스러운
**「Celestial Sky Glassmorphism (천상적 스카이 글래스모피즘)」 보안관제(SOC) 대시보드**를 구현하라.

---

# 1. 프로젝트 정체성 및 대주제 (Project Theme)

본 대시보드는 **「AI for Security + Security for AI」**를 표방하는 **AegisAI 통합 보안관제 플랫폼**이다.
UI의 모든 시각적 요소와 컴포넌트는 다음 두 가지 핵심 축을 명확히 전달해야 한다:

1. **AI for Security (AI 기반 보안관제 고도화):**
   - 네트워크 침입탐지 엔진 (Suricata 8.0.6 AF_PACKET 실시간 캡처 + Snort 3.12.2 오프라인 검증)
   - 중앙 SIEM 상관분석 (Wazuh 4.14.7 + Elasticsearch 8.19.20 611건 적재)
   - 4단계 공격 킬체인 상태 머신 (Reconnaissance ➔ Initial Access ➔ Lateral Movement ➔ C2)
   - 로컬 LLM 기반 AI SOC Copilot (사실 기반 Grounding, 침해사고 요약, 플레이북 권고)
   - Human-in-the-Loop (HITL) 1-Click 승인 및 임시 방화벽 격리 (Single-use 900s Nonce)

2. **Security for AI (AI 시스템 자체 방어 및 거버넌스):**
   - **AI 보안 7대 원칙 (STD-SEC-AI-001) 준수 배지:** 불신(Zero Trust), 최소화, 최소권한, 격리, 검증, 인간통제, 추적성.
   - **AI Security Gateway 가드레일:** Direct/Indirect Prompt Injection 차단, PII/Secret DLP 마스킹.
   - **보호 자산 차단 거부 (PolicyEngine):** 게이트웨이 및 SIEM 자해 차단(Self-DoS) 원천 방지.
   - **RAG 지식베이스 무결성:** 코사인 유사도 0.65 임계치 필터링 및 5초 스냅샷 롤백.

---

# 2. 기준 이미지 기반 디자인 언어: Celestial Sky Glassmorphism

제공된 하늘 이미지(`sky_bg.png`)는 **상단의 선명한 천상 블루(Vivid Azure Sky)에서 하단의 부드럽고 따스한 햇살 가득한 지평선 및 백색 구름(Ethereal Mist & White Clouds)**으로 이어지는 유려한 그라데이션을 가지고 있다.

### 2.1 색상 토큰 (Color Tokens)
- **배경 (Canvas Background):**
  - 고정 배경: `url('/static/sky_bg.png') no-repeat center center fixed; background-size: cover;`
  - 은은한 대기광 그라데이션 오버레이: `linear-gradient(180deg, rgba(224, 242, 254, 0.2) 0%, rgba(255, 255, 255, 0.4) 100%)`
- **글래스 패널 (Glass Panels & Surfaces):**
  - 카드/패널 바탕: `rgba(255, 255, 255, 0.82)` ~ `rgba(255, 255, 255, 0.90)`
  - 블러 필터: `backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);`
  - 테두리: `border: 1px solid rgba(255, 255, 255, 0.85);`
  - 그림자: `box-shadow: 0 10px 30px rgba(37, 99, 235, 0.08), 0 1px 3px rgba(0, 0, 0, 0.04);`
- **타이포그래피 (High-Contrast Celestial Slate):**
  - 제목/헤더: `#0F172A` (Deep Celestial Slate / Navy)
  - 본문/라벨: `#334155` (Slate 700)
  - 보조/타임스탬프: `#64748B` (Slate 500)
  - 코드/단언 텍스트: `#0369A1` (Azure Blue), `#0D9488` (Teal), `JetBrains Mono` 폰트
- **보안 위험도 배지 (Vibrant Translucent Severity Badges):**
  - **CRITICAL:** 텍스트 `#DC2626`, 배경 `rgba(254, 226, 226, 0.85)`, 테두리 `rgba(248, 113, 113, 0.5)` (Sunset Coral)
  - **HIGH:** 텍스트 `#D97706`, 배경 `rgba(254, 243, 199, 0.85)`, 테두리 `rgba(251, 191, 36, 0.5)` (Solar Amber)
  - **MEDIUM:** 텍스트 `#0284C7`, 배경 `rgba(224, 242, 254, 0.85)`, 테두리 `rgba(56, 189, 248, 0.5)` (Sky Topaz)
  - **LOW/INFO:** 텍스트 `#0D9488`, 배경 `rgba(204, 251, 241, 0.85)`, 테두리 `rgba(45, 212, 191, 0.5)` (Cloud Teal)
  - **SAFE/PASS:** 텍스트 `#059669`, 배경 `rgba(209, 250, 229, 0.85)`, 테두리 `rgba(52, 211, 153, 0.5)` (Emerald Horizon)

---

# 3. 레이아웃 및 6대 핵심 컴포넌트 설계

### 1. 상단 글로벌 헤더 (Floating Glass Header)
- 좌측: 쉴드 아이콘(🛡️) + **AegisAI** 타이틀 + `AI for Security × Security for AI` 배지 + 엔진 태그 (`Suricata 8.0.6 · Snort 3.12.2 · Wazuh 4.14.7 · 7대 원칙 준수`).
- 중앙: 탭 내비게이션 (Dashboard, Monitor, Incidents, Policy, AI Analysis, Reports) - 활성 탭은 선명한 Sky Blue 필(`bg-sky-500/20 text-sky-800 font-bold border-b-2 border-sky-600`).
- 우측: 실시간 텔레메트리 상태 배지 (`🟢 SOC ONLINE`), 알림 카운트, LLM 선택기 (Mock Baseline / Qwen3.5 9B), **[☀️ Sky Mode / 🌙 Dark Mode] 테마 전환 토글 버튼**.

### 2. 최상단 KPI 메트릭 카드 (Frosted Glass KPI Cards)
- 4개의 플로팅 글래스 카드 구성:
  1. **Core SOC Status:** 실시간 패킷 수집률 (100% 무손실), 활성 IDS 룰 (52,596개), EVE 로그 스트림.
  2. **AI Security Gateway:** 프롬프트 인젝션 차단율 (100%), DLP 마스킹 비밀번호 (20종), 차단 정책 상태.
  3. **Threat Chain Incidents:** 다단계 공격 인시던트 수 (예: `INC-10.77.20.50`), 최고 위험도(HIGH), 킬체인 단계.
  4. **HITL Dual-Control:** 대기 중인 승인 티켓 (Pending Nonce), 실행된 격리 규칙(Executed), 잔여 TTL.

### 3. 실시간 인터랙티브 위협 매트릭스 & 지도 (Tactical Threat Canvas)
- 어두운 배경 대신, 반투명한 화이트/블루 반사판 위에 D3.js 기반 전술 지도 및 실시간 공격 벡터 궤적이 청량한 사이언/에메랄드/크림슨 광선으로 투사됨.
- 스캔라인 및 펄스 효과가 구름 위를 부유하는 홀로그램처럼 연출됨.

### 4. 4단계 다단계 킬체인 파이프라인 뷰 (Kill-Chain Progression Ribbon)
- 정찰(Recon) ➔ 초기 침투(Initial Access) ➔ 측면 이동(Lateral) ➔ C2 유출(Exfiltration)의 4단계가 구름 형태의 부드러운 스텝퍼로 시각화.
- 진행 중인 공격 단계는 펄스 발광 애니메이션과 함께 선명한 호박색(Amber)으로 강조.

### 5. AI Copilot 심층 조사 패널 (Grounded AI Investigation Drawer)
- 반투명 아크릴 글래스 질감의 우측 드로어 또는 모달.
- 상단: 분석 신뢰도 게이지 (Confidence Score 98.5%), 환각률 (0.0%), Grounding 증적 매핑 (`EV-INC-01~18`).
- 본문: 관측된 사실(Observed Facts), 위협 가설(Hypotheses), 미확인 요소(Unknowns), 추천 플레이북.
- 하단: **1-Click 승인 티켓 (APR-xxxx)** 및 방화벽 CLI 프리뷰 (`nft add rule inet filter input ip saddr 10.77.20.50 counter drop`).

### 6. AI 보안 7대 원칙 준수 상태 위젯 (AI Governance Widget)
- 대시보드 사이드바 또는 하단에 배치된 7대 원칙 인디케이터:
  - P1. 불신(Zero Trust) ✅
  - P2. 최소화(Minimization) ✅
  - P3. 최소권한(Least Privilege) ✅
  - P4. 격리(Isolation) ✅
  - P5. 검증(Verification) ✅
  - P6. 인간통제(HITL) ✅
  - P7. 추적성(Traceability) ✅

---

# 4. 프론트엔드 코드 요구사항

1. **순수 CSS 글래스모피즘 클래스 제공:**
   - `.glass-panel`, `.glass-header`, `.glass-card`, `.glass-modal`
   - 크로스 브라우징을 위해 `-webkit-backdrop-filter` 및 표준 `backdrop-filter` 동시 선언.
2. **테마 전환(Theme Toggle) 스크립트:**
   - `localStorage`를 연동하여 `theme-sky-glass`와 `theme-twilight-dark` 모드 간 1초 이내 무깜빡임 전환 지원.
3. **고해상도 반응형 그리드:**
   - 1920x1080 데스크톱 풀스크린뿐만 아니라 모바일/태블릿에서도 글래스 카드들이 유연하게 리플로우되도록 설계.
4. **접근성(WCAG AA) 명도 대비 보장:**
   - 흰색 반투명 배경 위에서도 모든 텍스트가 명도 대비 4.5:1 이상을 유지하도록 `#0F172A` 및 `#1E293B`의 짙은 슬레이트 컬러를 채택할 것.
```

---

## 3. 핵심 CSS 스타일 명세 (Sky Glassmorphism CSS Snippet)

아래는 본 대시보드에 실제로 적용된 스카이 글래스모피즘의 핵심 CSS 정의입니다:

```css
/* ============================================================================== */
/* Celestial Sky Glassmorphism Theme (sky_bg.png 기반)                           */
/* ============================================================================== */
body.theme-sky-glass {
    background: url('/static/sky_bg.png') no-repeat center center fixed !important;
    background-size: cover !important;
    color: #0f172a !important;
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
}

/* Floating Glass Header */
body.theme-sky-glass .soc-header {
    background: rgba(255, 255, 255, 0.88) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border-bottom: 1px solid rgba(186, 230, 253, 0.8) !important;
    box-shadow: 0 4px 25px rgba(37, 99, 235, 0.08) !important;
}

/* Frosted Acrylic Sidebar */
body.theme-sky-glass .soc-sidebar {
    background: rgba(255, 255, 255, 0.82) !important;
    backdrop-filter: blur(24px) !important;
    -webkit-backdrop-filter: blur(24px) !important;
    border-right: 1px solid rgba(186, 230, 253, 0.7) !important;
    box-shadow: 2px 0 20px rgba(37, 99, 235, 0.06) !important;
}

/* Glass Card & Modal Panels */
body.theme-sky-glass .soc-panel,
body.theme-sky-glass .soc-card {
    background: rgba(255, 255, 255, 0.88) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border: 1px solid rgba(255, 255, 255, 0.9) !important;
    box-shadow: 0 10px 30px rgba(37, 99, 235, 0.09), 0 1px 3px rgba(0, 0, 0, 0.05) !important;
    color: #0f172a !important;
    border-radius: 12px;
}

/* Card Header with Soft Azure Glow */
body.theme-sky-glass .soc-panel-header {
    background: rgba(240, 249, 255, 0.92) !important;
    border-bottom: 1px solid rgba(186, 230, 253, 0.7) !important;
    color: #0f172a !important;
    font-weight: 700;
}

/* High-Contrast Crisp Tables */
body.theme-sky-glass .soc-table th {
    background: rgba(224, 242, 254, 0.9) !important;
    color: #0369a1 !important;
    border-bottom: 1px solid rgba(186, 230, 253, 0.8) !important;
}

body.theme-sky-glass .soc-table td {
    border-bottom: 1px solid rgba(241, 245, 249, 0.9) !important;
    color: #1e293b !important;
}

body.theme-sky-glass .soc-table tr:hover {
    background: rgba(224, 242, 254, 0.45) !important;
}

/* Active Nav Pill */
body.theme-sky-glass .nav-item-active {
    background: rgba(14, 165, 233, 0.18) !important;
    color: #0284c7 !important;
    border-left: 3px solid #0284c7 !important;
    font-weight: 700 !important;
}
```

---

## 4. 프롬프트 적용 결과 및 라이브 확인 방법

1. **정적 이미지 저장:** `dashboard/static/sky_bg.png`에 사용자 원본 하늘 이미지가 복사·배치되었습니다.
2. **라이브 대시보드 반영:** `dashboard/templates/index.html`에 Celestial Sky Glassmorphism 스타일 및 테마 전환기가 탑재되었습니다.
3. **직접 접속 확인:**
   - 브라우저에서 `http://localhost:8000/` 접속.
   - 상단 우측의 **[☀️ Sky Theme]** 버튼을 통해 푸른 하늘 바탕의 글래스모피즘 테마와 클래식 다크 테마를 즉시 전환할 수 있습니다.
