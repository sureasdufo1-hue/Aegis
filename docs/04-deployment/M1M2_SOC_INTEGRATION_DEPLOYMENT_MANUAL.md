# M1·M2 통합 네트워크 인프라 기반 SOC 관제 시스템 구축 및 배포 매뉴얼

```
========================================================================================
             ENTERPRISE SOC DETECTION & INCIDENT MONITORING PLATFORM
                   차세대 보안관제 인프라 구축 및 현장 배포 가이드
========================================================================================
- 대상 환경: M1·M2 통합 네트워크 보안 인프라 (Cisco L3/L2, AhnLab TrusGuard, DMZ/서버팜)
- 관제 스택: Suricata 8.0.6, Snort 3, ELK Stack 8.17.3, Wazuh 4.14.7, FastAPI AI Web Console
- 참조 문서: 모바일분석_보고서_최종본 / M1·M2 통합 네트워크 보안 인프라 구축 및 재구축 매뉴얼
- 작성 일자: 2026-09-23
- 문서 버전: v2.0 (상세 배포본)
========================================================================================
```

---

## 목차

1. **사업 및 구축 개요**
   * 1.1 구축 목적 및 배경
   * 1.2 배포 대상 및 범위
   * 1.3 기본 원칙 및 패킷 가시성 기준선
2. **배포 사전 준비 및 소프트웨어 다운로드 가이드**
   * 2.1 하드웨어 및 운영체제 사전 요구사항
   * 2.2 핵심 소프트웨어 및 도구 공식 다운로드 명세표
   * 2.3 네트워크 포트 및 프로토콜 개방 요구사항
3. **네트워크 및 IP 주소 체계 매핑표**
   * 3.1 Lab 격리망 ↔ M1·M2 실제 인프라 1:1 대응표
   * 3.2 물리 포트 및 가상 스위치 결선 기준
4. **단계별 상세 구축 및 배포 절차 (Step-by-Step)**
   * 단계 1. L3 스위치 SPAN 포트 미러링 활성화 (Cisco cb-l3sw01)
   * 단계 2. 관제 소스코드 다운로드 및 작업 디렉터리 구성
   * 단계 3. 네트워크 패킷 센서(`soc-sensor`) 설치 및 설정
   * 단계 4. 중앙 SIEM 플랫폼(`soc-siem`) 기동 (Docker ELK 8.17.3 + Wazuh)
   * 단계 5. 키바나 관제 대시보드 및 실시간 위협 지도 프로비저닝
   * 단계 6. AhnLab TrusGuard 방화벽 Syslog 연동
   * 단계 7. AI 침해사고 조사 및 SOAR 웹 콘솔 가동 (FastAPI + Ollama)
5. **네트워크 IP 변경 시 필수 수정 파일 가이드 (Configuration Cheat Sheet)**
   * 5.1 Suricata 홈 네트워크(`HOME_NET`) 수정
   * 5.2 Logstash 인제스트 및 방화벽 파이프라인 수정
   * 5.3 GeoIP 위치 매핑 및 키바나 프로비저닝 스크립트 수정
   * 5.4 SOAR 보호 서버 목록(`PROTECTED_SUBNETS`) 수정
6. **품질 검증 게이트 및 합격 판정표 (Quality Gates)**
   * 6.1 6대 핵심 검증 게이트 명세
   * 6.2 단위/통합 테스트 자동화 실행표
7. **장애 대응 및 롤백 가이드 (Troubleshooting & Rollback)**
   * 7.1 주요 장애 증상별 원인 및 조치표
   * 7.2 비상 롤백 표준 절차

---

## 1. 사업 및 구축 개요

### 1.1 구축 목적 및 배경
본 매뉴얼은 `M1·M2 통합 네트워크 보안 인프라`(AhnLab TrusGuard 방화벽, Cisco L3/L2 스위치, DMZ 웹 서버, VLAN 10/20/30 서버팜, VMware 게스트 가상망) 환경에 최신 엔터프라이즈 보안관제(SOC) 플랫폼을 완벽히 이식하기 위한 표준 지침서입니다.

단순한 도구 설치에 그치지 않고, **"네트워크 트래픽 미러링 ➔ 듀얼 IDS(Suricata/Snort) 실시간 패킷 센싱 ➔ ELK/Wazuh SIEM 중앙 집중화 ➔ 다크모드 실시간 위협 지도 시각화 ➔ 로컬 AI 기반 4단계 심층 침해조사 ➔ SOAR 인간 승인 기반 원클릭 방화벽 차단"**에 이르는 전주기 방어 체계를 다른 엔지니어가 처음부터 끝까지 혼자서 완벽하게 재현할 수 있도록 구체적인 명령어와 다운로드 경로를 제공합니다.

### 1.2 배포 대상 및 범위
```
┌────────────────────────────────────────────────────────────────────────┐
│                        배포 대상 인프라 구성 영역                      │
├────────────────────┬───────────────────────────────────────────────────┤
│ 경계 방화벽        │ AhnLab TrusGuard 차세대 방화벽 (eth0~eth3)         │
│ 백본 스위치        │ Cisco Catalyst L3SW (cb-l3sw01, Gi1/0/1~24)       │
│ 워크그룹 스위치    │ Cisco L2SW1 (업무망), Cisco L2SW2 (서버팜)         │
│ 가상화 호스트      │ Windows 10/11 물리 PC (VMware Workstation Bridged) │
│ 네트워크 센서      │ [soc-sensor] 전용 물리 PC / VM (구 Analyse PC 2)  │
│ 통합 SIEM 및 관제  │ [soc-siem] 중앙 서버 (구 Analyse PC 1 또는 LOG)    │
└────────────────────┴───────────────────────────────────────────────────┘
```

### 1.3 기본 원칙 및 패킷 가시성 기준선
1. **패킷 가시성 우선 (Visibility Before IDS):** L3 스위치의 SPAN 트래픽이 센서의 캡처 인터페이스에서 `tcpdump`로 온전히 수신되기 전에는 다운스트림 IDS 및 SIEM 작업을 진행하지 않습니다.
2. **캡처 인터페이스 무IP 원칙:** 센서의 패킷 수집 전용 NIC에는 IP 주소를 일체 부여하지 않고 순수 수신(Promiscuous) 전용으로 운영합니다.
3. **버전 고정 (Pinned Versioning):** 실무 운영 안정성을 위해 모든 소프트웨어와 Docker 이미지는 검증된 고정 버전을 사용하며, 임의로 `latest` 태그를 사용하지 않습니다.

---

## 2. 배포 사전 준비 및 소프트웨어 다운로드 가이드

### 2.1 하드웨어 및 운영체제 사전 요구사항
시스템을 구축하기 전, 배포 대상 컴퓨터 2대(센서 서버, 관제 서버)의 하드웨어 사양을 확인합니다:

| 시스템 구분 | 권장 하드웨어 사양 | 권장 운영체제(OS) | 필수 네트워크 인터페이스(NIC) |
|---|---|---|---|
| **관제 서버 (`soc-siem`)**<br/>(구 Analyse PC 1 / LOG) | CPU 6코어 이상<br/>RAM 16GB~24GB<br/>SSD 100GB 이상 | Ubuntu 22.04 LTS 또는<br/>Windows 11 (WSL2) | **NIC 1개:** L3SW Gi1/0/4 관리망(`192.168.40.6/30`) 또는 VLAN 30(`192.168.30.3`) 연결 |
| **네트워크 센서 (`soc-sensor`)**<br/>(구 Analyse PC 2) | CPU 4코어 이상<br/>RAM 8GB~16GB<br/>SSD 50GB 이상 | Ubuntu 22.04 LTS Server | **NIC 2개 필수:**<br/>• NIC 1 (수집용): L3SW Gi1/0/13 연결 (IP 없음)<br/>• NIC 2 (관리용): 관리망 연결 |

---

### 2.2 핵심 소프트웨어 및 도구 공식 다운로드 명세표

아래 표의 다운로드 링크와 명령어를 이용하여 공인된 공식 설치 바이너리를 준비합니다:

| 소프트웨어 명칭 | 권장 버전 | 공식 다운로드 경로 (URL) 및 설치 명령어 | 주요 역할 및 비고 |
|---|---|---|---|
| **Git for Windows / Linux** | 2.40+ | https://git-scm.com/downloads<br/>`sudo apt update && sudo apt install -y git` | 프로젝트 저장소 소스코드 복제 |
| **Docker Desktop / Engine** | 26.0+ | https://www.docker.com/products/docker-desktop/<br/>`curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh` | ELK 및 Wazuh 컨테이너 런타임 |
| **Python** | 3.11.x | https://www.python.org/downloads/<br/>`sudo apt install -y python3 python3-pip python3-venv` | 대시보드 프로비저닝 및 FastAPI 콘솔 |
| **본 관제 시스템 저장소** | v1.0 | `git clone https://github.com/sureasdufo1-hue/Aegis.git Suricata-Snort-SOC-Lab` | 전체 룰셋, 파이프라인, 웹 콘솔 소스 |
| **Suricata IDS** | **8.0.6** | PPA: `sudo add-apt-repository ppa:oisf/suricata-stable -y`<br/>`sudo apt update && sudo apt install -y suricata` | 실시간 패킷 침해 탐지 (Primary IDS) |
| **Snort IDS** | **3.12.2.0** | https://github.com/snort3/snort3/releases<br/>`libDAQ 3.0.27`: https://github.com/snort3/libdaq/releases | 오프라인 PCAP 검증 및 룰 교차 분석 |
| **Elasticsearch** | **8.17.3** | Docker Hub: `docker.elastic.co/elasticsearch/elasticsearch:8.17.3` | 분산 보안 빅데이터 색인 엔진 |
| **Logstash** | **8.17.3** | Docker Hub: `docker.elastic.co/logstash/logstash:8.17.3` | 실시간 EVE/Syslog 파이프라인 파싱 |
| **Kibana** | **8.17.3** | Docker Hub: `docker.elastic.co/kibana/kibana:8.17.3` | 16개 패널 관제 대시보드 & 위협 지도 |
| **Wazuh Manager/Indexer** | **4.14.7** | Docker Hub: `wazuh/wazuh-manager:4.14.7`, `wazuh-indexer:4.14.7` | 호스트 엔드포인트 SIEM 통합 |
| **Wazuh Agent (Linux)** | **4.14.7** | https://packages.wazuh.com/4.x/apt/ (Debian/Ubuntu)<br/>`curl -s https://packages.wazuh.com/key/GPG-KEY-WAZUH \| sudo apt-key add -` | DMZ Web, DB 서버 호스트 감사 로그 수집 |
| **Ollama (로컬 LLM)** | 0.3.0+ | https://ollama.com/download<br/>`curl -fsSL https://ollama.com/install.sh \| sh` | AI 심층 침해조사 파이프라인 추론 엔진 |
| **Qwen 추론 모델** | 7B / 9B | `ollama pull qwen2.5:7b` (또는 `qwen2.5-coder:7b`) | 온프레미스 폐쇄망 보안 인과관계 분석 |
| **Wireshark & Npcap** | 최신 안정판 | https://www.wireshark.org/download.html<br/>https://npcap.com/#download | 패킷 로우레벨 디버깅 및 포렌식 |

---

### 2.3 네트워크 포트 및 방화벽 개방 요구사항

서버 간 원활한 통신을 위해 허용되어야 하는 인바운드/아웃바운드 포트 목록입니다:

| 출발지 (Source) | 목적지 (Destination) | 포트 / 프로토콜 | 용도 |
|---|---|---|---|
| 센서 (`soc-sensor`) | 관제 서버 (`soc-siem`) | `5044 / TCP` | Suricata EVE 로그 전송 (Logstash Beats) |
| 센서 (`soc-sensor`) | 관제 서버 (`soc-siem`) | `5045 / TCP` | Snort 3 알림 로그 스트림 전송 |
| TrusGuard 방화벽 | 관제 서버 (`soc-siem`) | `5514 / UDP` | 방화벽 차단/세션 Syslog 수신 |
| DMZ Web / DB 서버 | 관제 서버 (`soc-siem`) | `1514 / TCP` | Wazuh Agent 이벤트 보고 |
| DMZ Web / DB 서버 | 관제 서버 (`soc-siem`) | `1515 / TCP` | Wazuh Agent 자동 등록 (Enrollment) |
| 보안 분석가 PC | 관제 서버 (`soc-siem`) | `5602 / TCP` | Kibana 엔터프라이즈 관제 대시보드 웹 접속 |
| 보안 분석가 PC | 관제 서버 (`soc-siem`) | `8501 / TCP` | FastAPI AI 관제 포털 및 인간 승인 큐 접속 |
| 관제 서버 내부 | 로컬호스트 | `11434 / TCP` | Ollama LLM 추론 API (내부 전용 바인딩) |

---

## 3. 네트워크 및 IP 주소 체계 매핑표

### 3.1 Lab 격리망 ↔ M1·M2 실제 인프라 1:1 대응표

| 영역 구분 | 기존 실습 Lab 기준 | **M1·M2 실제 환경 IP / 객체명** | 비고 및 서브넷 마스크 |
|---|---|---|---|
| **외부 / 공격망** | `10.77.20.0/24` | **`10.10.70.128/25`** | TrusGuard `eth1` (10.10.70.214, 상위 GW .129) |
| **방화벽 SNAT_IP** | N/A | **`10.10.70.163`** | 내부망에서 외부 나갈 때 출발지 변환 객체 |
| **방화벽 WEB_VIP** | N/A | **`10.10.70.164`** | 외부에서 DMZ Web 접근 시 목적지 변환 객체 |
| **방화벽 Transit** | `10.77.10.1` ↔ `10.77.20.1` | **`192.168.40.1/30` ↔ `.40.2/30`** | TrusGuard `eth2` ↔ Cisco L3SW `Gi1/0/24` |
| **DMZ 웹 서버** | N/A | **`172.16.10.10/24`** | TrusGuard `eth3` (GW: `172.16.10.1`) |
| **VLAN 10 (관리망)** | `10.77.10.0/24` | **`192.168.10.0/24`** | L3 SVI `.10.1` (Admin PC: `.10.2`, VM1: `.10.101`) |
| **VLAN 20 (내부망)** | `10.77.20.0/24` | **`192.168.20.0/24`** | L3 SVI `.20.1` (User PC: `.20.2`, VM2: `.20.101`) |
| **VLAN 30 (서버팜)** | `10.77.30.0/24` | **`192.168.30.0/24`** | L3 SVI `.30.1` (DB: `.30.2`, LOG/SIEM: `.30.3`) |
| **Analyse 관리망** | N/A | **`192.168.40.4/30`** | L3SW `Gi1/0/4` (`.40.5`) ↔ 관제 서버 (`.40.6`) |
| **SPAN 패킷 미러링**| Hyper-V Port Mirroring | **Cisco SPAN (`Gi1/0/13`)** | Source: `Gi1/0/24` (양방향) ➔ Dest: `Gi1/0/13` |

---

## 4. 단계별 상세 구축 및 배포 절차 (Step-by-Step)

```
[구축 흐름도]
[단계 1: L3 SPAN 설정] ➔ [단계 2: 저장소 다운로드] ➔ [단계 3: 센서 Suricata 배포]
                                                            │
┌───────────────────────────────────────────────────────────┘
▼
[단계 4: Docker SIEM 기동] ➔ [단계 5: 대시보드 프로비저닝] ➔ [단계 6: TrusGuard 연동] ➔ [단계 7: AI 콘솔 가동]
```

---

### [단계 1] L3 스위치 SPAN 포트 미러링 활성화 (Cisco cb-l3sw01)

Cisco L3 스위치 콘솔 케이블 연결 후 방화벽 Transit 트래픽(`Gi1/0/24`)을 센서 연결 포트(`Gi1/0/13`)로 복제 송출합니다.

```cisco
! 1. 특권 EXEC 모드 진입 및 전역 설정
enable
configure terminal

! 2. 방화벽 Transit 인터페이스 점검 (Source 대상)
interface GigabitEthernet1/0/24
 description TRANSIT_TO_TRUSGUARD_ETH2
 no switchport
 ip address 192.168.40.2 255.255.255.252
 no shutdown
exit

! 3. 센서 연결 포트 설정 (Destination 대상 - IP 설정 제거 및 활성화)
interface GigabitEthernet1/0/13
 description SPAN_DESTINATION_TO_SOC_SENSOR
 no shutdown
exit

! 4. SPAN 모니터 세션 구성 (양방향 트래픽 미러링)
monitor session 1 source interface GigabitEthernet1/0/24 both
monitor session 1 destination interface GigabitEthernet1/0/13
end

! 5. 설정 검증 및 메모리 저장
show monitor session all
copy running-config startup-config
```

* **성공 검증 출력:**
  ```text
  cb-l3sw01# show monitor session 1
  Session 1
  ---------
  Type                   : Local Session
  Source Ports           :
      Both               : Gi1/0/24
  Destination Ports      : Gi1/0/13
  Encapsulation          : Native
  Ingress                : Disabled
  ```

---

### [단계 2] 관제 소스코드 다운로드 및 작업 디렉터리 구성

관제 서버(`soc-siem`) 및 센서 서버(`soc-sensor`)에서 프로젝트 소스코드를 다운로드합니다.

```bash
# 1. 작업 디렉터리 생성 및 소스코드 Clone
mkdir -p /opt/soc-platform
cd /opt/soc-platform
git clone https://github.com/sureasdufo1-hue/Aegis.git Suricata-Snort-SOC-Lab
cd Suricata-Snort-SOC-Lab

# 2. 배포 환경 변수 템플릿 복사 및 패스워드 설정
cp .env.example .env
chmod 600 .env

# 3. .env 파일 수정 (인증 정보 설정)
sed -i 's/ELASTIC_PASSWORD=.*/ELASTIC_PASSWORD=changeme_soc_lab_strong_pass_2026/' .env
```

---

### [단계 3] 네트워크 패킷 센서(`soc-sensor` / 구 Analyse PC 2) 설치 및 설정

센서 서버의 `ens33` 인터페이스가 L3SW `Gi1/0/13`에 연결된 상태에서 수행합니다.

#### 3.1 캡처 NIC 무IP 및 프로미스큐어스 모드 설정
```bash
# 캡처 인터페이스 IP 제거 및 무차별 모드 활성화
sudo ip -4 addr flush dev ens33
sudo ip -6 addr flush dev ens33
sudo ip link set ens33 promisc on
sudo ip link set ens33 up

# 패킷 미러링 수신 확인 (GATE-NET-01 게이트 검증)
sudo tcpdump -eni ens33 -c 10
```
> **판정:** 관리자 PC나 Web 서버 트래픽이 `tcpdump` 콘솔에 패킷 덤프로 출력되면 정상입니다.

#### 3.2 Suricata 설치 및 설정 (`/etc/suricata/suricata.yaml`)
```bash
# 1. Suricata 최신 안정판 설치
sudo add-apt-repository ppa:oisf/suricata-stable -y
sudo apt update && sudo apt install -y suricata jq

# 2. 홈 네트워크 기준선을 M1·M2 환경으로 수정
sudo cp /etc/suricata/suricata.yaml /etc/suricata/suricata.yaml.bak
sudo tee -a /etc/suricata/suricata.yaml > /dev/null << 'EOF'

# --- M1·M2 Custom SOC Configuration ---
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
outputs:
  - eve-log:
      enabled: yes
      filetype: regular
      filename: eve.json
      types:
        - alert
        - http
        - dns
        - tls
EOF

# 3. 프로젝트 전용 커스텀 탐지 룰 복사
sudo cp -r suricata/rules/* /etc/suricata/rules/

# 4. 설정 구문 검증 및 서비스 기동
sudo suricata -T -c /etc/suricata/suricata.yaml
sudo systemctl restart suricata
sudo systemctl enable suricata
```

---

### [단계 4] 중앙 SIEM 플랫폼(`soc-siem`) 기동 (Docker ELK 8.17.3 + Wazuh)

관제 서버(`192.168.40.6` 또는 `192.168.30.3`)에서 Docker Compose를 사용하여 컨테이너 스택을 기동합니다.

```bash
cd /opt/soc-platform/Suricata-Snort-SOC-Lab

# 1. Docker Compose 문법 사전 검증
docker compose -f infrastructure/elk/docker-compose.elk.yml config

# 2. ELK 스택 백그라운드 기동
docker compose -f infrastructure/elk/docker-compose.elk.yml up -d

# 3. 컨테이너 헬스체크 (1~2분 대기 후 확인)
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

* **정상 상태 확인:**
  * `soc-elasticsearch` (Up, healthy, `127.0.0.1:9201->9200/tcp`)
  * `soc-logstash` (Up, healthy, `5044-5047/tcp`, `5514/udp`)
  * `soc-kibana` (Up, healthy, `127.0.0.1:5602->5601/tcp`)

---

### [단계 5] 키바나 관제 대시보드 및 실시간 위협 지도 프로비저닝

M1·M2 네트워크에 특화된 Ingest Pipeline, Data View, 16개 패널 대시보드, 전세계 실시간 위협 지도를 자동으로 배포합니다.

```bash
# 프로비저닝 스크립트 실행
python3 infrastructure/elk/scripts/provision_kibana_dashboard.py
```

* **정상 실행 완료 로그:**
  ```text
  ======================================================================
   Phase ELK-11: Kibana Data Views & Enterprise SOC Dashboard Provisioning
   (With Global Cyber Threat Geospatial Map & Origin Analytics)
  ======================================================================
  [Step 0] Configuring High-Fidelity ECS GeoIP Mappings & Pipeline...
  [PASS] Confirmed geo_point mapping for source.geo.location with fielddata enabled.
  [PASS] Ingest pipeline 'soc-geoip-enrichment-pipeline' registered.
  [Step 1] Provisioning Kibana Data Views...
  [PASS] Provisioned Data View: soc-unified-logs (logs-*)
  [Step 2] Provisioning Saved Search 'soc-threat-event-feed'... [PASS]
  [Step 3-A] Provisioning Global Cyber Threat Geospatial Map... [PASS]
  [Step 3-B] Provisioning Enterprise Kibana Lens Visualizations (14 objects)... [PASS]
  [Step 4] Provisioning Enterprise SOC Threat Operations Console... [PASS]
  [*] Access URL: http://127.0.0.1:5602/app/dashboards#/view/soc-unified-threat-dashboard
  >>> Phase ELK-11 Kibana Enterprise Threat Map Dashboard: PASS <<<
  ```

---

### [단계 6] AhnLab TrusGuard 방화벽 Syslog 연동

TrusGuard 관리자 웹 GUI(`https://10.0.0.254`)에 접속하여 방화벽 로그를 관제 서버로 실시간 전송합니다:

1. **로그 설정 메뉴 이동:** `기본 설정` ➔ `로그/알람` ➔ `Syslog 서버` 선택
2. **신규 서버 등록:**
   * **서버 IP:** `192.168.40.6` (관제 서버 관리 IP) 또는 `192.168.30.3`
   * **수신 포트:** `5514`
   * **프로토콜:** `UDP`
   * **로그 카테고리:** `보안정책(차단/허용)`, `NAT 변환`, `침입탐지(IPS)` 전체 체크
3. **설정 저장 및 정책 적용:** `적용(Apply)` 클릭하여 방화벽 룰 반영

---

### [단계 7] AI 침해사고 조사 및 SOAR 웹 콘솔 가동 (FastAPI + Ollama)

#### 7.1 로컬 LLM 추론 엔진 기동
```bash
# Ollama 백그라운드 서비스 시작 및 모델 로딩
sudo systemctl start ollama
ollama pull qwen2.5:7b

# 추론 엔진 헬스체크
curl http://127.0.0.1:11434/api/tags
```

#### 7.2 FastAPI SOC 웹 포털 기동
```bash
cd /opt/soc-platform/Suricata-Snort-SOC-Lab

# 가상환경 활성화 및 의존성 패키지 설치
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# FastAPI 서버 백그라운드 실행 (포트 8501)
python3 -m uvicorn dashboard.app:app --host 0.0.0.0 --port 8501 --reload &
```

* **접속 확인:**
  * **Kibana 대시보드:** `http://<관제서버IP>:5602/app/dashboards#/view/soc-unified-threat-dashboard`
  * **SOC 웹 포털 콘솔:** `http://<관제서버IP>:8501`

---

## 5. 네트워크 IP 변경 시 필수 수정 파일 가이드

현장 실습망이나 운영 환경의 IP 대역이 달라질 경우, 아래 **4개 파일만 수정**하면 전체 시스템이 자동으로 연동됩니다:

### 5.1 `suricata/suricata.yaml` (탐지 대역)
```yaml
# 내부 보호망 대역 변경 시 수정
vars:
  address-groups:
    HOME_NET: "[변경할_내부_서브넷1,변경할_서브넷2,...]"
    HTTP_SERVERS: "[새로운_웹서버_IP]"
    SQL_SERVERS: "[새로운_DB서버_IP]"
```

### 5.2 `infrastructure/elk/scripts/provision_kibana_dashboard.py` (GeoIP 매핑)
```python
# 라인 140~175 부근 Ingest Pipeline Painless 스크립트 수정
if (ip == '10.10.70.163' || ip.startsWith('10.10.70.')) {
    ctx.source.geo.country_name = 'External WAN';
    ctx.source.geo.location = ['lat': 37.5665, 'lon': 126.9780];
} else if (ip == '172.16.10.10') {
    ctx.source.geo.country_name = 'DMZ Web Farm';
}
```

### 5.3 `infrastructure/elk/pipeline/firewall.conf` (Syslog 포트)
```ruby
input {
  udp {
    port => 5514 # 방화벽에서 전송하는 포트와 일치시킴
    type => "syslog"
  }
}
```

### 5.4 `dashboard/app.py` (SOAR 자동 격리 방어 서버 보호 목록)
```python
# 실수로 내부 주요 서버가 차단 룰에 등록되지 않도록 화이트리스트 지정
PROTECTED_SUBNETS = [
    "192.168.30.0/24",  # 서버팜 (DB, LOG)
    "172.16.10.0/24",   # DMZ 서버
    "192.168.10.1/32"   # L3 게이트웨이
]
```

---

## 6. 품질 검증 게이트 및 합격 판정표 (Quality Gates)

배포 작업 완료 후 각 단계의 통과 여부를 객관적 증적으로 판정합니다:

| 게이트 ID | 점검 대상 항목 | 검증 기준 및 확인 명령어 | 기대 결과 (PASS 기준) | 판정 |
|:---:|---|---|---|:---:|
| **GATE-NET-01** | L3 SPAN 패킷 미러링 | `sudo tcpdump -eni ens33 -c 10` | FW Transit 통과 패킷 10개 이상 관측 | **PASS** |
| **GATE-SURI-01** | Suricata 패킷 실시간 탐지 | `curl http://10.10.70.164/` 공격 시도 후 `tail -n 1 /var/log/suricata/eve.json` | `event_type: "alert"` JSON 레코드 생성 | **PASS** |
| **GATE-SIEM-01** | ELK 인프라 컨테이너 상태 | `docker ps` 및 `curl http://127.0.0.1:9201/_cluster/health` | 클러스터 상태 `status: "green"`, 3개 컨테이너 healthy | **PASS** |
| **GATE-MAP-01** | 실시간 전세계 위협 지도 | 브라우저 키바나 맵 레이어 확인 | TOC 패널 경고(`⚠️`) 0건, 공격 발원지 레드 마커 정상 표시 | **PASS** |
| **GATE-AI-01** | AI 심층 침해조사 파이프라인 | FastAPI 콘솔에서 [AI 심층 조사] 클릭 | 타이머 동작 후 4단계 스텝 모두 `✅ 완료` 배지 전환 | **PASS** |
| **GATE-SOAR-01** | 인간 승인 큐 차단 연계 | [승인] 버튼 클릭 후 방화벽/L3 차단 명령 | `nftables` / Cisco ACL 차단 규칙 정상 주입 | **PASS** |

### 자동화 테스트 스위트 실행
```bash
# 전체 인프라 및 대시보드 자동화 단위/통합 테스트 (21개 항목)
pytest tests/test_elk_infrastructure.py tests/test_dashboard_track2_ux.py
```
> **합격 기준:** `21 passed (100%)`

---

## 7. 장애 대응 및 롤백 가이드 (Troubleshooting & Rollback)

### 7.1 주요 장애 증상별 원인 및 조치표

| 증상 (Symptom) | 1차 점검 사항 | 근본 원인 | 권장 조치 및 복구 방법 |
|---|---|---|---|
| **Kibana에 패킷 로그가 전혀 수집되지 않음** | 센서 서버의 `eve.json` 파일 크기 증가 여부 확인 | SPAN 세션 미러링 미동작 또는 방화벽 포트 5044 차단 | 1) L3SW `show monitor session 1` 확인<br/>2) 센서에서 `nc -zv <관제IP> 5044` 통신 점검 |
| **세계 지도에 마커가 안 보이고 `⚠️` 아이콘 발생** | 키바나 맵 레이어 TOC의 경고 메시지 클릭 | Data View `indexPatternId` 불일치 또는 Fielddata 비활성화 | `python3 infrastructure/elk/scripts/provision_kibana_dashboard.py` 재실행 후 브라우저 `Ctrl + F5` |
| **AI 조사 모달창이 진행 중 상태로 멈춤** | 개발자 도구(F12) 콘솔 네트워크 응답 확인 | 백엔드 조사 완료 후 UI 스텝 배지 업데이트 누락 | 본 저장소 최신 버전 적용 확인 (커밋 `5c9e947` 적용 시 4단계 자동 완료) |
| **방화벽 Syslog가 Logstash에 안 들어옴** | `sudo netstat -unlp \| grep 5514` 확인 | TrusGuard Syslog 전송 포트 불일치 또는 UDP 드롭 | TrusGuard 정책의 Syslog 서버 IP 및 포트 5514 재확인 |

### 7.2 비상 롤백 표준 절차
운영 환경에 예기치 못한 네트워크 지연이나 부하가 발생할 경우 아래 순서로 신속히 원래 상태로 복구합니다:

1. **L3 스위치 SPAN 포트 미러링 즉시 해제 (네트워크 부하 제거):**
   ```cisco
   cb-l3sw01# configure terminal
   no monitor session 1
   end
   ```
2. **관제 서버 Docker 컨테이너 일괄 중지:**
   ```bash
   docker compose -f infrastructure/elk/docker-compose.elk.yml down
   ```
3. **TrusGuard 방화벽 Syslog 전송 중지:**
   * TrusGuard 웹 GUI ➔ `기본 설정` ➔ `로그/알람` ➔ 등록된 Syslog 서버 비활성화/삭제.
