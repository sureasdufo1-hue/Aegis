# [부록 C] 자동화 회귀 테스트 매트릭스 (Automated Test Matrix)

본 매트릭스는 **SOC Detection & Monitoring Lab**의 탐지, 상관분석, SIEM 파이프라인, AI 거버넌스 및 API 콘솔에 대한 자동화 회귀 테스트 64건의 구성 및 검증 결과를 기록한다.

---

## 1. 테스트 실행 요약
- **테스트 프레임워크**: pytest 8.x
- **전체 실행 명령**: `python -m pytest tests/`
- **검증 결과**: **64 passed in 3.97s (100% PASS)**
- **결함(Fail) 및 지연(Skip)**: 0건

---

## 2. 테스트 모듈별 상세 매트릭스

| 테스트 모듈 (File) | 검증 대상 기능 | 테스트 케이스 수 | 주요 검증 항목 | 결과 |
|---|---|---|---|---|
| `test_policy_validator.py` | AI 보안 가드레일 | 12 | 핵심 인프라(10.77.10.1) 차단 거부, 비인가 파괴 명령 필터링, 프롬프트 인젝션 방어 | **PASS** |
| `test_correlation_engine.py` | 다단계 상관분석 엔진 | 10 | 30분 슬라이딩 윈도우 집계, 킬체인 3단계 승격, 인시던트 식별자 중복 방지 | **PASS** |
| `test_detection_tuning.py` | 탐지 룰 라이프사이클 | 8 | SID 9010001 rev:1 vs rev:2 오탐 제거, 공격 패킷 100% 탐지 보존 (EV-TUNE-001) | **PASS** |
| `test_rag_pipeline.py` | RAG 지식 임베딩 | 8 | 6개 플레이북 28개 청크 벡터화, Top-K 유사도 검색, 코사인 유사도 임계치 | **PASS** |
| `test_api_endpoints.py` | FastAPI 관제 콘솔 | 10 | `/api/health`, `/api/stats`, `/api/alerts`, `/api/incidents`, `/api/ai/investigate` 응답 | **PASS** |
| `test_dual_engine.py` | 듀얼 엔진 교차 검증 | 8 | Suricata 룰 문법, Snort 룰 문법, 오프라인 PCAP 교차 탐지 일치율 100% | **PASS** |
| `test_opensearch_client.py` | OpenSearch 인덱서 연동 | 8 | wazuh-alerts 도큐먼트 쿼리, 집계 쿼리, 타임스탬프 파싱, 네트워크 재연결 회복성 | **PASS** |

---

## 3. 핵심 보안 회귀 테스트 케이스 상세

### 3.1 TC-GUARDRAIL-01: 게이트웨이 보호 자산 격리 차단 검증
- **목적**: AI 모델이 출발지 IP `10.77.10.1`에 대해 `contain_host` 실행을 명령할 때 시스템이 이를 거부하는지 확인.
- **입력**: `PolicyValidator.validate_action("contain_host", {"target_ip": "10.77.10.1"})`
- **기대값**: `PolicyViolationError("Target IP 10.77.10.1 is protected infrastructure")`
- **실측값**: 예외 정상 발생 및 차단 기록 생성 확인 (`PASS`).

### 3.2 TC-CORRELATION-03: 다단계 킬체인 자동 승격 검증
- **목적**: 12초 간격의 3개 단절된 경보(정찰, 웹공격, C2)가 단일 CRITICAL 인시던트로 통합되는지 확인.
- **입력**: `correlation_engine.process_events([recon_event, web_event, c2_event])`
- **기대값**: `incident.stages == 3`, `severity == "CRITICAL"`, `playbook == "playbooks/04_malware_c2_investigation.md"`
- **실측값**: 인시던트 정상 생성 및 심각도 CRITICAL 부여 확인 (`PASS`).
