#!/usr/bin/env python3
"""
Incident case studies data (INC-01, INC-02, INC-03) for Aegis SOC Master Portfolio.
"""
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent.resolve()

INC1_DATA = {
    "title": "제1장. [INC-01] 다단계 지능형 킬체인 표적 침해사고 분석서",
    "id": "INC-10.77.20.20-1787727443",
    "meta_tbl": [
        ("사고 식별자", "INC-10.77.20.20-1787727443", "사고 심각도", "CRITICAL (P1 등급)"),
        ("공격 출발지", "10.77.20.20 (soc-attacker)", "피해 대상 자산", "10.77.30.20:80, 4444 (soc-victim)"),
        ("발생 일시", "2026-08-26 15:56:23 ~ 15:56:35 (지속: 12초)", "최종 사고 판정", "TRUE_POSITIVE (실제 침투 공격)"),
        ("탐지 엔진", "Suricata 8.0.6 (1차) + Snort 3 (2차)", "공식 증적 번호", "EV-E2E-002 (OpenSearch wazuh-alerts)")
    ],
    "timeline": [
        ("1단계 정찰 (Recon): ", "15:56:23 - 공격자(10.77.20.20)가 내부 서버(10.77.30.20:80)로 플래그가 0인 TCP 패킷을 발송하여 열린 포트를 탐색함 (Suricata SID: 9000001 적발, 플로우 ID: 920000000027384)."),
        ("2단계 침투 (Initial Access): ", "15:56:28 - 5초 후 공격자가 웹 애플리케이션(/dvwa)에 UNION SELECT 쿼리를 주입하여 데이터베이스 관리자 계정 정보를 열람함 (Suricata SID: 9010001 적발, 플로우 ID: 920000000027385)."),
        ("3단계 장악 (Execution/C2): ", "15:56:35 - 7초 후 피해 서버에서 공격자의 4444 포트로 거꾸로 나가는 TCP 리버스 셸 세션을 맺고 유닉스 셸(/bin/sh) 프롬프트를 획득함 (Suricata SID: 9030010 적발, 플로우 ID: 920000000027386).")
    ],
    "eve_code": (
        '{\n'
        '  "timestamp": "2026-08-26T15:56:35.129482+0900",\n'
        '  "flow_id": 920000000027386,\n'
        '  "in_iface": "ens224",\n'
        '  "src_ip": "10.77.30.20", "src_port": 4444,\n'
        '  "dest_ip": "10.77.20.20", "dest_port": 4444,\n'
        '  "alert": {\n'
        '    "signature_id": 9030010,\n'
        '    "signature": "SOC-MALWARE: Interactive Reverse Shell Session Established (/bin/sh prompt detected)",\n'
        '    "category": "A Network Trojan was detected",\n'
        '    "severity": 1\n'
        '  },\n'
        '  "payload_printable": "Linux soc-victim 6.8.0-40-generic #40-Ubuntu SMP x86_64\\n$ whoami\\nwww-data\\n$"\n'
        '}'
    ),
    "img": BASE_DIR / "docs" / "ai" / "evidence_annotated" / "evidence_p2_01_multistage_incident.jpg",
    "fig_title": "[그림 2-1] 다단계 킬체인 실측 침해사고(INC-10.77.20.20-1787727443) OpenSearch 색인 증적",
    "fig_desc": "단일 공격자(10.77.20.20)가 12초 만에 감행한 정찰(Rule 100201), 웹 침투(Rule 100202), C2 역방향 셸(Rule 100203)의 실제 도큐먼트가 OpenSearch wazuh-alerts 인덱스에 밀리초 단위로 색인된 원시 쿼리 증적입니다.",
    "meta": {
        "id": "EV-E2E-002",
        "result": "정상 (PASS)",
        "title": "실측 다단계 킬체인 침해사고 전건 색인",
        "target": "OpenSearch wazuh-alerts-4.x-*",
        "details": "Alert ID 1787727385.25830, .27182, .24350 연속 색인 확인, 12초 타임라인 전 주기 보존"
    }
}

INC2_DATA = {
    "title": "제2장. [INC-02] 웹 SQL Injection 및 데이터베이스 정찰 사고 분석서",
    "id": "INC-10.77.20.88-1788772741",
    "desc": "사고 식별자: INC-10.77.20.88-1788772741 (심각도: HIGH / P2 등급)\n공격자(10.77.20.88)가 sqlmap 자동화 취약점 스캐너를 구동하여 웹 게시판 파라미터에 'information_schema.tables' 조회 쿼리를 주입한 사건입니다.",
    "code": (
        'GET /dvwa/vulnerabilities/sqli/?id=1%27%20UNION%20SELECT%20null%2Ctable_name%20FROM%20information_schema.tables-- HTTP/1.1\n'
        'Host: 10.77.30.20\n'
        'User-Agent: sqlmap/1.8.3#stable\n'
        'Response: HTTP/1.1 200 OK (Suricata SID 9010003 Triggered)'
    ),
    "img": BASE_DIR / "docs" / "ai" / "evidence_annotated" / "evidence_p2_02_sqli_incident.jpg",
    "fig_title": "[그림 2-2] sqlmap/1.8.3 DB 스키마 정찰 적발 및 PDO Prepared Statement 패치 증적",
    "fig_desc": "Nginx 접근 로그에 남은 sqlmap 자동화 공격 도구의 information_schema 탐색 흔적과, 취약한 동적 SQL 쿼리를 방어하기 위해 적용된 PDO Prepared Statement 소스코드 git diff 및 IP 차단 증적입니다.",
    "meta": {
        "id": "EV-INC-002",
        "result": "정상 (PASS)",
        "title": "웹 SQLi 정찰 적발 및 시큐어 코딩 패치",
        "target": "soc-victim /var/log/nginx/access.log & low.php",
        "details": "sqlmap User-Agent 및 UNION SELECT 탐지, PDO 파라미터라이징 패치 완료, 2차 유출 0건 방어"
    },
    "conclusion": "조치 및 결론: Suricata와 Snort 보조 엔진이 동시에 탐지하였으며, RAG 가이드에 따라 IP를 차단하고 웹 소스코드에 Prepared Statement 패치를 적용하여 실제 사용자 계정 테이블 유출을 사전에 방어하였습니다."
}

INC3_DATA = {
    "title": "제3장. [INC-03] 코어 게이트웨이 이상 트래픽 및 AI 오차단 방지 분석서",
    "id": "INC-10.77.10.1-1788772755",
    "desc": "사고 식별자: INC-10.77.10.1-1788772755 (심각도: MEDIUM / P3 등급)\n사고 개요: Hyper-V 가상 스위치 헬스체크 주기로 인해 게이트웨이(10.77.10.1)가 내부 서버들로 초당 150건의 ICMP Echo 핑을 일시 발송하여 DoS 임계치 룰(SID 9000003)이 동작하였습니다.",
    "code": (
        '[AI Copilot Tool Call Attempt]: contain_host(target_ip="10.77.10.1")\n'
        '[PolicyValidator Enforcement Result]: SECURITY RULE VIOLATION\n'
        'Target IP 10.77.10.1 is registered in PROTECTED_INFRASTRUCTURE_ASSETS (soc-gateway).\n'
        'Automated network containment is STRICTLY PROHIBITED to prevent self-inflicted DoS.\n'
        'Action status: REJECTED (차단 실행 강제 취소 완료)'
    ),
    "img": BASE_DIR / "docs" / "ai" / "evidence_annotated" / "evidence_p2_03_gateway_guardrail.jpg",
    "fig_title": "[그림 2-3] 코어 게이트웨이(10.77.10.1) 격리 시도 PolicyValidator 100% 강제 차단 증적",
    "fig_desc": "AI 모델이 게이트웨이 헬스체크 트래픽을 공격으로 오인하여 contain_host('10.77.10.1') 도구를 호출했을 때, 독립 정책 검증기가 보호 인프라 위반으로 판단하여 실행을 즉시 강제 거부(REJECTED)한 증적입니다.",
    "meta": {
        "id": "EV-INC-003",
        "result": "정상 (PASS)",
        "title": "보호 인프라 오차단 방지 정책 가드레일 입증",
        "target": "FastAPI /api/ai/tools/execute & PolicyValidator",
        "details": "Target IP 10.77.10.1 격리 시도 원천 차단, 관제망 자해성 DoS(Self-Inflicted DoS) 방지 성공 입증"
    },
    "conclusion": "분석 결론: 만약 AI의 제안대로 게이트웨이를 차단했다면 관제망 전체가 마비되는 대형 장애가 발생했을 것입니다. 하지만 시스템에 내장된 PolicyValidator가 이를 100% 강제 거부함으로써, AI 기술 도입 시 가장 우려되는 '환각에 의한 인프라 오차단'을 완벽하게 방어한 실증 사례입니다. 최종 판정: 정상 이상징후(BENIGN_ANOMALY)."
}
