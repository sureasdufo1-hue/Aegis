# 🔍 Suricata vs. Snort 3 심층 비교 분석 및 보안 관제(SOC) 아키텍처

---

## 1. 개요 및 탄생 배경

| 항목 | **Suricata (v7.x)** | **Snort 3 (v3.x)** |
|---|---|---|
| **개발 주체** | OISF (Open Information Security Foundation) | Cisco Talos |
| **태생적 특징** | 처음부터 **멀티스레딩(Multi-threading)** 및 하드웨어 가속 최적화 기반 설계 | 단일 스레드(Snort 2)의 한계를 극복하고 **멀티스레딩 + Lua 설정**으로 전면 재설계 |
| **로그 형식** | **EVE JSON** (표준화된 통합 텔레메트리 스트림) | Unified2, Alert Fast, **Alert JSON** |
| **주요 활용처** | 대규모 트래픽 모니터링, Threat Hunting, NSM (Network Security Monitoring) | 엔터프라이즈 IPS 인라인 차단, Cisco 보안 생태계 연동 |

---

## 2. 핵심 기능 비교

### 2.1 멀티스레딩 및 성능 (Performance & Concurrency)
- **Suricata**:
  - `AF_PACKET`, `DPDK`, `eBPF/XDP` 지원으로 10Gbps~40Gbps+ 고속 네트워크 트래픽 실시간 패킷 처리.
  - 패킷 캡처, 디코딩, 스트림 리어셈블리, 탐지 엔진이 독립된 스레드 풀에서 병렬 실행.
- **Snort 3**:
  - 유연한 Lua 스크립트 기반 구성 및 스레드 풀 아키텍처 도입.
  - Snort 2 대비 CPU 코어 확장성 및 메모리 효율 대폭 개선.

### 2.2 애플리케이션 계층 텔레메트리 (Application Layer & EVE JSON)
- **Suricata EVE JSON**:
  - 단순 Alert뿐만 아니라 `HTTP`, `DNS`, `TLS`, `SSH`, `SMB`, `NFS`, `Flow`, `File Metadata`, `MD5/SHA256 해시`를 **단일 JSON 스트림**으로 출력.
  - SIEM(Elasticsearch, Splunk, OpenSearch, Vector)과의 연동 편의성이 압도적.
- **Snort 3 Alert JSON**:
  - 패킷 헤더 및 경보 메타데이터 중심의 JSON 출력 지원.

---

## 3. 룰(Rule) 문법 비교

### 동일한 SQL Injection 공격 탐지 룰 비교

#### Suricata 7.x 룰 (`web_attacks.rules`):
```suricata
alert http any any -> $HTTP_SERVERS $HTTP_PORTS (
    msg:"SOC-ATTACK: Web SQL Injection - UNION SELECT Attempt";
    flow:established,to_server;
    http.uri;
    content:"union",nocase;
    content:"select",nocase;
    classtype:web-application-attack;
    sid:1000001;
    rev:1;
    metadata:attack_technique T1190, severity High;
)
```

#### Snort 3 룰 (`web_attacks.rules`):
```snort
alert tcp any any -> $HTTP_SERVERS $HTTP_PORTS (
    msg:"SNORT-ATTACK: Web SQL Injection UNION SELECT";
    flow:to_server,established;
    http_uri;
    content:"union",nocase;
    content:"select",nocase;
    classtype:web-application-attack;
    sid:2000010;
    rev:1;
)
```
