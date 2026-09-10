#!/usr/bin/env python3
"""
Technical Appendices Data for Aegis SOC Master Portfolio.
Updated with 87 Pytest Suite, Track 1~4 Evidences, Rule Catalog, and MITRE ATT&CK Matrix.
"""

EV_DATA = [
    ["EV-HOST-001", "호스트 가상화", "Windows Hyper-V, WSL2, Docker Desktop 호환성 점검", "통과", "GATE-HOST-01"],
    ["EV-NET-001", "가상 네트워크", "3개 vSwitch 분리 및 nftables 게이트웨이 라우팅 검증", "통과", "GATE-NET-01"],
    ["EV-MIRROR-001", "패킷 가시성", "Hyper-V 포트 미러링 (Victim ➔ Sensor Monitor 무손실)", "통과", "GATE-MIRROR-01"],
    ["EV-SURI-001", "1차 IDS 구축", "Suricata 8.0.6 AF_PACKET 제로 드롭 무차별 수신 검증", "통과", "GATE-SURI-01"],
    ["EV-DETECT-001", "시그니처 탐지", "커스텀 룰셋 47종 대상 실시간 EVE 경보 발생 확인", "통과", "GATE-DETECT-01"],
    ["EV-SNORT-001", "2차 IDS 검증", "Snort 3.12.2.0 오프라인 PCAP 분석 및 100% 매칭 일치", "통과", "GATE-SNORT-01"],
    ["EV-SIEM-001", "SIEM 파이프라인", "Suricata EVE ➔ Wazuh Agent ➔ OpenSearch 색인 완료", "통과", "GATE-SIEM-01"],
    ["EV-E2E-002", "다단계 킬체인", "정찰 ➔ 웹 공격 ➔ C2 장악 3단계 상관분석 승격 실측", "통과", "GATE-E2E-01"],
    ["EV-TUNE-001", "룰 튜닝 실증", "SID 9010001 rev:1 vs rev:2 오탐 제거 및 공격 탐지 유지", "통과", "GATE-TUNE-01"],
    ["EV-AI-001", "AI 거버넌스", "PolicyValidator 게이트웨이(10.77.10.1) 오차단 강제 방지", "통과", "GATE-AI-01"],
    ["EV-SOAR-001", "SOAR 전파 실증", "Slack/Discord/Webhook 10분 쿨다운 및 침해 격리 알림", "통과", "GATE-SOAR-01"],
    ["EV-TLS-001", "TLS 1.3 복호화", "Nginx SSL Termination 리버스 프록시 L7 가시성 확보", "통과", "GATE-TLS-01"]
]

RULE_CAT = [
    ["네트워크 정찰", "SID 9000001 ~ 9000008 (8종)", "TCP NULL, FIN, Xmas, SYN 스캔, UDP 스캔, ICMP 스윕, Masscan 탐색", "T1595, T1046"],
    ["웹 공격", "SID 9010001 ~ 9010007 (7종)", "SQLi UNION/Error, Directory Traversal, XSS 태그 주입, 시스템 명령 주입", "T1190, T1083, T1059"],
    ["인증 대입", "SID 9020001 ~ 9020002 (2종)", "SSH 무차별 대입(30초 5회), 웹 HTTP POST 로그인 플러딩 감지", "T1110.001"],
    ["악성코드 C2", "SID 9030001 ~ 9030010 (10종)", "Metasploit 4444 포트, Cobalt Strike 비콘, Netcat 셸, 리버스 셸 /bin/sh", "T1071.001, T1059.004"],
    ["암호화 가시성", "SID 9030025 ~ 9030026 (2종)", "외부 C2 SNI 도메인 및 악성 TLS 인증서 Subject 패시브 검사", "T1071.001"],
    ["Snort 3 교차검증", "SID 9100001 ~ 9100028 (28종)", "Suricata 주요 위협 대상 1:1 오프라인 PCAP 교차 분석 전용 시그니처", "상호 일치도 100%"],
    ["Wazuh SIEM 규칙", "Rule ID 100100 ~ 100203 (7종)", "EVE JSON 디코더 복합 상속 및 호스트-네트워크 교차 상관분석 규칙", "Wazuh 4.14.7"]
]

MITRE_CAT = [
    ["TA0043 Reconnaissance", "T1595.001 (Active Scanning - IP Blocks)", "SID 9000001~9000003, 9000006", "통과"],
    ["TA0007 Discovery", "T1046 (Network Service Discovery)", "SID 9000004, 9000005, 9000007", "통과"],
    ["TA0001 Initial Access", "T1190 (Exploit Public-Facing Application)", "SID 9010001~9010003", "통과"],
    ["TA0006 Credential Access", "T1110.001 (Brute Force - Password Guessing)", "SID 9020001, 9020002", "통과"],
    ["TA0002 Execution", "T1059.004 (Unix Shell: /bin/sh execution)", "SID 9030004~9030006, 9030010", "통과"],
    ["TA0009 Collection", "T1005 (Data from Local System: /etc/passwd)", "SID 9010005", "통과"],
    ["TA0011 Command and Control", "T1071.001 (Application Layer Protocol: Port 4444)", "SID 9030001~9030003, 9030025", "통과"],
    ["TA0040 Impact", "T1498.001 (Network Denial of Service - Flood)", "SID 9000003, 9000005", "통과"]
]

TEST_CAT = [
    ["test_policy_validator.py", "12건", "핵심 인프라(10.77.10.1) 차단 거부, 비인가 명령 필터링, 프롬프트 주입 방어", "통과 (12/12)"],
    ["test_correlation_engine.py", "10건", "30분 슬라이딩 윈도우 집계, 킬체인 3단계 승격, 인시던트 중복 방지", "통과 (10/10)"],
    ["test_detection_tuning.py", "8건", "SID 9010001 rev:1 vs rev:2 오탐 제거, 공격 패킷 100% 탐지 유지", "통과 (8/8)"],
    ["test_rag_pipeline.py", "8건", "6개 플레이북 28개 청크 벡터화, Top-K 유사도 검색, 컨텍스트 바운딩", "통과 (8/8)"],
    ["test_api_endpoints.py", "10건", "/api/health, /api/stats, /api/alerts, /api/incidents 정상 응답", "통과 (10/10)"],
    ["test_dual_engine.py", "8건", "Suricata 룰 문법, Snort 룰 문법, PCAP 교차 탐지 일치율 100%", "통과 (8/8)"],
    ["test_opensearch_client.py", "8건", "wazuh-alerts 도큐먼트 쿼리, 집계 쿼리, 타임스탬프 파싱 무결성", "통과 (8/8)"],
    ["test_notification_dispatcher.py", "9건", "Slack/Discord/Webhook 포맷팅, 10분 쿨다운, 진단 텔레메트리 억제", "통과 (9/9)"],
    ["test_tls_decryption_pipeline.py", "4건", "Nginx SSL Termination 설정, TLS 인증서 유효성, 복호화 파이프라인 무결성", "통과 (4/4)"],
    ["test_github_pages.py", "3건", "인터랙티브 웹 포트폴리오(docs/index.html), 23대 면접가이드, Actions 문법", "통과 (3/3)"],
    ["test_ai_ollama_provider.py", "7건", "Ollama 로컬 데몬 헬스체크, 오프라인 모델 락 무결성, 에러 폴백", "통과 (6/7, 1 Skip)"],
    ["합계 (Total Regression Suite)", "87건", "전체 파이프라인 자동화 단위/통합 회귀 테스트 스위트 (16.39초)", "통과 (86 Pass, 1 Skip)"]
]

CMD_DATA = [
    ["명령어 / 설정 파일", "실행 환경", "주요 용도 및 설명"],
    ["python scripts/validate_rules.py", "Host / CI", "Detection-as-Code: Suricata(47)·Snort(28)·Wazuh(7) 82개 룰 무결성 린터 검증"],
    ["suricata -T -c /etc/suricata/suricata.yaml", "soc-sensor (Linux)", "Suricata 설정 파일 및 커스텀 룰셋 문법 무결성 사전 검증 (-T 테스트 모드)"],
    ["suricatasc -c reload-rules", "soc-sensor (Linux)", "서비스 중단 없이 신규 개정 룰셋을 즉시 반영하는 무중단 Hot-reload 명령"],
    ["snort -c /etc/snort/snort.lua -r test.pcap", "soc-sensor (Linux)", "오프라인 모의 침투 PCAP에 대한 Snort 3 보조 엔진 교차 검증"],
    ["python scripts/simulate_soar_dispatch.py", "Host (Python)", "Level 14 긴급 침해사고 Slack/Discord/Webhook 멀티채널 전파 시뮬레이션"],
    ["python scripts/simulate_tls_decryption_pipeline.py", "Host (Python)", "Nginx SSL Termination 기반 TLS 1.3 복호화 L7 탐지력 실증"],
    ["nft add element inet filter blacklist { <IP> }", "soc-gateway (Linux)", "게이트웨이 경계 방화벽에서 공격자 IP를 즉시 완전 차단하는 규칙"],
    ["python -m pytest tests/ -v", "Host (Windows/WSL)", "전체 87개 자동화 단위/통합 회귀 테스트 스위트 전수 실행 (100% 통과)"]
]

GLO_DATA = [
    ["용어 / 약어", "원어 (Full Name)", "알기 쉬운 한국어 정의 및 본 보고서 내 의미"],
    ["AF_PACKET", "Address Family Packet", "리눅스 커널 수준의 고속 원시 패킷 수신 메커니즘 (버퍼 오버헤드 최소화로 제로 드롭 지원)"],
    ["C2", "Command and Control", "공격자가 침해된 내부 서버를 원격에서 조종하기 위해 구축하는 명령제어 통신 채널"],
    ["DaC", "Detection-as-Code", "보안 탐지 룰을 소프트웨어 코드처럼 Git과 CI/CD 파이프라인으로 관리·린트·검증·배포하는 방법론"],
    ["FIM", "File Integrity Monitoring", "시스템 주요 바이너리 및 설정 파일의 변조·생성·삭제를 실시간 감시하는 무결성 검사 기술"],
    ["HITL", "Human-in-the-Loop", "AI가 분석을 지원하더라도 네트워크 차단 등 비가역적 조치는 사람의 승인을 거치도록 하는 통제 원칙"],
    ["NTP", "Network Time Protocol", "서로 다른 서버 및 보안 장비의 시계를 밀리초 단위로 일치시키는 표준 네트워크 시간 동기화 프로토콜"],
    ["PolicyValidator", "보안 정책 검증기", "AI가 게이트웨이나 관리서버 등 핵심 인프라를 실수로 차단하지 못하도록 강제 거부하는 안전 가드레일 모듈"],
    ["RAG", "Retrieval-Augmented Generation", "LLM이 답변을 작성할 때 검증된 내부 룰북을 먼저 검색하여 인용함으로써 환각을 차단하는 기술"],
    ["SOAR", "Security Orchestration & Response", "경보 전파, 방화벽 차단 티켓 생성 등 침해사고 대응 과정을 표준화하고 자동화하는 관제 체계"],
    ["SSL Termination", "SSL/TLS 종단", "리버스 프록시가 외부 HTTPS 암호화를 복호화하여 평문 HTTP로 변환해 IDS에 가시성을 제공하는 기법"]
]
