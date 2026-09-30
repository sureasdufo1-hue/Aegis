# [AegisAI UI/UX 마스터 프롬프트]
# Datadog & Cloudflare 스타일 「Cloud-Clear Pristine Light」 엔터프라이즈 SOC 대시보드 리디자인 프롬프트 명세서

> **문서 코드:** `PRMT-UIUX-LIGHT-001` (v2.0.0 — Option A 채택)  
> **디자인 컨셉:** **Cloud-Clear Pristine Light (청명한 엔터프라이즈 주간 관제 테마)**  
> **핵심 원칙:** **하늘 사진 배경 전면 배제 (Zero Image Background)**, 100% 솔리드 화이트 카드, 눈 피로 제로, WCAG AAA 명도 대비(7:1 이상) 보장.  
> **프로젝트 대주제:** **「AI for Security + Security for AI」 AegisAI Unified SOC Platform**  
> **벤치마크 대상:** Datadog Cloud SIEM, Cloudflare Radar, Microsoft Sentinel, CrowdStrike Falcon

---

## 1. 프롬프트 개요 및 사용 목적

본 문서는 **기존의 칙칙한 검은색(#000000) 사이버 다크 화면과 배경 사진 투과로 인한 가시성 저하를 모두 극복**하고, Datadog 및 Cloudflare Radar와 같은 **현대적이고 극도로 정갈한 'Cloud-Clear Pristine Light' 엔터프라이즈 SOC 콘솔**을 구현하기 위한 **AI 생성 및 프론트엔드 엔지니어링 마스터 프롬프트**입니다.

이 프롬프트는 ChatGPT, Claude, Cursor, v0, Bolt.new 등의 AI 코딩 어시스턴트나 프론트엔드 엔지니어에게 그대로 전달하여 즉시 최고 등급의 대시보드 코드를 생성할 수 있습니다.

---

## 2. 복사하여 바로 사용하는 마스터 프롬프트 (Copy-and-Paste Master Prompt)

```markdown
# Role & Expertise
당신은 최고 수준의 엔터프라이즈 **Security UI/UX 디자이너 겸 시니어 프론트엔드 엔지니어**다.
기존의 칙칙한 Matrix 스타일 검은색 화면이나, 가독성을 해치는 사진 배경을 일절 배제하고,
**Datadog Cloud SIEM 및 Cloudflare Radar** 수준의 극도로 정갈하고 시인성이 뛰어난
**「Cloud-Clear Pristine Light」 엔터프라이즈 보안관제(SOC) 대시보드**를 구현하라.

---

# 1. 디자인 철학: "Dashboard is a Decision Surface, Not an Artistic Wallpaper"

1. **사진 배경 전면 배제 (Zero Image Background):**
   - 배경에 사진이나 불필요한 질감 텍스처를 일절 넣지 않는다.
   - 캔버스는 은은하고 청명한 미세 슬레이트 오프화이트(`background-color: #F8FAFC; background-image: linear-gradient(180deg, #F0F7FF 0%, #F8FAFC 180px);`)를 사용한다.
2. **100% 솔리드 화이트 카드 (Solid High-Contrast Cards):**
   - 모든 텔레메트리 패널과 카드는 100% 불투명 퓨어 화이트(`background-color: #FFFFFF; border: 1px solid #E2E8F0;`)로 구성하여 배경 블리드스루(Bleed-through)를 원천 차단한다.
3. **WCAG AAA 명도 대비 (Contrast Ratio 7:1 이상):**
   - IP 주소(`10.77.20.50`), 포트 번호, 패킷 바이트, 타임스탬프 등 초정밀 데이터는 깊은 딥 네이비(`color: #0F172A`) 및 슬레이트(`color: #334155`)로 렌더링하여 12시간 교대 근무에도 눈의 피로가 전혀 없어야 한다.
4. **선택적 다크 모드 토글 (Dual-Mode):**
   - 기본값은 `Cloud-Clear Pristine Light`이며, 우측 상단 토글을 통해 CrowdStrike 스타일의 `Charcoal Dark (#0A0E17)`로 1초 내에 전환될 수 있도록 CSS 변수 및 클래스를 설계한다.

---

# 2. 프로젝트 정체성 및 대주제 (Project Theme Integration)

본 대시보드는 **「AI for Security + Security for AI」**를 표방하는 **AegisAI 통합 보안관제 플랫폼**이다.
화면의 모든 위젯과 정보 계층은 다음 두 가지 핵심 축을 명확히 전달해야 한다:

1. **AI for Security (AI 기반 보안관제 고도화):**
   - **Core SOC 텔레메트리:** Suricata 8.0.6 (AF_PACKET 고속 실시간 탐지) + Snort 3.12.2 (오프라인 PCAP 교차 검증).
   - **중앙 SIEM 연동:** Wazuh 4.14.7 + Elasticsearch 8.19.20 (실측 611건 인덱싱).
   - **4단계 공격 킬체인 상태 머신:** Reconnaissance ➔ Initial Access / Exploit ➔ Lateral Movement ➔ C2 Exfiltration.
   - **Grounded AI Copilot:** 사실 기반(Grounding) 침해사고 요약, 위협 가설, 미확인 요소, SOP 플레이북 추천.
   - **Human-in-the-Loop (HITL) 1-Click 승인:** 분석가 사전 승인 티켓 (Single-use 900s Nonce), Dry-Run 방화벽 격리 (`nft add rule inet filter input ip saddr ...`).

2. **Security for AI (AI 시스템 자체 방어 및 거버넌스):**
   - **AI 보안 7대 원칙 (STD-SEC-AI-001) 준수 배지:** 불신(Zero Trust), 최소화, 최소권한, 격리, 검증, 인간통제, 추적성.
   - **AI Security Gateway 인라인 가드레일:** Direct/Indirect Prompt Injection 차단, PII/Secret DLP 정규식 실시간 마스킹.
   - **보호 자산 차단 거부 (PolicyEngine):** 게이트웨이(`10.77.10.1`) 및 SIEM(`10.77.10.30`) 자해 차단(Self-DoS) 원천 방지.
   - **RAG 지식베이스 무결성:** 코사인 유사도 0.65 임계치 필터링 및 5초 스냅샷 롤백.

---

# 3. 색상 토큰 및 타이포그래피 (Color & Typography Tokens)

- **캔버스 배경:** `#F8FAFC` (Slate-50, 부드러운 스카이 틴트 `#F0F7FF` 헤더 그라데이션)
- **카드 표면:** `#FFFFFF` (Solid Pure White, `border: 1px solid #E2E8F0; box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);`)
- **헤더/사이드바:** `#FFFFFF` (Solid White, `border-color: #E2E8F0;`)
- **주요 텍스트:**
  - 제목/헤더: `#0F172A` (Slate-900 / Deep Navy)
  - 본문/라벨: `#334155` (Slate-700)
  - 보조/타임스탬프: `#64748B` (Slate-500)
  - 인라인 코드/IP: `#0284C7` (Sky-700), `#0F172A`, 폰트 `JetBrains Mono`
- **보안 위험도 배지 (Datadog Style Solid Crisp Pills):**
  - **CRITICAL:** 텍스트 `#B91C1C`, 배경 `#FEF2F2`, 테두리 `#FECACA` (Solid Red-50)
  - **HIGH:** 텍스트 `#C2410C`, 배경 `#FFF7ED`, 테두리 `#FED7AA` (Solid Amber-50)
  - **MEDIUM:** 텍스트 `#0369A1`, 배경 `#F0F9FF`, 테두리 `#BAE6FD` (Solid Sky-50)
  - **LOW/INFO:** 텍스트 `#0F766E`, 배경 `#F0FDFA`, 테두리 `#99F6E4` (Solid Teal-50)
  - **SAFE/PASS:** 텍스트 `#15803D`, 배경 `#F0FDF4`, 테두리 `#BBF7D0` (Solid Emerald-50)
- **활성 탭 / 포커스:**
  - 활성 내비게이션: `background-color: #EFF6FF; color: #1D4ED8; border-left: 3px solid #2563EB; font-weight: 700;`

---

# 4. 레이아웃 및 5대 핵심 컴포넌트 설계

### 1. 상단 글로벌 헤더 (Crisp White Enterprise Nav)
- 좌측: 쉴드 아이콘(🛡️) + **AegisAI** 볼드 로고 + `AI for Security × Security for AI` 배지 + `Suricata 8.0.6 · Snort 3.12.2 · Wazuh 4.14.7 · AI 보안 7대 원칙 준수` 메타 태그.
- 중앙: 글로벌 탭 (Dashboard, Monitor, Incidents, Policy, AI Analysis, Reports).
- 우측: 실시간 상태 (`🟢 SOC ONLINE`), 알림 카운트, LLM 선택기 (Mock Baseline / Qwen3.5 9B), **[☀️ Pristine Light / 🌙 Charcoal Dark] 테마 토글 버튼**.

### 2. 최상단 KPI 메트릭 카드 (Solid White KPI Grid)
- 4개의 퓨어 화이트 카드 구성:
  1. **Core SOC Status:** 패킷 수집률 100% 무손실, 로드된 시그니처 52,596개, EVE 스트리밍 상태.
  2. **AI Security Gateway:** 인젝션 차단율 100%, DLP 마스킹 시크릿 20종, 정책 위반 0건.
  3. **Threat Chain Incidents:** 활성 인시던트 수 (예: `INC-10.77.20.50`), 공격 단계, 최고 위험도.
  4. **HITL Dual-Control:** 대기 중인 승인 티켓 (Pending Nonce), 실행 완료된 규칙, 잔여 TTL(60분).

### 3. 실시간 위협 매트릭스 & 이벤트 테이블 (High-Density Telemetry Stream)
- 솔리드 화이트 패널 위에 D3.js 기반 전술 지도 및 실시간 알림 테이블 배치.
- 테이블 헤더는 정갈한 슬레이트 그레이(`#F1F5F9`), 행 간 구분선은 미세 헤어라인(`#F1F5F9`), 호버 시 청량한 연하늘빛(`#F0F7FF`) 하이라이트.

### 4. 4단계 킬체인 파이프라인 리본 (Kill-Chain Stepper)
- Recon ➔ Initial Access ➔ Lateral Movement ➔ C2 Exfiltration의 4단계 스텝퍼.
- 진행 중인 공격 단계는 선명한 솔리드 앰버(`#D97706`)와 부드러운 펄스 배지로 명확히 표시.

### 5. AI Copilot 심층 조사 패널 & 1-Click HITL 승인 콘솔 (Right Drawer)
- 우측 슬라이드 패널 또는 모달.
- 상단: 분석 신뢰도(Confidence 98.5%), 환각률(0.0%), 증적 매핑(`EV-INC-01~18`).
- 본문: 관측된 사실(Observed Facts), 위협 가설, 추천 대응 플레이북.
- 하단: **1-Click 승인 티켓 (APR-xxxx)**, 검토 메모 입력창, 녹색 **[1-Click 승인 및 집행]** 버튼 및 방화벽 CLI 프리뷰 (`nft add rule inet filter input ip saddr ...`).

---

# 5. 프론트엔드 코드 품질 기준

1. **Zero External Image Dependency:** 외부 이미지 없이 순수 HTML/CSS/Tailwind만으로 렌더링되어 로딩 지연이 없어야 함.
2. **반응형 1920x1080 최적화:** 와이드 모니터에서 데이터가 한눈에 들어오는 멀티 컬럼 그리드 지원.
3. **접근성 준수:** 모든 텍스트 명도 대비 4.5:1 이상(WCAG AA/AAA).
4. **상태 관리 영속성:** `localStorage`를 통해 테마 설정(Light/Dark) 및 뷰 모드가 영구 유지됨.
```

---

## 3. 핵심 CSS 스타일 명세 (Cloud-Clear Pristine Light Snippet)

```css
/* ============================================================================== */
/* Datadog & Cloudflare Style "Cloud-Clear Pristine Light" Enterprise Theme        */
/* ============================================================================== */
body.theme-light-pristine {
    background-color: #f8fafc !important;
    background-image: linear-gradient(180deg, #f0f7ff 0%, #f8fafc 180px, #f8fafc 100%) !important;
    color: #0f172a !important;
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
}

body.theme-light-pristine .soc-header {
    background-color: #ffffff !important;
    border-bottom: 1px solid #e2e8f0 !important;
    box-shadow: 0 1px 3px 0 rgba(15, 23, 42, 0.05) !important;
}

body.theme-light-pristine .soc-sidebar {
    background-color: #ffffff !important;
    border-right: 1px solid #e2e8f0 !important;
    box-shadow: 1px 0 3px 0 rgba(15, 23, 42, 0.03) !important;
}

body.theme-light-pristine .soc-panel {
    background-color: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.04), 0 1px 2px -1px rgba(0, 0, 0, 0.04) !important;
    color: #0f172a !important;
    border-radius: 8px !important;
}

body.theme-light-pristine .soc-panel-header {
    background-color: #fcfdfe !important;
    border-bottom: 1px solid #e2e8f0 !important;
    color: #0f172a !important;
    font-weight: 700 !important;
}

body.theme-light-pristine .soc-table th {
    background-color: #f1f5f9 !important;
    color: #475569 !important;
    border-bottom: 1px solid #cbd5e1 !important;
    font-weight: 700 !important;
}

body.theme-light-pristine .soc-table td {
    border-bottom: 1px solid #f1f5f9 !important;
    color: #0f172a !important;
}

body.theme-light-pristine .soc-table tr:hover {
    background-color: #f0f7ff !important;
}

/* High Readability Severity Pills (Datadog Style) */
body.theme-light-pristine .sev-critical {
    color: #b91c1c !important;
    background-color: #fef2f2 !important;
    border: 1px solid #fecaca !important;
    font-weight: 700 !important;
}
body.theme-light-pristine .sev-high {
    color: #c2410c !important;
    background-color: #fff7ed !important;
    border: 1px solid #fed7aa !important;
    font-weight: 700 !important;
}
body.theme-light-pristine .sev-medium {
    color: #0369a1 !important;
    background-color: #f0f9ff !important;
    border: 1px solid #bae6fd !important;
    font-weight: 700 !important;
}
body.theme-light-pristine .sev-low {
    color: #0f766e !important;
    background-color: #f0fdfa !important;
    border: 1px solid #99f6e4 !important;
    font-weight: 700 !important;
}
body.theme-light-pristine .sev-info {
    color: #15803d !important;
    background-color: #f0fdf4 !important;
    border: 1px solid #bbf7d0 !important;
    font-weight: 700 !important;
}
```

---

## 4. 라이브 대시보드 실측 확인

현재 가동 중인 로컬 대시보드(`http://localhost:8000/`)에 본 Cloud-Clear Pristine Light 스타일이 기본값으로 적용되었습니다.

1. 브라우저에서 `http://localhost:8000/` 접속.
2. 뭉개짐이나 시각적 간섭을 유발하던 사진 배경이 완전히 사라지고, **Datadog 스타일의 정갈한 솔리드 화이트 카드와 고대비 텍스트**로 가시성이 100% 확보되었는지 확인.
3. 상단 헤더 우측의 **[☀️ Pristine Light]** 버튼을 통해 언제든지 CrowdStrike 스타일의 다크 모드와 토글 가능.
