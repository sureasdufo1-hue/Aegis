# M1·M2 통합 네트워크 인프라 기반 SOC 관제 시스템 배포 매뉴얼

> **문서 버전:** v1.0  
> **대상 인프라:** M1·M2 통합 네트워크 보안 인프라 (Cisco L3/L2, AhnLab TrusGuard, VMware Workstation)  
> **연동 시스템:** SOC Detection & Monitoring Platform (Suricata 8.0.6, Snort 3, ELK 8.17.3, Wazuh 4.14.7, FastAPI AI Web Console)  
> **작성 일자:** 2026-09-23  

---

## 1. 개요 및 배포 아키텍처

본 매뉴얼은 `M1·M2 통합 네트워크 보안 인프라 구축 및 재구축 매뉴얼`에 명시된 물리·가상망 환경(AhnLab TrusGuard 차세대 방화벽, Cisco L3/L2 스위치, DMZ 웹 서버, VLAN 10/20/30 서버팜, SPAN 수집망)에 **실시간 듀얼 IDS, 통합 SIEM, AI 심층 침해사고 분석, SOAR 인간 승인 대응 플랫폼**을 구축하는 엔지니어링 표준 절차서입니다.

처음 작업을 수행하는 엔지니어도 IP 대역 변경 및 포트 연결을 혼동 없이 따라 할 수 있도록 **사전 점검 ➔ IP 매핑 ➔ 센서 배포 ➔ SIEM/대시보드 기동 ➔ 연동 검증** 순으로 기술합니다.

```
                           [ 외부망 / 공격자 시뮬레이션 ]
                                 (10.10.70.128/25)
                                        │
                               [ eth1: 10.10.70.214 ]
                    ┌───────────────────┴───────────────────┐
                    │      AhnLab TrusGuard 차세대 방화벽   │
                    │   - NAT: SNAT .163 / WEB_VIP .164     │
                    └───────┬───────────────────────┬───────┘
          [eth3: 172.16.10.1]                       │ [eth2: 192.168.40.1/30 Transit]
                    │                               │
            ┌───────┴───────┐                       │
            │  DMZ Web 서버 │                       │
            │ 172.16.10.10  │                       │
            │ (Wazuh Agent) │                       │
            └───────────────┘               [Gi1/0/24: 192.168.40.2/30]
                                            ┌───────┴────────────────────────┐
                                            │      Cisco L3SW (cb-l3sw01)    │
                                            │   - SVI 10: 192.168.10.1/24    │
                                            │   - SVI 20: 192.168.20.1/24    │
                                            │   - SVI 30: 192.168.30.1/24    │
                                            │   - Gi1/0/13: SPAN 복제 송출  │
                                            │   - Gi1/0/4:  관리망 .40.5/30  │
                                            └───────┬──────────────┬─────────┘
                   ┌────────────────────────────────┘              └──────────────────┐
     [Gi1/0/13 SPAN 미러링]                                               [Gi1/0/4 관리망 .40.5]
                   │                                                                  │
      ┌────────────┴─────────────┐                                      ┌─────────────┴─────────────┐
      │  [soc-sensor] 센서 서버   │                                      │   [soc-siem] 관제 서버    │
      │  (구 Analyse PC 2 고도화) │                                      │   (구 Analyse PC 1 / LOG) │
      │ ──────────────────────── │                                      │ ───────────────────────── │
      │ • 무IP 캡처 NIC (AF_PACKET)│────── eve.json (5044/TCP) ─────────▶ │ • Elasticsearch 8.17.3    │
      │ • Suricata 8.0.6 실시간    │                                      │ • Logstash 8.17.3         │
      │ • Snort 3 오프라인 검증  │                                      │ • Kibana 8.17.3 (Port 5602)│
      │ • Wazuh Agent            │                                      │ • FastAPI 웹 콘솔 (8501) │
      └──────────────────────────┘                                      │ • AI 심층 조사 엔진 (Qwen)│
                                                                        └───────────────────────────┘
```

---

## 2. 네트워크 및 IP 주소 체계 매핑표

기존 실습용 격리망 IP(`10.77.x.x`)를 M1·M2 실제 네트워크 환경으로 변환하는 공식 기준표입니다:

| 영역 구분 | 기존 Lab IP (격리 가상망) | **M1·M2 실제 환경 IP / 객체** | 연결 인터페이스 및 역할 |
|---|---|---|---|
| **외부 / 공격망** | `10.77.20.0/24` | **`10.10.70.128/25`** | TrusGuard `eth1` (10.10.70.214, 상위 GW .129) |
| **방화벽 SNAT / VIP** | N/A | **`10.10.70.163` / `.164`** | `SNAT_IP` (.163), `WEB_VIP` (.164) |
| **방화벽 Transit** | `10.77.10.1` ↔ `10.77.20.1` | **`192.168.40.1/30` ↔ `.40.2/30`** | TrusGuard `eth2` ↔ Cisco L3SW `Gi1/0/24` |
| **DMZ 웹 서버** | N/A | **`172.16.10.10/24`** | TrusGuard `eth3` (GW: `172.16.10.1`) |
| **VLAN 10 (관리망)** | `10.77.10.0/24` | **`192.168.10.0/24`** | L3 SVI `192.168.10.1` (Admin PC: `.10.2`, VM1: `.10.101`) |
| **VLAN 20 (내부망)** | `10.77.20.0/24` | **`192.168.20.0/24`** | L3 SVI `192.168.20.1` (User PC: `.20.2`, VM2: `.20.101`) |
| **VLAN 30 (서버팜)** | `10.77.30.0/24` | **`192.168.30.0/24`** | L3 SVI `192.168.30.1` (DB: `.30.2`, LOG/SIEM: `.30.3`) |
| **Analyse 관리망** | N/A | **`192.168.40.4/30`** | L3SW `Gi1/0/4` (`.40.5`) ↔ 관제 서버 (`.40.6`) |
| **SPAN 패킷 미러링**| Hyper-V Port Mirroring | **Cisco SPAN (`Gi1/0/13`)** | Source: `Gi1/0/24` (양방향) ➔ Dest: `Gi1/0/13` |

---

## 3. 사전 요구사항 및 장비 준비

### 3.1 하드웨어 및 OS 사양
1. **관제 서버 (`soc-siem` - 구 Analyse PC 1 또는 VLAN30 LOG 서버):**
   * **OS:** Ubuntu 22.04 LTS 또는 Windows 10/11 (WSL2/Docker Desktop)
   * **사양:** CPU 4코어 이상, RAM 16GB 이상, SSD 100GB 이상
   * **설치 소프트웨어:** Docker Engine 24+, Docker Compose v2, Python 3.10+
2. **센서 서버 (`soc-sensor` - 구 Analyse PC 2):**
   * **OS:** Ubuntu 22.04 LTS Server 권장
   * **사양:** CPU 4코어 이상, RAM 8GB 이상
   * **NIC 2개 필수:**
     * `NIC 1 (캡처용)`: L3SW `Gi1/0/13` 연결 (**IP 미할당**, 프로미스큐어스 모드)
     * `NIC 2 (관리용)`: L3SW `Gi1/0/4` (`192.168.40.6/30`) 또는 VLAN 10/30 스위치 연결

---

## 4. 단계별 상세 배포 절차

### 1단계: Cisco L3SW SPAN 패킷 미러링 설정 (cb-l3sw01)

L3 스위치 콘솔에 접속하여 방화벽 Transit 구간 트래픽을 센서로 복제하도록 설정합니다.

```cisco
cb-l3sw01# configure terminal

! 1. 방화벽 Transit 인터페이스 확인
interface GigabitEthernet1/0/24
 description TRANSIT_TO_TRUSGUARD_ETH2
 no switchport
 ip address 192.168.40.2 255.255.255.252
 no shutdown
exit

! 2. SPAN 목적지 포트 활성화 (센서 연결 포트)
interface GigabitEthernet1/0/13
 description SPAN_DESTINATION_TO_SOC_SENSOR
 no shutdown
exit

! 3. SPAN 세션 구성 (Transit 포트의 양방향 패킷 복제)
monitor session 1 source interface GigabitEthernet1/0/24 both
monitor session 1 destination interface GigabitEthernet1/0/13
end

! 4. 설정 검증 및 저장
show monitor session all
copy running-config startup-config
```

> **검증 기준:** `show monitor session 1` 실행 시 `Source Ports: Gi1/0/24 Both`, `Destination Ports: Gi1/0/13` 상태가 출력되어야 합니다.

---

### 2단계: 센서 서버 (`soc-sensor`) 캡처 NIC 및 Suricata 설정

#### 2.1 캡처 NIC 무IP 설정 (Ubuntu Linux)
센서의 캡처 인터페이스(예: `ens33`)는 IP 주소 없이 순수 패킷 캡처용으로 활성화합니다.

```bash
# 1. 캡처 NIC IPv4/IPv6 제거 및 무차별 모드(Promiscuous) 활성화
sudo ip link set ens33 promisc on
sudo ip -4 addr flush dev ens33
sudo ip link set ens33 up

# 2. tcpdump를 통한 미러링 패킷 인입 실측 (GATE-NET-01)
sudo tcpdump -eni ens33 -c 10
```
> [!IMPORTANT]
> `tcpdump`에서 방화벽 통과 트래픽(`192.168.40.1 <-> 192.168.40.2`)이나 VLAN 패킷이 캡처되지 않으면 이후 모든 IDS 작업이 무의미합니다. 반드시 패킷 인입을 먼저 확인하십시오.

#### 2.2 Suricata 네트워크 기준선 변경 (`/etc/suricata/suricata.yaml`)
M1·M2 내부망을 보호 대역(`HOME_NET`)으로 정의합니다.

```yaml
# /etc/suricata/suricata.yaml 수정
vars:
  address-groups:
    HOME_NET: "[192.168.10.0/24,192.168.20.0/24,192.168.30.0/24,172.16.10.0/24,192.168.40.0/30]"
    EXTERNAL_NET: "!$HOME_NET"
    HTTP_SERVERS: "[172.16.10.10]"
    SQL_SERVERS: "[192.168.30.2]"

af-packet:
  - interface: ens33
    cluster-id: 99
    cluster-type: cluster_flow
    defrag: yes
    use-mmap: yes

default-log-dir: /var/log/suricata
```

```bash
# Suricata 구문 검증 및 서비스 재시작
sudo suricata -T -c /etc/suricata/suricata.yaml
sudo systemctl restart suricata
sudo tail -f /var/log/suricata/eve.json
```

---

### 3단계: 관제 서버 (`soc-siem`) ELK 스택 및 파이프라인 배포

관제 서버(`192.168.40.6` 또는 `192.168.30.3`)에 접속하여 저장소를 Clone하고 Docker 스택을 기동합니다.

```bash
# 1. 레포지토리 Clone 및 이동
git clone <repository-url> Suricata-Snort-SOC-Lab
cd Suricata-Snort-SOC-Lab

# 2. 환경 변수 설정
cp .env.example .env
# .env 파일 내 ELASTIC_PASSWORD 및 노출 바인딩 IP 확인
```

#### 3.1 Logstash 수집 파이프라인 IP 확인 (`infrastructure/elk/pipeline/`)
* **Suricata 파이프라인 (`suricata.conf`):** Beats 포트 `5044/TCP` 리슨 ➔ `logs-suricata.eve-default` 색인
* **TrusGuard 방화벽 파이프라인 (`firewall.conf`):** Syslog UDP `5514/UDP` 리슨 ➔ TrusGuard에서 로그 전송 대상을 관제 서버 IP로 지정

#### 3.2 ELK 스택 기동
```bash
# Docker Compose 실행
docker compose -f infrastructure/elk/docker-compose.elk.yml up -d

# 컨테이너 상태 점검 (모두 healthy 상태여야 함)
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

---

### 4단계: 키바나 대시보드 및 M1·M2 GeoIP 자동 프로비저닝

M1·M2 네트워크 대역에 맞게 Ingest Pipeline과 키바나 16개 패널 대시보드를 1회 자동 생성합니다.

```bash
# 프로비저닝 스크립트 실행
python infrastructure/elk/scripts/provision_kibana_dashboard.py
```

**스크립트 실행 결과:**
* `[Step 0]` M1·M2 IP 기반 GeoIP Ingest Pipeline 자동 등록
* `[Step 1]` 5개 Data View (`soc-unified-logs`, `logs-*` 등) 생성
* `[Step 3-A]` 전세계 실시간 위협 지도 (`soc-map-global-threats`) 생성
* `[Step 3-B]` 14개 Kibana Lens 시각화 객체 등록
* `[Step 4]` `SOC 통합 위협 관제 대시보드` 16패널 일괄 배포 완료

---

### 5단계: TrusGuard 방화벽 Syslog 연동

AhnLab TrusGuard 관리자 웹 GUI(`https://10.0.0.254` 또는 내부 관리 IP)에 접속하여 관제 서버로 Syslog를 전송합니다:

1. **로그 설정:** `기본 설정` ➔ `로그/알람` ➔ `Syslog 서버` 이동
2. **서버 추가:**
   * **서버 IP:** `192.168.40.6` (관제 서버 관리 IP) 또는 `192.168.30.3`
   * **포트:** `5514` (UDP)
   * **로그 유형:** 방화벽 보안정책 로그(허용/차단), NAT 변환 로그, 관리자 감사 로그 선택
3. **적용:** 저장 후 TrusGuard 정책 반영

---

### 6단계: FastAPI 웹 관제 콘솔 및 AI 비서 기동

분석가용 통합 보안 포털과 로컬 LLM 기반 침해사고 조사 파이프라인을 기동합니다.

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. FastAPI 웹 콘솔 백그라운드 실행
python -m uvicorn dashboard.app:app --host 0.0.0.0 --port 8501 --reload
```

* **키바나 관제 대시보드:** `http://192.168.40.6:5602/app/dashboards#/view/soc-unified-threat-dashboard`
* **SOC 통합 웹 콘솔:** `http://192.168.40.6:8501`

---

## 5. IP 변경 시 필수 수정 파일 체크리스트

현장 네트워크 상황에 따라 서브넷이 변경될 경우, 아래 4개 핵심 파일의 IP 값을 수정하십시오:

| 파일 경로 | 수정 파라미터 | 기본값 | 현장 변경 시 가이드 |
|---|---|---|---|
| `suricata/suricata.yaml` | `vars.address-groups.HOME_NET` | `[192.168.0.0/16, 172.16.10.0/24]` | M1·M2 내부망 서브넷 전체를 대괄호 내에 등록 |
| `infrastructure/elk/scripts/provision_kibana_dashboard.py` | `provision_geoip_pipeline_and_mappings()` 내 Painless 스크립트 | `10.10.70.x`, `172.16.10.10` | IP별 국가/도시명/위경도(GeoPoint) 매핑 수정 |
| `infrastructure/elk/pipeline/firewall.conf` | `syslog port` / `grok pattern` | `5514 / UDP` | TrusGuard Syslog 포트 및 로그 포맷 매칭 |
| `dashboard/app.py` | `PROTECTED_SUBNETS` | `["192.168.30.0/24", "172.16.10.0/24"]` | SOAR IP 차단 시 보호해야 할 핵심 서버 대역 정의 |

---

## 6. 최종 통합 검수 및 합격 판정 (Acceptance Test)

M1·M2 매뉴얼 제20장(T01~T20)에 이어 관제 파이프라인 6대 핵심 게이트를 검증합니다:

```
[GATE-NET-01] 패킷 미러링 수신 검증
 └─ soc-sensor에서 tcpdump 실행 시 TrusGuard eth2 ↔ L3SW Gi1/0/24 통신 패킷 관측? ➔ PASS

[GATE-SURI-01] 침해 탐지 이벤트 생성 검증
 └─ 외부망에서 Web(10.10.70.164) 공격 트래픽 유입 시 /var/log/suricata/eve.json에 Alert 기록? ➔ PASS

[GATE-SIEM-01] ELK 통합 수집 및 시각화 검증
 └─ Kibana 대시보드(Port 5602) 실시간 피드에 이벤트 출력 및 세계 지도에 레드 마커 표시? ➔ PASS

[GATE-AI-01] AI 심층 침해사고 조사 파이프라인 검증
 └─ FastAPI 웹 콘솔에서 [AI 심층 조사] 트리거 시 0.2초 내 분석 완료 및 4단계 스텝 '완료' 표시? ➔ PASS

[GATE-SOAR-01] 인간 승인 큐 및 차단 연계 검증
 └─ 관제사가 [승인] 클릭 시 방화벽/L3 차단 명령어 프리뷰 생성 및 정책 격리 수행? ➔ PASS
```

---

## 7. 장애 발생 시 진단 및 롤백 (Troubleshooting)

### 증상 1. 키바나 대시보드에 실시간 패킷/이벤트가 전혀 들어오지 않음
* **원인 1:** L3SW SPAN 세션 설정 누락 또는 포트 미연결
  * **조치:** L3SW에서 `show monitor session 1` 확인. `Gi1/0/13` 링크 상태 `connected` 확인.
* **원인 2:** 센서 `soc-sensor`의 Logstash 포트(5044) 방화벽 차단
  * **조치:** 센서에서 `nc -zv <관제서버IP> 5044` 테스트.

### 증상 2. 세계 지도 레이어에 `⚠️` 경고 아이콘이 뜨고 마커가 안 보임
* **원인:** Kibana Maps의 Data View 매핑 식별자 또는 Fielddata 문제
  * **조치:** `python infrastructure/elk/scripts/provision_kibana_dashboard.py` 재실행 후 브라우저 캐시 새로고침(`Ctrl + F5`).

### 롤백(Rollback) 절차
1. **L3SW SPAN 해제:**
   ```cisco
   cb-l3sw01# configure terminal
   no monitor session 1
   end
   ```
2. **Docker SIEM 서비스 중지:**
   ```bash
   docker compose -f infrastructure/elk/docker-compose.elk.yml down
   ```
3. **TrusGuard Syslog 전송 비활성화:**
   TrusGuard GUI에서 등록한 Syslog 목적지 서버 삭제 후 적용.
