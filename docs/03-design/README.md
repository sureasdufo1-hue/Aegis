# 📐 03. 보안관제 프로젝트 상세설계서 (LLD v1.0)

> **원본 문서**: [`보안관제_프로젝트_상세설계서(LLD)_v1.0.pdf`](./보안관제_프로젝트_상세설계서(LLD)_v1.0.pdf)  
> **문서 버전**: v1.0 (48 Pages)  
> **기준 일자**: 2026-08-24  
> **프로젝트 명**: SOC Detection & Monitoring Lab  

---

## 1. 컴포넌트별 상세 스펙 및 설정 (Detailed Specifications)

### 1.1 Hyper-V 가상 스위치 및 포트 미러링 설정
- **vSwitch 목록**:
  - `soc-vsw-mgmt` (Internal)
  - `soc-vsw-attack` (Private)
  - `soc-vsw-victim` (Private)
- **Port Mirroring PowerShell 구성**:
  ```powershell
  # Source (Victim)
  Set-VMNetworkAdapter -VMName "soc-victim" -PortMirroring Source
  # Destination (Sensor Monitor NIC)
  Set-VMNetworkAdapter -VMName "soc-sensor" -Name "nic-monitor" -PortMirroring Destination
  ```

### 1.2 Suricata 8.x 상세 구성
- **EVE JSON 경로**: `/var/log/suricata/eve.json`
- **SID 할당 대역**: `9000000` ~ `9099999`
  - `9000000–9009999`: Network & Reconnaissance
  - `9010000–9019999`: Web Application Attacks
  - `9020000–9029999`: Authentication & Brute Force
  - `9030000–9039999`: Lab / Malware C2
- **AF_PACKET 인터페이스**: `nic-monitor` (Promiscuous mode, Cluster ID: 99)

### 1.3 Snort 3 상세 구성
- **SID 할당 대역**: `9100000` ~ `9199999`
- **실행 모드**: `snort -c /etc/snort/rules/local.rules -r traffic.pcap -A alert_json`

### 1.4 Wazuh 4.14.7 Docker 포트 바인딩 및 파이프라인
- **공개 포트 (MGMT Zone)**:
  - `1514/TCP`: Agent Event Ingestion
  - `1515/TCP`: Agent Registration Service
  - `443/TCP`: Wazuh Dashboard Web UI
- **로컬 전용 포트 (Localhost)**:
  - `9200/TCP`: Wazuh Indexer
  - `55000/TCP`: Wazuh Manager REST API

---

## 2. 게이트웨이 방화벽 정책 (nftables / iptables LLD)

```text
Default Policy: DROP

[INPUT]
- lo: ACCEPT
- ESTABLISHED, RELATED: ACCEPT
- MGMT -> GW (SSH: 22): ACCEPT

[FORWARD]
- ATTACK (10.77.20.20) -> VICTIM (10.77.30.20) (TCP 80, 443, 3000, 22): ACCEPT
- VICTIM (10.77.30.20) -> WAZUH (10.77.10.10) (TCP 1514, 1515): ACCEPT
- ATTACK -> MGMT: DROP & LOG
- DEFAULT: DROP
```
