# 🛡️ SOC Playbook 01: 포트 스캔 및 네트워크 정찰(Reconnaissance) 분석 가이드

---

## 1. 개요 (Overview)
- **위협 정의**: 공격자가 대상 시스템의 열린 포트, 운영체제(OS), 서비스 데몬 버전을 식별하기 위해 수행하는 능동적 정찰(Active Reconnaissance) 활동.
- **MITRE ATT&CK**: `T1595` (Active Scanning), `T1046` (Network Service Discovery)
- **탐지 룰 ID**: Suricata `sid:1000101` ~ `1000104`, Snort `sid:2000020` ~ `2000022`

---

## 2. 1차 관제 분석 절차 (Triage Steps)

### Step 1: 공격자 IP 프로파일링
- **출발지 IP(Source IP)**의 공인 IP 여부 및 평판 확인:
  - AbuseIPDB, VirusTotal, Shodan 조회
  - Tor Exit Node, 공용 VPN, 클라우드(AWS, DigitalOcean) 대역 여부 식별
- **스캔 방식 식별**:
  - `NULL Scan` (Flags: 0): 방화벽 필터링 우회 시도
  - `XMAS Scan` (Flags: FIN, PSH, URG): RFC 793 준수 OS 판별 시도
  - `SYN Scan` (Half-open Scan): 빠른 고속 포트 열림 여부 판별

### Step 2: 피해 대상(Destination) 영향도 평가
- 타깃 IP가 대외 서비스 DMZ 서버인지, 내부 DB/관리망 서버인지 자산 중요도 확인.
- 방화벽(Firewall) 및 Security Group 차단 로그와 교차 검증 (실제 TCP 3-way Handshake 완료 여부).

---

## 3. 침해 대응 및 조치 (Containment & Mitigation)

1. **단순 인터넷 전역 스캔 (Internet-wide Scanner, 예: Shodan/Censys)**:
   - 방화벽에서 기본 DROP 처리 중인 경우 -> `INFO/LOW` 티켓으로 분류 및 모니터링.
2. **표적형 포트 스캔 (Targeted Reconnaissance)**:
   - 특정 서버의 특정 포트(22, 3306, 8080 등)에 집중적인 정찰이 이어진 후 Exploit 시도가 관찰될 경우 -> **즉시 방화벽 인바운드 차단(IP Block)** 조치.

---

## 4. 룰 튜닝 가이드 (Rule Tuning)
- 내부 모니터링 시스템(Zabbix, Nagios)이나 취약점 점검 도구(Nessus) IP에 의한 오탐 발생 시:
  ```suricata
  # 특정 내부 스캐너 IP 예외 처리
  pass ip 192.168.1.50 any -> any any (msg:"Whitelisted Internal Nessus Scanner"; sid:9990001; rev:1;)
  ```
