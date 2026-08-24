# 🧪 05. SOC Lab 종합 테스트 및 검증 계획서 (Testing & Quality Gates)

> **기준 문서**: SOC Detection & Monitoring Lab Implementation Plan v1.0 (Section 45)  
> **적용 규정**: AGENTS.md Section 17 (Testing Rules)  
> **검증 대상**: 전체 파이프라인 (네트워크 ➔ 미러링 ➔ 듀얼 IDS ➔ SIEM ➔ 상관분석 ➔ 튜닝)  

---

## 1. 테스트 케이스 매트릭스 (Test Case Matrix)

| Test ID | 대상 단계 | 요구사항 ID | 검증 항목 | 검증 방식 | 성공 기준 (Pass Criteria) | 증적 (Evidence) |
|---|---|---|---|---|---|---|
| **TC-HOST-001** | Phase 0 | `REQ-HOST-01` | 호스트 가상화/리소스 검증 | `verify_host_readiness.ps1` | Hyper-V 활성, WSL2 >= 2.1.5, Docker 정상, RAM >= 32GB | `EV-HOST-001` |
| **TC-REPO-001** | Phase 1 | `REQ-REPO-01` | 레포지토리 구조 및 보안 설정 | 디렉토리 트리 검사 & Pytest | 27개 표준 디렉토리 생성, 시크릿 ignore, 10/10 pytest 통과 | `EV-REPO-001` |
| **TC-NET-001** | Phase 2 | `REQ-NET-01` | 3개 가상 스위치 및 호스트 IP | `Get-VMSwitch`, `Get-NetIPAddress` | `soc-vsw-*` 3종 생성, `10.77.10.10/24` 바인딩 | `EV-NET-INFRA-001` |
| **TC-VM-001** | Phase 3 | `REQ-VM-01` | 4대 VM 생성 및 어댑터 매핑 | `Get-VM`, `Get-VMNetworkAdapter` | 4개 Gen 2 VM 생성, 총 7개 NIC 지정 스위치 연결 | `EV-VM-001` |
| **TC-ROUTE-001** | Phase 5 | `REQ-NET-01` | 게이트웨이 라우팅 & 호스트 경로 | `Get-NetRoute`, `ping` | 호스트 ➔ `10.77.30.0/24 via 10.77.10.1` 라우팅 등록 | `EV-NET-INFRA-001` |
| **TC-FW-001** | Phase 6 | `REQ-NET-01` | 게이트웨이 망분리 방화벽 격리 | nftables 룰셋 검증 (`nft -c -f`) | 공격망 ➔ 관리망 차단, 공격망 ➔ 희생망 허용 | `EV-FW-001` |
| **TC-MIRROR-001**| Phase 7 | `REQ-NET-02` | Hyper-V 포트 미러링 모드 | `Get-VMNetworkAdapter` | 희생 서버: `Source`, 센서 모니터링 NIC: `Destination` | `EV-MIRROR-CONFIG-001`|
| **TC-SURI-001** | Phase 10 | `REQ-IDS-01` | Suricata 8.x 설정 및 룰 로드 | `suricata -T -c suricata.yaml` | 설정 구문 오류 0건, 9000~9030 커스텀 룰셋 로드 | `EV-SURI-001` |
| **TC-SNORT-001**| Phase 14 | `REQ-IDS-02` | Snort 3 오프라인 PCAP 검증 | `snort -T -c snort.lua` | Snort 3 검증 모드 정상, 9100 커스텀 룰셋 로드 | `EV-SNORT-001` |
| **TC-SIEM-001** | Phase 19 | `REQ-SIEM-01`| Wazuh EVE JSON 로그 수집 파이프라인 | `local_rules.xml` 디코딩 검증 | Suricata `eve.json` ➔ Wazuh Alert 디코딩/인덱싱 성공 | `EV-WAZUH-001` |
| **TC-ANALYSIS-001**| Phase 22 | `REQ-SOC-01`| 다단계 킬체인 상관분석 엔진 | `python -m analyzer.main` | 정찰 ➔ 초기 침투 ➔ C2 3단계 공격 단일 Incident 그룹화 | `EV-ANALYSIS-001` |
| **TC-TUNE-001** | Phase 25 | `REQ-SOC-02`| 오탐(False Positive) 룰 튜닝 | Before/After 트래픽 검증 | 정상 트래픽 오탐 제거 + 공격 트래픽 탐지 유지 동시 만족 | `EV-TUNE-001` |

---

## 2. 자동화 단위 테스트 실행 (Pytest Suite)

### 실행 명령:
```bash
pytest -v
```

### 테스트 결과 요약:
```text
tests/test_correlation.py::test_multi_stage_correlation PASSED           [ 10%]
tests/test_dashboard_api.py::test_dashboard_index_html PASSED            [ 20%]
tests/test_dashboard_api.py::test_dashboard_api_stats PASSED             [ 30%]
tests/test_dashboard_api.py::test_dashboard_api_alerts PASSED            [ 40%]
tests/test_dashboard_api.py::test_dashboard_api_incidents PASSED         [ 50%]
tests/test_parsers.py::test_suricata_eve_parser PASSED                   [ 60%]
tests/test_parsers.py::test_snort_parser PASSED                          [ 70%]
tests/test_threat_intel.py::test_threat_intel_ip_match PASSED            [ 80%]
tests/test_threat_intel.py::test_threat_intel_domain_match PASSED        [ 90%]
tests/test_threat_intel.py::test_threat_intel_benign_ip PASSED           [100%]

======================== 10 passed in 0.69s ========================
```
