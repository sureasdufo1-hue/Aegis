# CURRENT_STATE_REPORT — Phase 0 통합 현황조사

작성일: 2026-09-23 KST  
조사 범위: 저장소, 제공 PDF/M3~M7 계획, 현 Windows/VMware/Docker의 읽기 전용 상태. 물리 스위치·방화벽·서버·PC2 로그인/설정 조회는 수행하지 못했다.

## 요청된 20개 조사 항목

| # | 항목 | 상태 | 관찰/결론 |
|---:|---|---|---|
| 1 | 기존 SOC 구조 | VERIFIED | `suricata/`, `snort/`, `wazuh/`, `infrastructure/elk/`, `dashboard/`, `analyzer/`, `evidence/` 존재. 기존 주 모델은 10.77.* Lab. |
| 2 | M1/M2 네트워크 기준 | TARGET | Cisco/TrusGuard·DMZ·VLAN10/20/30·Transit·PC2 SPAN 주소를 PDF에서 확인; 현재 장비 설정 미검증. |
| 3 | M3~M7 계획/실제 | TARGET/UNKNOWN | 2026-09-22 정정판 5개 접근 가능. Web/DB/LOG/ELK/NTP·SPAN 계획 확인; 물리 구축 증거 없음. 구판 주소는 사용 금지. |
| 4 | 관리자 PC 역할 | TARGET/UNKNOWN | 목표 `.10.2` 브라우저 관제. 현 조사 PC는 `.70.151`; 같은 장비라고 확인 불가. |
| 5 | LOG `.30.3` 사양/서비스 | UNKNOWN | M5 제안 8GB·RAID1·rsyslog, M6 ELK 동거. 실제 CPU/RAM/NIC/RAID/프로세스 미확인. |
| 6 | Analyse PC2 사양/NIC | UNKNOWN | SPAN 수집 NIC 무IP가 목표. 실제 OS·NIC 2개 여부·관리 경로 미확인. |
| 7 | Wazuh 실행 위치 | VERIFIED/UNKNOWN | 현 PC Docker의 4.14.7 3개 컨테이너 실행. 물리 목표 위치·원격 Agent 없음/미확인. |
| 8 | ES/Kibana 실행 위치 | VERIFIED/UNKNOWN | 현 PC Docker의 8.17.3 ELK 3개 실행. LOG `.30.3` 운영 여부 미확인. |
| 9 | Suricata/Snort 실행 위치 | CONFIGURED/UNKNOWN | 저장소 설정과 과거 로그 존재, 현재 Docker IDS 미실행. VMware 게스트 서비스 미접근. |
| 10 | FastAPI 실행 위치 | CONFIGURED/UNKNOWN | 코드 있음, 현 Windows PC 8501 리스너 없음. 다른 VM/서버는 미검증. |
| 11 | LOG/ELK 기능 중복 | BLOCKED | LOG 원본 보존과 ES 색인은 역할이 다름. 현재 실제 LOG 서비스 미확인 및 8GB 대비 ELK 사용량 초과로 배치 결론 보류. |
| 12 | Lab↔물리망 연동 가능성 | BLOCKED | 현재 PC `.70.151`, Lab VMnet `10.77.*`; 실제 `.30.3`/PC2 경로와 승인 ACL·ADR 없음. 단순 IP 치환 불가. |
| 13 | 변경 없이 재활용 | CONFIGURED | 룰/테스트/대시보드 UI/상관엔진 코드·Wazuh 4.14.7·ELK 파이프라인 구조는 후보. 물리 이벤트에 대한 무변경 재사용 성공은 미검증. |
| 14 | 이전 대상 | TARGET | 현 PC Docker ELK/Wazuh 백엔드의 최종 운영 위치 재결정, 센서 런타임·데이터 소스 분리. 데이터 이관 필요량은 미확인. |
| 15 | 신규 구축 대상 | TARGET | 물리 LOG 원문 수집, TrusGuard/Cisco/Web/DB 입력 어댑터, PC2 관리 경로, 실제 Agent·E2E 증거가 필요할 가능성. 설치 여부는 실사 후 결정. |
| 16 | 추가 IP/NIC/VM | UNKNOWN | PC2 관리 IP는 필요하지만 주소 미배정. PC2 NIC·LOG 용량/별도 분석 VM 필요 여부 미확인. 임의 배정 금지. |
| 17 | 네트워크·접근통제 | TARGET | LOG 수집 포트, Wazuh Agent, 관리자 Kibana/FastAPI, PC2 관리 전송의 최소권한 ACL 검토 필요. VLAN30 기존 차단 우회 금지. |
| 18 | 권장 물리 배치 | TARGET/BLOCKED | Admin은 브라우저; PC2는 패시브 캡처; LOG는 원문 수신·보존; ELK/Wazuh/FastAPI는 자원·승인 후 별도/통합 결정. |
| 19 | 권장 데이터 흐름 | TARGET | 물리 장비·Web/DB→LOG 원문→ES; PC2 EVE→승인 경로→중앙 수집; 호스트→Wazuh→선정 경보→ES; ES→상관엔진→FastAPI. 동일 사건 추적 필요. |
| 20 | Phase 1 가능 여부 | BLOCKED(확정) | 설계 조사·선택안 작성은 가능. 최종 배치/배포는 물리 실사, ADR 승인, IP·ACL·자원 검증 전 불가. |

## 주요 사실과 불확실성

- `vmrun list`는 VMware 5개 VM 실행을 보여 준다. VMX 파일은 2 vCPU/4GB 설정을 보여 주지만 게스트 OS/서비스/패킷 수집은 입증하지 않는다.
- 로컬 Wazuh Manager의 원격 Agent 목록에는 Manager 자신만 있다. 과거 인덱스 문서와 합성 이벤트 주입 스크립트는 실제 물리망 경보의 증거가 아니다.
- M1/M2 PDF의 VM1 게이트웨이 ARP 실패, VM2 통신 미검증, SPAN 미설정은 **문서 작성 당시 이력**이다. 현재도 실패한다고 단정하지 않고 Phase 2 재검증 대상으로 남긴다.
- 이 보고서는 읽기 전용 현황 기록이며 어떤 운영 게이트도 `PASS`로 올리지 않는다.

## Phase Result

Phase: 0 — 프로젝트 통합 현황조사  
Target: 기존 Lab/물리 계획/현재 접근 가능 런타임 구분  
Status: **BLOCKED** — 물리 자산의 실제 상태와 승인 ADR 없이 현황 완료 조건(유지·변경·이전·신규 대상의 최종 확정)을 충족하지 못함.

### Completed

- 접근 가능한 M1/M2·정정 M3~M7 문서, 저장소, 현 PC의 VMware·Docker·네트워크를 조사했다.
- 6개 Phase 0 결과물과 `00` 기준선, `01` 현재 아키텍처를 작성했다.

### Runtime Values

- 현 PC `10.10.70.151/25`, 63.8GiB RAM. 로컬 ELK 8.17.3, Wazuh 4.14.7 Docker 컨테이너 실행.
- 물리 LOG `.30.3`/PC2/관리 PC `.10.2`: **NOT VERIFIED**.

### Tests / Evidence

- 읽기 전용 명령: `Get-NetIPConfiguration`, `Get-NetRoute`, `vmrun list`, `vmrun getGuestIPAddress`, `docker ps`, `docker stats --no-stream`, Wazuh Agent 목록, 저장소 파일·설정 검색. 이 보고서의 값은 2026-09-23 순간 관측이다.
- 물리 장비 T01~T20, SPAN 패킷, EVE→Wazuh→ES→Incident 테스트: **미실행**. 객관적 결과 없으므로 `PASS` 없음.

### Issues / Changes / Rollback

- 이슈: `DESIGN-ISSUE-001`, 물리 장비 미접근, ELK 용량, stale M3~M7 주소, Lab/물리 IP 충돌 가능성.
- 운영 변경 없음. 추가된 것은 현황 문서뿐이므로 서비스 롤백 대상 없음.

### Git / Gate / Next Phase

- Branch: `main`; Commit/SHA: 없음(이번 조사에서 커밋하지 않음).
- Gate: `GATE-NET-01` 및 물리망 Phase 0 완료 게이트 = **BLOCKED**.
- 다음 단계: Phase 1에서 장비별 실사·자원/경로·ADR 의사결정. Phase 2 네트워크 검증과 SPAN `tcpdump` 전 IDS 이전·SIEM 연동 착수 금지.
- 현장 인계용 점검 순서·장비별 확인 방법·T01~T20 증거 기준: [지금 완료·확인해야 할 사항](02-OPEN-ITEMS-VERIFICATION.md).
