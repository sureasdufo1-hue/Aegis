# [부록 A] 탐지 룰 카탈로그 (Detection Rule Catalog)

본 카탈로그는 **SOC Detection & Monitoring Lab**에 배포된 1차 탐지 엔진(Suricata 8.0.6)의 27개 커스텀 룰 및 2차 교차검증 엔진(Snort 3.12.2.0)의 10개 커스텀 룰의 전체 명세를 기록한다.

---

## 1. Suricata 8.0.6 커스텀 룰 카탈로그 (Total: 27 Rules)

### 1.1 네트워크 스캔 및 정찰 (Reconnaissance: SID 9000001 ~ 9000008)
| SID | Rev | 프로토콜 | 출발지 ➔ 목적지 | 시그니처 명칭 (Message) | MITRE ATT&CK | 분류 (Classtype) |
|---|---|---|---|---|---|---|
| `9000001` | 1 | TCP | $ATTACK any ➔ $VICTIM any | SOC-SCAN: Nmap Stealth NULL Scan Detected (Zero Flags) | T1595.001 | network-scan |
| `9000002` | 1 | TCP | $ATTACK any ➔ $VICTIM any | SOC-SCAN: Nmap Stealth FIN Scan Detected | T1595.001 | network-scan |
| `9000003` | 1 | TCP | $ATTACK any ➔ $VICTIM any | SOC-SCAN: Nmap Xmas Tree Scan Detected (FPU Flags) | T1595.001 | network-scan |
| `9000004` | 1 | TCP | $ATTACK any ➔ $VICTIM any | SOC-SCAN: Nmap TCP SYN Stealth Port Scan Rate Limit Exceeded | T1046 | network-scan |
| `9000005` | 1 | UDP | $ATTACK any ➔ $VICTIM any | SOC-SCAN: Nmap UDP Port Scan Activity Detected | T1046 | network-scan |
| `9000006` | 1 | ICMP | $ATTACK any ➔ $VICTIM any | SOC-SCAN: Nmap ICMP Sweep Ping Sweep Detected | T1595.001 | network-scan |
| `9000007` | 1 | TCP | $ATTACK any ➔ $VICTIM any | SOC-SCAN: Masscan Rapid Banner Grabbing Probe Detected | T1046 | network-scan |
| `9000008` | 1 | TCP | $ATTACK any ➔ $VICTIM any | SOC-SCAN: Aggressive TCP Connect Full Handshake Scan Rate | T1046 | network-scan |

### 1.2 웹 애플리케이션 공격 (Web Application: SID 9010001 ~ 9010007)
| SID | Rev | 프로토콜 | 출발지 ➔ 목적지 | 시그니처 명칭 (Message) | MITRE ATT&CK | 분류 (Classtype) |
|---|---|---|---|---|---|---|
| `9010001` | 2 | HTTP | $ATTACK any ➔ $VICTIM 80 | SOC-ATTACK: Web SQL Injection - UNION SELECT Pattern Detected | T1190 | web-application-attack |
| `9010002` | 1 | HTTP | $ATTACK any ➔ $VICTIM 80 | SOC-ATTACK: Web SQL Injection - Error Based / Boolean-based Payload | T1190 | web-application-attack |
| `9010003` | 1 | HTTP | $ATTACK any ➔ $VICTIM 80 | SOC-ATTACK: Web SQL Injection - information_schema Reconnaissance Attempt | T1190 | web-application-attack |
| `9010004` | 1 | HTTP | $ATTACK any ➔ $VICTIM 80 | SOC-ATTACK: Web Directory Traversal - ../ Path Access Attempt | T1083 | web-application-attack |
| `9010005` | 1 | HTTP | $ATTACK any ➔ $VICTIM 80 | SOC-ATTACK: Web Directory Traversal - Sensitive File (/etc/passwd) Access | T1005 | web-application-attack |
| `9010006` | 1 | HTTP | $ATTACK any ➔ $VICTIM 80 | SOC-ATTACK: Web XSS - Cross-Site Scripting <script> Tag Injection | T1059.007 | web-application-attack |
| `9010007` | 1 | HTTP | $ATTACK any ➔ $VICTIM 80 | SOC-ATTACK: Web Command Injection - System Command Separator (; / &&) | T1059.004 | web-application-attack |

### 1.3 인증 무차별 대입 (Authentication Brute Force: SID 9020001 ~ 9020002)
| SID | Rev | 프로토콜 | 출발지 ➔ 목적지 | 시그니처 명칭 (Message) | MITRE ATT&CK | 분류 (Classtype) |
|---|---|---|---|---|---|---|
| `9020001` | 1 | TCP | $ATTACK any ➔ $VICTIM 22 | SOC-AUTH: SSH Brute Force - High Frequency Connection Attempts | T1110.001 | authentication-attack |
| `9020002` | 1 | HTTP | $ATTACK any ➔ $VICTIM 80 | SOC-AUTH: Web HTTP POST Login Brute Force Rate Limit Exceeded | T1110.001 | authentication-attack |

### 1.4 악성코드 및 리버스 셸 C2 (Malware & C2: SID 9030001 ~ 9030010)
| SID | Rev | 프로토콜 | 출발지 ➔ 목적지 | 시그니처 명칭 (Message) | MITRE ATT&CK | 분류 (Classtype) |
|---|---|---|---|---|---|---|
| `9030001` | 1 | TCP | $VICTIM any ➔ $ATTACK 4444 | SOC-MALWARE: Suspicious Outbound Connection to Metasploit Default Port | T1071.001 | trojan-activity |
| `9030002` | 1 | TCP | $VICTIM any ➔ $ATTACK any | SOC-MALWARE: Outbound Meterpreter Reverse TCP Stager Handshake | T1071.001 | trojan-activity |
| `9030003` | 1 | HTTP | $VICTIM any ➔ $ATTACK any | SOC-MALWARE: Outbound Cobalt Strike Beacon HTTP Check-in Traffic | T1071.001 | trojan-activity |
| `9030004` | 1 | TCP | $VICTIM any ➔ $ATTACK any | SOC-MALWARE: Netcat Raw TCP Shell Spawning Interactive Stream | T1059.004 | trojan-activity |
| `9030005` | 1 | TCP | $VICTIM any ➔ $ATTACK any | SOC-MALWARE: Bash /dev/tcp Outbound Socket Execution Handshake | T1059.004 | trojan-activity |
| `9030006` | 1 | TCP | $VICTIM any ➔ $ATTACK any | SOC-MALWARE: Python Socket Pty Spawn Reverse Shell Stream | T1059.004 | trojan-activity |
| `9030007` | 1 | TCP | $VICTIM any ➔ $ATTACK any | SOC-MALWARE: Suspicious Base64 Encoded Interactive Shell Commands | T1059.004 | trojan-activity |
| `9030008` | 1 | DNS | $VICTIM any ➔ $ATTACK 53 | SOC-MALWARE: DNS Tunneling - High Entropy Subdomain Query Stream | T1071.004 | trojan-activity |
| `9030009` | 1 | TCP | $VICTIM any ➔ $ATTACK any | SOC-MALWARE: Linux /bin/sh or /bin/bash Interactive Prompt Banner | T1059.004 | trojan-activity |
| `9030010` | 1 | TCP | $VICTIM 4444 ➔ $ATTACK 4444 | SOC-MALWARE: Interactive Reverse Shell Session Established (/bin/sh) | T1059.004 | trojan-activity |

---

## 2. Snort 3.12.2.0 커스텀 룰 카탈로그 (Total: 10 Rules)

| SID | Rev | 프로토콜 | 출발지 ➔ 목적지 | 시그니처 명칭 (Message) | 대응 Suricata SID |
|---|---|---|---|---|---|
| `9100001` | 2 | TCP | $EXTERNAL_NET any ➔ $HOME_NET 80 | SOC-SNORT: Web Suspicious Path Access Attempt | `9010001` |
| `9100002` | 1 | TCP | $EXTERNAL_NET any ➔ $HOME_NET 80 | SOC-SNORT: Web SQL Injection UNION SELECT Pattern | `9010001` |
| `9100003` | 1 | TCP | $EXTERNAL_NET any ➔ $HOME_NET 80 | SOC-SNORT: Web Directory Traversal /etc/passwd Pattern | `9010005` |
| `9100004` | 1 | TCP | $EXTERNAL_NET any ➔ $HOME_NET 22 | SOC-SNORT: SSH Inbound Connection Threshold Exceeded | `9020001` |
| `9100005` | 1 | TCP | $EXTERNAL_NET any ➔ $HOME_NET any | SOC-SNORT: TCP NULL Scan Flags Detected | `9000001` |
| `9100006` | 1 | TCP | $EXTERNAL_NET any ➔ $HOME_NET any | SOC-SNORT: TCP Xmas Scan Flags Detected | `9000003` |
| `9100007` | 1 | TCP | $HOME_NET any ➔ $EXTERNAL_NET 4444 | SOC-SNORT: Outbound Traffic to Known Reverse Shell Port 4444 | `9030001` |
| `9100008` | 1 | TCP | $HOME_NET any ➔ $EXTERNAL_NET any | SOC-SNORT: Interactive Unix Shell Banner Detected (/bin/sh) | `9030010` |
| `9100009` | 1 | UDP | $EXTERNAL_NET any ➔ $HOME_NET any | SOC-SNORT: High Rate Inbound UDP Flood Detected | `9000005` |
| `9100010` | 1 | ICMP | $EXTERNAL_NET any ➔ $HOME_NET any | SOC-SNORT: Excessive ICMP Echo Request Threshold | `9000006` |
