"""
Deterministic Korean Security Terminology Dictionary & Localization Mappings.
Provides consistent, professional translations for UI labels, alert categories,
severities, MITRE ATT&CK techniques, and containment policy verdicts.
Does not alter or mutate raw evidence.
"""

# 1. Severity Translations (위험도 매핑)
SEVERITY_MAP = {
    "CRITICAL": {
        "ko": "심각",
        "en": "Critical",
        "desc": "즉각적인 격리 및 차단이 필요한 긴급 침해 사고 (RCE, C2, 악성코드 역방향 셸 등)",
        "badge_class": "bg-red-500/20 text-red-400 border-red-500/30",
    },
    "HIGH": {
        "ko": "높음",
        "en": "High",
        "desc": "공격 시도 및 활성 취약점 악용 시도 (SQL 인젝션, 무차별 대입 등)",
        "badge_class": "bg-orange-500/20 text-orange-400 border-orange-500/30",
    },
    "MEDIUM": {
        "ko": "보통",
        "en": "Medium",
        "desc": "정찰 행위, 비정상 스캔 및 의심스러운 트래픽 활동",
        "badge_class": "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
    },
    "LOW": {
        "ko": "낮음",
        "en": "Low",
        "desc": "보안 정책 위반 가능성 및 비인가 프로토콜 접근",
        "badge_class": "bg-blue-500/20 text-blue-400 border-blue-500/30",
    },
    "INFORMATIONAL": {
        "ko": "정보",
        "en": "Informational",
        "desc": "단순 감사 로그 및 시스템 정상 이벤트",
        "badge_class": "bg-slate-700 text-slate-300 border-slate-600",
    },
}

# 2. Engine Translations (탐지 엔진 매핑)
ENGINE_MAP = {
    "SURICATA": {
        "ko": "Suricata 8.x 침입탐지시스템",
        "short": "Suricata",
        "desc": "AF_PACKET 고속 미러링 실시간 네트워크 시그니처 엔진",
    },
    "SNORT": {
        "ko": "Snort 3 침입탐지시스템",
        "short": "Snort 3",
        "desc": "오프라인/2차 검증 및 규칙 비교 엔진",
    },
    "WAZUH": {
        "ko": "Wazuh SIEM 통합 로그 분석",
        "short": "Wazuh",
        "desc": "호스트 에이전트 및 중앙 오픈서치 인덱서",
    },
}

# 3. Killchain & Attack Stage Translations (공격 단계 매핑)
ATTACK_STAGE_MAP = {
    "1. Reconnaissance": {
        "ko": "1단계: 정보 수집 및 정찰",
        "en": "1. Reconnaissance",
        "short": "정찰 (Recon)",
        "meaning": "공격자가 대상 시스템의 열린 포트, 서비스 및 운영체제 정보를 수집하는 단계",
    },
    "2. Initial Access / Exploitation": {
        "ko": "2단계: 초기 침투 및 취약점 악용",
        "en": "2. Initial Access / Exploitation",
        "short": "초기 침투 (Initial Access)",
        "meaning": "공개 서비스 취약점(SQLi, XSS 등)이나 무차별 대입을 통해 내부 진입을 시도하는 단계",
    },
    "3. Command & Control / Execution": {
        "ko": "3단계: 명령제어(C2) 및 악성코드 실행",
        "en": "3. Command & Control / Execution",
        "short": "명령제어 (C2 / Execution)",
        "meaning": "공격자가 타깃 호스트에 리버스 셸을 수립하거나 원격 제어 통신을 지속하는 단계",
    },
    "4. Exfiltration": {
        "ko": "4단계: 데이터 유출",
        "en": "4. Exfiltration",
        "short": "정보 유출 (Exfiltration)",
        "meaning": "내부 기밀 정보나 자산을 외부 공격자 서버로 반출하는 단계",
    },
    "Generic Security Activity": {
        "ko": "일반 보안 이벤트",
        "en": "Generic Security Activity",
        "short": "일반 이벤트",
        "meaning": "특정 공격 단계로 분류되지 않은 단발성 보안 경보",
    },
}

# 4. Common Alert Signatures & Meanings (주요 경보 시그니처 사전)
SIGNATURE_MAP = {
    "SOC-SCAN: Nmap Stealth NULL Scan Detected (Zero Flags)": {
        "ko_title": "Nmap 스텔스 NULL 포트 스캔 탐지",
        "category_ko": "정보 수집 시도 (스캔)",
        "explanation": "TCP 플래그가 전혀 설정되지 않은 비정상 패킷을 전송하여 방화벽을 우회하고 열린 포트를 탐색하는 정찰 기법입니다.",
        "investigation_guide": "출발지 IP가 최근 다른 포트나 호스트를 지속적으로 스캔했는지 확인하고 웹 서버 접근 여부를 추적하십시오.",
    },
    "SOC-ATTACK: Web SQL Injection - UNION SELECT Pattern Detected": {
        "ko_title": "웹 애플리케이션 SQL 인젝션 공격 시도 탐지",
        "category_ko": "웹 애플리케이션 공격",
        "explanation": "HTTP 파라미터에 'UNION SELECT' 구문을 삽입하여 데이터베이스 내부 정보를 비인가 조회하려는 공격입니다.",
        "investigation_guide": "웹 서버의 응답 코드(200 OK vs 500/403)와 응답 데이터 크기를 확인하여 실제 데이터베이스 질의 성공 여부를 검증하십시오.",
    },
    "SOC-ATTACK: SSH Brute Force Attack - High Frequency Connection Threshold Exceeded": {
        "ko_title": "SSH 계정 무차별 대입 공격 (Brute Force) 탐지",
        "category_ko": "관리자 권한 획득 시도",
        "explanation": "단시간 내에 비정상적으로 높은 빈도로 SSH 접속을 시도하여 유효한 계정 자격증명을 탈취하려는 공격입니다.",
        "investigation_guide": "대상 호스트의 `/var/log/auth.log`를 검토하여 'Accepted password' 기록이 존재하는지, 성공한 로그인이 있는지 점검하십시오.",
    },
    "SOC-MALWARE: Interactive Reverse Shell Session Established (/bin/sh prompt detected)": {
        "ko_title": "대화형 리버스 셸 세션 수립 의심 (/bin/sh 프롬프트 감지)",
        "category_ko": "네트워크 트로이목마 / C2",
        "explanation": "내부 호스트에서 공격자 IP로 아웃바운드 연결이 맺어지고 유닉스 셸 프롬프트가 오간 패턴이 탐지되었습니다. 침해 가능성이 매우 높습니다.",
        "investigation_guide": "피해 호스트의 실행 중인 프로세스 트리(sh, bash, python 등) 및 외향 연결 소켓을 즉각 격리하고 메모리 덤프를 확보하십시오.",
    },
}

# 5. MITRE ATT&CK Techniques (MITRE ATT&CK 매핑 사전)
MITRE_TECHNIQUE_MAP = {
    "T1046": {
        "name_ko": "네트워크 서비스 탐색",
        "name_en": "Network Service Discovery",
        "tactic": "Discovery (정찰/탐색)",
        "desc": "공격자가 원격 시스템에서 실행 중인 서비스와 포트를 식별하기 위해 스캔 도구를 사용하는 기법",
    },
    "T1190": {
        "name_ko": "외부 공개 애플리케이션 취약점 악용",
        "name_en": "Exploit Public-Facing Application",
        "tactic": "Initial Access (초기 침투)",
        "desc": "인터넷에 공개된 웹 서버나 서비스의 취약점(SQLi, RCE)을 이용하여 내부로 침투하는 기법",
    },
    "T1110": {
        "name_ko": "무차별 대입 공격",
        "name_en": "Brute Force",
        "tactic": "Credential Access (자격 증명 접근)",
        "desc": "사전 공격이나 무작위 입력을 통해 유효한 사용자 계정의 암호를 추측하는 기법",
    },
    "T1110.001": {
        "name_ko": "비밀번호 추측",
        "name_en": "Password Guessing",
        "tactic": "Credential Access (자격 증명 접근)",
        "desc": "일반적이거나 유출된 비밀번호 목록을 무차별 대입하는 하위 기법",
    },
    "T1059": {
        "name_ko": "명령어 및 스크립트 인터프리터",
        "name_en": "Command and Scripting Interpreter",
        "tactic": "Execution (명령 실행)",
        "desc": "공격자가 시스템 내부에서 셸 명령어(sh, bash, powershell 등)를 실행하는 기법",
    },
    "T1059.004": {
        "name_ko": "유닉스 셸 명령어 실행",
        "name_en": "Unix Shell",
        "tactic": "Execution (명령 실행)",
        "desc": "유닉스 계열 시스템에서 `/bin/sh` 또는 `/bin/bash` 셸을 통해 악성 명령을 내리는 기법",
    },
    "T1071": {
        "name_ko": "애플리케이션 계층 프로토콜 (C2)",
        "name_en": "Application Layer Protocol",
        "tactic": "Command and Control (명령 및 제어)",
        "desc": "HTTP, DNS 등의 표준 프로토콜을 위장하여 공격자 C2 서버와 통신하는 기법",
    },
}

# 6. Policy Verdicts (결정론적 정책 검증 결과 매핑)
POLICY_VERDICT_MAP = {
    "ALLOWED": {
        "ko": "정책 검증 통과 (승인 가능)",
        "badge_class": "bg-green-500/20 text-green-400 border-green-500/30",
        "desc": "대상 주소가 보호 인프라와 겹치지 않고 구문이 안전함",
    },
    "DENIED_PROTECTED_ASSET": {
        "ko": "정책 검증 거부: 보호 인프라 차단 불가",
        "badge_class": "bg-red-500/20 text-red-400 border-red-500/30",
        "desc": "게이트웨이, SIEM 호스트, DNS 등 운영 필수 자원은 차단할 수 없습니다.",
    },
    "DENIED_SYNTAX_ERROR": {
        "ko": "정책 검증 거부: 비정상 구문 / 인젝션 감지",
        "badge_class": "bg-red-500/20 text-red-400 border-red-500/30",
        "desc": "셸 메타문자(; & | ` $ > <)가 포함되어 실행이 차단되었습니다.",
    },
    "DENIED_INVALID_TARGET": {
        "ko": "정책 검증 거부: 유효하지 않은 IP / CIDR",
        "badge_class": "bg-red-500/20 text-red-400 border-red-500/30",
        "desc": "IPv4 주소 또는 CIDR 형식이 올바르지 않습니다.",
    },
    "DENIED_FAIL_CLOSED": {
        "ko": "정책 검증 거부: 안전 기본값(Fail-Closed) 차단",
        "badge_class": "bg-red-500/20 text-red-400 border-red-500/30",
        "desc": "예외 상황으로 인해 안전을 위해 차단되었습니다.",
    },
}

# 7. Approval Status & Actions (인간 승인 상태 및 조치 유형 매핑)
APPROVAL_STATUS_MAP = {
    "PENDING": {
        "ko": "분석가 검토 대기",
        "en": "Pending Analyst Review",
        "badge_class": "bg-amber-500/20 text-amber-400 border-amber-500/30 animate-pulse",
    },
    "APPROVED": {
        "ko": "조치 승인됨",
        "en": "Approved",
        "badge_class": "bg-blue-500/20 text-blue-400 border-blue-500/30",
    },
    "REJECTED": {
        "ko": "분석가 반려됨 (오탐/보류)",
        "en": "Rejected",
        "badge_class": "bg-red-500/20 text-red-400 border-red-500/30",
    },
    "EXECUTED": {
        "ko": "모의 실행 완료 (Dry-Run)",
        "en": "Executed (Dry-Run)",
        "badge_class": "bg-green-500/20 text-green-400 border-green-500/30",
    },
    "EXPIRED": {
        "ko": "승인 유효기간 만료",
        "en": "Expired",
        "badge_class": "bg-slate-700 text-slate-400 border-slate-600",
    },
}

ACTION_TYPE_MAP = {
    "BLOCK_IP": "공격자 IP 차단 (Inbound Block)",
    "ISOLATE_HOST": "피해 호스트 격리 (Host Isolation - SIEM 통신 유지)",
    "RATE_LIMIT": "네트워크 대역폭 제한 (Rate Limiting)",
    "GENERATE_TICKET": "보안 운영 2선 티켓 발행 (SOC Tier 2 Ticket)",
    "TUNE_RULE": "탐지 시그니처 임계치 튜닝 (Rule Tuning)",
}

EXECUTION_MODE_MAP = {
    "DRY_RUN": {
        "ko": "모의 실행 (Dry-Run 시뮬레이션 - 호스트 변경 없음)",
        "short": "모의 실행 (Dry-Run)",
        "is_safe": True,
    },
    "TICKET_ONLY": {
        "ko": "티켓 발행 모드 (실제 네트워크 변경 없음)",
        "short": "티켓 발행 (Ticket-Only)",
        "is_safe": True,
    },
    "LIVE": {
        "ko": "실제 방화벽 규칙 적용 (주의: 관리자 특별 권한 필요)",
        "short": "실제 적용 (Live)",
        "is_safe": False,
    },
}

# 8. Common SOC UI Dictionary (일반 관제 UI 용어 사전)
COMMON_UI_KO = {
    "dashboard_title": "보안관제 센터 (SOC Operations Center)",
    "dashboard_subtitle": "Suricata 8.x + Snort 3 듀얼 엔진 IDS & 증적 기반 AI 코파일럿",
    "view_mode": "화면 표시 모드",
    "view_mode_en": "원문 (English)",
    "view_mode_ko": "한국어 해석 (Korean)",
    "view_mode_split": "나란히 보기 (Split View)",
    "btn_refresh": "새로고침",
    "btn_investigate": "AI 심층 조사",
    "btn_interpret": "한국어 해석",
    "btn_approve_dry_run": "모의 실행 승인 (Dry-Run)",
    "btn_reject": "반려",
    "btn_view_evidence": "증적 및 원본 보기",
    "btn_view_output": "실행 결과 확인",
    "filter_search_placeholder": "IP, 규칙명, SID, 또는 카테고리 검색...",
    "filter_all": "전체",
    "table_timestamp": "발생 시각 (KST)",
    "table_engine": "탐지 엔진",
    "table_severity": "위험도",
    "table_signature": "탐지 규칙 (시그니처)",
    "table_src_ip": "출발지 IP:포트",
    "table_dst_ip": "목적지 IP:포트",
    "table_mitre": "MITRE ATT&CK",
    "table_actions": "조치",
    "observed_facts": "확인된 객관적 사실 (Observed Facts)",
    "hypotheses": "추정 가설 (Hypotheses)",
    "unknowns": "미확인 사항 (Unknowns - 추가 조사 필요)",
    "recommended_actions": "AI 권고 대응 조치 (Recommended Containment)",
    "status_mock_warning": "모의 분석 결과 (Mock Baseline - 실제 LLM 분석 아님)",
    "status_real_llm": "로컬 LLM 분석 완료",
}
