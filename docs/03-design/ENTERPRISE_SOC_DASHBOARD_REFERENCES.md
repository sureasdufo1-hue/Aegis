# [AegisAI UI/UX 벤치마크]
# 엔터프라이즈급 SOC 관제 대시보드 레퍼런스 분석 및 UI/UX 개선 프레임워크

> **문서 코드:** `REF-UIUX-SOC-001` (v1.0.0)  
> **목적:** 엔터프라이즈급 글로벌 보안관제 솔루션(CrowdStrike, Microsoft Sentinel, Datadog, Elastic Security, Palo Alto Cortex)의 UI/UX 레퍼런스를 수집·분석하여, 가시성(Visibility)과 전문성을 극대화한 차세대 AegisAI 대시보드 리디자인 기준선 수립.  
> **핵심 해결 과제:** 배경 사진 투과로 인한 가시성 저하(Low Contrast) 원천 해결, 데이터 고밀도성(Data Density) 확보, AI for Security × Security for AI 주제의 직관적 표출.

---

## 1. 문제 분석: 왜 단순 사진 배경 + 글래스모피즘이 SOC에서 실패하는가?

현재 상태에서 발생한 **가시성 저하(Visibility Failure)**는 보안 엔지니어링 및 인지심리학적 관점에서 필연적인 현상입니다:

```
[ 문제점 1: 텍스트-배경 간 명도 대비 간섭 (Visual Interference) ]
- 현상: 뭉게구름의 백색 영역과 푸른 하늘 경계면이 반투명 유리 패널 뒤로 비치면서, 
        동일한 패널 내에서도 텍스트가 놓인 위치에 따라 명도 대비가 수시로 변함.
- 영향: IP 주소(10.77.20.50), 패킷 바이트, 타임스탬프 등 초정밀 데이터 판독 시 심각한 눈의 피로 유발.

[ 문제점 2: 차트 및 시각화 데이터의 기준선(Baseline) 왜곡 ]
- 현상: Line Chart, Bar Chart, Geo Map 뒤로 구름 질감이 투과되어 
        차트의 축(Axis)과 그리드 라인이 배경의 구름 경계선과 시각적으로 혼동됨.

[ 문제점 3: 보안 위험도(Severity) 컬러 신호의 희석 ]
- 현상: High(호박색), Medium(하늘색) 배지가 푸른 하늘 배경과 색상환(Color Wheel) 상에서 
        인접하여 경보(Alert)의 긴급성이 한눈에 들어오지 않음 (Glanceability 저하).
```

> **엔터프라이즈 SOC의 대원칙:**  
> **"Dashboard is an Operational Decision Surface, Not an Artistic Wallpaper."**  
> (관제 대시보드는 심미적 배경화면이 아니라, 1초 안에 침해사고를 판별하고 차단하는 '운영 의사결정 작업대'여야 한다.)

---

## 2. 글로벌 엔터프라이즈 5대 관제 대시보드 레퍼런스 정밀 분석

### 2.1 [Reference 1] CrowdStrike Falcon Console
- **주요 특징:**
  - **색상 체계:** 짙은 차콜 슬레이트(`#0A0E17`, `#111827`) + 하이퍼 사이언(`#00E5FF`) + 크림슨 레드(`#FF3860`).
  - **정보 계층:** 좌측 64px 슬림 아이콘 레일, 상단 글로벌 위협 포스처 바, 중앙 4단계 킬체인 트리아지 큐.
  - **핵심 장점:** **Threat Graph & Living Model**. 불필요한 장식 그래픽을 전면 배제하고, 경보 클릭 시 인과관계 프로세스 트리(Process Tree)가 즉각 오버레이됨.
- **AegisAI 적용점:**
  - 다단계 공격 인시던트(`INC-10.77.20.50`) 클릭 시 프로세스/네트워크 연관 관계를 직관적으로 펼치는 사이드 드로어 구조 차용.

---

### 2.2 [Reference 2] Microsoft Sentinel & Defender XDR
- **주요 특징:**
  - **색상 체계:** Microsoft Fluent Design. 고대비 솔리드 카드(`#FFFFFF` in Light / `#1F1F1F` in Dark) + 아주르 블루(`#0078D4`) 악센트.
  - **레이아웃:** 3분할 캔버스.
    - 좌측 (30%): 실시간 우선순위 인시던트 큐 (Severity, Owner, Status).
    - 중앙 (45%): 사고 조사 타임라인 및 ATT&CK TTP 매핑 그래프.
    - 우측 (25%): Security Copilot AI 추천 조치 및 1-Click 실행 패널.
  - **핵심 장점:** 단일 화면에서 컨텍스트 전환(Context Switching) 없이 **경보 확인 ➔ AI 요약 ➔ 방화벽 격리**가 30초 내에 완결됨.
- **AegisAI 적용점:**
  - 우리가 구현한 `AegisAI HITL 1-Click 승인` 프로세스를 Sentinel의 우측 Copilot 액션 드로어 형태로 완벽히 일치시킬 수 있음.

---

### 2.3 [Reference 3] Datadog Cloud SIEM & Security Platform
- **주요 특징:**
  - **색상 체계:** 업계 최고의 라이트 테마 가독성. 캔버스 배경 오프화이트(`#F8FAFC`), 카드 표면 솔리드 화이트(`#FFFFFF`), 헤어라인 보더(`#E2E8F0`), 깊은 네이비 텍스트(`#0F172A`).
  - **정보 밀도:** 작은 패딩(4px~8px), 모노스페이스 IP 주소, 미니 스파크라인(Sparklines) 인라인 배치.
  - **핵심 장점:** 12시간 교대 근무에도 눈의 피로가 전혀 없는 완벽한 명도 대비(Contrast Ratio 7:1 이상)와 청량한 시인성.
- **AegisAI 적용점:**
  - 사용자가 요청한 **"맑고 청명한 하늘"의 느낌을 Datadog 식의 'Cloud-Clear Pristine Light' 테마로 승화**시킬 수 있는 최고의 레퍼런스.

---

### 2.4 [Reference 4] Elastic Security (Kibana SIEM) & Wazuh 4.x
- **주요 특징:**
  - **색상 체계:** 다크 슬레이트 기반의 데이터 집중형 콘솔.
  - **레이아웃:** 상단 글로벌 타임 레인지 피커(`Last 15 minutes`), KQL/Lucene 검색 바, 시계열 이벤트 히스토그램, 하단 EVE/로그 테이블.
  - **핵심 장점:** 원시 로그(Raw JSON)와 집계 데이터(Aggregate Metrics) 간의 1초 피벗팅(Pivoting).
- **AegisAI 적용점:**
  - 우리가 이미 구축한 Elasticsearch 8.19.20(611건 적재) 및 Suricata EVE 로그와의 1:1 연동 데이터 테이블 레이아웃 최적화.

---

### 2.5 [Reference 5] Palo Alto Networks Cortex XSOAR / XSIAM
- **주요 특징:**
  - **색상 체계:** 모던 클라우드 네이비 + 앰버 골드 + 에메랄드 그린.
  - **핵심 장점:** **Automated Playbook Execution & Analyst Approval Gate**. 자동화된 플레이북 흐름 중 고위험 작업에서 일시 정지(Pause)되고 분석가의 서명을 요구하는 HITL 거버넌스 시각화.
- **AegisAI 적용점:**
  - `STD-SEC-AI-001`의 제6원칙(인간통제)과 제7원칙(추적성)을 플레이북 스텝퍼 형태로 대시보드에 표출.

---

## 3. 종합 비교 매트릭스 (Enterprise SOC Dashboard Benchmarks)

| 비교 항목 | CrowdStrike Falcon | MS Sentinel | Datadog Cloud SIEM | Elastic Security | Palo Alto Cortex | **AegisAI 목표 모델** |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **주요 테마** | Cyber Dark | Fluent Dark/Light | **Cloud-Clear Light** | Dark Analytics | Cloud Navy | **Aegis Dual-Mode (Sky/Dark)** |
| **캔버스 배경** | 솔리드 차콜 | 솔리드 다크/화이트 | **미세 슬레이트 오프화이트** | 솔리드 다크 | 미세 네이비 틴트 | **솔리드 글래스 + 상단 대기광** |
| **카드 표면** | 100% 불투명 솔리드 | 100% 불투명 솔리드 | **100% 불투명 화이트** | 100% 불투명 | 100% 불투명 | **96% 불투명 솔리드 카드** |
| **배경 사진 활용**| 절대 사용 안 함 | 배너/로그인에만 사용 | **헤더 앰비언트에만 사용** | 사용 안 함 | 사용 안 함 | **상단 헤더 앰비언트 메시** |
| **가시성(Contrast)**| 극상 (AAA) | 극상 (AAA) | **극상 (7:1 이상)** | 상 (AA) | 극상 (AAA) | **극상 (WCAG AAA 준수)** |
| **AI 기능 표출** | Charlotte AI 바 | Copilot 사이드바 | Bits AI 추천 | Elastic AI 어시스턴트 | XSIAM 자율 엔진 | **Grounded Copilot + 7대 원칙** |
| **HITL 승인 UI** | 원클릭 격리 | 인시던트 액션 버튼 | 인시던트 티켓 연동 | 알림 규칙 액션 | **플레이북 승인 게이트** | **1-Click Nonce 승인 큐** |

---

## 4. 엔터프라이즈는 '하늘/구름/Aegis' 컨셉을 어떻게 시각화하는가? (4대 모던 기법)

글로벌 디자인 시스템(Apple macOS, Cloudflare Radar, Vercel, Datadog)은 사진을 본문 뒤에 깔지 않고 다음과 같이 고급스럽게 소화합니다:

```
[ 기법 1: Top Hero Ambient Sky Mesh (상단 대기광 헤더) ]
- 전체 본문 뒤에 사진을 깔지 않고, 상단 120px 헤더 및 브랜딩 영역에만 
  제공해주신 청명한 하늘과 구름의 대기광(Atmospheric Sky Glow)을 유려하게 블러 처리하여 배치.
- 본문 데이터 영역(테이블, 차트)은 100% 솔리드 슬레이트/화이트로 유지하여 
  가시성을 완벽하게 보장하면서도 상단에서 하늘의 청량한 아이덴티티를 획득.

[ 기법 2: Cloud-Clear Pristine Light Canvas (청명한 주간 관제 테마) ]
- 배경을 '사진'이 아닌 '하늘의 빛을 머금은 미세 슬레이트 블루(#F0F9FF ~ #F8FAFC)'로 설정.
- 카드 패널은 완벽한 솔리드 퓨어 화이트(#FFFFFF)에 1px 정밀 보더(#BAE6FD)와 
  부드러운 스카이 블루 섀도우(rgba(14, 165, 233, 0.08))를 적용하여 구름 위의 청명한 맑음을 표현.

[ 기법 3: High-Contrast Solid Glass (96% 불투명 솔리드 글래스) ]
- 글래스모피즘을 쓰더라도 투명도를 10%~20%로 두지 않고, 96% 이상의 고농도 화이트/슬레이트로 두어 
  배경의 구름 텍스처가 글자를 침범하지 못하도록 차단(Zero Bleed-through).

[ 기법 4: Aegis Sky Accent System (천상적 기능성 컬러링) ]
- Sky Blue(#0284C7, #0EA5E9)는 '정상 텔레메트리 및 관제 링크'의 메인 악센트로 사용.
- Cloud Teal(#0D9488)은 'AI 보안 게이트웨이 및 암호학적 Nonce 안전 상태'에 사용.
- 대비되는 Crimson(#DC2626)과 Amber(#D97706)는 위협 탐지 시 극적인 시인성을 발휘.
```

---

## 5. 차세대 AegisAI 대시보드 리디자인 4단계 로드맵

1. **Phase 1: 가시성 회복 (Visibility Restoration)**
   - 본문 작업대 영역의 배경을 고대비 솔리드 캔버스로 분리하여 IP 및 패킷 데이터 판독성 100% 회복.
2. **Phase 2: 상단 앰비언트 스카이 헤더 구축 (Ambient Sky Hero Integration)**
   - 제공해주신 하늘 이미지를 상단 글로벌 브랜딩 바 및 헤어로 배치하여 프로젝트의 심미성과 청량감 극대화.
3. **Phase 3: 3분할 엔터프라이즈 레이아웃 적용 (Sentinel/Datadog 구조)**
   - 좌측: 4단계 공격 킬체인 인시던트 큐 (`INC-10.77.20.50`).
   - 중앙: Suricata 8.0.6 & Elasticsearch 8.19.20 원시 이벤트 스트림 및 차트.
   - 우측: Grounded AI Copilot + AI 보안 7대 원칙 준수 위젯 + 1-Click HITL 승인 콘솔.
4. **Phase 4: 주간/야간 원클릭 스위칭 (Dual Enterprise Mode)**
   - `☀️ Cloud-Clear Light (Datadog 스타일 청명 관제)` ↔ `🌙 Deep Azure Dark (CrowdStrike 스타일 야간 관제)`
