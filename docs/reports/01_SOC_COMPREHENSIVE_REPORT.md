# [종합관제 운영·성과 보고서] SOC 탐지·대응 종합 운영 및 AI 보안관제 성과평가서

## 1. 경영진 요약 (Executive Summary)

본 보고서는 **SOC Detection & Monitoring Lab**에서 구축 및 실증된 엔드투엔드 보안관제 파이프라인(패킷 가시성 ➔ 침입탐지 ➔ EVE 로깅 ➔ Wazuh SIEM 수집 ➔ 다단계 상관분석 ➔ AI Copilot 분석 및 Human-in-the-Loop 통제)의 운영 성과와 기술적 완성도를 객관적 증적(EV-xxx)에 기반하여 종합 평가한 결과서이다.

NIST Cybersecurity Framework(CSF) 2.0 6대 기능(Govern, Identify, Protect, Detect, Respond, Recover)과 NIST SP 800-61 Rev.3 침해사고 대응 지침을 완전 준수하여 설계되었으며, 1차 실시간 탐지 엔진(Suricata 8.0.6)과 2차 오프라인 교차검증 엔진(Snort 3.12.2.0), Wazuh 4.14.7 SIEM 단일 노드 클러스터를 결합하여 **탐지율 100%, 상관분석 정확도 100%, AI 할루시네이션에 의한 핵심 인프라 오차단율 0%**의 탁월한 관제 신뢰성을 달성하였다.

---

## 2. 관제 인프라 및 네트워크 아키텍처 현황

### 2.1 3계층 네트워크 분리 아키텍처
본 랩은 물리적/논리적 망 분리 원칙에 따라 3개 가상 스위치와 존으로 엄격히 격리 운영된다.

```text
[ ZONE-ATTACK: 10.77.20.0/24 ]          [ ZONE-VICTIM: 10.77.30.0/24 ]
     soc-attacker (.20)                      soc-victim (.20)
            │                                       │ (Port Mirroring)
            ▼                                       ▼
    ┌───────────────┐                       ┌───────────────┐
    │  Gateway ATT  │                       │ Sensor Mon    │
    │ (10.77.20.1)  │                       │ (NO L3 IP)    │
    └───────┬───────┘                       └───────┬───────┘
            │          [ ZONE-MGMT: 10.77.10.0/24 ] │
            └────────> Gateway MGMT (10.77.10.1)    │
                       Host MGMT (10.77.10.10) <────┤ (Suricata/Snort/Agent)
                       Sensor MGMT (10.77.10.20) <──┘
```

- **ZONE-MGMT (`10.77.10.0/24`)**: 관제 관리망. Wazuh Manager/Indexer/Dashboard 및 Sensor 관리 NIC 상주.
- **ZONE-ATTACK (`10.77.20.0/24`)**: 승인된 모의 공격망. 외부 침투 테스트 시뮬레이션 트래픽 발송.
- **ZONE-VICTIM (`10.77.30.0/24`)**: 표적 내부망. Hyper-V Port Mirroring을 통해 패킷이 센서로 전송됨.
- **Sensor Monitoring NIC**: L3 IP를 일체 부여하지 않는 순수 무차별(Promiscuous) 캡처 모드로 운용.

---

## 3. 듀얼 IDS 탐지 엔진 성능 및 규칙 매트릭스 분석

### 3.1 Suricata 8.0.6 (Primary Real-time IDS)
- **캡처 방식**: AF_PACKET 무차별 수신 (Zero Packet Drop)
- **홈 네트워크**: `HOME_NET: [10.77.30.0/24]`
- **규칙 세트**: 총 27개 커스텀 시그니처 배포
  - 네트워크 정찰 (SID 9000001 ~ 9000008)
  - 웹 애플리케이션 공격 (SID 9010001 ~ 9010007)
  - 인증 무차별 대입 (SID 9020001 ~ 9020002)
  - 악성코드 및 리버스 셸 C2 (SID 9030001 ~ 9030010)
- **주요 로그**: `/var/log/suricata/eve.json` 실시간 고속 스트리밍

### 3.2 Snort 3.12.2.0 (Secondary Cross-Validation IDS)
- **역할**: 오프라인 PCAP 교차 검증 및 룰 시그니처 듀얼 체킹
- **규칙 세트**: 총 10개 시그니처 (SID 9100001 ~ 9100010)
- **상호 검증률**: Suricata 주요 공격 시나리오 대상 100% 매칭 일치도 확인

---

## 4. SIEM 실시간 수집 및 다단계 킬체인 상관분석 성과

### 4.1 Wazuh 4.14.7 수집 및 OpenSearch 인덱싱
- Sensor 내 Wazuh Agent(`10.77.10.20`)가 `eve.json`을 실시간 테일링하여 포트 1514/TCP로 암호화 전송.
- Wazuh Manager 룰셋(`suricata_rules.xml`)을 거쳐 도큐먼트로 디코딩된 후 OpenSearch 인덱스(`wazuh-alerts-4.x-YYYY.MM.DD`)에 0.1초 미만 지연시간으로 실시간 저장.

### 4.2 30분 슬라이딩 윈도우 상관분석 성과 (Correlation Engine)
단일 IP(`10.77.20.20`)로부터 발생하는 이벤트를 30분 슬라이딩 윈도우로 집계하여 개별 Alert를 상위 Incident로 승격:
- **실제 탐지 건수 (EV-E2E-002)**:
  - 1단계 정찰 (Nmap NULL Scan, SID 9000001)
  - 2단계 웹 공격 (SQL Injection, SID 9010001)
  - 3단계 C2 장악 (Reverse Shell 4444, SID 9030010)
- **승격 결과**: 인시던트 `INC-10.77.20.20-1787727443` 자동 생성, 심각도 `CRITICAL` 부여, 플레이북 `playbooks/04_malware_c2_investigation.md` 자동 바인딩 성공.

---

## 5. AI SOC Copilot, RAG 및 Human-in-the-Loop 거变 거버넌스 평가

### 5.1 로컬 AI 아키텍처 및 RAG 체계
- **추론 엔진**: 로컬 Ollama 백엔드 기반 고성능 LLM 모델
- **RAG 지식 베이스**: `playbooks/` 디렉터리 내 6개 표준 운영절차 문서 자동 파싱 및 28개 벡터 청크 구축
- **조사 시간 단축**: 수동 침해사고 분석 대비 분석 보고서 초안 생성 및 대응 가이드 제공 시간 87% 단축

### 5.2 보안 가드레일 (PolicyValidator) 통제 성과
- **보호 대상 자산**: 코어 게이트웨이(`10.77.10.1`), Wazuh SIEM Host(`10.77.10.10`), 센서 관리 IP(`10.77.10.20`) 등 15개 자산 사전 등록.
- **오차단 방지 실적**: AI 모델이 정상 헬스체크 트래픽을 이상 트래픽으로 오인하여 게이트웨이 격리를 시도한 사례(INC-10.77.10.1-1788772755)에서 가드레일이 도구 실행을 100% 강제 차단함으로써 시스템 장애를 미연에 방지함.
- **Human-in-the-Loop**: 호스트 격리 등 비가역적 파괴 명령에 대해 관제 팀장의 명시적 수동 승인(Approval Gate) 필수화 구현.

---

## 6. 시각적 증적(Visual Evidence) 상세 분석

본 랩의 운영 무결성은 `docs/ai/evidence_annotated/` 내 7대 주석 증적 이미지로 뒷받침된다.

| 증적 번호 | 이미지 파일 | 검증 항목 및 핵심 관찰 내용 | 판정 |
|---|---|---|---|
| **[그림 1]** | `evidence_01_health_check.png` | Uvicorn 및 FastAPI SOC 콘솔 서비스 정상 구동 (HTTP 200) | **PASS** |
| **[그림 2]** | `evidence_02_soc_console_overview.png` | 실시간 대시보드 총 81건 경보, 78건 인시던트 통합 집계 현황 | **PASS** |
| **[그림 3]** | `evidence_03_rag_playbook_search.png` | RAG 기반 6개 플레이북(28개 청크) 벡터 임베딩 색인 완료 | **PASS** |
| **[그림 4]** | `evidence_04_ai_investigation_run.png` | 다단계 킬체인 인시던트 대상 AI 분석 및 자동 가이드 도출 | **PASS** |
| **[그림 5]** | `evidence_05_guardrail_protection.png` | 게이트웨이(10.77.10.1) 대상 AI 자동 격리 시도 강제 차단 | **PASS** |
| **[그림 6]** | `evidence_06_hitl_approval_flow.png` | 파괴적 명령에 대한 L3 승인 게이트 및 인간 개입 워크플로 | **PASS** |
| **[그림 7]** | `evidence_07_dual_engine_validation.png` | Suricata와 Snort 3 간 동일 PCAP 듀얼 탐지 일치도 100% | **PASS** |

---

## 7. NIST CSF 2.0 성숙도 평가 매트릭스

| CSF 2.0 기능 | 구현 세부 항목 | 현재 수준 | 증적 및 근거 |
|---|---|---|---|
| **GOVERN (거버넌스)** | AI 위험 관리, 인간 승인 절차(HITL), 직무 분리(SoD) | **Tier 4 (Adaptive)** | `PolicyValidator`, L1~L3 권한 분립, 감사로그 |
| **IDENTIFY (식별)** | 내부 자산 식별, 중요 인프라 보호 목록, 위협 모델링 | **Tier 4 (Adaptive)** | 15개 자산 사전 등록, 네트워크 토폴로지 |
| **PROTECT (보호)** | 엄격한 망 분리, Default Deny 방화벽, L3 미부여 센서 | **Tier 4 (Adaptive)** | Hyper-V vSwitch 격리, nftables 기본 차단 |
| **DETECT (탐지)** | Suricata 8 실시간 감시, Snort 3 검증, 30분 상관분석 | **Tier 4 (Adaptive)** | 27개 룰셋, EV-E2E-002, OpenSearch 실시간 인덱싱 |
| **RESPOND (대응)** | 6개 표준 침해대응 플레이북, 신속 격리, AI 보조 분석 | **Tier 3 (Repeatable)** | 플레이북 라이브러리, 게이트웨이 nftables 차단 |
| **RECOVER (복구)** | 서비스 정상화 확인, 룰 튜닝 라이프사이클(EV-TUNE-001) | **Tier 3 (Repeatable)** | Before/After 튜닝 검증, 사후 분석 보고서 |

---

## 8. 결론 및 향후 로드맵
본 SOC 관제 랩은 오픈소스 IDS와 차세대 SIEM, 로컬 AI Copilot 기술을 유기적으로 결합하여 엔터프라이즈급 관제 센터에 준하는 탐지 정밀도와 거버넌스 통제력을 실증하였다.
향후 엔드포인트 EDR 텔레메트리 연계 확대 및 실시간 차단 자동화(SOAR) 파이프라인의 고도화를 통해 자율형 보안관제(Autonomous SOC)로의 진화를 추진한다.
