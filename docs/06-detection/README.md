# 🎯 06. 탐지 룰셋 엔지니어링 및 엔진 비교 (Detection Engineering)

> **기준 문서**: SOC Architecture HLD v1.0 / LLD v1.0  
> **적용 규정**: AGENTS.md Section 12 (Suricata), Section 13 (Snort), Section 20 (MITRE ATT&CK)  

---

## 1. 듀얼 IDS 엔진 역할 분담 (Dual-Engine Architecture)

| 구분 | Primary IDS: Suricata 8.0.6 | Secondary IDS: Snort 3.12.2.0 |
|---|---|---|
| **운영 모드** | **실시간 인라인/패시브 모니터링** (`AF_PACKET`) | **오프라인 PCAP 교차 검증 및 룰 비교 분석** |
| **패킷 캡처** | `nic-monitor` (무IP 인터페이스, Promiscuous mode) | PCAP 파일 재생 (`-r traffic.pcap`) |
| **출력 텔레메트리** | `eve.json` (EVE JSON v2 포맷, Wazuh 연동) | `alert_json.txt` (Snort 3 JSON Logger) |
| **SID 할당 대역** | `9000000` ~ `9099999` | `9100000` ~ `9199999` |
| **멀티스레딩** | 고성능 파이프라인 (Worker 스레드 모델) | 멀티스레드 패킷 처리 엔진 |

---

## 2. 5대 위협 카테고리별 룰셋 매핑 (Rule Mapping Matrix)

### 2.1 정찰 및 스캔 탐지 (Reconnaissance & Discovery)
* **MITRE ATT&CK**: `T1046` (Network Service Discovery), `T1595` (Active Scanning)
* **Suricata Rules**: [`suricata/rules/9000-network-recon.rules`](file:///C:/Users/user/Documents/ChatGPT/Suricata-Snort-SOC-Lab/suricata/rules/9000-network-recon.rules)
  * `9000001`: Nmap Stealth NULL Scan (`flags:0`)
  * `9000002`: Nmap Stealth XMAS Scan (`flags:FPU`)
  * `9000003`: Nmap Stealth FIN Scan (`flags:F`)
  * `9000010`: Nikto 웹 취약점 스캐너 식별 (`http.user_agent; content:"Nikto"`)
* **Snort Rules**: [`snort/rules/9100-local.rules`](file:///C:/Users/user/Documents/ChatGPT/Suricata-Snort-SOC-Lab/snort/rules/9100-local.rules)
  * `9100020`: Nmap Stealth NULL Scan
  * `9100021`: Nmap Stealth XMAS Scan

### 2.2 웹 애플리케이션 공격 (Web Exploitation)
* **MITRE ATT&CK**: `T1190` (Exploit Public-Facing Application), `T1083` (File and Directory Discovery)
* **Suricata Rules**: [`suricata/rules/9010-web-attacks.rules`](file:///C:/Users/user/Documents/ChatGPT/Suricata-Snort-SOC-Lab/suricata/rules/9010-web-attacks.rules)
  * `9010001`: SQL Injection UNION SELECT 탐지 (`http.uri; content:"union"; content:"select"`)
  * `9010021`: LFI 민감 파일(`/etc/passwd`) 접근 탐지
  * `9010040`: Apache Log4j RCE JNDI Lookup (`http.header; pcre:"/\$\{jndi:(ldap|rmi|dns):\/\//i"`)
* **Snort Rules**: [`snort/rules/9100-local.rules`](file:///C:/Users/user/Documents/ChatGPT/Suricata-Snort-SOC-Lab/snort/rules/9100-local.rules)
  * `9100010`: Web SQL Injection UNION SELECT
  * `9100013`: Apache Log4j JNDI RCE Exploit

### 2.3 무차별 대입 인증 공격 (Credential Access)
* **MITRE ATT&CK**: `T1110` (Brute Force), `T1110.001` (Password Guessing)
* **Suricata Rules**: [`suricata/rules/9020-auth-bruteforce.rules`](file:///C:/Users/user/Documents/ChatGPT/Suricata-Snort-SOC-Lab/suricata/rules/9020-auth-bruteforce.rules)
  * `9020001`: SSH 고빈도 SYN 연결 임계치 초과 (`threshold:type both, count 5, seconds 30`)
  * `9020010`: 웹 로그인 폼 POST 요청 폭증 탐지 (`/login`, `count 10, seconds 60`)

### 2.4 C2 통신 및 데이터 유출 (Command & Control & Exfiltration)
* **MITRE ATT&CK**: `T1071.004` (DNS C2), `T1059.004` (Unix Shell), `T1048` (Exfiltration Over Alternative Protocol)
* **Suricata Rules**: [`suricata/rules/9030-malware-c2.rules`](file:///C:/Users/user/Documents/ChatGPT/Suricata-Snort-SOC-Lab/suricata/rules/9030-malware-c2.rules)
  * `9030001`: 비정상 장문 DNS 질의 (DNS 터널링 의심)
  * `9030010`: 대화형 리버스 쉘 세션 연결 (`content:"/bin/sh"`)
* **Snort Rules**: [`snort/rules/9100-local.rules`](file:///C:/Users/user/Documents/ChatGPT/Suricata-Snort-SOC-Lab/snort/rules/9100-local.rules)
  * `9100030`: Interactive Reverse Shell `/bin/sh` Output
  * `9100035`: Suspicious DNS Tunneling Query

---

## 3. Suricata vs Snort 문법 비교 요약

| 기능 | Suricata 8.0.6 문법 | Snort 3.12.2.0 문법 |
|---|---|---|
| **HTTP URI 검사** | `http.uri; content:"/admin";` | `http_uri; content:"/admin";` |
| **HTTP 헤더 검사** | `http.header; content:"User-Agent";` | `http_header; content:"User-Agent";` |
| **정규표현식 매칭** | `pcre:"/\$\{jndi:/i";` | `pcre:"/\$\{jndi:/i";` |
| **임계치(Threshold)**| `threshold:type both, track by_src, count 5, seconds 10;` | `detection_filter:track by_src, count 5, seconds 10;` |
| **메타데이터 태깅** | `metadata:attack_technique T1190, severity High;` | `metadata:service http;` |
