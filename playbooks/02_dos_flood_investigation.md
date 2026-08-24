# 🛡️ SOC Playbook 02: 서비스 거부 공격(DoS / ICMP & TCP SYN Flood) 분석 가이드

---

## 1. 개요 (Overview)
- **위협 정의**: 공격자가 대상 시스템 또는 네트워크 대역에 대량의 ICMP Echo 또는 TCP SYN 패킷을 전송하여 네트워크 대역폭 고갈 및 서비스 마비를 유발하는 서비스 거부(Denial of Service) 공격.
- **MITRE ATT&CK**: `T1498` (Network Denial of Service), `T1498.001` (Direct Network Flood)
- **탐지 룰 ID**: Suricata `sid:9000021`, Snort `sid:9100002`

---

## 2. 1차 관제 분석 절차 (Triage Steps)

### Step 1: 트래픽 볼륨 및 초당 패킷 수(PPS) 분석
- **임계치 초과 여부 확인**:
  - Suricata `threshold` 조건 (초당 25패킷 이상 지속) 발동 여부 확인
  - EVE JSON의 `stats` 및 `flow` 로그를 통해 출발지 IP별 대역폭 점유율 분석
- **출발지 IP 스푸핑(Spoofing) 여부 확인**:
  - 동일한 서브넷 또는 비정상적인 IP 대역에서 랜덤한 소스 포트로 대량 유입되는지 식별

### Step 2: 타깃 시스템 가용성 및 리소스 상태 점검
- 대상 서버(`soc-victim`)의 CPU, 메모리 사용량 및 네트워크 패킷 드롭율 점검.
- 웹 서버(HTTP 80/3000) 및 SSH 서비스의 정상 응답 여부(`curl`, `nc`) 헬스체크.

---

## 3. 침해 대응 및 완화 조치 (Containment & Mitigation)

1. **게이트웨이 방화벽 임계치 제어 (Rate Limiting)**:
   - 게이트웨이 `nftables`에 IP별 초당 허용 패킷 제한 룰 적용:
     ```bash
     sudo nft add rule inet filter forward ip protocol icmp limit rate 5/second accept
     sudo nft add rule inet filter forward ip protocol icmp drop
     ```
2. **공격자 IP 블랙리스트 등록**:
   - 공격자 IP(`10.77.20.20` 등)에 대해 인바운드 트래픽 완전 차단(DROP).
3. **SYN Proxy / SYN Cookies 활성화**:
   - 커널 TCP 파라미터 활성화: `sysctl -w net.ipv4.tcp_syncookies=1`

---

## 4. 탐지 룰 튜닝 가이드 (Rule Tuning)
- 정상적인 네트워크 진단 도구나 헬스체크 모니터링에 의한 오탐 발생 시:
  ```suricata
  # 특정 관리자 IP에 대한 ICMP threshold 상향 조정 또는 예외
  pass icmp 10.77.10.10 any -> $HOME_NET any (msg:"Whitelisted Admin Diagnostic Ping"; sid:9000099; rev:1;)
  ```
