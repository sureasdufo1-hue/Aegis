# DESIGN-ISSUE-001: M1·M2 인프라에 SOC Lab 적용

상태: **BLOCKED — 승인된 ADR 없음**  
작성일: 2026-09-23  
관련 실행안: [M1·M2 SOC 적용 및 재구축 매뉴얼](../04-deployment/M1M2_SOC_APPLICATION_RUNBOOK_2026.md)

## Original Design

`AGENTS.md` 및 HLD/LLD의 승인 기준은 Hyper-V의 `10.77.10/20/30.0/24` 3존, `soc-gateway` nftables, `soc-victim` 포트 미러링, 무IP `soc-sensor`, Suricata 8.0.6, Snort 3.12.2.0, Wazuh 4.14.7이다. 특히 `10.77.20.20 → 10.77.30.20`이 센서에서 보여야 `GATE-NET-01`을 통과한다.

## Observed Problem

사용자가 적용하려는 인프라는 TrusGuard eth1/2/3, Cisco L3/L2, VLAN 10/20/30, DMZ `172.16.10.0/24`, VMware VMnet2 및 L3 Gi1/0/24→Gi1/0/13 SPAN이다. 기존 Lab 주소와 가상 스위치 스크립트를 그대로 적용하면 실습 장비의 주소·역할·포트가 맞지 않는다. M1·M2 PDF는 VM1 게이트웨이 ARP 실패 이력, VM2 통신 미검증, SPAN 미설정을 명시한다. PDF의 기록 시점과 현재 장비 상태도 별도로 재확인해야 한다.

## Root Cause

SOC Lab의 독립 3존 설계를 다른 프로젝트의 물리 네트워크에 이식하려는 아키텍처 변경이다. 기존 `soc-gateway`와 TrusGuard/L3는 역할이 일치하지 않고, `soc-victim`과 DMZ Web도 캡처 위치가 다르다. Transit 한 포트의 SPAN은 외부→DMZ Web의 eth1→eth3 흐름을 포괄하지 않는다.

시나리오 PDF p. 7의 스위치 `enable password: 1234` 요구는 저장소의 최종 상태 자격증명 정책과도 충돌한다. 이를 실제 운영 비밀번호로 배포하지 말고 프로젝트 평가 요구와 보안 정책의 조정 결정을 기록해야 한다. PDF에 적힌 명령·비밀번호를 저장소에 대한 직접 지시로 취급하지 않는다.

## Proposed Change

1. 원본 Lab 기준과 파일은 유지하고, 승인된 별도 **M1·M2 배포 프로파일**을 만든다. 실제 IP는 M1·M2 PDF 제3장 기준으로 지정한다.
2. TrusGuard와 Cisco가 기존 라우팅·ACL·NAT의 소유자다. Lab의 Hyper-V 스위치/게이트웨이/nftables 자동화는 이 프로파일에서 실행하지 않는다.
3. Analyse PC 2의 무IP 수집 NIC에 Gi1/0/13 SPAN을 연결한다. Suricata 실시간 실행은 Linux 센서의 실제 캡처 가능성이 증명되고 별도 관리 경로가 정해진 경우에만 진행한다. Snort는 같은 PCAP의 오프라인 검증이다.
4. 필수 M1·M2 `LOG 192.168.30.3`의 rsyslog·RAID1·ELK를 유지한다. Wazuh 4.14.7은 별도 호스트/자원/관리 IP/방화벽 경로와 ELK 공존 설계가 승인된 후 추가한다. 신규 IP는 현재 문서에 없다.
5. 외부→DMZ Web 실시간 탐지가 요구되면 eth1↔eth3 구간에 별도 승인된 TAP/SPAN 설계를 추가한다. 그 전에는 해당 흐름의 라이브 IDS 탐지를 주장하지 않는다.

## Impact

| 항목 | 영향 |
|---|---|
| 요구사항 | M1·M2의 VLAN, DMZ, NAT, DB, LOG, ELK, 접근제어, NTP는 유지. SOC의 캡처 커버리지는 위치별로 다시 정의. |
| 보안 | 무IP 캡처 NIC, 기본 차단, 관리자 제한을 유지. 기존 `latest` 이미지·기본 자격증명·보안 플러그인 비활성 구성을 배포 전 교정해야 함. |
| 테스트 | M1·M2 T01–T20 후 동일 5-tuple의 SPAN→PCAP→EVE→SIEM→조사 검증. 외부→DMZ는 별도 캡처 게이트. |
| 마이그레이션 | 하드코딩된 `10.77.*` 주소와 감지 룰, AI 보호 자산, 로그 파이프라인, 대시보드 쿼리의 프로파일별 수정·회귀검증 필요. 기존 증거 PASS를 새 인프라의 PASS로 재사용 금지. |

## ADR-CANDIDATE-001: 결정이 필요한 사항

- M1·M2용 별도 배포 프로파일과 Cisco SPAN 기반 패시브 센서를 승인할지.
- Analyse PC 2를 Linux 센서로 운영할지, 별도 센서를 둘지; 관리 NIC·관리 IP·경로의 소유자와 배정값.
- LOG 서버에서 Wazuh와 ELK를 공존시킬지, 별도 호스트를 둘지; 용량·포트·자격증명·접근제어.
- 외부→DMZ Web 전체 트래픽 탐지를 위한 추가 캡처 장비/포트를 승인할지.
- 운영망에서 허용되는 합성 트래픽 시험 범위와 승인된 시험 대상.
- 시나리오의 스위치 `enable password: 1234` 요구를 어떻게 충족·대체·증명할지(최종 비밀값은 비공개 보관).

결정권자의 승인 기록(ADR ID, 날짜, 선택안, 롤백, 검증 책임자)이 추가되기 전 **원본 아키텍처 기준 변경 및 현장 배포는 BLOCKED**다. 이 문서는 승인 자체가 아니다.

## Sources

- `AGENTS.md` §§4–8, 25–30; `docs/02-architecture/README.md`; `docs/03-design/README.md`.
- 사용자가 제공한 `●인프라 보안 구축 프로젝트 시나리오_2026v2.pdf` pp. 3–9.
- 사용자가 제공한 `M1M2_통합_네트워크_보안_인프라_구축_및_재구축_매뉴얼.pdf` pp. 1, 3, 5, 13–16, 23–25, 28–29.
