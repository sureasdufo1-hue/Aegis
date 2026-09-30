# LOG_SOURCE_INVENTORY — 수집 경로와 증명 수준

| 원천 | 현재 관측 경로 | M1/M2 목표 경로 | 판정/미해결 |
|---|---|---|---|
| Suricata | 저장소 `logs/suricata/eve.json` 최종 수정 2026-09-07; 내용은 `10.77.20.20→10.77.30.20` Lab 이벤트. Logstash Beats 5044/TCP 5047 설정 존재 | PC2 SPAN → 센서 EVE → 승인된 관리 경로 → 중앙 수집/ES·Wazuh | CONFIGURED; 물리 패킷/실시간 EVE UNKNOWN |
| Snort | 저장소 `logs/snort/alert_json.txt` 최종 수정 2026-08-24; Logstash TCP 5045 설정 | 승인 PCAP의 오프라인 검증 → 중앙 분석 | CONFIGURED; 물리 PCAP·탐지 UNKNOWN |
| Wazuh 호스트 이벤트 | 로컬 Docker Manager의 `agent_control -l`에는 Manager 000만 있음. Manager `alerts.json` 0줄, 별도 `eve.json` 11줄; 과거 인덱스 문서 존재 | Web/DB/LOG/PC/VM Agent → Manager → Indexer; 선정 경보만 ES | 원격 Agent·실시간 연동 UNKNOWN/미검증 |
| TrusGuard | 현재 `firewall.conf`는 `soc-gateway` nftables `SOC-FW-*` 형식의 5514/UDP 파서 | 장비 로그 → LOG `.30.3` 원문 보존 → TrusGuard 전용 파싱 | 현 파서 재사용 불가 가능성 높음; 실제 샘플 필요 |
| Cisco L2/L3 | 저장소에 물리 장비 수집 증거 없음 | 승인 Syslog/NTP → LOG 원문 → ELK | UNKNOWN |
| Web / DB | 저장소 ELK 파이프라인에 M5 `/var/log/backuplog` 원문 파일 입력 없음 | Web·DB 원문 → LOG `.30.3` rsyslog/RAID → Logstash 파일 입력 → ES | TARGET; 실제 LOG 수신 UNKNOWN |
| Windows/Ubuntu 호스트 | 현재 물리 Agent 등록 증거 없음 | 승인 장비별 Wazuh Agent → Manager | UNKNOWN |
| Wazuh 선정 경보 → ELK | Logstash가 Wazuh Manager `alerts.json` 볼륨과 TCP 5046을 읽도록 설정됨 | 중복·선별·보존 정책 합의 후 ES | CONFIGURED; 현재 생생한 동일 이벤트 추적 미검증 |

Logstash 파이프라인 순간 누적 입력/출력 카운터(방화벽 10, Suricata 20, Snort 10, Wazuh 12)는 파이프라인 동작 흔적일 뿐, 물리 M1/M2 원천이라는 증거가 아니다. 기존 검증 스크립트에는 합성 이벤트 주입이 포함된다. Wazuh Indexer의 과거 문서도 현재 원격 Agent 수신 증거가 아니다.

## 데이터 저장 위치

- 현재 ELK는 이 Windows PC Docker의 `soc-es-data`, `soc-kibana-data`, `soc-logstash-data` 볼륨을 사용한다. Wazuh는 별도 Docker 볼륨 및 로그 경로를 사용한다.
- 현재 `logs/` 파일은 저장소의 과거 Lab 데이터다. M5 목표 `/var/log/backuplog`와 물리 LOG 서버 RAID 상태는 조사하지 못했다.
- 데이터 이전·삭제·중복 저장 정책은 백업·원본 보존·용량·재처리 절차 확인 전 확정하지 않는다.
