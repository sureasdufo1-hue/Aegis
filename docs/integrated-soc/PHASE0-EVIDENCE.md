# Phase 0 읽기 전용 관측 증거

관측 시점: 2026-09-23 약 11:09 KST. 명령은 현 Windows PC `DESKTOP-QIFELML`에서 실행했다. 출력은 관련 항목만 발췌했으며 운영 설정을 변경하지 않았다. 이 기록은 물리 M1/M2 장비에 접속한 증거가 아니다.

| 증거 ID | 명령/자료 | 관측값 | 한계 |
|---|---|---|---|
| EV-HOST-P0-001 | `Get-NetIPConfiguration`, `Get-NetAdapter` | 이더넷 `10.10.70.151/25`, GW `.129`, 1Gbps Up; 이더넷 2 Disabled; VMnet10 `10.77.10.1/24`, VMnet8 `192.168.111.1/24`, VMnet1 `192.168.135.1/24` | 현 PC만의 IP/어댑터 상태 |
| EV-HOST-P0-002 | `docker ps --format ...` | `soc-elasticsearch`, `soc-kibana`, `soc-logstash` 8.17.3 healthy; `soc-wazuh-manager`, `soc-wazuh-indexer`, `soc-wazuh-dashboard` 4.14.7 Up | 컨테이너 실행만 증명; 물리 LOG 배치/데이터 품질은 아님 |
| EV-HOST-P0-003 | `docker stats --no-stream` | ES 5.032GiB/6GiB, Kibana 1.72GiB/2GiB, Logstash 2.607GiB/3GiB; 합계 9.359GiB | 단일 순간값; 피크/추세 아님 |
| EV-WAZUH-P0-001 | `docker exec soc-wazuh-manager /var/ossec/bin/agent_control -l` | `ID: 000`, 로컬 Manager 한 개만 목록에 있음 | 다른 Wazuh 설치/물리 호스트는 조사하지 못함 |
| EV-WAZUH-P0-002 | Manager 로그 줄 수 조회 | `/var/ossec/logs/alerts/alerts.json`: 0줄, `/var/ossec/logs/eve.json`: 11줄 | 줄 수만 확인; 11줄의 실제 원천/탐지 정상성은 증명하지 않음 |
| EV-SURI-P0-001 | `Get-Item logs/suricata/eve.json`, `logs/snort/alert_json.txt` | 최종 수정 2026-09-07 20:10:57 KST / 2026-08-24 16:16:35 KST | 과거 저장소 파일; 물리 실시간 입력 아님 |
| EV-CONFIG-P0-001 | `rg` 및 Compose 파일 읽기 | Suricata/Snort `HOME_NET`은 `10.77.30.0/24`; 루트 Docker IDS는 `latest`; ELK는 8.17.3 핀 | 설정 존재만 증명; IDS 실행 상태 아님 |
| EV-UI-P0-001 | `Get-NetTCPConnection -LocalPort 8501 -State Listen` | 현 PC에 결과 없음 | 다른 VM/서버의 FastAPI 실행은 배제 못함 |
| EV-VM-P0-001 | `vmrun list`, `vmrun getGuestIPAddress`, VMX 파일 읽기(같은 날 이전 조회) | 5개 `soc-*` VMware VM 실행; sensor `.10.20`, gateway `192.168.111.140`, victim `10.77.30.100`, siem `.10.30`; 각 VMX 2vCPU/4GB | VMware Tools 대표 주소; NIC 전체/서비스/패킷 증거 아님. 이번 최종 재조회에서는 `vmrun`이 PATH에서 발견되지 않아 이전 관측값을 유지한다. |

물리 M1/M2 자산에 대한 증거 ID는 **아직 없음**. T01~T20, SPAN·PCAP, LOG 원문, Web/DB, Wazuh Agent, ES 실데이터, Incident 결과에 `PASS`를 부여하지 않는다.
