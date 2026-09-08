# [부록 B] MITRE ATT&CK v19.2 커버리지 매트릭스 (MITRE Coverage Matrix)

본 매트릭스는 **SOC Detection & Monitoring Lab**에서 구축된 침입탐지 시그니처 및 다단계 상관분석 엔진이 MITRE ATT&CK v19.2 프레임워크의 어떤 전술(Tactics)과 기법(Techniques)을 커버하는지 체계적으로 정리한 참조 문서이다.

---

## 1. 전술별 기법 커버리지 요약

| ATT&CK 전술 (Tactic) | Tactic ID | 매핑 기법 수 | 주요 기법 ID | 담당 탐지 규칙 (SID) |
|---|---|---|---|---|
| **Reconnaissance** | `TA0043` | 2 | T1595.001, T1595.002 | `9000001, 9000002, 9000003, 9000006` |
| **Discovery** | `TA0007` | 2 | T1046, T1083 | `9000004, 9000005, 9000007, 9000008, 9010004` |
| **Initial Access** | `TA0001` | 1 | T1190 | `9010001, 9010002, 9010003` |
| **Credential Access** | `TA0006` | 1 | T1110.001 | `9020001, 9020002` |
| **Execution** | `TA0002` | 3 | T1059.004, T1059.007, T1203 | `9010006, 9010007, 9030004, 9030005, 9030006, 9030010` |
| **Collection** | `TA0009` | 1 | T1005 | `9010005` |
| **Command and Control** | `TA0011` | 3 | T1071.001, T1071.004, T1571 | `9030001, 9030002, 9030003, 9030008` |
| **Impact** | `TA0040` | 2 | T1498.001, T1499.001 | `9000003 (DoS), 9000006 (Flood)` |

---

## 2. 기법별 상세 매핑 및 검증 현황

| 기법 ID | 기법 명칭 (Technique Name) | 하위 기법 (Sub-technique) | 탐지 룰 ID | 탐지 수준 | 실측 검증 여부 |
|---|---|---|---|---|---|
| **T1595** | Active Scanning | `.001` (Scanning IP Blocks) | `9000001~9000003` | Signature / Protocol Flag | **실측 검증 완료 (PASS)** |
| **T1046** | Network Service Discovery | - | `9000004, 9000005, 9000007` | Threshold / Rate Limit | **실측 검증 완료 (PASS)** |
| **T1190** | Exploit Public-Facing Application | - | `9010001~9010003` | Deep Packet Inspection | **실측 검증 완료 (PASS)** |
| **T1083** | File and Directory Discovery | - | `9010004` | HTTP URI Path Inspection | **실측 검증 완료 (PASS)** |
| **T1005** | Data from Local System | - | `9010005` | File Path (/etc/passwd) | **실측 검증 완료 (PASS)** |
| **T1059** | Command and Scripting Interpreter | `.004` (Unix Shell) | `9030004~9030006, 9030010` | Interactive Banner/Prompt | **실측 검증 완료 (PASS)** |
| **T1059** | Command and Scripting Interpreter | `.007` (JavaScript) | `9010006` | Payload Tag Pattern | **실측 검증 완료 (PASS)** |
| **T1110** | Brute Force | `.001` (Password Guessing) | `9020001, 9020002` | Session Frequency Counter | **실측 검증 완료 (PASS)** |
| **T1071** | Application Layer Protocol | `.001` (Web Protocols) | `9030003` | C2 Beacon Pattern | **실측 검증 완료 (PASS)** |
| **T1071** | Application Layer Protocol | `.004` (DNS) | `9030008` | High-Entropy Query String | **실측 검증 완료 (PASS)** |
| **T1498** | Network Denial of Service | `.001` (Direct Network Flood) | `9000005, 9000006` | Volumetric Threshold | **실측 검증 완료 (PASS)** |

---

## 3. 다단계 킬체인 상관분석 매핑 경로
- **정찰 단계**: T1595.001 (Nmap NULL Scan) ➔
- **초기 침투**: T1190 (Web SQL Injection) ➔
- **지휘 통제**: T1071.001 & T1059.004 (Reverse Shell 4444 세션 확립)
- **상관분석 인시던트**: `INC-10.77.20.20-1787727443` (전체 경로 통합 추적 성공)
