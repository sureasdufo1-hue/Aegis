# 지금 완료·확인해야 할 사항과 확인 방법

작성일: 2026-09-23 KST  
범위: M1/M2 물리 인프라에 기존 SOC Lab을 **별도 프로파일로** 통합하기 위한 작업 인계표. 이 문서는 작업 지시·확인 절차이지, 현장 장비의 완료 증명이나 설정 변경 승인이 아니다.

## 1. 먼저 읽을 결론

- **지금 확인된 것:** 현 조사 PC는 `10.10.70.151/25`이고, 이 PC의 Docker에서 ELK `8.17.3` 및 Wazuh `4.14.7` 컨테이너가 실행 중이다. Wazuh Manager에 등록된 원격 Agent는 없다. 상세 근거는 [Phase 0 보고서](CURRENT_STATE_REPORT.md)와 [관측 증거](PHASE0-EVIDENCE.md)를 본다.
- **아직 확인되지 않은 것:** 관리자 PC `192.168.10.2`, LOG `192.168.30.3`, Analyse PC 2, Cisco/TrusGuard의 **현재** 설정·자원·연결·SPAN 패킷, 물리망 로그·탐지·Incident. M1/M2 문서의 당시 `VERIFIED`는 2026-09-23 런타임 `PASS`가 아니다.
- **즉시 작업 우선순위:** ① 접근권한·변경승인·복구 경로 ② 현장 자산/IP/배선/설정 실사 ③ M1/M2 T01~T18 검증 ④ SPAN 실제 패킷 수신 ⑤ LOG/ELK/Wazuh 배치 결정 ⑥ IDS·수집·SOC E2E. **패킷 가시성 전 IDS 의존 작업 금지.**
- 기존 Hyper-V·`10.77.*` 승인 기준을 물리망 주소로 일괄 치환하지 않는다. `DESIGN-ISSUE-001`에 대한 **승인 ADR**이 없으므로 새 배포 프로파일의 실제 적용은 `BLOCKED`다. 설계 조사와 읽기 전용 조회는 계속할 수 있다.

`PASS`/`FAIL`/`BLOCKED`는 **게이트 판정**에만 사용한다. 아래 `미확인`은 아직 시험을 수행하지 않았다는 뜻이며 `FAIL`이 아니다. `PASS`에는 장비·시각·명령/화면·실제값·증거 ID가 필요하다.

## 2. 지금 가능한 읽기 전용 확인: 작업 목록

아래 명령의 `<...>`는 실제 장비·인터페이스·경로를 확인한 뒤 입력한다. 출력에 계정·비밀값·개인정보·전체 설정이 있으면 저장소에 올리지 말고 승인된 보관 위치에 저장한 후 공유본만 마스킹한다.

| ID | 확인/완료해야 할 사항 | 어디서·왜·어떻게 확인 | 정상 기준 / 실패 시 첫 점검 | 남길 증거 | 현재 |
|---|---|---|---|---|---|
| A01 | 작업 범위·소유자·ADR 결정 | 프로젝트 책임자: `DESIGN-ISSUE-001`의 원본 Lab 보존, M1/M2 별도 프로파일, PC2 센서, LOG/ELK/Wazuh 배치, DMZ 사각지대·시험 범위를 승인 ADR로 결정 | 승인자·날짜·선택안·영향·롤백·담당자가 기록됨. 미승인 시 설정 변경 중지 | ADR ID/승인본 | BLOCKED |
| A02 | 장비 접속·복구 수단·백업 | Cisco 콘솔, TrusGuard 관리자 화면, VM/서버 콘솔의 접속 주체 확인. 각 장비의 현재 설정/VM 백업 및 복원 담당자 확인 | 관리 경로와 백업 **복원 가능성**이 명확함. 원격만 가능하거나 백업 없으면 변경 중지 | 백업 시각·보관처·복원 점검 기록(비밀값 제외) | 미확인 |
| A03 | 실제 배선·포트 점유 | Cisco `show interfaces status`, `show interfaces trunk`, 가능하면 `show cdp neighbors detail`; 현장 케이블 라벨/사진. TrusGuard eth1/2/3 링크 화면 | L3 Gi1/0/24↔FW eth2, Gi1/0/13↔PC2, L3 Gi1/0/4↔PC1, L2SW1 Gi1/0/4 후보 점유가 실제와 일치. CDP 부재만으로 실패 판정 금지 | 포트 양단 표·링크 상태·사진 | 미확인 |
| A04 | M1/M2 IP·VLAN·라우트·ACL·NAT 현값 | Cisco `show vlan brief`, `show ip interface brief`, `show ip route`, `show ip access-lists`, 관련 인터페이스 `show running-config interface ...`; TrusGuard 인터페이스/주소객체/NAT/정책/라우팅 화면 | [IP 목록](IP_INVENTORY.md)의 주소·역할과 비교. WAN `.214`, SNAT 객체 `.163`, VIP 객체 `.164`를 구분. 값이 다르면 원인·승인 여부 조사, 즉시 덮어쓰기 금지 | 마스킹된 설정 차이표·화면 | 미확인 |
| A05 | 관리자·내부 PC 실제 NIC/IP | **각 해당 PC**의 PowerShell `Get-NetAdapter`, `Get-NetIPConfiguration`, `Get-NetRoute -AddressFamily IPv4` | Admin `.10.2`, User `.20.2`와 GW가 실제 NIC에 매핑. 현 조사 PC `.70.151`을 Admin으로 가정하지 않음 | 명령 출력·호스트명·시각 | 미확인 |
| A06 | VMware 호스트 2 NIC·VMnet2 | **VMware 물리 호스트**의 `Get-NetAdapter`, `Get-NetIPConfiguration`, `Get-NetAdapterBinding -Name '<실측_두번째_NIC>'`; VMware Virtual Network Editor와 VM1/VM2 네트워크 어댑터 화면 | 두 번째 물리 NIC가 실제 Trunk 포트에 연결, VMnet2가 해당 NIC에 수동 Bridged, 두 VM이 Custom VMnet2. 브리지 표시만으로 VLAN 태그 전달 증명 불가 | NIC 설명/MAC↔스위치 포트↔VMnet2 대응표 | 미확인 |
| A07 | VM1·VM2 IP·VLAN·ARP | **각 VM 콘솔**에서 `ip -br addr`, `ip route`, `ip -d link show`, `ip neigh`; 스위치 `show mac address-table interface gigabitEthernet 1/0/4` | VM1 `vlan10` `.10.101/24`, VM2 `vlan20` `.20.101/24`, 각 GW `.10.1/.20.1`; 서로 다른 MAC이 VLAN별 학습. PDF의 VM1 ARP 실패는 과거 이력 | VM별 출력·실제 MAC·VLAN별 스위치 학습 | 미확인 |
| A08 | PC2 OS·NIC·SPAN 목적지 | **Analyse PC2 로컬 콘솔**에서 OS/CPU/RAM/저장공간/NIC 이름·MAC·연결 상태 확인. Windows: `Get-ComputerInfo`, `Get-NetAdapter`, `Get-NetIPConfiguration`; Linux: `cat /etc/os-release`, `lscpu`, `free -h`, `lsblk`, `ip -br addr`, `ip route` | 수집 NIC와 관리 NIC를 물리적으로 구분. 수집 NIC에는 L3 IP·기본 GW가 없음. 관리 IP는 **미배정**이며 임의 할당 금지 | PC2 자산표·NIC↔Gi1/0/13 배선·IP 출력 | 미확인 |
| A09 | LOG `.30.3` 실제 사양·RAID·rsyslog | **LOG 서버 콘솔**에서 `cat /etc/os-release`, `lscpu`, `free -h`, `lsblk -o NAME,SIZE,TYPE,MOUNTPOINTS`, `df -hT`, `cat /proc/mdstat`, `findmnt /var/log/backuplog`, `systemctl status rsyslog --no-pager`, `sudo ss -lunp` | M5 제안과 실제 자원/RAID1/마운트/수신 포트/원본 파일을 구별. RAID 장치명이 확인된 경우에만 `mdadm --detail <실측_MD_장치>` 조회. 8GB 제안은 ELK 동거 승인 근거 아님 | 자원·마운트·서비스·보존량/일 측정표 | 미확인 |
| A10 | 현 ELK/Wazuh 데이터·위치·노출 | **현재 Docker 호스트**에서 `docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'`, `docker stats --no-stream`; Wazuh Manager에서 `agent_control -l`. 설정은 저장소 Compose·Pipeline 파일과 대조 | 현재 PC의 서비스와 LOG `.30.3` 서비스를 혼동하지 않음. ES/Logstash/Kibana 순간 메모리 약 9.36GiB(2026-09-23)는 **용량 경고**; 장기 피크·디스크·수집량 재측정. 0.0.0.0 포트의 실제 접근 경계 검토 | 버전/포트/리소스·Agent 목록(비밀값 제외) | 일부 관측, 최종 배치 미확인 |
| A11 | M3~M7 계획과 실물 차이 | 정정판 M3(5), M4(4), M5(4), M6(4), M7(4)의 목표값을 Web/DB/LOG/PC2 실측값과 1:1 비교 | 구판 DB `.30.10`, LOG `.30.20`, Admin `.10.10`, PC1 `.10.50` 등을 사용하지 않음. 다른 값이면 현장 변경 이력 확인 | 자산별 `목표/실제/차이/결정` 표 | 미확인 |
| A12 | NTP·로그 시각 기준 | 각 Linux `timedatectl status`(Chrony 사용 시 `chronyc sources -v`), Windows `w32tm /query /status`, 스위치/방화벽의 시각·NTP 상태 화면 | 로그 원천 간 시간대·동기화 상태와 오차가 기록됨. 오차 허용치는 승인된 시험 기준에서 확정 | 장비별 시각·타임존·오프셋 | 미확인 |

**A01~A12의 조회는 설정을 바꾸지 않는다.** `Get-...`, `show ...`, `status`, `ip ... show`는 확인용이다. `configure terminal`, `ip addr flush`, `netplan apply`, NIC 브리지 변경, 케이블 이동, 서비스 재시작, 볼륨 삭제는 이 표에 포함되지 않으며 ADR·백업·변경 창·롤백 계획이 선행되어야 한다.

## 3. M1/M2 T01~T20 현장 검증표

아래의 `ping`, TCP 접속, HTTP 요청, 로그 테스트는 해당 장비 소유자와 **승인된 실습 대상·변경 창**에서만 수행한다. 특히 외부 테스트는 임의 인터넷 대상이 아니다. `Test-NetConnection`의 성공은 애플리케이션 정상·정책 준수의 단독 증거가 아니다. PDF의 모든 T 결과는 작성 당시 `미기록`이므로 현재도 미검증이다.

| ID | 실행 장비 / 확인 방법 | 정상 결과·실패 시 점검 | 증거 |
|---|---|---|---|
| T01 | L2SW1: `show interfaces status`로 관리자/내부 PC 실제 Access 포트 확인 | 두 포트 connected. 실패 시 케이블·상대 NIC·포트 shutdown | 포트 출력/양단 라벨 |
| T02 | L2SW1↔L3: 양쪽 `show interfaces trunk` | VLAN10/20 허용·forwarding. 실패 시 포트 매핑·allowed VLAN·링크 | 양단 trunk 출력 |
| T03 | L2SW2↔L3: 양쪽 `show interfaces trunk` | VLAN10/20/30 허용·forwarding. 실패 시 동일 | 양단 trunk 출력 |
| T04 | L3: `show ip interface brief`, `show vlan brief` | VLAN10/20/30 SVI `up/up`. 실패 시 VLAN 활성 포트·SVI shutdown | SVI 출력 |
| T05 | Admin `.10.2`: `ping 192.168.10.1`; L3 `show ip arp` | GW 왕복+ARP. 실패 시 IP/GW/VLAN10/Access 포트 | Ping·ARP |
| T06 | User `.20.2`: `ping 192.168.20.1`; L3 `show ip arp` | GW 왕복+ARP. 실패 시 VLAN20/포트 | Ping·ARP |
| T07 | DB `.30.2`와 LOG `.30.3` **각각**: `ip -br addr`, `ip route`, `ping -c 4 192.168.30.1` | 둘 모두 GW 왕복+ARP. 실패 시 NIC/VLAN30/호스트 정책 | 서버별 Ping·ARP |
| T08 | L3: `ping 192.168.40.1`, `show ip arp`, `show ip route`; TrusGuard 인터페이스 상태 | `.40.2/30↔.40.1/30` 경로. 실패 시 Gi1/0/24↔eth2 결선/Zone | 양쪽 인터페이스·Ping·ARP |
| T09 | PC1 `.40.6`: `ping 192.168.40.5`(Windows라면 `ipconfig /all` 병행) | 별도 `.40.4/30` 관리 링크 왕복. 실패 시 PC1↔L3 Gi1/0/4. PC2와 혼동 금지 | PC1 IP·Ping |
| T10 | Admin `.10.2`: 승인된 DB 서비스에 `Test-NetConnection 192.168.30.2 -Port 3306`; L3 ACL hit 확인 | 관리자 허용. ICMP는 DB 호스트 정책에 따라 별도 판정. 실패 시 ACL 방향·DB 리슨·호스트 방화벽 | TCP 결과·ACL 카운터 |
| T11 | VM1 `.10.101`: 승인된 신규 DB TCP 연결 시도; `show ip access-lists VLAN10_TO_VLAN30` | 비관리 VLAN10→DB 신규 연결 차단, deny hit 증가. 실패 시 실제 VM1 주소·ACL 순서/적용 방향 | 시도 결과·ACL 카운터 |
| T12 | User `.20.2`: 승인된 신규 DB TCP 연결 시도; `show ip access-lists VLAN20_TO_VLAN30` | VLAN20→DB 신규 연결 차단. 실패 시 적용 인터페이스/방향·예외 | 시도 결과·ACL 카운터 |
| T13 | VM1: `ping -I vlan10 -c 4 192.168.10.1`, `ip neigh show dev vlan10`; L2SW1 VLAN10 MAC 확인 | `lladdr` 학습+왕복. PDF 당시 ARP `FAILED` 재검증. 실패 시 VMnet2→Ethernet2 브리지·tag·trunk·MAC 순서로 추적 | Ping·neighbor·MAC |
| T14 | VM2: `ping -I vlan20 -c 4 192.168.20.1`, `ip neigh show dev vlan20`; L2SW1 VLAN20 MAC 확인 | VM2 별도 MAC·VLAN20 학습+왕복. 실패 시 인터페이스 이름/태그/브리지 | Ping·neighbor·MAC |
| T15 | **승인된 외부 시험 PC**: Web VIP `.164`의 80/443에 `Test-NetConnection`; 방화벽 NAT 세션/hit·Web access log 대조 | DNAT `.164→172.16.10.10`과 실제 Web 응답. 443 미구축이면 443은 BLOCKED. 실패 시 VIP 상위 ARP/route·정책·Web listener | PC 응답·NAT 세션·Web 로그 |
| T16 | Admin/User PC: **승인된 외부 테스트 주소**로 접속; TrusGuard NAT 세션 화면 | 변환 후 출발지가 SNAT 객체 `.163`. WAN 인터페이스 `.214`와 혼동 금지. 실패 시 NAT 규칙 hit·상위 NAT | 원본/변환 주소·세션 ID |
| T17 | Web `.10.10`: 승인된 DB `.30.2:3306` 연결 및 애플리케이션/MySQL 응답; 방화벽 hit/log | TCP뿐 아니라 실제 서비스 응답. 실패 시 Web/DB GW·DB 계정/리슨·FW 정책 | Web/DB/FW 동일 시각 로그 |
| T18 | Web/FW에서 승인된 로그 한 건을 발생·조회하고 LOG `.30.3`의 rsyslog 원문/시각을 대조 | 실제 원천·도착·원문 보존 경로 확인. 파일 존재만으로 PASS 금지. 실패 시 ACL·수신 포트·포맷·디스크·시간 | 원천 로그 ID·LOG 수신 시각·파일 참조 |
| T19 | L3 `show monitor session all`; PC2 해당 NIC Wireshark 또는 `tcpdump`에서 **Transit 통과가 확인된 승인 트래픽** 관찰 | Gi1/0/24 양방향→Gi1/0/13 실제 5-tuple·시간 일치, 원래 FW↔L3 경로 유지. 실패 시 source routed-port 지원·포트 점유·PC2 NIC | 세션 상태·짧은 PCAP SHA-256·5-tuple |
| T20 | Cisco/TrusGuard: 승인된 저장·재로그인/재조회 절차, 변경 전후 설정 비교 | 저장 설정이 의도와 일치하고 관리 접근 유지. 실패 시 백업·롤백 계획으로 복구 | 저장 시각·마스킹된 차이·재로그인 결과 |

T01~T18의 물리 서비스/보안 경로를 증거로 확인한 뒤 T19의 SPAN 실수신을 통합 게이트로 다룬다. 읽기 전용 SPAN 지원·포트 점유 조회는 먼저 할 수 있다. **T19 설정 화면만으로 `GATE-MIRROR-01`을 PASS 처리하지 않는다.** `tcpdump`/Wireshark에 목표 트래픽이 없다면 센서·Suricata·Wazuh 연동은 중지한다. `Gi1/0/24` Transit SPAN은 외부↔DMZ Web의 방화벽 `eth1↔eth3` 직접 경로와 내부 같은 VLAN 트래픽을 포괄하지 않는다.

## 4. SPAN·IDS·로그·SOC를 붙이기 전 추가 결정

| ID | 할 일 | 확인 방법과 완료 기준 | 막히면 |
|---|---|---|---|
| B01 | PC2 수집 NIC와 관리 경로 확정 | PC2 NIC별 MAC↔케이블↔L3 Gi1/0/13 대조. `ip -br addr`/`Get-NetIPConfiguration`에서 수집 NIC **무IP/무GW** 확인. 관리 NIC가 별도 없으면 로컬 콘솔·승인된 전달 경로 사용 | 관리 NIC/IP/ACL은 주소 점유·승인 뒤 결정; 수집 NIC에 임시 IP 부여 금지 |
| B02 | SPAN 지원·실수신 | L3 `show version`, `show running-config interface gigabitEthernet 1/0/24`, `...1/0/13`, `show monitor session all`; PC2에서 **실측 인터페이스**에 한해 `sudo tcpdump -eni <CAPTURE_NIC> -c 50` 또는 Wireshark로 제한된 수신 확인 | Routed Port source 미지원이면 Gi1/0/24를 Access로 바꾸지 말고 TAP/대체 설계 ADR. 캡처 전 명령은 관리자 승인 필요 |
| B03 | 센서 런타임·버전 | PC2 또는 승인 Linux 센서에서 `suricata -V`, `suricata --build-info`, `snort -V`와 libDAQ 버전, 실제 NIC/AF_PACKET 지원, 서비스 상태 확인 | Suricata `8.0.6`, Snort `3.12.2.0`, libDAQ `3.0.27`와 다르면 `VERSION-DRIFT-xxx`. 패킷 전 설치·탐지 완료 주장 금지 |
| B04 | 기존 Lab 설정 분리 | 저장소 `suricata/config/suricata.yaml`, `snort/config/snort.lua`, `infrastructure/elk/`, `dashboard/`, `analyzer/`의 `10.77.*`와 입력 경로를 목록화. M1/M2 전용 파일/테스트 설계 | 전역 치환·원본 덮어쓰기 금지. 원본 `HOME_NET=10.77.30.0/24` 유지 |
| B05 | LOG+ELK 통합/분리 | LOG의 실제 RAM/CPU/디스크/RAID·원문 유입량·보존 기간과 현 ELK의 피크 사용량을 측정. M5 8GB 제안 vs 현 ELK 순간 약 9.36GiB를 비교 | 수용 불가면 승인된 별도 ELK 호스트·IP·ACL·M6 설계 변경 필요. Wazuh Indexer 자원도 별도 산정 |
| B06 | 원본 로그/파서 | LOG `/var/log/backuplog`에 Web·DB·FW·Cisco의 **실제 샘플**이 도착하는지 확인. 기존 Logstash는 nftables 형식과 4개 Lab 파이프라인에 맞춰져 있어 TrusGuard/Cisco·M5 원문 입력을 별도로 설계 | 샘플 없으면 파서 성공 주장 금지; 원천별 타임존·장비명·이벤트 ID 기록 |
| B07 | Wazuh Agent/노출 | 승인 Manager 호스트·주소·라우트 확정 후 Web/DB/LOG/PC Agent 등록 목록·상태 확인. `docker exec soc-wazuh-manager /var/ossec/bin/agent_control -l`; 1514/1515와 Dashboard 443은 승인 출발지만, 55000/9200은 로컬 전용 확인 | 현 PC Manager에는 로컬 ID 000만 있음. 설치 위치 미확정이면 Agent 배포 금지 |
| B08 | SOC UI·상관·NAT | FastAPI 실행 호스트/포트 확인, Admin `.10.2` 브라우저에서 인증된 접근. 같은 사건의 원본 IP와 `source.nat.ip=.163`, `destination.nat.ip=.164`/Web `.10.10` 변환을 분리해 ECS·Incident로 연결 | `8501` 현 PC 리스너 없음. 로컬 mock/과거 `10.77.*` 이벤트를 실데이터로 오인하지 않음 |
| B09 | 동일 이벤트 E2E·증거 | 승인된 작은 PCAP/무해 시험에서 PC2 패킷→Suricata `eve.json`(timestamp/flow_id/SID)→수집 원본→ES/Wazuh 문서→상관 Incident→분석가 판정·재시험을 한 ID로 연결 | 단계 하나라도 미입증이면 해당 게이트 BLOCKED/FAIL. Snort는 같은 PCAP의 보조 오프라인 비교 |

### 변경 전 필수 체크

아래는 *계획을 승인한 다음* 각 변경 직전에 채운다. 값이 하나라도 비어 있으면 변경하지 않는다.

| 필드 | 기록할 내용 |
|---|---|
| Current State | 장비명·현재 IP/포트/설정·서비스·백업 시각 |
| Target State / Reason | M1/M2 기준값과 변경 이유, 영향 범위 |
| Authority | 승인 ADR·작업 승인자·시험 범위·변경 창 |
| Backup / Rollback | 보관 위치·복구 담당자·실제 되돌릴 절차와 확인법 |
| Implementation | **실측** 장비·인터페이스·명령·작업자 |
| Validation | 기대값/실제값, 긍정·부정 테스트, 관리 접속 유지 |
| Evidence | `EV-*` ID, 시각(KST), 캡처 해시, 로그/스크린샷의 승인 보관처 |

## 5. 가장 먼저 요청할 자료와 담당자에게 전달할 질문

1. **네트워크 담당자:** L2SW1/2·L3SW·TrusGuard의 현재 구성 백업, 포트 양단 표, `show monitor session all`, Gi1/0/24 routed-port SPAN 지원 여부, T01~T20 실제 최근 시험 결과가 있는가?
2. **VMware/PC 담당자:** 현 조사 PC의 비활성 `이더넷 2`가 문서의 VMware 호스트 NIC인가? VMnet2는 어느 물리 NIC에 Bridged인가? VM1/VM2 실제 MAC·게이트웨이 ARP 결과는? Analyse PC1과 PC2는 각각 어느 장비인가?
3. **서버 담당자:** LOG `.30.3`의 현재 OS·CPU·RAM·디스크·RAID1·마운트·rsyslog·NTP·일일 로그량은? Web `.10.10`과 DB `.30.2`의 실제 서비스/로그/접근통제는?
4. **SOC/변경 승인자:** PC2 관리 IP/경로, ELK·Wazuh·FastAPI 운영 호스트, DMZ 별도 가시성의 요구 수준, 허용된 시험 트래픽·변경 창, 기존 Lab 보존 방식과 ADR 선택은?

이 네 묶음의 실제 답변이 들어오기 전에는 새 IP·NIC·VM 수량, LOG+ELK 공존, Wazuh 이전, 운영 ACL 개방을 확정하지 않는다.

## 6. 증거 기록 양식과 다음 게이트

```text
항목 ID / Gate:
장비·실측 NIC/포트:
담당자·관측 시각(KST):
기준 문서/목표값:
실행한 읽기 명령 또는 승인된 시험:
실제 출력/값:
기대값과 차이:
결과: PASS / FAIL / BLOCKED
원인 또는 미확인 이유:
증거 ID·보관 위치(비밀/원본 로그는 저장소 제외):
변경 여부·백업·롤백 결과:
다음 조치/책임자:
```

**게이트 순서:** ADR·호스트/복구 준비 → T01~T18 연결·라우팅·정책·서비스·로그 → T19 SPAN/PC2 실수신 (`GATE-MIRROR-01`, `GATE-NET-01`) → Suricata/PCAP/Snort → Wazuh·ELK 동일 이벤트 → 조사·튜닝·E2E. T20은 변경 저장·재접속/복구 검증으로 닫는다. 상세 배포 절차는 [M1/M2 SOC 적용 매뉴얼](../04-deployment/M1M2_SOC_APPLICATION_RUNBOOK_2026.md)을 따른다. 현재 통합 배포 상태는 **IMPLEMENTATION BLOCKED**다.

## 출처

- `AGENTS.md` §§2–11, 14, 17–18, 25–30: 승인 기준, 패킷 선행, 게이트, 보안·증거 규칙.
- `M1M2_통합_네트워크_보안_인프라_구축_및_재구축_매뉴얼.pdf` (2026-09-20), pp. 3–6, 13–25: 주소·배선·VMware·SPAN·T01~T20. 문서의 설정 예시는 현재 장비에 자동 적용하지 않는다.
- 정정 M3~M7 계획, [Phase 0 현황 보고서](CURRENT_STATE_REPORT.md), [IP 목록](IP_INVENTORY.md), [서비스 목록](SERVICE_INVENTORY.md), [차이 분석](PROJECT_GAP_ANALYSIS.md).
