# 침해유형별 탐지·대응 룰북: IR-06
# 다단계 킬체인 복합 침해사고 (Multi-Stage Attack Chain Correlation)

> **시나리오 코드**: `RULE-IR-06`  
> **공격 전술**: MITRE ATT&CK `Reconnaissance` ➔ `Initial Access` ➔ `Command and Control`  
> **기법 체인**: `T1595` (Scan) ➔ `T1190` (Exploit Web) ➔ `T1059` (Command Execution)  
> **연계 엔진**: `analyzer/detection/correlation_engine.py` (30분 슬라이딩 윈도우)  
> **실측 증적**: [`evidence/EV-E2E-002/`](file:///C:/Users/user/Documents/ChatGPT/Suricata-Snort-SOC-Lab/evidence/EV-E2E-002/)  
> **검증 상태**: `VERIFIED`  

---

## 1. 다단계 공격 체인 및 상관분석 메커니즘

단일 경보(Single Alert)만을 모니터링할 경우, 정찰 스캔은 단순 경보로 취급되어 간과되기 쉽습니다. 그러나 지능형 지속 위협(APT)은 반드시 정찰 ➔ 침투 ➔ C2 연결의 순차적 단계를 거칩니다.  
본 랩의 `CorrelationEngine`은 동일 공격자(`10.77.20.20`)로부터 30분 이내에 발생하는 이종 경보들을 세션으로 결합하여 2개 이상의 공격 단계가 교차할 때 즉시 **복합 침해사고(Incident)**로 자동 승격시킵니다.

```text
[단계 1: 정찰 (Reconnaissance)]
  - 15:55:18 | Nmap NULL Stealth Scan 탐지 (SID 9000001)
  - 공격 단계: "1. Reconnaissance" 분류
        │
        ▼ (동일 세션 추적: 30분 윈도우 유지)
[단계 2: 초기 침투 (Initial Access / Exploitation)]
  - 15:55:48 | Web SQL Injection UNION SELECT 탐지 (SID 9010001)
  - 공격 단계: "2. Initial Access / Exploitation" 분류
  - 🚨 상관분석 엔진 1차 승격 (다단계 위협 경보)
        │
        ▼
[단계 3: 원격 제어 (Command & Control / Execution)]
  - 15:56:18 | Interactive Reverse Shell /bin/sh 포트 4444 수립 (SID 9030010)
  - 공격 단계: "3. Command & Control / Execution" 분류
  - 🚨🚨 최종 최고 등급 P1 CRITICAL 사고 자동 확정 (INC-10.77.20.20-1787727443)
```

---

## 2. 상관분석 엔진 룰 및 승격 알고리즘

### 2.1 공격 단계 매핑 로직 (`classify_stage`)
```python
def classify_stage(self, alert: NormalizedAlert) -> str:
    sig = alert.signature.upper()
    if any(k in sig for k in ["SCAN", "RECON", "NULL", "XMAS", "FIN", "NIKTO", "DIRBUSTER"]):
        return "1. Reconnaissance"
    elif any(k in sig for k in ["SQL INJECTION", "XSS", "TRAVERSAL", "BRUTE FORCE", "LOG4J"]):
        return "2. Initial Access / Exploitation"
    elif any(k in sig for k in ["REVERSE SHELL", "METERPRETER", "COBALT", "BEACON", "TUNNELING"]):
        return "3. Command & Control / Execution"
    elif any(k in sig for k in ["EXFILTRATION", "CREDIT CARD", "LEAK"]):
        return "4. Exfiltration"
    return "Generic Security Activity"
```

### 2.2 사고 승격 및 플레이북 자동 바인딩
- **조건**: `len(stages) >= 2` 또는 `any(severity == CRITICAL)`
- **자동 바인딩 플레이북**:
  - C2 단계 포함 시: `playbooks/04_malware_c2_investigation.md` 자동 지정
  - Exploitation 단계 포함 시: `playbooks/03_web_attack_investigation.md` 자동 지정
  - Recon 단계 포함 시: `playbooks/01_port_scan_investigation.md` 자동 지정

---

## 3. 원본 텔레메트리 연계 매핑 (`EV-E2E-002`)

| 단계 | Suricata SID | Flow ID | Wazuh Alert ID | 탐지 룰 메시지 | OpenSearch 인덱스 |
|---|---|---|---|---|---|
| **1. 정찰** | `9000001` | `920000000027384` | `1787727385.25830` | Nmap Stealth NULL Scan Detected | `wazuh-alerts-4.x-2026.08.26` |
| **2. 침투** | `9010001` | `920000000027385` | `1787727385.27182` | Web SQL Injection - UNION SELECT Pattern | `wazuh-alerts-4.x-2026.08.26` |
| **3. C2** | `9030010` | `920000000027386` | `1787727385.24350` | Interactive Reverse Shell Session Established | `wazuh-alerts-4.x-2026.08.26` |

---

## 4. AI-Orchestrated SOC Copilot 통합 분석 워크플로우

1. **상관사고 발생 감지**:
   - 웹 관제 콘솔에 붉은색 경고 배너 및 `INC-10.77.20.20-1787727443` 카드 표출.
2. **원클릭 AI 심층 조사 트리거**:
   - 분석가가 [AI 심층 조사] 버튼 클릭.
   - 4단계 백그라운드 파이프라인 가동:
     - **1단계**: 보안 도구 호출 (`lookup_threat_intel`, `verify_pcap_integrity`)
     - **2단계**: RAG 지식베이스 검색 (800자 청크 추출)
     - **3단계**: 로컬 LLM(Qwen 3.5) 추론 (경과시간 스톱워치 및 75% 프로그레스 바 표출)
     - **4단계**: 독립 정책 검증기(`PolicyValidator`) 대응안 검증
3. **분석 결과 구조화 (Pydantic AIIncidentAnalysis)**:
   - 사실(Facts): 10.77.20.20이 스캔 후 SQLi를 통해 리버스 셸을 수립함.
   - 가설(Hypotheses): 공격자가 데이터베이스 덤프 및 내부망 추가 전파를 준비 중임.
   - 기법(Techniques): `T1046`, `T1190`, `T1059`
   - 제안 조치: `ISOLATE_HOST(10.77.30.20)`, `BLOCK_IP(10.77.20.20)`

---

## 5. 단계별 긴급 대응 및 사후 통제

1. **인간 승인 큐(HITL Approval Gate) 결정**:
   - 분석가가 제안 조치 2건(호스트 격리, 공격자 차단)을 확인하고 [모의 실행 승인(Dry-Run)] 또는 [실행 승인] 클릭.
2. **게이트웨이 nftables 룰 적용**:
   - 공격자 IP 차단 및 피해 호스트 통신 격리 (SIEM 포트 1514만 예외 유지).
3. **피해 호스트 세션 종료 및 무결성 복구**:
   - `/bin/sh` 프로세스 사살, 임시 생성 파일 삭제, 웹 취약점 패치.
4. **사후 룰북 피드백**:
   - 상관분석 윈도우(30분) 적정성 평가 및 상관 규칙 임계치 최적화.
