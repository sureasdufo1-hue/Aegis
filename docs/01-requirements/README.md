# 📋 01. 보안관제 포트폴리오 프로젝트 요구사항 정의서 (v1.0)

> **원본 문서**: [`보안관제_포트폴리오_프로젝트_요구사항_정의서_v1.0.pdf`](./보안관제_포트폴리오_프로젝트_요구사항_정의서_v1.0.pdf)  
> **문서 버전**: v1.0 (38 Pages)  
> **기준 일자**: 2026-08-24  
> **프로젝트 명**: SOC Detection & Monitoring Lab  

---

## 1. 프로젝트 목적 및 배경 (Project Objective)

본 프로젝트는 단순한 보안 툴 설치나 일회성 실습을 넘어, **실제 기업 보안관제센터(SOC) 환경과 동일한 엔드투엔드(End-to-End) 위협 탐지, 로그 수집, 킬체인 분석, 오탐/미탐 튜닝, 침해사고 대응 및 포트폴리오 입증 체계**를 구축하는 것을 목표로 합니다.

```
[ 위협 트래픽 발생 ] ──> [ 가상 네트워크 전송 ] ──> [ 포트 미러링 수집 ]
                                                            │
                                                            ▼
[ 침해사고 보고서 & 증적 ] <── [ 오탐/미탐 튜닝 ] <── [ 듀얼 IDS 탐지 ]
                                                            │
                                                            ▼
                                                   [ SIEM 상관분석 ]
```

---

## 2. 핵심 요구사항 목록 (Core Requirements)

### 2.1 네트워크 및 인프라 요구사항 (REQ-NET)
- **REQ-NET-01 (망 분리)**: 공격망(`ZONE-ATTACK`, `10.77.20.0/24`), 희생망(`ZONE-VICTIM`, `10.77.30.0/24`), 관리망(`ZONE-MGMT`, `10.77.10.0/24`)으로 엄격히 분리된 3대 영역 구성.
- **REQ-NET-02 (패킷 미러링)**: Hyper-V Port Mirroring을 통해 희생 서버(`soc-victim`) 인바운드/아웃바운드 전체 트래픽을 무손실로 센서(`soc-sensor`) 모니터링 NIC에 복제.
- **REQ-NET-03 (무IP 센서 NIC)**: 패킷 캡처용 모니터링 인터페이스는 L3 IP를 할당하지 않는 패시브 모드로 동작하여 센서 자체 노출 방지.

### 2.2 침입탐지(IDS/IPS) 요구사항 (REQ-IDS)
- **REQ-IDS-01 (Primary IDS - Suricata 8.x)**: AF_PACKET 멀티스레드 기반 실시간 패킷 검사 및 EVE JSON 텔레메트리 출력.
- **REQ-IDS-02 (Secondary IDS - Snort 3.x)**: 동일 공격 트래픽/PCAP에 대한 교차 검증 및 룰 문법 비교 분석.
- **REQ-IDS-03 (시그니처 룰셋 엔지니어링)**: 웹 공격(SQLi, XSS, RCE, Log4j), 정찰(Nmap 스텔스 스캔), 무차별 대입, C2 비콘, DNS 터널링 유출을 탐지하는 전용 커스텀 룰셋 구축.

### 2.3 통합 보안 관제(SIEM) 및 분석 요구사항 (REQ-SIEM & REQ-SOC)
- **REQ-SIEM-01 (Wazuh 4.x 연동)**: Suricata `eve.json` 로그를 Wazuh Agent ➔ Manager ➔ Indexer ➔ Dashboard 파이프라인으로 실시간 수집 및 인덱싱.
- **REQ-SOC-01 (트라이아지 및 킬체인 분석)**: 원시 EVE 로그, PCAP, 탐지 룰을 교차 분석하여 `TRUE_POSITIVE`, `FALSE_POSITIVE`, `BENIGN` 판정.
- **REQ-SOC-02 (탐지 룰 튜닝)**: 정상 업무 트래픽에 의한 오탐을 제거하고, 우회 공격 트래픽에 대한 탐지력을 보존하는 Before/After 검증 루프 구현.
- **REQ-SOC-03 (증적 기반 산출물)**: 각 단계별 명령 결과, EVE 로그, 해시 검증된 PCAP, 스크린샷을 메타데이터와 함께 체계적으로 기록.
