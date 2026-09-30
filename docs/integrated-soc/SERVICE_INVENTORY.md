# SERVICE_INVENTORY — 현재 서비스와 설정

관측: 2026-09-23 KST, 현 Windows PC와 로컬 Docker에 한정. `running`은 E2E `PASS`가 아니다.

| 구성요소 | 현재 위치·버전·상태 | 대상/차이 |
|---|---|---|
| Docker Desktop | 현 PC, 29.8.0 동작 | M1/M2 LOG 서버의 Docker 여부는 미확인 |
| Elasticsearch / Logstash / Kibana | 현 PC Docker, 각 `8.17.3`, 컨테이너 healthy | M6 정정 계획은 LOG `.30.3` 동일 호스트, 8.15.x 제안. 사용자 첨부의 8.19.20은 과거 기록일 뿐. 버전 선택/호환성/승인 필요 |
| Wazuh Manager / Indexer / Dashboard | 현 PC Docker, `4.14.7`, running; healthcheck 판정 없음 | 실제 물리망 호스트/Agent/경로 미확정 |
| Suricata / Snort | 저장소 설정·규칙은 존재, 현재 Docker 실행 목록에는 없음; VM 게스트 실행 상태 미확인 | PC2 수집/PCAP 검증 전 이전 금지 |
| Filebeat / Elastic Agent | 현 PC Windows 서비스·Docker 컨테이너·저장소 구성에서 확인되지 않음 | VM/물리 서버 설치 여부는 UNKNOWN; 설치 전 기존 경로 조사 |
| FastAPI SOC Console | `dashboard/app.py`, `dashboard/elk_client.py` 코드 존재; 현 PC 8501 리스너 없음 | 배치 호스트 미확정; 기본값은 로컬 로그/mock LLM, ES localhost 9201 참조 |
| Correlation Engine | `analyzer/detection/correlation_engine.py` 코드·테스트 존재 | 10.77.* 보호 자산/이벤트 스키마를 물리 프로파일로 분리 필요 |
| Ollama | 실행 파일 검색됨; 현 PC 프로세스/서비스 실행 증거 없음 | 선택 구성; 통합 필수 게이트 아님 |

## 현재 네트워크 노출·용량 주의

- ELK: ES `127.0.0.1:9201`, Kibana `127.0.0.1:5602`, Logstash `0.0.0.0:5044–5047/TCP`와 `5514/UDP`.
- Wazuh: Dashboard `0.0.0.0:443,5601`, Manager `0.0.0.0:1514,1515`; API `127.0.0.1:55000`, Indexer `127.0.0.1:9200`. 이는 현재 바인딩 관측이며, 접근 가능성/방화벽 보호가 검증됐다는 뜻은 아니다.
- Docker 통계 순간값: ES 약 5.03GiB, Kibana 1.72GiB, Logstash 2.61GiB(합계 약 9.36GiB). Compose 메모리 상한 합계 11GiB. M5 제안 8GB LOG 서버로 그대로 이전할 수 없다는 용량 경고이며 장기 피크/디스크 IOPS 측정은 아직 없다.
- ELK Compose에는 자격증명 fallback 값이 코드에 포함되어 있다. **값을 문서에 재기록하지 않는다.** Phase 1 보안 검토에서 비밀 관리·교체·접근 범위를 확인한다.
- 현재 `docker-compose.yml`의 IDS `latest` 태그는 승인 핀 버전 정책과 충돌한다. 현 실행 중 IDS가 있다는 증거는 아니다.
