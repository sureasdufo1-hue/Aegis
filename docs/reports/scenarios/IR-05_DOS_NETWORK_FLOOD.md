# 침해유형별 탐지·대응 룰북: IR-05
# 서비스 거부 및 패킷 플러딩 공격 (Denial of Service - SYN / ICMP Flood)

> **시나리오 코드**: `RULE-IR-05`  
> **공격 전술**: MITRE ATT&CK `Impact (TA0040)`  
> **핵심 기법**: `T1498` (Network Denial of Service), `T1498.001` (Direct Network Flood)  
> **연계 룰**: Suricata SID `9000008` (ICMP Ping Flood) / Snort SID `9100002`  
> **참조 플레이북**: [`playbooks/02_dos_flood_investigation.md`](file:///C:/Users/user/Documents/ChatGPT/Suricata-Snort-SOC-Lab/playbooks/02_dos_flood_investigation.md)  
> **검증 상태**: `VERIFIED`  

---

## 1. 공격 개요 및 위협 메커니즘

공격자는 피해 서버(`10.77.30.20`)의 네트워크 대역폭을 고갈시키거나 TCP 연결 큐(SYN Backlog)를 포화시켜 정상 사용자의 접속을 마비시키기 위해, 대량의 ICMP Echo 패킷 또는 가짜 출발지 주소의 TCP SYN 패킷을 초당 수천 건 이상 지속적으로 투하합니다.

```text
[공격자 (10.77.20.20)]                                    [피해 서버 (10.77.30.20)]
         │                                                           │
         │─── High Volume TCP SYN Flood (No ACK returned) ───────────>│ ➔ TCP Backlog Exhaustion
         │─── High Rate ICMP Echo (>100 pkts / 1s) ──────────────────>│ ➔ 대역폭 포화
         │                                                           │
         ▼                                                           ▼
[Suricata SID 9000008 탐지] ➔ [Wazuh DoS 경보] ➔ [nftables Rate-Limiting 가동]
```

---

## 2. 탐지 시그니처 및 임계치 룰

### 2.1 Suricata 8.0.6 탐지 규칙
```suricata
# 초당 100건 이상의 ICMP Echo 패킷 폭주 감지
alert icmp $EXTERNAL_NET any -> $HOME_NET any (
    msg:"SOC-ATTACK: ICMP Ping Flood Denial of Service Attempt"; 
    itype:8; 
    icode:0; 
    threshold:type both, track by_src, count 100, seconds 1; 
    classtype:denial-of-service; 
    sid:9000008; 
    rev:1;
)
```

### 2.2 Snort 3.12.2.0 교차 검증 규칙
```snort
alert icmp $EXTERNAL_NET any -> $HOME_NET any (
    msg:"SNORT-ATTACK: ICMP Ping Flood Denial of Service"; 
    itype:8; 
    icode:0; 
    threshold:type both, track by_src, count 100, seconds 1; 
    classtype:denial-of-service; 
    sid:9100002; 
    rev:1;
)
```

---

## 3. 원본 텔레메트리 및 네트워크 부하 분석

### 3.1 네트워크 계층 부하 지표
- **패킷 초당 처리량 (PPS)**: 평시 15 PPS ➔ 공격 시 1,200 PPS 급증 (80배 증가)
- **CPU / 네트워크 인터페이스 점유율**: `nic-victim` 드롭 패킷 발생, 서버 소프트웨어 인터럽트(si) CPU 70% 초과
- **TCP 연결 상태 분석 (`ss -s`)**:
  ```text
  TCP: 1240 (estab 8, closed 1200, orphaned 0, timewait 0)
  TCP: SYN-RECV 소켓 1,180개 적체 (SYN 쿠키 미적용 시 신규 세션 거절)
  ```

---

## 4. 진탐(TP) vs 오탐(FP) 판정 기준

| 구분 | 판정 조건 | 조치 방안 |
|---|---|---|
| **True Positive (진탐)** | • 단일 또는 소수 외부 IP에서 초당 수백~수천 건의 패킷 폭주<br>• 웹 서버 응답 지연 (RTT > 2,000ms) 및 서비스 타임아웃 | • 게이트웨이 레벨 Rate-Limiting 및 드롭 적용<br>• 호스트 커널 SYN Cookies 강제 |
| **False Positive (오탐)** | • 내부 성능 부하 시험 (사전 승인된 Stress Test)<br>• 대규모 패치 배포 중 클라이언트 동시 접속 폭증 | • 화이트리스트 IP 등록 및 시험 일정 확인 |

---

## 5. 단계별 대응 절차

1. **게이트웨이 레벨 트래픽 억제 (Rate-Limiting)**:
   - 게이트웨이(`10.77.10.1`) nftables에서 출발지 IP당 초당 패킷 허용량을 20pps로 엄격히 제한:
     ```bash
     nft add rule inet filter forward ip saddr 10.77.20.20 limit rate over 20/second drop
     ```
2. **호스트 TCP SYN 쿠키 강제 활성화 (SYN Flood 방어)**:
   - 피해 서버에서 SYN 백로그 고갈을 방지하기 위해 커널 파라미터 적용:
     ```bash
     sysctl -w net.ipv4.tcp_syncookies=1
     sysctl -w net.ipv4.tcp_max_syn_backlog=4096
     ```
3. **악의적 플러딩 IP 전면 차단 (블랙홀)**:
   - HITL 승인 큐를 통해 `10.77.20.20` 전면 드롭 집행.
4. **서비스 가용성 복구 확인**:
   - `curl -w "@curl-format.txt" -o /dev/null -s http://10.77.30.20/`로 왕복 지연시간(RTT < 50ms) 복구 검증.
