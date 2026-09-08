# [증적 관리대장] SOC 랩 전 주기 검증 증적 및 무결성 대장 (Evidence Register)

## 1. 개요 및 증적 관리 원칙
본 증적 관리대장은 **SOC Detection & Monitoring Lab**에서 수행된 네트워크 가시성 확보, 탐지 엔진 검증, SIEM 연동, 침해사고 분석, AI 보안 통제 및 탐지 룰 튜닝에 이르기까지 전 주기에 걸쳐 산출된 객관적 증적(EV-xxx)을 종합 관리한다.

모든 증적은 디지털 포렌식 원칙(무결성, 신뢰성, 재현성)을 충족하기 위해 SHA-256 해시값과 Git 커밋 이력을 보존하며, 추측에 의한 결과(Probably PASS 등)는 전면 배제하고 실측 데이터만을 기록한다.

---

## 2. 공식 증적 등록 목록 (Official Evidence Register)

| 증적 ID | 영역 (Area) | 검증 대상 및 시나리오 | 최종 결과 | 게이트 판정 | 관련 아티팩트 및 증거 자료 |
|---|---|---|---|---|---|
| **EV-HOST-001** | 호스트 인프라 | Windows Hyper-V, WSL2, Docker Desktop 호환성 | **PASS** | `GATE-HOST-01` | 호스트 환경 점검 로그, PowerShell 출력 |
| **EV-NET-001** | 가상 네트워크 | 3개 vSwitch 분리 및 고정 IP 통신 무결성 | **PASS** | `GATE-NET-01` | nftables 규칙, 라우팅 테이블 덤프 |
| **EV-MIRROR-001** | 패킷 가시성 | Hyper-V 포트 미러링 (Victim ➔ Sensor Monitor) | **PASS** | `GATE-MIRROR-01` | `sensor_mirror_rx.pcap`, tshark 카운트 |
| **EV-SURI-001** | 1차 IDS 구축 | Suricata 8.0.6 AF_PACKET 무차별 수신 검증 | **PASS** | `GATE-SURI-01` | `suricata.log`, 인터페이스 통계 로그 |
| **EV-DETECT-001** | 시그니처 탐지 | 커스텀 룰셋 27종에 대한 실시간 EVE 경보 발생 | **PASS** | `GATE-DETECT-01` | `eve.json`, 경보 페이로드 덤프 |
| **EV-PCAP-001** | 패킷 보존 | 시나리오별 공격 및 정상 트래픽 PCAP 보존 | **PASS** | `GATE-PCAP-01` | 공격 유형별 원시 PCAP 및 SHA-256 |
| **EV-SNORT-001** | 2차 IDS 검증 | Snort 3.12.2.0 오프라인 PCAP 교차 검증 | **PASS** | `GATE-SNORT-01` | Snort alert_fast 로그, 비교 매트릭스 |
| **EV-WAZUH-001** | SIEM 연동 | Wazuh 4.14.7 Docker 단일 노드 클러스터 기동 | **PASS** | `GATE-WAZUH-01` | `docker-compose.yml`, 컨테이너 상태 |
| **EV-SIEM-001** | 파이프라인 수집 | Suricata EVE ➔ Wazuh Agent ➔ OpenSearch 인덱싱 | **PASS** | `GATE-SIEM-01` | `wazuh-alerts-4.x` 도큐먼트 쿼리 결과 |
| **EV-E2E-002** | 다단계 킬체인 | 정찰 ➔ 웹 공격 ➔ C2 장악 3단계 상관분석 및 콘솔 표출 | **PASS** | `GATE-PHASE31-01` | `e2e_verification_result.json`, API 응답 |
| **EV-TUNE-001** | 룰 라이프사이클 | SID 9010001 (rev:1 ➔ rev:2) 오탐 제거 및 공격 100% 탐지 | **PASS** | `GATE-TUNE-01` | `verify_detection_tuning.py` 실행 로그 |
| **EV-AI-001** | AI 거버넌스 | PolicyValidator 핵심 인프라(10.77.10.1) 오차단 강제 방지 | **PASS** | `GATE-AI-01` | AI 툴 호출 거부 로그, 테스트 결과 |

---

## 3. 시각적 주석 증적 현황 (Visual Annotated Evidence)

| 시각 증적 번호 | 참조 이미지 경로 | 점검 항목 및 기술 검증 내용 | 검증 결과 |
|---|---|---|---|
| **[그림 1]** | `docs/ai/evidence_annotated/evidence_01_health_check.png` | FastAPI SOC 백엔드 헬스체크 정상 응답 (HTTP 200) | **정상 (PASS)** |
| **[그림 2]** | `docs/ai/evidence_annotated/evidence_02_soc_console_overview.png` | 웹 관제 콘솔 실시간 통계 (81건 알람, 78건 인시던트) | **정상 (PASS)** |
| **[그림 3]** | `docs/ai/evidence_annotated/evidence_03_rag_playbook_search.png` | RAG 임베딩 기반 플레이북 검색 및 연관도 랭킹 산출 | **정상 (PASS)** |
| **[그림 4]** | `docs/ai/evidence_annotated/evidence_04_ai_investigation_run.png` | 다단계 킬체인 인시던트 대상 AI 사고 조사 결과 자동 생성 | **정상 (PASS)** |
| **[그림 5]** | `docs/ai/evidence_annotated/evidence_05_guardrail_protection.png` | PolicyValidator에 의한 핵심 인프라(10.77.10.1) 차단 거부 | **정상 (PASS)** |
| **[그림 6]** | `docs/ai/evidence_annotated/evidence_06_hitl_approval_flow.png` | 비가역적 파괴 명령 대상 관제 팀장 수동 승인 흐름 | **정상 (PASS)** |
| **[그림 7]** | `docs/ai/evidence_annotated/evidence_07_dual_engine_validation.png` | Suricata와 Snort 3 간 상호 교차 검증 100% 일치 | **정상 (PASS)** |
