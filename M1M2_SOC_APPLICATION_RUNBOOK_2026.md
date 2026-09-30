# M1·M2 인프라에 SOC Detection Lab 적용: IP 전환·배포·검증 매뉴얼

버전: 계획안 1.0 (2026-09-23)  
상태: **문서 작성 완료 / 현장 구축 BLOCKED**  
변경 관리: [DESIGN-ISSUE-001 / ADR-CANDIDATE-001](../02-architecture/DESIGN-ISSUE-001-M1M2-SOC-INTEGRATION.md)  
대상: CB 정보통신 M1·M2 네트워크 보안 인프라와 별도 SOC 확장

이 문서는 두 사용자 제공 PDF의 **기록된 주소·포트**를 배포 입력값으로 정리한 실행안이다. PDF 속 `VERIFIED`는 당시 화면/CLI에서 확인되었다는 뜻이며 현재 통신 성공을 뜻하지 않는다. 실제 장비의 IP, MAC, 인터페이스, 케이블, 자원은 작업 당일 다시 확인한다. 저장소의 Hyper-V·`10.77.*` 기준은 승인된 원본 Lab으로 유지한다. 여기서 제안한 M1·M2 프로파일은 ADR 승인 전까지 실행하지 않는다.

## 1. 적용 범위와 결정해야 할 차이

M1·M2 프로젝트 자체 요구사항은 **DMZ Web `172.16.10.10` ↔ 내부 DB `192.168.30.2`**, LOG `192.168.30.3`의 RAID1·rsyslog·ELK, TrusGuard NAT/정책, L3 ACL, VLAN 10/20/30, NTP 및 L3 SPAN이다. SOC Lab의 Suricata/Snort/증거 체인을 여기에 붙인다. 필수 ELK를 Wazuh로 대체하지 않는다. Wazuh는 자원·네트워크·접근제어 승인 후 추가 통합한다.

```text
VLAN 10/20 ── L3 Gi1/0/24 ── TrusGuard eth2 ── eth1 ── 외부
                     │ SPAN both → Gi1/0/13 → Analyse PC 2 (캡처 NIC 무IP)
                     └────────────────────────→ PCAP → Suricata EVE → ELK/Wazuh
VLAN 30 (DB .30.2, LOG .30.3) ─┘
TrusGuard eth3 ── DMZ Web 172.16.10.10
```

**캡처 경계:** Gi1/0/24의 Transit SPAN은 이 포트를 실제 통과하는 VLAN↔방화벽 흐름을 볼 수 있다. 외부 `WEB_VIP 10.10.70.164` → 방화벽 eth1 → eth3 → Web 흐름과 VLAN 간 L3 내부 흐름은 이 포트를 지나지 않으므로 이 SPAN만으로 관측할 수 없다. 외부 Web 공격의 실시간 IDS 탐지는 별도 승인된 DMZ 측 TAP/미러링과 실수신 검증 전까지 `BLOCKED`다. Web→DB는 경로상 Transit을 지날 수 있지만 실제 PCAP으로 증명한다.

## 2. IP·VLAN·포트 원장: 기존 Lab과 M1·M2의 대응

약칭을 생략하지 말고 설정 시 아래 **전체 주소**를 사용한다. 서로 다른 `/30`을 `/24`로 합치지 않는다.

| M1·M2 역할 | 실제 주소/연결 | Lab에서 바뀌는 의미 | 확인 상태 |
|---|---|---|---|
| TrusGuard 관리 eth0 | `10.0.0.254/24` | Lab 게이트웨이 관리 IP의 직접 대체가 아님 | PDF 기록, 현재 재확인 |
| 외부망/eth1/WAN GW | `10.10.70.128/25`; `10.10.70.214/25`; `10.10.70.129` | `10.77.20.0/24` 전용 공격망과 동일하지 않음 | PDF 기록, 현재 재확인 |
| SNAT_IP | `10.10.70.163` | 내부 VLAN 10/20 출발지 변환 객체, NIC 주소 아님 | PDF 기록, 세션 시험 필요 |
| WEB_VIP | `10.10.70.164` | Web 공개 DNAT 객체, Web NIC 주소 아님 | PDF 기록, 세션 시험 필요 |
| 방화벽 Transit | FW eth2 `192.168.40.1/30` ↔ L3 Gi1/0/24 `192.168.40.2/30` (`192.168.40.0/30`) | Lab `soc-gateway` 3 NIC/nftables 제거 대상이 아니라 **별도 프로파일에서 사용하지 않음** | PDF 기록, 현재 재확인 |
| DMZ | FW eth3 `172.16.10.1/24` ↔ Web `172.16.10.10/24`, GW `.10.1` | Lab Victim `10.77.30.20`의 웹 **서비스 역할** 대응 | Web OS 적용 재확인 |
| VLAN 10 관리자 | `192.168.10.0/24`; L3 SVI `.10.1`; Admin PC `.10.2`; VM1 `.10.101`; L2SW2 관리 `.10.12` | Lab MGMT의 1:1 치환 아님. VLAN10에는 일반 VM도 있음 | VM1 GW ARP 실패 이력 |
| VLAN 20 사용자 | `192.168.20.0/24`; L3 SVI `.20.1`; PC `.20.2`; VM2 `.20.101` | Lab Attack 존이 아님. 사용자 VLAN을 공격자 대역으로 취급 금지 | VM2 목표/미검증 |
| VLAN 30 서버팜 | `192.168.30.0/24`; L3 SVI `.30.1`; DB `.30.2`; LOG `.30.3` | Lab Victim 망과 1:1 치환 아님. DB·LOG 모두 보호 자산 | DB/LOG OS·서비스 재확인 |
| Analyse PC 1 관리 링크 | L3 Gi1/0/4 `192.168.40.5/30` ↔ PC1 `192.168.40.6/30` (`192.168.40.4/30`) | `.40.0/30` Transit과 별도 네트워크 | PC1 왕복 재확인 |
| Analyse PC 2 수집 NIC | L3 Gi1/0/24 SPAN source both → Gi1/0/13 destination → PC2 NIC **무IP·무GW** | Lab 센서 모니터 NIC의 기능 대응. Linux 인터페이스명은 실측 | PDF상 SPAN TARGET |
| SOC 실시간 전송용 관리 IP | **미배정** | Lab 센서 `10.77.10.20`, Wazuh Host `10.77.10.10`의 자동 치환 금지 | 네트워크 담당자 배정 필요 |
| 공격 시험 PC | **미지정** | Lab Attacker `10.77.20.20`의 자동 치환 금지 | 시험 대상/출발지 승인 필요 |

`SNAT_IP .163`, `WEB_VIP .164`, WAN NIC `.214`는 서로 다른 객체다. 이전 VIP `.152`, DB/LOG `.30.10/.30.20`은 최신 M1·M2 기준값으로 쓰지 않는다. DNS 주소와 센서 관리 IP도 PDF에 확정되어 있지 않다.

### 2.1 실제 트래픽 경로와 정책

| 흐름 | 기대 경로/정책 | SOC 수집 위치 |
|---|---|---|
| VLAN10/20 → 승인된 외부 시험지 | L3 → FW eth2 → eth1, SNAT `.163` | Transit SPAN 대상 |
| 승인된 외부 시험 PC → WEB_VIP `.164` | eth1→eth3 DNAT→Web `.10.10`, HTTP/HTTPS | Transit SPAN **대상 밖** |
| Web `.10.10` → DB `.30.2` | FW eth3→eth2→L3→VLAN30, MySQL 실제 서비스 포트만 | Transit 통과 여부 PCAP 검증 |
| Web/FW/Switch → LOG `.30.3` | 기존 rsyslog·보안정책·저장 경로 | 수집 로그 및 시간 검증 |
| Admin `.10.2` → VLAN30 | L3 ACL 허용 및 각 호스트 정책 | Gi1/0/24를 안 지나면 Transit SPAN 대상 밖 |
| 일반 VLAN10 / VLAN20 → VLAN30 | L3 ACL 차단 | L3 ACL hit와 단말 실패를 함께 증명 |

시나리오 PDF pp. 5–9의 `210.95.199.0/24` 양방향 차단, 관리자 1명만 방화벽 GUI/DMZ SSH/Kibana 접속, DB 호스트 방화벽의 거부 로그, 비표준 원격 접속 포트, NTP 등은 M1·M2 기본 검수 항목이다. SOC 추가 때문에 이 정책을 완화하지 않는다. 해당 공인 대역에는 연결 시험을 보내지 않고 정책 객체·카운터와 승인된 합성 데이터로 검증한다. 시나리오 p. 7의 스위치 `enable password: 1234`는 최종 자격증명 정책과 충돌하므로 DESIGN-ISSUE-001에서 결정한다.

## 3. 저장소 전환 범위: 주소를 바꾸는 순서

**원본 파일에 전역 검색·치환을 하지 않는다.** 승인 후 별도 M1·M2 설정 파일/배포 프로파일을 생성해 원본 Lab을 보존하고, 아래 파일의 값을 프로파일에 반영한다. 수정 전 `rg -n '10\.77\.|192\.168\.111\.|172\.24\.'`로 누락을 찾는다.

| 대상 | 구체적 변경 | 사전/사후 검증 |
|---|---|---|
| `infrastructure/hyper-v/*`, `infrastructure/network/netplan_gateway.yaml`, `netplan_victim.yaml`, `gateway_nftables.conf`, `setup_attacker.sh` | M1·M2 배포 경로에서 **실행 제외**. TrusGuard/Cisco/기존 OS 설정이 네트워크 기준 | M1·M2 PDF 4–17장 및 T01–T17. Lab 값으로 덮어쓰지 않음 |
| `suricata/config/suricata.yaml` | 별도 프로파일에서 `HOME_NET: "[192.168.10.0/24,192.168.20.0/24,192.168.30.0/24,172.16.10.0/24]"`; `EXTERNAL_NET: "!$HOME_NET"`; `HTTP_SERVERS: "[172.16.10.10]"`; `SQL_SERVERS: "[192.168.30.2]"`; `af-packet.interface`는 실측 NIC | `suricata -T`, SPAN PCAP 재생, EVE의 `src_ip/dest_ip`; `192.168.40.0/30`은 Transit 인프라로 별도 변수/룰 고려 |
| `suricata/rules/*`, `snort/rules/*`, `snort/config/snort.lua` | HTTP/SSH 실제 포트와 `$EXTERNAL_NET` 방향성 재검토. `DMZ_NET`, `SERVER_NET`, `USER_NET` 같은 별도 변수로 Web→DB **내부→내부** 룰 작성. 기존 `$EXTERNAL_NET → $HOME_NET` 룰만으로 이 흐름은 탐지되지 않을 수 있음. SID 범위 유지, 변경 시 `rev` 증가 | SID 중복 검사, `suricata -T`, `snort -T`, 동일 PCAP 경보 비교 |
| `analyzer/ai/policy/protected_assets.py` 및 방화벽 액션 경로 | 새 GW `.10.1/.20.1/.30.1`, FW `.40.1/.214`, L3 `.40.2/.40.5`, 관리자 `.10.2`, DB `.30.2`, LOG `.30.3`, VIP/SNAT 객체를 보호 대상으로 검토. 외부 운영 장비 자동 차단은 별도 정책·승인 필요 | 허용/거부 테스트, HITL dry-run. `dashboard/app.py`에 `PROTECTED_SUBNETS` 상수가 있다고 가정하지 않음 |
| `infrastructure/elk/*`, `dashboard/elk_client.py`, Wazuh Compose/Agent | LOG/별도 SIEM 실제 IP로 바인딩·출발지 허용목록·로그 경로·파이프라인을 조정. 기본 자격증명과 Security Plugin 비활성 설정은 배포 전 교정 | `docker compose config`, 포트 바인딩/health, 같은 시험 이벤트의 수집·색인·대시보드 조회 |
| `dashboard/*`, `analyzer/*`, `scenarios/*`, `tests/*`, `docs/*`, `pcaps/metadata/*` | 10.77 예시·필터·상관 키·테스트 데이터와 **실제 M1·M2 증거**를 구분. 기존 합성 PCAP의 IP를 실제 관측값으로 표기 금지 | 테스트/문서 대조, PCAP SHA-256, 새 Incident ID |

주의: `HOME_NET` 네 대역 지정은 **룰 검토 출발점**이다. Transit SPAN만 있는 동안 외부→Web 패킷을 만들어내지는 않는다. 대시보드 GeoIP도 사설/실습 공인 IP를 실제 공격 발원지로 지오코딩하지 않는다.

### 3.1 서비스 연결과 수신 포트 (최종 바인딩은 배치안에서 확정)

| 출발지 → 목적지 | 목적/포트 | 배포 전 확인 |
|---|---|---|
| PC2 센서 관리 NIC → LOG/ELK | EVE 전달: Beats `5044/TCP` **또는** JSON lines `5047/TCP` | 두 전송 방식 중 하나를 선택하고 송신 에이전트·인증·수신 정책을 실제 구현. 현재 저장소의 Logstash 입력만으로 송신기는 생기지 않음 |
| TrusGuard/Switch/Web → LOG `.30.3` | 기존 rsyslog 수신 포트와 Logstash `5514/UDP`는 별도 | 장비 GUI와 LOG의 실제 소켓·저장 경로 확인; 중복 수집 방지 |
| 센서/Web/DB Agent → Wazuh Host | `1514/TCP` 이벤트, `1515/TCP` 등록 | Wazuh 호스트 IP 배정·라우팅·TrusGuard/호스트 방화벽 승인 후만 개방 |
| LOG/별도 SIEM 로컬 | Elasticsearch `9201/TCP`, Wazuh Indexer `9200/TCP`, Manager API `55000/TCP` | 루프백 바인딩; 두 인덱서의 메모리/디스크 동시 사용량 확인 |
| Admin PC `.10.2` → Kibana/Wazuh/SOC 콘솔 | Kibana `5602/TCP`, Wazuh Dashboard `443/TCP`, SOC API `8501/TCP`는 저장소 예시 | 요구사항상 보안담당자 1명만 허용. 실제 배포는 HTTPS·인증·ACL·호스트 방화벽을 확정하고 비관리 PC 차단 시험 |

네트워크 경로가 미확정인 포트는 열지 않는다. 특히 Analyse PC2의 SPAN 수집 NIC에는 L3 주소나 송신 경로를 만들지 않는다.

## 4. 배포 전 준비 및 M1·M2 기반 구축

### P0 — 변경 승인·백업·작업 원장

1. DESIGN-ISSUE-001의 ADR을 결정하고 관리자·센서·SIEM의 호스트/관리 IP, 관리 NIC, 포트, 장비 소유자를 확정한다. 기존 `192.168.30.3`은 LOG 서버이고, `192.168.40.6`은 Analyse PC 1이다. **두 주소를 임의로 SOC 신규 서버에 재사용하지 않는다.**
2. L3/L2 `show running-config`, `show startup-config`, `show interfaces trunk`, `show ip route`, `show ip access-lists`, `show monitor session all`과 TrusGuard 인터페이스·라우트·주소 객체·NAT·정책 화면을 백업한다. 파일에 장비/시각을 기록하고 비밀값을 마스킹한다.
3. 현장 결선을 사진·포트 라벨로 기록한다. L2SW1 Gi1/0/4는 VMware용 **제안 포트**이며 Access 일괄 설정 범위와 겹칠 수 있다. 사용 가능 여부를 확인한다. Gi1/0/13의 기존 사용과 Gi1/0/24 Routed Port의 SPAN 지원 여부도 확인한다.
4. M1·M2 PDF 제20장 T01–T20 상태표를 새 날짜로 복제한다. 과거 VM1 ARP 실패, VM2 미검증, SPAN 미설정 및 NAT hit 0 이력은 현재 PASS로 옮기지 않는다.

**게이트:** 승인 ADR/롤백·백업·현장 주소 충돌 확인 완료. 미충족 시 `BLOCKED`.

### P1 — 물리망·라우팅·정책을 먼저 검증

M1·M2 PDF 제4–17장의 L2SW1/2 Trunk, L3 SVI, FW Transit/기본·정적 경로, NAT 객체 및 정책, VLAN ACL, VMware VMnet2 Bridged를 **해당 장비 콘솔에서** 재구축·검증한다. 기존 설정이 있는 장비에 예시 블록을 무조건 다시 붙여 넣지 않는다.

검증 순서: 링크 → VLAN/MAC → ARP → 게이트웨이 Ping → 반환 라우트 → ACL 허용/차단 → NAT 세션 → Web↔DB 서비스 → LOG 수신. 특히 VM1 `192.168.10.101 → 192.168.10.1` ARP 왕복과 VM2 `192.168.20.101 → 192.168.20.1`을 다시 시험한다. WAN `.214`, SNAT `.163`, VIP `.164`를 구분하고 방화벽의 내부 3개 정적 경로가 `192.168.40.2`로 향하는지 확인한다. Web→DB는 TCP 3306과 실제 MySQL 응답·방화벽 hit를 함께 기록한다.

**게이트:** 해당 M1·M2 T01–T18이 증거를 갖춘 PASS여야 IDS 단계로 진행한다. 기존 프로젝트의 M1·M2 기능을 SOC 배포로 대체하지 않는다.

### P2 — SPAN 실수신 (최우선 SOC 게이트)

1. L3 `show monitor session all`을 먼저 저장하고 session 1이 비어 있는지, Gi1/0/24 Routed Port를 source로 쓸 수 있는지 장비/펌웨어에서 확인한다. Gi1/0/13에 다른 업무가 없고 PC2 수집 NIC가 연결되어 있는지 확인한다.
2. 승인된 변경 창에서 M1·M2 PDF 제19장대로 `monitor session 1 source interface GigabitEthernet1/0/24 both` 및 `monitor session 1 destination interface GigabitEthernet1/0/13`을 적용한다. Gi1/0/24의 Routed Port 설정·IP는 건드리지 않는다.
3. PC2의 **실제** 수집 NIC를 식별한다. 관리 NIC와 혼동하지 않고 수집 NIC만 IPv4/IPv6 주소·기본 GW 없이 둔다. 기존 NIC의 IP를 확인 없이 flush하지 않는다. Linux 센서라면 `ip -br addr`, `ip -br link`, `tcpdump -eni <실측_수집_NIC> -c 50`을 쓴다. Windows PC2라면 Wireshark/Npcap에서 해당 NIC를 지정한다.
4. 관리자 PC `.10.2`에서 **승인된** 외부 시험 대상으로 Ping/HTTP를 발생시킨다. `show monitor session all`의 source/destination 상태와 PC2 PCAP의 시각·5-tuple·양방향 패킷을 대조한다. 캡처 파일 SHA-256을 기록한다. 원래 FW↔L3 통신도 재검증한다.

**GATE-MIRROR-01 / GATE-NET-01:** 설정 존재와 실수신은 별개다. PC2에서 정확한 시험 흐름이 보이지 않으면 `FAIL` 또는 원인 미확인 시 `BLOCKED`; IDS 설치 단계 중지. Gi1/0/24 source 미지원이면 포트를 Access로 바꾸지 말고 설계 대안을 ADR로 결정한다.

### P3 — 센서·Suricata·Snort 배포

1. PC2를 Linux 센서로 운영할지, SPAN NIC에 직접 연결한 별도 Linux 장비를 둘지 결정한다. Windows PC2 Wireshark만 사용 가능하면 먼저 **오프라인 PCAP 검증**으로 제한한다. VM 경유 캡처는 브리지·promiscuous·태그가 실제 통과하는지 추가 검증한다.
2. 센서에 승인된 Suricata **8.0.6**, Snort **3.12.2.0**, libDAQ **3.0.27**을 설치하고 `suricata --build-info`, `snort -V`, DAQ 버전을 기록한다. 패키지 저장소가 다른 버전을 제공하면 조용히 업그레이드하지 않고 `VERSION-DRIFT`를 작성한다.
3. 원본 `suricata/config/suricata.yaml`을 읽고 새 프로파일 파일에 위 `HOME_NET/HTTP_SERVERS/SQL_SERVERS`와 실측 AF_PACKET NIC를 **한 번씩만** 반영한다. 기존 YAML 끝에 두 번째 `vars:`나 `outputs:` 블록을 추가하지 않는다. 저장소 룰 소스와 `/etc/suricata/rules/` 런타임 경로를 구분한다.
4. 서비스 재시작 **전** `suricata -T -c <M1M2_CONFIG>`, `snort -T -c <M1M2_SNORT_CONFIG>`로 검증한다. PC2가 받은 동일 PCAP을 Suricata/Snort에 재생해 SID·src/dst·룰이 맞는지 확인한다. 실시간 Suricata는 `eve.json`의 고유 시각/flow_id/SID와 원 PCAP을 연결한다.

작업자 점검 명령(대괄호 값은 현장 실측 후 치환):

```bash
ip -br link
ip -br addr
sudo tcpdump -eni <SPAN_NIC> -c 50
sha256sum <승인된_소형_PCAP>
suricata -T -c <M1M2_CONFIG>
snort -T -c <M1M2_SNORT_CONFIG>
snort -c <M1M2_SNORT_CONFIG> -r <동일_PCAP> -A alert_json
```

PCAP을 재생할 Suricata 구문은 설치 버전의 `suricata --help`에서 확인하고 실시간 수집 프로세스와 충돌하지 않게 실행한다. 센서의 `eve.json`에서 `event_type`, `timestamp`, `src_ip`, `dest_ip`, `alert.signature_id`, `flow_id`를 원 PCAP과 비교한다.

**GATE-SURI-01 / GATE-DETECT-01 / GATE-PCAP-01 / GATE-SNORT-01:** SPAN 패킷·EVE·양 엔진 비교·PCAP 해시가 실제 증거로 연결되어야 PASS. 일반 `curl`로 웹 경보가 반드시 나온다고 가정하지 않는다.

### P4 — 필수 M1·M2 LOG·ELK 연동

1. LOG `192.168.30.3`에서 RAID1(5GB×2, `/var/log/backuplog`), rsyslog의 FW/Switch/Web 수신, DB/Web 로그 수집, NTP를 먼저 검증한다. 저장 공간·RAM·CPU를 실측한 뒤 필수 ELK 설치 방식을 확정한다.
2. 저장소 `infrastructure/elk/docker-compose.elk.yml`은 **그대로 배포 가능한 운영 설정이 아니다**. 기본값 비밀번호, `0.0.0.0` 수집 포트 바인딩, Wazuh 외부 볼륨 의존성, 정적 파이프라인 자격증명을 점검하고 승인된 호스트 바인딩·비밀 저장 방식으로 별도 프로파일을 만든다. `docker compose ... config`를 통과시킨 뒤 각 컨테이너 health, 제한된 관리 PC의 Kibana 접근, 비관리 PC 차단을 확인한다.
3. Suricata EVE 전달은 승인된 경로를 하나 선택한다: 센서 관리 NIC를 통한 Agent/Beats 전송 또는 무IP PC2의 해시 검증된 PCAP/EVE 수동 전달. `5044/TCP`는 Beats 입력이고 `5047/TCP`는 Logstash JSON lines 입력이므로 송신 방식과 입력을 맞춘다. **SPAN 전용 NIC로 SIEM 연결을 시도하지 않는다.**
4. 단일 고유 시험 이벤트의 EVE 원문→Logstash 수신→Elasticsearch 문서 ID→Kibana 조회를 기록한다. FW Syslog는 기존 rsyslog 수신을 유지하고, Logstash `5514/UDP` 직수신은 포트·전송 방식·중복 보관 정책을 확정한 경우에만 추가한다.

배포 명령은 **수정된 별도 프로파일의 경로**로 실행한다. 원본 예시 Compose가 통과했다는 사실만으로 실환경 배포를 승인하지 않는다.

```bash
docker compose -f <M1M2_ELK_COMPOSE> config --quiet
docker compose -f <M1M2_ELK_COMPOSE> up -d
docker compose -f <M1M2_ELK_COMPOSE> ps
```

**게이트:** M1·M2 필수 LOG/ELK의 실제 수신과 조회를 별개로 검증. 단순 컨테이너 `Up`은 로그 통합 PASS가 아니다.

### P5 — Wazuh·SOC 조사 확장 (ADR 승인 후)

1. Wazuh 배치 위치를 결정한다. LOG `.30.3` 공존은 5GB×2 로그 볼륨과 ELK 외의 **별도 인덱스 자원**을 요구하므로 RAM/디스크/포트/백업을 실측해야 한다. Analyse PC1 `.40.6`은 이미 관리 PC이므로 임의 전용 서버로 전환하지 않는다. 별도 호스트라면 담당자가 새 IP와 경로를 배정한다.
2. Wazuh 4.14.7 Manager/Indexer/Dashboard, 센서 및 필요 시 Web/DB Agent를 설치한다. `1514/1515/TCP`는 필요한 출발지에만, `9200/55000/TCP`는 로컬 전용, Dashboard는 승인된 관리자에게만 노출한다. 기존 Compose의 `admin/admin` 및 보안 플러그인 비활성 상태는 운영 배포 전 수정한다. ELK Kibana와 Wazuh Dashboard의 포트도 충돌 없이 배치한다.
3. `/var/log/suricata/eve.json`의 **같은** 이벤트가 Agent→Manager alert ID→Indexer 문서→Dashboard 검색에 나타나는지 검증한다. ELK 이벤트와는 timestamp/flow_id/SID로 연결한다. SIEM 호스트 및 Agent의 NTP 상태를 먼저 확인한다.
4. SOC 조사표준에 따라 raw EVE, PCAP SHA-256, 룰 rev, 연관 로그, ATT&CK 근거, `TRUE_POSITIVE/FALSE_POSITIVE/BENIGN/UNRESOLVED` 판정을 기록한다. 정상/허용 트래픽과 승인된 합성 공격 PCAP으로 튜닝 전후를 비교한다.

**GATE-WAZUH-01 / GATE-SIEM-01 / GATE-ANALYSIS-01 / GATE-TUNE-01 / GATE-E2E-01:** 각 단계의 동일 이벤트 식별자가 연결되지 않으면 PASS 금지. AI·SOAR 자동 차단은 P0/P1 게이트 완료와 별도 정책 승인 후에만 검토한다.

## 5. 현장 검증표와 증거

| 순서 | 실행 위치 | 최소 관측값 | 다음 단계 조건 |
|---|---|---|---|
| 0 | L2/L3/FW/VM | 설정 백업, 관리 접근, 실제 IP·결선 | ADR/변경 창 승인 |
| 1 | M1·M2 T01–T18 | VLAN/MAC/ARP, NAT hit, Web↔DB, LOG | 모든 핵심 흐름 증거 |
| 2 | L3·PC2 | `show monitor session all` + 같은 5-tuple PCAP | 양방향 SPAN 실수신 |
| 3 | 센서 | Suricata/Snort 버전, `-T`, EVE SID/flow_id, PCAP 해시 | 탐지 재현 |
| 4 | LOG/ELK | rsyslog 파일, Logstash 수신, ES 문서, Kibana 조회 | 같은 이벤트 연결 |
| 5 | Wazuh (승인 후) | Agent/Manager/Indexer/Dashboard의 같은 이벤트 | 전체 파이프라인 연결 |
| 6 | 조사·튜닝 | 사건 ID, ATT&CK 근거, 정상/공격 전후 비교 | 최종 증거 패키지 |

증거 폴더는 기존 `EV-*` 규칙을 따른다. 매 기록에 작업 시각(KST), 장비/실측 인터페이스, 명령, 기대/실제, `PASS/FAIL/BLOCKED`, PCAP 해시, 관련 EVE/룰/사건 ID, 롤백 결과를 남긴다. 기존 Lab의 `EV-E2E-*`나 M1·M2 PDF에 적힌 과거 상태를 새 배포의 PASS로 재사용하지 않는다. 네트워크 변경 중 실패하면 **해당 단계에서 중단**하고 백업 설정/배선과 변경 전 시험 결과를 기준으로 복구한다. SPAN만 되돌릴 때도 세션 번호·기존 세션을 확인한 후 해당 세션만 제거한다.

## 6. 현재 차단 항목 및 실행 인계

| 항목 | 현재 상태 | 해소 조건 |
|---|---|---|
| 아키텍처 변경 | `BLOCKED` | ADR 승인 및 M1·M2 프로파일 범위 확정 |
| VM1/VM2 게이트웨이 | VM1 실패 이력, VM2 미검증 | 현장 MAC→ARP→Ping 증거 |
| SPAN | PDF상 미설정/TARGET | Gi1/0/24 source 지원, Gi1/0/13 여유, PC2 양방향 PCAP |
| SOC 관리 경로/IP | 미배정 | 센서·SIEM 호스트/관리 NIC/IP/방화벽 정책 확정 |
| 외부→DMZ 라이브 웹 탐지 | Transit SPAN으로 수집 불가 | 별도 DMZ TAP/SPAN 설계·승인·실수신 |
| Wazuh와 ELK 공존 | 자원·보안설정 미검증 | 배치안, 용량, 자격증명, 포트 및 E2E 검증 |

## 출처

- 사용자 제공 `●인프라 보안 구축 프로젝트 시나리오_2026v2.pdf` pp. 2–10: 목표 구성, VLAN/DMZ, Web/DB/LOG/ELK, 정책·SPAN·NTP, 발표 산출물.
- 사용자 제공 `M1M2_통합_네트워크_보안_인프라_구축_및_재구축_매뉴얼.pdf` pp. 1–6, 13–16, 18–25, 28–29: 실제 주소/객체, 결선, 미검증 상태, SPAN, T01–T20.
- 저장소 `AGENTS.md`, `docs/01-requirements/`, `docs/02-architecture/`, `docs/03-design/`, `docs/04-deployment/`, `infrastructure/`, `suricata/`, `snort/`, `wazuh/`.
