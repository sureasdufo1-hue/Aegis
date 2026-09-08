# [부록 E] 용어 정의 및 약어집 (Glossary & Abbreviations)

본 용어집은 **SOC Detection & Monitoring Lab** 보고서 및 룰북 전반에 사용된 기술적 용어, 보안 표준, 아키텍처 및 도구 명칭의 표준 정의를 제공한다.

---

## 1. 표준 보안 및 아키텍처 용어

| 용어 (Term) | 원어 / 약어 | 정의 및 본 프로젝트 내 의미 |
|---|---|---|
| **AF_PACKET** | Address Family Packet | 리눅스 커널 수준의 고속 원시 패킷 수신 메커니즘으로, 중간 버퍼 오버헤드를 최소화하여 고속 트래픽 무손실 수신 지원. |
| **C2** | Command and Control | 공격자가 피해 시스템에 악성코드나 리버스 셸을 설치한 후 원격에서 제어 명령을 하달하고 결과를 탈취하는 통신 채널. |
| **DaC** | Detection as Code | 탐지 룰 및 시그니처를 소프트웨어 소스코드처럼 버전 관리(Git), 자동화 테스트, 지속적 통합(CI/CD) 파이프라인으로 운영하는 기법. |
| **EVE JSON** | Extensible Event Format | Suricata의 기본 구조화 이벤트 출력 포맷으로, 경보, 플로우, DNS, HTTP 등 모든 메타데이터를 표준 JSON으로 기록. |
| **FIM** | File Integrity Monitoring | 시스템 주요 바이너리 및 설정 파일의 해시값 변경, 생성, 삭제를 실시간 모니터링하여 침해 여부를 탐지하는 기술 (Wazuh 내장). |
| **HITL** | Human-in-the-Loop | AI 모델이 판단 및 추천을 수행하더라도 파괴적 명령(네트워크 격리, 프로세스 종료 등) 실행은 인간 분석가의 최종 승인을 요구하는 통제 방식. |
| **MTTD** | Mean Time to Detect | 위협 행위가 발생한 시점부터 보안 관제 시스템에 의해 유의미한 경보로 탐지될 때까지 걸리는 평균 시간. |
| **MTTR** | Mean Time to Respond | 침해사고가 식별된 시점부터 차단, 격리 등 초기 봉쇄 조치가 완료될 때까지 걸리는 평균 시간. |
| **NIST CSF 2.0** | Cybersecurity Framework | NIST가 발표한 차세대 사이버보안 프레임워크로, Govern(거버넌스), Identify, Protect, Detect, Respond, Recover의 6대 핵심 기능으로 구성. |
| **NIST SP 800-61 Rev.3**| Incident Handling Guide | 컴퓨터 보안 침해사고 대응 지침의 2025 최신 개정판으로, 지속적 모니터링과 협업 기반 인시던트 대응 프레임워크 제시. |
| **Promiscuous Mode** | 무차별 모드 | 네트워크 인터페이스 카드가 자신의 MAC 주소가 아닌 목적지로 향하는 모든 패킷을 폐기하지 않고 캡처하여 상위 IDS 엔진에 전달하는 모드. |
| **RAG** | Retrieval-Augmented Generation | 거대언어모델(LLM)이 답변을 생성할 때 사전에 구축된 신뢰성 높은 내부 문서(플레이북) 벡터 데이터베이스에서 관련 정보를 검색하여 컨텍스트로 제공하는 기술. |
| **SoD** | Segregation of Duties | 직무 분리 원칙으로, 관제 모니터링(L1), 정밀 분석(L2), 대응 승인(L3/팀장), 룰 엔지니어링 간 권한과 역할을 엄격히 분리하여 내부 통제 강화. |

---

## 2. 프로젝트 특화 구성요소

| 구성요소 | 설명 |
|---|---|
| **soc-attacker** | 모의 공격 트래픽 발송 가상머신 (`10.77.20.20`, ZONE-ATTACK). |
| **soc-gateway** | 3개 서브넷 간 라우팅 및 패킷 필터링(nftables)을 수행하는 경계 방화벽 (`10.77.10.1`, `10.77.20.1`, `10.77.30.1`). |
| **soc-victim** | 표적 애플리케이션(DVWA 등) 및 서비스가 구동되는 내부망 희생자 가상머신 (`10.77.30.20`, ZONE-VICTIM). |
| **soc-sensor** | 무차별 캡처 인터페이스를 통해 미러링 트래픽을 수신하고 Suricata, Snort, Wazuh Agent를 구동하는 전용 센서 (`10.77.10.20`, ZONE-MGMT). |
| **PolicyValidator** | AI Copilot이 비인가 IP를 차단하거나 핵심 인프라를 실수로 격리하지 못하도록 코드 레벨에서 강제 통제하는 가드레일 모듈. |
| **correlation_engine** | 30분 슬라이딩 윈도우 기반으로 단절된 Alert를 MITRE 킬체인 단계별로 자동 병합하여 상위 Incident로 승격시키는 상관분석기. |
