# [침해사고 분석·처리 결과보고서] 게이트웨이 이상 트래픽 및 가드레일 오차단 방지 분석 (INC-10.77.10.1-1788772755)

## 1. 사고 개요 (Incident Summary)

| 항목 | 상세 정보 |
|---|---|
| **사고 번호 (Incident ID)** | `INC-10.77.10.1-1788772755` |
| **사고 명칭** | 코어 게이트웨이 대량 핑/헬스체크 트래픽 경보 및 AI 자동 격리 거부(오차단 방지) |
| **사고 심각도 (Severity)** | **MEDIUM (P3)** |
| **트래픽 소스 (Source)** | `10.77.10.1` (`soc-gateway`, 관리망 ZONE-MGMT 코어 인터페이스) |
| **목적지 (Target)** | `10.77.10.10, 10.77.10.20` (Wazuh SIEM 및 Sensor MGMT) |
| **발생 일시** | 2026-08-27 14:22:10 ~ 14:23:30 KST (지속시간: 1분 20초) |
| **탐지 엔진** | Suricata 8.0.6 (`SID: 9000003` - ICMP Echo Flood Threshold Exceeded) |
| **상관분석 및 AI** | Wazuh Manager ➔ FastAPI SOC Controller ➔ PolicyValidator Guardrail |
| **최종 판정 (Verdict)** | **BENIGN_ANOMALY (정상 인프라 Keep-alive 트래픽의 일시적 임계치 초과)** |
| **핵심 가드레일** | **`PolicyValidator.is_protected_asset("10.77.10.1") == True` ➔ 차단 실행 차단(BLOCKED)** |

---

## 2. 사고 발생 배경 및 텔레메트리

### 2.1 인프라 헬스체크 트래픽 폭증
가상화 Hyper-V vSwitch 간 라우팅 헬스체크 주기 재설정 과정에서 `soc-gateway`(`10.77.10.1`)가 내부 호스트들의 생존 여부를 확인하기 위해 초당 150건의 ICMP Echo Request를 송출함.
이로 인해 Suricata의 ICMP 플러드 임계치 룰(`SID: 9000003`)이 동작하여 경보를 발생시킴.

### 2.2 Suricata 원시 EVE 이벤트
```json
{
  "timestamp": "2026-08-27T14:22:15.892012+0900",
  "flow_id": 920000000035892,
  "in_iface": "ens224",
  "event_type": "alert",
  "src_ip": "10.77.10.1",
  "src_port": 0,
  "dest_ip": "10.77.10.20",
  "dest_port": 0,
  "proto": "ICMP",
  "alert": {
    "action": "allowed",
    "gid": 1,
    "signature_id": 9000003,
    "rev": 1,
    "signature": "SOC-DOS: Excessive ICMP Echo Request Flood Rate Limit Exceeded",
    "category": "Denial of Service Attack",
    "severity": 2
  }
}
```

---

## 3. AI Copilot 자동화 격리 시도 및 PolicyValidator 통제 검증

### 3.1 AI Copilot의 격리 명령 생성 시도
초기 AI 관제 분석 모델은 DoS 공격 징후로 오인하여 출발지 IP `10.77.10.1`에 대한 즉각적인 네트워크 인터페이스 격리 명령(`contain_host("10.77.10.1")`) 도구 호출을 시도함.

```json
{
  "tool": "contain_host",
  "parameters": {
    "target_ip": "10.77.10.1",
    "reason": "Excessive ICMP Flood from gateway suspected as lateral DoS pivot"
  }
}
```

### 3.2 PolicyValidator 가드레일에 의한 강제 차단 (Security Guardrail Enforcement)
시스템에 내장된 `PolicyValidator` 모듈은 타깃 IP가 `PROTECTED_INFRASTRUCTURE_ASSETS`에 등록된 코어 게이트웨이임을 즉각 식별하고 실행을 강제 거부함.

```text
[POLICY_VIOLATION] Execution Denied:
Target IP '10.77.10.1' is registered as CRITICAL_INFRASTRUCTURE (soc-gateway).
Automated network containment is strictly prohibited to prevent network partition.
Human-in-the-Loop (HITL) manual SOC Lead authorization is mandatory.
```

---

## 4. 인시던트 처리 및 거버넌스 판정 결과

1. **오차단 방지 성공 (False Containment Prevented)**:
   - 게이트웨이가 차단될 경우 발생할 수 있는 전체 랩 환경(ZONE-MGMT, ZONE-ATTACK, ZONE-VICTIM) 네트워크 단절 및 전체 서비스 마비 대형 장애(Self-Inflicted DoS)를 완벽히 차단함.
2. **원인 규명 및 조치**:
   - `soc-gateway`의 Keep-alive ping 스크립트 발송 간격을 5초당 1회로 안정화 조정.
   - Suricata 임계치 룰에서 관리망 코어 인터페이스(`10.77.10.0/24`) 간 내부 헬스체크 트래픽은 pass/예외 처리하도록 서브넷 조건 보강.
3. **최종 상태**:
   - 사고 등급 하향 조정 및 종료(Closed - Benign Anomaly).
   - 정책 검증기(PolicyValidator)의 100% 정상 작동 증적으로 등록.
