# [침해사고 분석·처리 결과보고서] 웹 애플리케이션 표적 SQL Injection 공격 (INC-10.77.20.88-1788772741)

## 1. 사고 개요 (Incident Summary)

| 항목 | 상세 정보 |
|---|---|
| **사고 번호 (Incident ID)** | `INC-10.77.20.88-1788772741` |
| **사고 명칭** | 웹 애플리케이션 SQL Injection 및 비인가 데이터베이스 덤프 시도 |
| **사고 심각도 (Severity)** | **HIGH (P2)** |
| **공격 출발지 (Attacker)** | `10.77.20.88` (`soc-attacker-sub`, 공격망 ZONE-ATTACK) |
| **피해 대상 (Victim)** | `10.77.30.20:80` (`soc-victim`, 내부망 ZONE-VICTIM) |
| **발생 일시** | 2026-08-27 10:14:02 ~ 10:14:48 KST (지속시간: 46초) |
| **탐지 엔진** | Suricata 8.0.6 (`SID: 9010001, 9010003`) + Snort 3 (`SID: 9100001`) |
| **상관분석 및 SIEM** | Wazuh Manager 4.14.7 ➔ Indexer (OpenSearch) ➔ AI RAG Copilot 분석 |
| **최종 판정 (Verdict)** | **TRUE_POSITIVE (웹 취약점 익스플로잇 시도)** |
| **관련 증적** | `EV-WEB-003`, `sqli_dump_attempt.pcap`, `wazuh_alert_sqli.json` |

---

## 2. 사고 발생 타임라인 및 패킷 분석 (Timeline & Packet Details)

```text
[10:14:02] Nmap HTTP 취약점 스캐너 구동 (User-Agent: sqlmap/1.8.3#stable)
    │
[10:14:15] 다중 파라미터 조작 SQL Injection 쿼리 주입 (SID: 9010001 rev:2)
    │     (URI: /dvwa/vulnerabilities/sqli/?id=1'+OR+'1'='1&Submit=Submit)
    ▼
[10:14:31] 데이터베이스 스키마 정보 탈취 시도 (SID: 9010003 rev:1)
    │     (URI: /dvwa/vulnerabilities/sqli/?id=1'+UNION+SELECT+null,table_name+FROM+information_schema.tables--)
    ▼
[10:14:48] 비정상 500 에러 및 DB 에러 반환 확인 후 공격자 세션 단절
```

### 2.1 주요 패킷 페이로드 덤프
```http
GET /dvwa/vulnerabilities/sqli/?id=1%27%20UNION%20SELECT%20null%2Ctable_name%20FROM%20information_schema.tables-- HTTP/1.1
Host: 10.77.30.20
User-Agent: sqlmap/1.8.3#stable (https://sqlmap.org)
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Connection: close
Referer: http://10.77.30.20/dvwa/vulnerabilities/sqli/
Cookie: PHPSESSID=9a8b7c6d5e4f3a2b1c0d; security=low
```

---

## 3. 원시 텔레메트리 및 탐지 내역

### 3.1 Suricata EVE Alert Event
```json
{
  "timestamp": "2026-08-27T10:14:31.849102+0900",
  "flow_id": 920000000031849,
  "in_iface": "ens224",
  "event_type": "alert",
  "src_ip": "10.77.20.88",
  "src_port": 51234,
  "dest_ip": "10.77.30.20",
  "dest_port": 80,
  "proto": "TCP",
  "alert": {
    "action": "allowed",
    "gid": 1,
    "signature_id": 9010003,
    "rev": 1,
    "signature": "SOC-ATTACK: Web SQL Injection - information_schema Reconnaissance Attempt",
    "category": "Web Application Attack",
    "severity": 2,
    "metadata": {
      "mitre_attack_id": ["T1190"],
      "rule_origin": "custom"
    }
  },
  "http": {
    "hostname": "10.77.30.20",
    "url": "/dvwa/vulnerabilities/sqli/?id=1'+UNION+SELECT+null,table_name+FROM+information_schema.tables--",
    "http_user_agent": "sqlmap/1.8.3#stable",
    "http_method": "GET",
    "protocol": "HTTP/1.1",
    "status": 200,
    "length": 4512
  }
}
```

### 3.2 AI RAG Copilot 자동 진단 소견 (FastAPI Tool Execution)
- **질의 컨텍스트**: `playbooks/03_web_attack_investigation.md` 자동 임베딩 검색 (Top-1 similarity score: 0.932).
- **진단 결과**: 악의적 자동화 도구(sqlmap)를 통한 표적 데이터 추출 시도로 판정. 백엔드 DB 레코드 유출 가능성 존재.
- **추천 조치**: `soc-gateway` 방화벽에서 IP `10.77.20.88`에 대한 80/TCP 접근 차단 및 웹 세션 쿠키 강제 파기.

---

## 4. 대응 및 조치 내역 (Mitigation Actions)

1. **임시 차단**:
   - `soc-gateway` nftables IP 블랙리스트 등록:
     ```bash
     nft add element inet filter blacklist { 10.77.20.88 }
     ```
2. **취약점 조치**:
   - 웹 소스코드 `dvwa/vulnerabilities/sqli/source/low.php` 내 동적 SQL 쿼리를 Prepared Statement (PDO) 구조로 리팩터링 적용.
3. **데이터 유출 조사**:
   - MySQL 감사로그(`general_log`) 대조 결과, `information_schema.tables` 쿼리 1건 실행 후 시스템 테이블 구조는 일부 응답되었으나 실제 민감 사용자 계정 테이블(`users`) 데이터 덤프는 실패한 것으로 확인 (2차 피해 차단 성공).

---

## 5. 결론 및 감사 소견
본 건은 자동화 공격 툴(sqlmap)을 이용한 고속 취약점 정찰 시도였으나, Suricata 룰(`SID: 9010001, 9010003`)과 Snort 보조 엔진에 의해 실시간으로 탐지되었으며, 관제 요원 및 게이트웨이 방화벽의 신속한 차단을 통해 실제 비즈니스 데이터베이스 탈취를 사전에 방어하였다.
