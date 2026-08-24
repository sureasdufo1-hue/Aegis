# ✍️ IDS/IPS 시그니처 룰 엔지니어링 가이드 (Rule Writing & Tuning)

---

## 1. 룰 기본 구조 (Rule Anatomy)

```
[Action] [Protocol] [Source IP] [Source Port] -> [Dest IP] [Dest Port] ( [Options] )
```

- **Action**: `alert` (경보 발생), `drop` (인라인 차단 및 패킷 폐기), `pass` (화이트리스트 통과), `reject` (RST/ICMP Unreachable 전송 후 차단).
- **Protocol**: `ip`, `tcp`, `udp`, `icmp`, `http`, `dns`, `tls`, `ssh`, `ftp`.
- **Direction**: `->` (단방향), `<>` (양방향).

---

## 2. 핵심 옵션 및 키워드

### 2.1 메타데이터 및 식별자
- `msg:"경보 메시지"`: 관제 콘솔에 표시될 상세 경보 이름.
- `sid:1000001`: Signature ID (커스텀 룰은 1,000,000번대 이상 사용 권장).
- `rev:1`: 룰 개정 버전 번호.
- `classtype:web-application-attack`: 취약점/공격 유형 분류.
- `metadata:attack_technique T1190, severity High`: MITRE ATT&CK 기법 번호 및 심각도.

### 2.2 페이로드 검사 (Payload Matching)
- `content:"문자열"`: 패킷 내 일치할 문자열 지정.
- `nocase`: 대소문자 구분 없이 매칭.
- `pcre:"/정규표현식/i"`: 정규표현식 기반 복합 패턴 매칭.
- `http.uri` / `http_uri`: HTTP Request URL 경로 영역으로 검색 한정 (CPU 효율 및 정확도 대폭 향상).
- `http.header` / `http_header`: HTTP 요청/응답 헤더 검사.
- `http.user_agent`: User-Agent 헤더 검사.

### 2.3 트래픽 제어 및 임계치 (Thresholding & Rate Limiting)
- **Suricata Threshold**:
  ```suricata
  threshold:type both, track by_src, count 10, seconds 60;
  ```
- **Snort Detection Filter**:
  ```snort
  detection_filter:track by_src, count 10, seconds 60;
  ```

---

## 3. 오탐/미탐 튜닝 (Rule Tuning)

1. **오탐(False Positive) 방지 팁**:
   - `content` 검색 시 `http.uri` 또는 `http.header` 등 버퍼(Buffer)를 명확히 지정할 것.
   - 포괄적인 단어 매칭(`content:"select"`) 대신 문맥이 포함된 패턴(`content:"union", content:"select"`) 사용.
2. **미탐(False Negative) 방지 팁**:
   - URL 인코딩(`%20`, `%2e%2e`), 16진수 인코딩 등 우회 기법 대응을 위해 정규표현식 또는 노멀라이저 활용.
