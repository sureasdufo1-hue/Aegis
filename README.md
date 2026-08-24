# 🛡️ SOC Detection & Monitoring Lab Portfolio

> **수리카타(Suricata 8.x)**와 **스노트(Snort 3)** 침입탐지시스템(IDS/IPS) 듀얼 엔진, **Wazuh 4.x SIEM**, **Hyper-V 포트 미러링 가상 인프라**, 그리고 **실시간 다단계 킬체인 상관분석 엔진**을 활용하여 실제 기업 보안관제센터(SOC) 환경과 동일한 위협 탐지, 오탐 튜닝, 침해사고 트라이아지 체계를 입증하는 종합 보안관제 포트폴리오입니다.

---

## 📑 목차 (Table of Contents)

1. [시스템 아키텍처 및 망분리 구성도](#1-시스템-아키텍처-및-망분리-구성도)
2. [End-to-End 침해사고 분석 파이프라인](#2-end-to-end-침해사고-분석-파이프라인)
3. [품질 게이트 및 증적 매트릭스 (Quality Gates)](#3-품질-게이트-및-증적-매트릭스-quality-gates)
4. [5대 공격 시나리오 & 듀얼 IDS 룰셋](#4-5대-공격-시나리오--듀얼-ids-룰셋)
5. [탐지 룰 튜닝 및 오탐 제거 라이프사이클](#5-탐지-룰-튜닝-및-오탐-제거-라이프사이클)
6. [실시간 상관분석 엔진 및 관제 콘솔 실행](#6-실시간-상관분석-엔진-및-관제-콘솔-실행)
7. [프로젝트 표준 문서 인덱스](#7-프로젝트-표준-문서-인덱스)

---

## 1. 시스템 아키텍처 및 망분리 구성도

```mermaid
graph TD
    subgraph Host["Windows 10/11 Host (vEthernet: 10.77.10.10)"]
        subgraph HyperV["Hyper-V 3-Zone Virtual Network Infrastructure"]
            subgraph AttackerVM["soc-attacker (Kali Linux 2026.2)"]
                AttackerNIC["nic-attack (10.77.20.20)"]
            end

            subgraph GatewayVM["soc-gateway (Ubuntu 22.04 Router/Firewall)"]
                GW_Att["nic-attack (10.77.20.1)"]
                GW_Vic["nic-victim (10.77.30.1)"]
                GW_Mgmt["nic-mgmt (10.77.10.1)"]
            end

            subgraph VictimVM["soc-victim (Ubuntu 22.04 + OWASP Juice Shop)"]
                VicNIC["nic-victim (10.77.30.20) [Mirror Source]"]
            end

            subgraph SensorVM["soc-sensor (Ubuntu 22.04 Passive Sensor)"]
                MonNIC["nic-monitor (NO IP) [Mirror Destination]"]
                SensMgmt["nic-mgmt (10.77.10.20)"]
                SuricataEng["Suricata 8.0.6 (AF_PACKET)"]
                SnortEng["Snort 3.12.2.0 (Offline Validation)"]
                WazuhAg["Wazuh Agent"]
            end
        end

        subgraph DockerWSL["Docker Desktop & SIEM Stack (ZONE-MGMT)"]
            WazuhMgr["soc-wazuh-manager (4.14.7)"]
            WazuhIdx["soc-wazuh-indexer (4.14.7)"]
            WazuhDash["soc-wazuh-dashboard (4.14.7)"]
            SOC_API["FastAPI SOC Dashboard (:8501)"]
        end
    end

    AttackerNIC <-->|ZONE-ATTACK (10.77.20.0/24)| GW_Att
    GW_Vic <-->|ZONE-VICTIM (10.77.30.0/24)| VicNIC
    VicNIC -.->|Hyper-V Port Mirroring| MonNIC
    MonNIC --> SuricataEng
    SuricataEng -->|eve.json| WazuhAg
    WazuhAg -->|1514/TCP| WazuhMgr
    WazuhMgr --> WazuhIdx --> WazuhDash
```

---

## 2. End-to-End 침해사고 분석 파이프라인

본 랩은 단순 툴 설치를 넘어 **패킷 발생부터 최종 튜닝 및 증적 보고서까지 끊어짐 없는 증적 체계**를 입증합니다:

```text
[1. Attacker]            soc-attacker (10.77.20.20)
       ↓
[2. Gateway]             soc-gateway (10.77.10.1 / 20.1 / 30.1) - nftables Default Deny 격리
       ↓
[3. Victim]              soc-victim (10.77.30.20) - OWASP Target
       ↓
[4. Port Mirroring]      Hyper-V vSwitch Mirroring (Source -> Destination nic-monitor)
       ↓
[5. Sensor]              soc-sensor (Passive Promiscuous Mode, NO L3 IP)
       ↓
[6. Suricata 8.0.6]      AF_PACKET Multi-threaded Ingestion
       ↓
[7. Detection Rule]      9000-series Custom Rules (SIDs 9000001, 9010040, 9030010)
       ↓
[8. eve.json]            Structured EVE JSON Telemetry Generated
       ↓
[9. Wazuh 4.14.7]        local_rules.xml Decoder Ingestion & Dashboard Indexing
       ↓
[10. SOC Analyst]        14-Step Investigation Standard & Triage
       ↓
[11. PCAP Verification]  SHA-256 Hashed PCAP Evidence (PCAP-20260824-ATK-*.pcap)
       ↓
[12. MITRE ATT&CK]       T1046 (Recon) -> T1190 (Exploit) -> T1059.004 / T1071 (C2)
       ↓
[13. Incident Verdict]   INC-20260824-001 = TRUE_POSITIVE
       ↓
[14. Detection Tuning]   SID:9010001 rev:1 -> rev:2 (False Positive Eliminated)
       ↓
[15. Evidence Package]   EV-HOST, EV-NET, EV-VM, EV-SURI, EV-SNORT, EV-WAZUH, EV-ANALYSIS, EV-TUNE
```

---

## 3. 품질 게이트 및 증적 매트릭스 (Quality Gates)

| Gate ID | 구현 단계 | 검증 항목 | 결과 | 증적 문서 (Evidence) |
|---|---|---|---|---|
| **`GATE-HOST-01`** | Phase 0 | Host 리소스 (Win11 26100, Hyper-V, WSL2, 64GB RAM, Docker) | **PASS** | [`evidence/EV-HOST-001/metadata.md`](evidence/EV-HOST-001/metadata.md) |
| **`GATE-REPO-01`** | Phase 1 | 레포지토리 구조, 보안 ignore, 단위 테스트 (10/10 Pytest PASS) | **PASS** | [`evidence/EV-REPO-001/metadata.md`](evidence/EV-REPO-001/metadata.md) |
| **`GATE-NET-INFRA-01`** | Phase 2 | 3-Zone Hyper-V vSwitch (`soc-vsw-*`) 및 호스트 IP (`10.77.10.10`) | **PASS** | [`evidence/EV-NET-INFRA-001/metadata.md`](evidence/EV-NET-INFRA-001/metadata.md) |
| **`GATE-VM-01`** | Phase 3 | 4대 Gen 2 VM 생성 (`soc-gateway/victim/sensor/attacker`) | **PASS** | [`evidence/EV-VM-001/metadata.md`](evidence/EV-VM-001/metadata.md) |
| **`GATE-MIRROR-CONFIG-01`** | Phase 7 | 포트 미러링 (`soc-victim`=Source, `soc-sensor`=Destination) | **PASS** | [`evidence/EV-MIRROR-CONFIG-001/metadata.md`](evidence/EV-MIRROR-CONFIG-001/metadata.md) |
| **`GATE-SURI-01`** | Phase 10 | Suricata 8.0.6 Baseline (`HOME_NET`, `AF_PACKET`, 9000계열 룰) | **PASS** | [`evidence/EV-SURI-001/metadata.md`](evidence/EV-SURI-001/metadata.md) |
| **`GATE-PCAP-01`** | Phase 12 | 6대 시나리오 PCAP 생성 및 SHA-256 무결성 해시 매니페스트 | **PASS** | [`evidence/EV-PCAP-001/metadata.md`](evidence/EV-PCAP-001/metadata.md) |
| **`GATE-SNORT-01`** | Phase 14 | Snort 3.12.2.0 Baseline (`alert_json`, 9100계열 검증 룰) | **PASS** | [`evidence/EV-SNORT-001/metadata.md`](evidence/EV-SNORT-001/metadata.md) |
| **`GATE-WAZUH-01`** | Phase 15~16 | Wazuh 4.14.7 Single-Node Docker 배포 및 포트 보안 하드닝 | **PASS** | [`evidence/EV-WAZUH-001/metadata.md`](evidence/EV-WAZUH-001/metadata.md) |
| **`GATE-ANALYSIS-01`** | Phase 22 | 다단계 킬체인 상관분석 엔진 (`Recon ➔ Exploit ➔ C2`) 판정 | **PASS** | [`evidence/EV-ANALYSIS-001/metadata.md`](evidence/EV-ANALYSIS-001/metadata.md) |
| **`GATE-TUNE-01`** | Phase 24~26 | 탐지 룰 튜닝 (정상 트래픽 오탐 제거 + 공격 탐지력 유지) | **PASS** | [`evidence/EV-TUNE-001/metadata.md`](evidence/EV-TUNE-001/metadata.md) |
| **`GATE-E2E-01`** | Phase 27 | 전체 파이프라인 단일 침해사고(`INC-20260824-001`) 연결 검증 | **PASS** | [`evidence/EV-E2E-001/metadata.md`](evidence/EV-E2E-001/metadata.md) |
| **`GATE-PORTFOLIO-01`**| Phase 29~30 | 100% 기술 문서화 및 최종 릴리즈 게이트 통과 | **PASS** | [`evidence/EV-PORTFOLIO-001/metadata.md`](evidence/EV-PORTFOLIO-001/metadata.md) |

---

## 4. 5대 공격 시나리오 & 듀얼 IDS 룰셋

| 시나리오 | 공격 기법 | MITRE ATT&CK | Suricata 8 SID | Snort 3 SID | PCAP 증적 |
|---|---|---|---|---|---|
| **01. Recon** | Nmap Stealth NULL / XMAS / FIN Scan | `T1046`, `T1595` | `9000001` ~ `9000004` | `9100020` ~ `9100022` | `PCAP-20260824-ATK-003-SCAN.pcap` |
| **02. Web Exploit**| SQLi (`UNION SELECT`), LFI (`/etc/passwd`), Log4j RCE | `T1190`, `T1083` | `9010001` ~ `9010040` | `9100010` ~ `9100013` | `PCAP-20260824-ATK-002-SQLI.pcap` |
| **03. Brute Force**| SSH 고빈도 무차별 대입 연결 | `T1110` | `9020001` | `9100025` | `PCAP-20260824-ATK-005-BRUTEFORCE.pcap` |
| **04. C2 & Exfil** | DNS Base64 서브도메인 터널링, Reverse Shell (`/bin/sh`) | `T1071`, `T1059.004` | `9030001` ~ `9030020` | `9100030` ~ `9100035` | `PCAP-20260824-ATK-006-C2REVERSESHELL.pcap` |
| **05. DoS Flood** | ICMP Ping Flood Denial of Service | `T1498` | `9000021` | `9100002` | `PCAP-20260824-ATK-001-ICMP.pcap` |

---

## 5. 탐지 룰 튜닝 및 오탐 제거 라이프사이클

```text
========================================================================================
Stage                Rule Definition                           Normal Traffic  Attack Traffic
========================================================================================
Baseline (rev:1)     alert http ... (http.method; "GET";)      ALERT (FP)      ALERT (Detected)
Tuned    (rev:2)     alert http ... (http.uri; "/suspicious";) NO ALERT (PASS) ALERT (Detected)
========================================================================================
Result: 정상 트래픽에 대한 오탐(False Positive)을 100% 제거하면서 목표 공격 탐지력 완벽 보존 (GATE-TUNE-01 = PASS)
```

---

## 6. 빠른 시작 가이드 (Quick Start)

### 6.1 파이썬 환경 구성 및 실습
```bash
# 1. 패키지 설치
pip install -r requirements.txt

# 2. 고충실도 모의 침해사고 로그 및 PCAP 샘플 생성
python scenarios/traffic_generator.py
python scripts/generate_pcap_samples.py

# 3. 킬체인 상관분석 엔진 실행 (위협 인텔리전스 & 자동 Incident 승격)
python -m analyzer.main

# 4. 탐지 룰 튜닝 검증 스크립트 실행
python scripts/verify_detection_tuning.py

# 5. 단위 및 통합 테스트 실행 (10/10 PASS)
pytest -v

# 6. 실시간 SOC 웹 관제 콘솔 기동 (http://localhost:8501)
python -m uvicorn dashboard.app:app --host 0.0.0.0 --port 8501 --reload
```

---

## 7. 프로젝트 표준 문서 인덱스

| 구분 | 문서 링크 | 설명 |
|---|---|---|
| **01. 요구사항** | [`docs/01-requirements/README.md`](docs/01-requirements/README.md) | 3대 영역 망분리, 듀얼 IDS, SIEM 요구사항 정의서 |
| **02. 아키텍처** | [`docs/02-architecture/README.md`](docs/02-architecture/README.md) | 시스템 토폴로지 및 IP/네트워크 기본설계서 (HLD) |
| **03. 상세설계** | [`docs/03-design/README.md`](docs/03-design/README.md) | 컴포넌트별 상세 스펙 및 nftables 방화벽 정책 (LLD) |
| **04. 구축계획** | [`docs/04-deployment/README.md`](docs/04-deployment/README.md) | 30단계 구축 순서 및 런타임 베이스라인 |
| **05. 테스트** | [`docs/05-testing/README.md`](docs/05-testing/README.md) | 12대 테스트 케이스(TC) 및 자동화 실행 가이드 |
| **06. 탐지공학** | [`docs/06-detection/README.md`](docs/06-detection/README.md) | Suricata vs Snort 문법 비교 및 MITRE ATT&CK 매핑 |
| **07. 트라이아지** | [`docs/07-investigation/README.md`](docs/07-investigation/README.md) | 14단계 침해사고 조사 표준 및 판정 기준 |
| **08. 사고보고서** | [`docs/08-incident/INC-20260824-001.md`](docs/08-incident/INC-20260824-001.md) | 다단계 킬체인 실사고 분석 보고서 |
| **09. 트러블슈팅**| [`docs/09-troubleshooting/README.md`](docs/09-troubleshooting/README.md) | 패킷 미러링 미도달 등 장애 해결 가이드 |
