# PROJECT_GAP_ANALYSIS — 기존 구조와 목표 구조의 차이

## 차이 비교

| 계층 | 현재 관측/설정 | M1/M2 통합 목표 | 필요한 실제 변경 | 우선순위 |
|---|---|---|---|---|
| 네트워크 | VMware Lab `10.77.*`; 현 PC 외부망 `.70.151`; 물리 장비 미접근 | TrusGuard/Cisco, DMZ, VLAN10/20/30, M1/M2 고정 IP | 기존 Lab 보존, 별도 물리 배포 프로파일·ADR·현장 T01~T20 | P0 |
| 패킷 가시성 | Hyper-V/VMware용 센서 설정과 과거 Lab 로그 | PC2 Gi1/0/13 무IP SPAN 수신 | PC2 NIC/관리 경로 실사, Gi1/0/24 실제 미러·동일 트래픽 PCAP 검증 | P0 |
| 수집 커버리지 | 기존 Lab은 victim mirror 전제 | Transit SPAN + 장비/호스트 로그 | DMZ `eth1↔eth3` 및 내부 동VLAN 사각지대 명시, 필요 시 별도 캡처 설계 | P0 |
| 로그 원본 | 현 PC Docker 볼륨·저장소 구 로그 | LOG `.30.3` rsyslog·RAID·원본 보존 | 실제 LOG 서비스/용량 확인 후 수신·보존·재전송 구축 | P0 |
| ELK | 현 PC Docker 8.17.3; 4개 Logstash 파이프라인 | 물리망 Web/DB/장비/IDS 통합 검색 | 위치/자원 결정, M5 원문 입력·TrusGuard/Cisco 파서, 버전/비밀 관리 | P1 |
| Wazuh | 현 PC Docker 4.14.7; 원격 Agent 없음 | 물리 Web/DB/LOG/PC/VM Agent | 서버 배치·관리 IP·ACL·Agent 등록·동일 이벤트 추적 | P1 |
| SOC 콘솔·상관분석 | 코드 존재, 현 PC 8501 미실행; 로컬 파일/mock/10.77 기본값 | 관리자 `.10.2` 브라우저, 실제 ES·Wazuh 기반 Incident | 프로파일별 데이터 소스·ECS/NAT 매핑·UI/권한·회귀시험 | P1 |
| 증거 | 과거 Lab EVE/PCAP/합성 이벤트·인덱스 | 물리 사건의 패킷→탐지→원본→SIEM→판정→튜닝 | 물리망 E2E 증거 새로 획득; 기존 PASS 재사용 금지 | P0/P1 |

## 우선순위와 Phase 1 결정 게이트

1. **P0 — 승인/자산 확인:** 원본 Lab 보존을 전제로 `DESIGN-ISSUE-001`의 ADR 승인 여부, 물리 자산 소유자/접근권한, PC2·LOG·Admin·Wazuh 후보 호스트의 OS/CPU/RAM/Disk/NIC/IP를 확정한다.
2. **P0 — 물리 네트워크:** 현재 TrusGuard/Cisco 설정을 백업·읽기 조회하고 M1/M2 주소·VLAN·라우트·ACL·NAT·NTP·T01~T20을 재검증한다. 과거 VM1 ARP와 SPAN 미설정 이력을 재시험한다.
3. **P0 — 패킷 선행 게이트:** PC2 캡처 NIC 무IP, 관리 NIC 별도, SPAN 트래픽과 `tcpdump`/PCAP 증거를 먼저 얻는다. Transit 밖 DMZ·내부 가시성은 별도 요구/센서 결정으로 처리한다.
4. **P0 — 용량/데이터 보호:** LOG 제안 8GB 대비 현 ELK 사용 약 9.36GiB. 장기 피크·인덱스/원본/RAID 용량·백업/복원 성능을 측정하여 LOG+ELK 통합 vs 분리, Wazuh Indexer 별도 여부를 결정한다. 신규 IP/VM은 승인 전 임의 생성하지 않는다.
5. **P1 — 최소 연동:** 새 물리 로그 입력 어댑터와 장비별 원본 샘플 테스트, Wazuh Agent, ECS/NAT 정규화, SOC UI/상관분석을 단계적으로 붙인다. 10.77.* 기존 설정을 전역 치환하지 않는다.
6. **P1 — E2E:** 승인된 Lab/현장 시험 범위에서 동일 이벤트 ID·시간·5-tuple·PCAP·룰·Wazuh/ES 문서·Incident·판정·튜닝 재시험까지 추적한다.

## 조건부 권장 배치/데이터 흐름

| 자산 | 조건부 권장 역할 | 확정 전 필요 증거 |
|---|---|---|
| Admin PC `.10.2` | Kibana/FastAPI 브라우저 클라이언트 | 실제 OS·접속 경로·인증·방화벽 |
| LOG `.30.3` | rsyslog 수신, 원본 보존/버퍼링, 최소권한 전달 | 실제 RAM/CPU/RAID/디스크/로그량; M5/M6 동일 호스트 가능성 |
| Analyse PC2 | 수집 NIC 무IP의 패시브 Suricata 센서; Snort는 동일 PCAP 오프라인 대조 | OS/NIC/캡처 패킷/관리 IP·ACL |
| ELK | LOG 호스트에 충분한 증설이 가능하면 동거; 그렇지 않으면 승인된 별도 분석 서버 | 부하 측정, 주소·ACL·운영 책임, M6 설계 변경 승인 |
| Wazuh | Agent 경로가 보장되는 승인 서버/VM에 Manager·Indexer·Dashboard | 호스트 자원/IP, TLS·비밀·포트, 중복 색인 정책 |
| FastAPI/상관엔진 | ELK 검색 경로와 권한이 있는 승인 서버에서 실행 | 실데이터 연결·가용성·Admin 독립성 |

권장 데이터 흐름: 장비/Web/DB 원본→LOG 보존→Logstash/ES; PC2 SPAN→Suricata EVE→승인 전송 경로→중앙 수집; 호스트→Wazuh→선정 경보→ES; 공통 ECS/NAT 필드→상관엔진→단일 Incident→FastAPI. DMZ 패킷이 Transit SPAN에 없으면 방화벽/Web 로그로만 분석하고 **패킷 탐지 완료라고 주장하지 않는다**.

Phase 1의 설계 조사 자체는 시작 가능하나, 최종 배치/설치/이전은 **BLOCKED**다. 필수 입력은 승인 ADR, 현장 자원/주소/포트 인벤토리, 패킷 가시성 및 서비스 경로의 객관적 증거다.
