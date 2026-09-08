# 침해유형별 탐지·대응 룰북: IR-02
# SSH 및 웹 인증 무차별 대입 공격 (Authentication Brute Force)

> **시나리오 코드**: `RULE-IR-02`  
> **공격 전술**: MITRE ATT&CK `Credential Access (TA0006)`  
> **핵심 기법**: `T1110` (Brute Force), `T1110.001` (Password Guessing)  
> **연계 룰**: Suricata SID `9020001~9020002` (SSH & Web Login Brute Force)  
> **참조 플레이북**: [`playbooks/05_ssh_brute_force_investigation.md`](file:///C:/Users/user/Documents/ChatGPT/Suricata-Snort-SOC-Lab/playbooks/05_ssh_brute_force_investigation.md)  
> **검증 상태**: `VERIFIED`  

---

## 1. 공격 개요 및 위협 메커니즘

공격자는 시스템 권한을 획득하기 위해 사전 대입(Dictionary Attack) 도구(Hydra, Medusa 등)를 활용하여 SSH 포트(22) 또는 웹 로그인 엔드포인트(`/login`)를 대상으로 고빈도 패스워드 대입을 시도합니다.

```text
[공격자 (10.77.20.20)]                                    [피해 서버 (10.77.30.20)]
         │                                                           │
         │─── 1. SSH Handshake & Auth Fail (User: root) ─────────────>│ ➔ /var/log/auth.log 기록
         │─── 2. SSH Handshake & Auth Fail (User: admin) ────────────>│
         │─── 3. SSH Handshake & Auth Fail (User: ubuntu) ───────────>│
         │─── N. High Frequency Connections (>5 conn / 60s) ────────>│ ➔ Suricata Threshold 트리거
         │                                                           │
         ▼                                                           ▼
[Suricata SID 9020001] ➔ [Wazuh Decoders (sshd_failed_login)] ➔ [SOC 경보 발령]
```

---

## 2. 탐지 시그니처 및 임계치 룰

### 2.1 Suricata 8.0.6 탐지 규칙 (임계치 제어)
```suricata
# 단일 출발지 IP에서 60초 동안 SSH 포트(22)로 5회 이상 연결을 시도하는 패턴 감지
alert tcp $EXTERNAL_NET any -> $HOME_NET 22 (
    msg:"SOC-ATTACK: SSH Brute Force Attack - High Frequency Connection Attempts"; 
    flow:to_server; 
    flags:S; 
    threshold:type both, track by_src, count 5, seconds 60; 
    classtype:attempted-admin; 
    sid:9020001; 
    rev:1;
)

# 웹 로그인 엔드포인트에 대한 고빈도 POST 요청 감지
alert http $EXTERNAL_NET any -> $HOME_NET [80,443,3000] (
    msg:"SOC-ATTACK: Web Login Brute Force - High Volume Authentication Requests"; 
    flow:to_server,established; 
    http.method; content:"POST"; 
    http.uri; content:"/login"; 
    threshold:type both, track by_src, count 10, seconds 60; 
    classtype:attempted-admin; 
    sid:9020002; 
    rev:1;
)
```

---

## 3. 원본 텔레메트리 및 로그 교차 분석

### 3.1 네트워크 계층 (`eve.json`)
```json
{
  "timestamp": "2026-08-26T16:10:02.112450+0900",
  "event_type": "alert",
  "src_ip": "10.77.20.20",
  "dest_ip": "10.77.30.20",
  "dest_port": 22,
  "proto": "TCP",
  "alert": {
    "signature_id": 9020001,
    "signature": "SOC-ATTACK: SSH Brute Force Attack - High Frequency Connection Attempts",
    "severity": 2
  }
}
```

### 3.2 호스트 계층 (`/var/log/auth.log` - Wazuh Agent 수집)
```text
Aug 26 16:10:01 soc-victim sshd[14210]: Failed password for invalid user root from 10.77.20.20 port 48212 ssh2
Aug 26 16:10:03 soc-victim sshd[14214]: Failed password for invalid user admin from 10.77.20.20 port 48214 ssh2
Aug 26 16:10:05 soc-victim sshd[14218]: Failed password for user testuser from 10.77.20.20 port 48216 ssh2
# ⚠️ 최우선 주의 지표: "Accepted password" 가 발생했는지 반드시 확인!
```

---

## 4. 진탐(TP) vs 오탐(FP) 및 위험도 판정

| 구분 | 관측 징후 및 로그 패턴 | 사고 등급 | 후속 조치 |
|---|---|:---:|---|
| **True Positive (침해 성공)** | • 수많은 실패 로그 후 `Accepted password` 로그 관측<br>• 비정상 프로세스 실행 및 쉘 오픈 징후 | **P1 (CRITICAL)** | • 피해 호스트 긴급 격리<br>• 세션 강제 종료 및 패스워드 재설정<br>• 메모리 포렌식 수행 |
| **True Positive (단순 공격 시도)** | • 지속적인 실패 로그만 기록됨 (`Failed password`)<br>• 성공 세션 전무 | **P3 (MEDIUM)** | • 방화벽 공격자 IP 임시 차단<br>• Fail2ban 연동 확인 |
| **False Positive (오탐)** | • 정상 사용자의 패스워드 오입력 (1~2회 후 성공)<br>• 내부 자동화 스크립트의 인증 키 만료 | **BENIGN** | • 계정 담당자 확인 및 키 갱신 안내 |

---

## 5. 단계별 대응 절차

1. **로그 성공 여부 확인**:
   - 피해 서버에서 공격자 IP의 로그인 성공 여부 즉시 쿼리:
     ```bash
     grep "10.77.20.20" /var/log/auth.log | grep "Accepted"
     ```
2. **침해 성공 시 긴급 세션 차단**:
   - 침투한 공격자의 세션 PID 확인 후 강제 종료:
     ```bash
     pkill -u <침해계정명> -9
     ```
3. **네트워크 인바운드 차단 승인**:
   - `PolicyValidator` 통과 후 HITL 큐에서 `10.77.20.20` 차단 승인.
4. **보안 강화 (재발 방지)**:
   - `/etc/ssh/sshd_config` 내 `PermitRootLogin no`, `PasswordAuthentication no` (SSH Key 전용 전환).
