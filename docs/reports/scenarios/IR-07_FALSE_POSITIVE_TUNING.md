# [룰북 IR-07] 탐지 룰 튜닝 및 오탐(False Positive) 제거 표준 운영절차

## 1. 개요 및 목적
본 룰북은 보안 관제 현장에서 발생하는 오탐(False Positive, FP) 및 과탐(Over-alerting)을 체계적으로 식별, 분석, 개선하고, 정상적인 비즈니스 트래픽에 대한 오차단·관제 피로도를 제거하면서도 공격 행위에 대한 탐지율(True Positive, TP) 100%를 보존하기 위한 탐지 엔지니어링 튜닝 라이프사이클(Detection Engineering Lifecycle) 표준을 규정한다.

NIST SP 800-61 Rev.3 "Post-Incident Activity & Continuous Improvement" 및 Detection-as-Code(DaC) 원칙에 따라, 룰 수정 시 형상 관리(Git), 회귀 검증(Regression Test), 듀얼 엔진 상호 검증, 객관적 증적(EV-TUNE-001) 확보 절차를 필수 수행한다.

---

## 2. 튜닝 라이프사이클 8단계 표준 프로세스

```text
[1. 오탐 식별] ──> [2. 원인 분석] ──> [3. PCAP 추출] ──> [4. 룰 개선]
   (Alert 확인)     (정상 업무 판정)    (원시 패킷/헤더)   (rev 증가/정규화)
                                                                 │
[8. 증적 등록] <── [7. 운영 배포] <── [6. 공격 유지 검증] <── [5. 오탐 제거 검증]
  (EV-TUNE-001)    (Hot-reload/커밋)    (공격 패킷 100% 탐지)  (정상 트래픽 경보 미발생)
```

| 단계 | 수행 항목 | 세부 내용 및 통제 기준 | 담당자 |
|---|---|---|---|
| **Step 1** | 오탐 접수 및 식별 | 관제 화면 대량 경보, 개발/운영 부서 정상 트래픽 차단 소명 접수 | L1 관제원 / L2 분석가 |
| **Step 2** | 정밀 원인 분석 | EVE 원시 이벤트, 페이로드 바이트, HTTP 헤더 정밀 디코딩 | L2 분석가 / 엔지니어 |
| **Step 3** | 패킷/로그 증적 확보 | Wireshark/tshark 기반 세션 추출 (`normal_traffic.pcap`, `attack_traffic.pcap`) | 포렌식 분석가 |
| **Step 4** | 룰 시그니처 개선 | 광범위 키워드 제거, 세부 프로토콜 버퍼(`http.uri`, `http.header`) 한정, `rev` 증가 | Detection Engineer |
| **Step 5** | 정상 트래픽 재검증 | 튜닝 룰셋 적용 후 정상 패킷 주입 ➔ 경보 미발생(No Alert) 확인 | 엔지니어 / QA |
| **Step 6** | 공격 트래픽 재검증 | 동일 룰셋에서 실제 공격 패킷 주입 ➔ 100% 정상 탐지(True Positive) 확인 | Red Team / 엔지니어 |
| **Step 7** | 운영 환경 배포 | `suricata -T` 문법 검증 ➔ `suricatasc -c reload-rules` 무중단 리로드 | 시스템 운영자 |
| **Step 8** | 증적 기록 및 형상 관리 | `metadata.md`, Before/After 비교표, Git 커밋 해시 등록 (`EV-TUNE-001`) | 감사관 / 리드 엔지니어 |

---

## 3. 대표 튜닝 실증 사례 (Case Study: HTTP Rule Tuning)

### 3.1 튜닝 대상 룰 개요 (SID: 9010001)
- **발생 문제**: 정상 웹 애플리케이션의 일반 `GET /index.html` 요청 시, 단순 `http.method: "GET"` 매칭 조건으로 인해 과도한 오탐 경보가 분당 수백 건 발생하여 관제 마비 초래.
- **개선 목표**: 정상 GET 요청에 대한 경보를 0건으로 제거하고, 악의적인 공격 URI(`GET /suspicious?query=...`)만을 정확히 탐지하도록 한정.

### 3.2 Before / After 시그니처 비교

#### [튜닝 전: Baseline rev:1 (과탐 유발)]
```suricata
# 광범위 매칭으로 인해 모든 HTTP GET 요청에 오탐 발생
alert http 10.77.20.0/24 any -> 10.77.30.20 80 (
    msg:"SOC-ATTACK: Broad HTTP GET Request Detected (FP prone)";
    flow:established,to_server;
    http.method; content:"GET";
    classtype:web-application-activity;
    sid:9010001; rev:1;
)
```

#### [튜닝 후: Tuned rev:2 (최적화 완료)]
```suricata
# URI 경로 제약(/suspicious) 및 세부 패턴 매칭을 추가하여 정상 트래픽 격리
alert http 10.77.20.0/24 any -> 10.77.30.20 80 (
    msg:"SOC-ATTACK: Web Application Suspicious Path Access Attempt";
    flow:established,to_server;
    http.method; content:"GET";
    http.uri; content:"/suspicious"; fast_pattern;
    classtype:web-application-attack;
    sid:9010001; rev:2;
)
```

---

## 4. 실측 검증 데이터 및 매트릭스

본 튜닝 결과는 `scripts/verify_detection_tuning.py` 및 `tests/test_detection_tuning.py` 자동화 파이프라인을 통해 전수 검증되었다.

| 검증 단계 (Stage) | 적용 룰 정의 (Rule Definition) | 정상 트래픽 주입 (Normal GET) | 악성 공격 트래픽 주입 (Attack Vector) | 판정 (Verdict) |
|---|---|---|---|---|
| **Baseline (rev:1)** | `http.method: "GET"` (단순 메서드) | **ALERT (False Positive 발생)** | **ALERT (Detected)** | **FAIL (과탐)** |
| **Tuned (rev:2)** | `http.uri: "/suspicious"` (경로 한정) | **NO ALERT (정상 통과)** | **ALERT (정상 탐지: TP)** | **PASS (최적화)** |

### 검증 게이트 통과 기준
1. **GATE-FP-01 (PASS)**: 오탐 원인이 상세 문서화되고 비즈니스 영향도가 분석되었는가?
2. **GATE-TUNE-CONFIG-01 (PASS)**: `rev` 번호가 증가되고 `suricata -T` 문법 테스트를 무결하게 통과하였는가?
3. **GATE-TUNE-01 (PASS)**: 정상 트래픽 오탐이 완전 제거되고, 공격 트래픽 탐지율이 100% 유지되었는가?

---

## 5. Snort 3 보조 엔진 동기화 규칙
Suricata 튜닝 시 Snort 보조 검증 룰(`SID: 9100001`) 역시 동일한 URI 제약 조건으로 동기화하여 듀얼 엔진 간 검증 불일치가 발생하지 않도록 통제한다.

```lua
-- snort/rules/local.rules (SID: 9100001 rev:2)
alert tcp $EXTERNAL_NET any -> $HOME_NET 80 (
    msg:"SOC-SNORT: Web Suspicious Path Access Attempt";
    flow:to_server,established;
    http_uri; content:"/suspicious",fast_pattern;
    classtype:web-application-attack;
    sid:9100001; rev:2;
)
```

---

## 6. 증적 및 형상 관리
- **공식 증적 ID**: `EV-TUNE-001` (`evidence/EV-TUNE-001/metadata.md`)
- **실행 스크립트**: `python scripts/verify_detection_tuning.py`
- **회귀 테스트**: `pytest tests/test_detection_tuning.py`
