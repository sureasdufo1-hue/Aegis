# 침해유형별 탐지·대응 룰북: IR-03
# 웹 애플리케이션 취약점 공격 (Web Application Attacks - SQLi / XSS / LFI / RCE)

> **시나리오 코드**: `RULE-IR-03`  
> **공격 전술**: MITRE ATT&CK `Initial Access (TA0001)`, `Execution (TA0002)`  
> **핵심 기법**: `T1190` (Exploit Public-Facing Application), `T1059` (Command and Scripting Interpreter)  
> **연계 룰**: Suricata SID `9010001~9010007` / Snort SID `9100003~9100006`  
> **참조 플레이북**: [`playbooks/03_web_attack_investigation.md`](file:///C:/Users/user/Documents/ChatGPT/Suricata-Snort-SOC-Lab/playbooks/03_web_attack_investigation.md)  
> **검증 상태**: `VERIFIED` (EV-TUNE-001, EV-E2E-002 연동)  

---

## 1. 공격 개요 및 위협 메커니즘

외부 웹 서버(`10.77.30.20:80`)의 파라미터 검증 미흡 취약점을 악용하여 백엔드 데이터베이스를 탈취하거나(SQL Injection), 서버 시스템 내부의 민감 설정 파일을 열람하고(Path Traversal/LFI), 최종적으로 원격 코드 실행(Log4j JNDI RCE)을 달성하는 웹 공격 벡터입니다.

```text
[공격자 (10.77.20.20)]                                    [웹 서버 (10.77.30.20:80)]
         │                                                           │
         │─── 1. SQLi: GET /item?id=1 UNION SELECT null,username ───>│ ➔ DB 유출 시도
         │─── 2. LFI: GET /view?file=../../../../etc/passwd ────────>│ ➔ 계정 정보 열람
         │─── 3. RCE: GET /login User-Agent: ${jndi:ldap://...} ────>│ ➔ 역방향 명령 실행
         │                                                           │
         ▼                                                           ▼
[Suricata SID 9010001 / 9010007] ➔ [Wazuh Manager (Alert)] ➔ [CorrelationEngine: Stage 2]
```

---

## 2. 탐지 시그니처 및 정규표현식

### 2.1 Suricata 8.0.6 탐지 규칙
```suricata
# Web SQL Injection - UNION SELECT 패턴 (Tuned rev:2)
alert http any any -> $HOME_NET [80,443,3000,8080] (
    msg:"SOC-ATTACK: Web SQL Injection - UNION SELECT Pattern Detected"; 
    flow:to_server,established; 
    http.uri; content:"UNION"; nocase; content:"SELECT"; nocase; distance:0; 
    classtype:web-application-attack; 
    sid:9010001; 
    rev:2;
)

# Web Local File Inclusion (LFI) - /etc/passwd 접근 탐지
alert http any any -> $HOME_NET [80,443,3000,8080] (
    msg:"SOC-ATTACK: Web LFI - Sensitive Credential File (/etc/passwd) Access Attempt"; 
    flow:to_server,established; 
    http.uri; content:"etc/passwd"; 
    classtype:web-application-attack; 
    sid:9010006; 
    rev:1;
)

# Apache Log4j JNDI 원격 코드 실행 시도 (${jndi:})
alert http any any -> $HOME_NET [80,443,3000,8080] (
    msg:"SOC-ATTACK: Remote Code Execution - Apache Log4j JNDI Exploit Attempt"; 
    flow:to_server,established; 
    content:"${jndi:"; nocase; 
    classtype:attempted-admin; 
    sid:9010007; 
    rev:1;
)
```

---

## 3. 원본 텔레메트리 및 HTTP 트랜잭션 분석

### 3.1 Suricata `eve.json` HTTP 페이로드 덤프
```json
{
  "timestamp": "2026-08-26T15:55:48.271820+0900",
  "event_type": "alert",
  "src_ip": "10.77.20.20",
  "dest_ip": "10.77.30.20",
  "dest_port": 80,
  "proto": "TCP",
  "alert": {
    "signature_id": 9010001,
    "signature": "SOC-ATTACK: Web SQL Injection - UNION SELECT Pattern Detected",
    "severity": 1
  },
  "http": {
    "hostname": "10.77.30.20",
    "url": "/search.php?query=1%27%20UNION%20SELECT%20null%2Ctable_name%20FROM%20information_schema.tables--",
    "http_method": "GET",
    "status": 200,
    "length": 4182
  }
}
```

### 3.2 핵심 분석 관점 (웹 서버 응답 코드)
- **응답 코드 200 OK & 대용량 반환 (Status 200, Length > 4000)**:  
  공격 쿼리가 데이터베이스에서 정상 실행되어 실제 테이블 명세나 데이터가 공격자에게 반환되었을 가능성이 매우 높은 **긴급 침해 정황(P1/P2)**.
- **응답 코드 500 Internal Server Error**:  
  SQL 문법 에러 유발 ➔ 취약점 존재 가능성 확인을 위한 탐침 단계.
- **응답 코드 403 Forbidden / 404 Not Found**:  
  WAF에 의해 차단되었거나 유효하지 않은 엔드포인트 ➔ 공격 시도 차단됨 (단순 모니터링).

---

## 4. 진탐(TP) 판정 및 다단계 상관 연계

```text
[판정 매트릭스]
HTTP URI/Body 악성 페이로드 관측 ➔ 웹 서버 HTTP 응답 분석
  ├─ HTTP 200 OK + 데이터 반환 ➔ TRUE_POSITIVE (공격 성공) ➔ 즉시 격리
  ├─ HTTP 500 에러 발생 ➔ TRUE_POSITIVE (취약점 확인 중) ➔ 코드 패치
  └─ HTTP 403/400 차단 ➔ TRUE_POSITIVE (시도 차단됨) ➔ IP 평판 주시
```

다단계 상관분석 엔진(`CorrelationEngine`)은 본 웹 공격 경보(Stage 2: Initial Access)가 수신되면, 선행된 포트 스캔(Stage 1)과 결합하여 즉시 **복합 침해사고(`INC-...`)**로 승격시킵니다.

---

## 5. 단계별 대응 절차

1. **공격자 즉시 차단**:
   - `PolicyValidator` 검증 거쳐 `10.77.20.20` 발 전체 웹 트래픽 차단.
2. **세션 종료 및 파라미터 임시 차단**:
   - 웹 서버(Nginx/Apache) 리버스 프록시 단에서 `UNION SELECT` 정규식 WAF 룰 즉시 활성화.
3. **데이터 유출 범위 포렌식**:
   - 웹 서버 액세스 로그(`access.log`)와 데이터베이스 감사 로그(`query.log`) 교차 대조.
   - 유출된 테이블(`users`, `credentials` 등) 확인 및 비밀번호 강제 초기화.
4. **시큐어 코딩 패치**:
   - 동적 SQL 결합(`"SELECT * FROM users WHERE id=" + input`)을 PreparedStatement(바인딩 변수) 구조로 전면 수정.
