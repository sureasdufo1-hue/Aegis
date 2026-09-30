"""MITRE ATT&CK Enterprise Matrix Navigator & Dynamic Heatmap Engine.

Provides an interactive 14-Tactics matrix grid, real-time detection hit counting,
threat hotspot heatmap coloring, and 1-click drilldowns to PCAP and XAI forensics.
Aligned with MITRE ATT&CK Enterprise Framework v19.2.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field


class TechniqueInfo(BaseModel):
    id: str = Field(description="MITRE 기법 식별자 (예: T1046, T1110.001)")
    name: str = Field(description="기법 영문 명칭")
    name_ko: str = Field(description="기법 국문 명칭")
    tactic_id: str = Field(description="상위 전술 식별자 (예: TA0007)")
    tactic_name: str = Field(description="상위 전술 명칭")
    tactic_name_ko: str = Field(default="", description="상위 전술 국문 명칭")
    description: str = Field(description="기법 설명 및 공격 행위 분석")
    mitigation: str = Field(description="권고 대응 및 완화 방안")
    mapped_sids: list[int] = Field(default_factory=list, description="연계 Suricata/Snort 룰 SID")
    hit_count: int = Field(default=0, description="실측 탐지 이벤트 건수")
    severity: str = Field(default="LOW", description="최고 심각도 (INFO, LOW, MEDIUM, HIGH, CRITICAL)")
    active: bool = Field(default=False, description="현재 활성 공격 여부")
    last_seen: str | None = Field(default=None, description="최근 탐지 일시")


class TacticInfo(BaseModel):
    id: str = Field(description="전술 식별자 (예: TA0001)")
    name: str = Field(description="전술 영문 명칭")
    name_ko: str = Field(description="전술 국문 명칭")
    order: int = Field(description="킬체인 순서 (1~14)")
    techniques: list[TechniqueInfo] = Field(default_factory=list, description="소속 기법 목록")
    tactic_hit_count: int = Field(default=0, description="전술 내 총 탐지 건수")
    total_hits: int = Field(default=0, description="전술 내 총 탐지 건수 (별칭)")
    coverage_percentage: float = Field(default=100.0, description="전술 커버리지 비율")
    has_active_threat: bool = Field(default=False, description="활성 위협 포함 여부")


class MitreMatrixReport(BaseModel):
    framework_version: str = Field(default="v19.2", description="MITRE ATT&CK Framework 버전")
    tactics: list[TacticInfo]
    total_tactics: int
    covered_tactics: int
    total_techniques: int
    active_techniques: int
    active_threat_techniques: int = 0
    total_detections: int
    coverage_percentage: float
    generated_at: str


TACTIC_DEFINITIONS: list[dict[str, Any]] = [
    {"id": "TA0043", "name": "Reconnaissance", "name_ko": "정찰", "order": 1},
    {"id": "TA0042", "name": "Resource Development", "name_ko": "자원 개발", "order": 2},
    {"id": "TA0001", "name": "Initial Access", "name_ko": "최초 침투", "order": 3},
    {"id": "TA0002", "name": "Execution", "name_ko": "실행", "order": 4},
    {"id": "TA0003", "name": "Persistence", "name_ko": "지속성 유지", "order": 5},
    {"id": "TA0004", "name": "Privilege Escalation", "name_ko": "권한 상승", "order": 6},
    {"id": "TA0005", "name": "Defense Evasion", "name_ko": "방어 우회", "order": 7},
    {"id": "TA0006", "name": "Credential Access", "name_ko": "자격증명 탈취", "order": 8},
    {"id": "TA0007", "name": "Discovery", "name_ko": "내부 탐색", "order": 9},
    {"id": "TA0008", "name": "Lateral Movement", "name_ko": "횡적 이동", "order": 10},
    {"id": "TA0009", "name": "Collection", "name_ko": "정보 수집", "order": 11},
    {"id": "TA0011", "name": "Command and Control", "name_ko": "C2 제어", "order": 12},
    {"id": "TA0010", "name": "Exfiltration", "name_ko": "데이터 유출", "order": 13},
    {"id": "TA0040", "name": "Impact", "name_ko": "서비스 타격", "order": 14},
]

TECHNIQUE_SEEDS: list[dict[str, Any]] = [
    # 1. Reconnaissance (TA0043)
    {
        "id": "T1595",
        "name": "Active Scanning",
        "name_ko": "능동 스캔",
        "tactic_id": "TA0043",
        "tactic_name": "Reconnaissance",
        "description": "네트워크 인프라의 개방 포트 및 취약 서비스를 능동적으로 탐색하는 행위",
        "mitigation": "외부 인터넷 접점 방화벽에서 비인가 정찰 IP 대역 임시 차단 및 Rate Limit 적용",
        "mapped_sids": [1000001, 1000003],
        "hit_count": 380,
        "severity": "HIGH",
        "active": True,
        "last_seen": "2026-09-30T10:02:11Z",
    },
    {
        "id": "T1592",
        "name": "Gather Victim Host Information",
        "name_ko": "피해 호스트 정보 수집",
        "tactic_id": "TA0043",
        "tactic_name": "Reconnaissance",
        "description": "타겟 웹 서버 배너, OS 핑거프린팅 등을 통한 시스템 구성 정보 수집",
        "mitigation": "웹 서버 및 네트워크 데몬의 서버 배너(ServerTokens) 숨김 설정",
        "mapped_sids": [9000001],
        "hit_count": 12,
        "severity": "LOW",
        "active": False,
        "last_seen": "2026-09-30T09:45:00Z",
    },
    {
        "id": "T1590",
        "name": "Gather Victim Network Information",
        "name_ko": "피해 네트워크 정보 수집",
        "tactic_id": "TA0043",
        "tactic_name": "Reconnaissance",
        "description": "타겟 서브넷 CIDR 및 토폴로지 구성에 대한 DNS/라우팅 정찰",
        "mitigation": "DNS 구역 전송(Zone Transfer) 차단 및 사설망 토폴로지 정보 노출 방지",
        "mapped_sids": [1000001],
        "hit_count": 5,
        "severity": "LOW",
        "active": False,
        "last_seen": "2026-09-30T09:30:00Z",
    },
    # 2. Resource Development (TA0042)
    {
        "id": "T1587",
        "name": "Develop Capabilities",
        "name_ko": "공격 도구 및 페이로드 제작",
        "tactic_id": "TA0042",
        "tactic_name": "Resource Development",
        "description": "익스플로잇 코드, 웹셸 또는 악성 페이로드를 사전에 컴파일하거나 조달",
        "mitigation": "CTI 피드 기반 악성 도구 해시 블랙리스트 등록 및 위협 인텔리전스 공유",
        "mapped_sids": [],
        "hit_count": 0,
        "severity": "INFO",
        "active": False,
        "last_seen": None,
    },
    {
        "id": "T1588",
        "name": "Obtain Capabilities",
        "name_ko": "공격 도구 및 취약점 정보 확보",
        "tactic_id": "TA0042",
        "tactic_name": "Resource Development",
        "description": "공개 Exploit-DB 또는 깃허브에서 공격 도구(PoC) 조달",
        "mitigation": "오픈소스 보안 취약점 모니터링 및 방어 서명 조기 도입",
        "mapped_sids": [],
        "hit_count": 0,
        "severity": "INFO",
        "active": False,
        "last_seen": None,
    },
    # 3. Initial Access (TA0001)
    {
        "id": "T1190",
        "name": "Exploit Public-Facing Application",
        "name_ko": "외부 공개 애플리케이션 취약점 공격",
        "tactic_id": "TA0001",
        "tactic_name": "Initial Access",
        "description": "웹 포트(80/8080)를 통해 SQL Injection 및 Apache Log4j(JNDI) 취약점을 공격하여 침투",
        "mitigation": "WAF 입력값 검증 룰 적용 및 취약 소프트웨어 긴급 보안 패치 배포",
        "mapped_sids": [9010001, 9010002, 9010003],
        "hit_count": 18,
        "severity": "CRITICAL",
        "active": True,
        "last_seen": "2026-09-30T10:15:08Z",
    },
    {
        "id": "T1566",
        "name": "Phishing",
        "name_ko": "피싱",
        "tactic_id": "TA0001",
        "tactic_name": "Initial Access",
        "description": "스피어 피싱 이메일 또는 악성 링크를 통한 최초 접근 시도",
        "mitigation": "이메일 게이트웨이 첨부파일 격리 및 악성 도메인 필터링",
        "mapped_sids": [],
        "hit_count": 0,
        "severity": "INFO",
        "active": False,
        "last_seen": None,
    },
    {
        "id": "T1078",
        "name": "Valid Accounts",
        "name_ko": "유효한 계정 도용",
        "tactic_id": "TA0001",
        "tactic_name": "Initial Access",
        "description": "탈취한 정상 사용자 또는 기본 관리자 계정을 악용하여 인가된 세션으로 침투",
        "mitigation": "다중 인증(MFA) 강제 적용 및 비인가 접속 지역 세션 즉각 격리",
        "mapped_sids": [9020001],
        "hit_count": 1,
        "severity": "MEDIUM",
        "active": False,
        "last_seen": "2026-09-30T08:10:00Z",
    },
    # 4. Execution (TA0002)
    {
        "id": "T1059",
        "name": "Command and Scripting Interpreter",
        "name_ko": "명령어 및 스크립트 인터프리터 실행",
        "tactic_id": "TA0002",
        "tactic_name": "Execution",
        "description": "익스플로잇 성공 후 /bin/sh 또는 PowerShell을 호출하여 시스템 명령어 실행",
        "mitigation": "웹 서버 데몬 계정(/var/www)의 셸 실행 권한 제한(/sbin/nologin) 및 AppArmor 강화",
        "mapped_sids": [9000004],
        "hit_count": 5,
        "severity": "HIGH",
        "active": True,
        "last_seen": "2026-09-30T10:16:12Z",
    },
    {
        "id": "T1203",
        "name": "Exploitation for Client Execution",
        "name_ko": "클라이언트 실행을 위한 취약점 공격",
        "tactic_id": "TA0002",
        "tactic_name": "Execution",
        "description": "애플리케이션 취약점을 이용해 웹 서버 프로세스 권한으로 임의 코드 실행",
        "mitigation": "WAF 가상 패치 및 웹 런타임 권한 축소",
        "mapped_sids": [9010002],
        "hit_count": 6,
        "severity": "HIGH",
        "active": True,
        "last_seen": "2026-09-30T10:16:00Z",
    },
    # 5. Persistence (TA0003)
    {
        "id": "T1505",
        "name": "Server Software Component",
        "name_ko": "서버 소프트웨어 구성요소(웹셸) 변조",
        "tactic_id": "TA0003",
        "tactic_name": "Persistence",
        "description": "웹 디렉터리에 악성 백도어 PHP/JSP 웹셸을 업로드하여 재접근 통로 확보",
        "mitigation": "파일 무결성 모니터링(Wazuh FIM) 가동 및 웹 업로드 디렉터리 실행 권한 제거",
        "mapped_sids": [9010003],
        "hit_count": 2,
        "severity": "MEDIUM",
        "active": False,
        "last_seen": "2026-09-30T09:20:00Z",
    },
    {
        "id": "T1053",
        "name": "Scheduled Task/Job (Cron)",
        "name_ko": "스케줄 작업/크론 등록",
        "tactic_id": "TA0003",
        "tactic_name": "Persistence",
        "description": "/etc/cron* 에 리버스 셸 또는 백도어 자동 재실행 작업 등록",
        "mitigation": "크론탭 디렉터리 무결성 검사(Wazuh FIM) 및 비인가 크론 수정 감시",
        "mapped_sids": [],
        "hit_count": 0,
        "severity": "LOW",
        "active": False,
        "last_seen": None,
    },
    # 6. Privilege Escalation (TA0004)
    {
        "id": "T1068",
        "name": "Exploitation for Privilege Escalation",
        "name_ko": "권한 상승을 위한 취약점 공격",
        "tactic_id": "TA0004",
        "tactic_name": "Privilege Escalation",
        "description": "로컬 커널 취약점이나 SUID 바이너리 오설정을 악용하여 루트 권한 획득 시도",
        "mitigation": "리눅스 커널 최신 패치 유지 및 비인가 SUID 바이너리 주기적 감사",
        "mapped_sids": [],
        "hit_count": 0,
        "severity": "INFO",
        "active": False,
        "last_seen": None,
    },
    {
        "id": "T1548",
        "name": "Abuse Elevation Control Mechanism (sudo)",
        "name_ko": "권한 상승 제어 메커니즘 악용",
        "tactic_id": "TA0004",
        "tactic_name": "Privilege Escalation",
        "description": "sudoers 취약점 또는 비밀번호 없는 sudo 권한을 악용해 root 권한 획득",
        "mitigation": "sudoers 최소 권한 정책 및 ALL=(ALL) NOPASSWD 설정 엄격 금지",
        "mapped_sids": [9020002],
        "hit_count": 0,
        "severity": "LOW",
        "active": False,
        "last_seen": None,
    },
    # 7. Defense Evasion (TA0005)
    {
        "id": "T1070",
        "name": "Indicator Removal on Host",
        "name_ko": "호스트 침해 흔적(로그) 삭제",
        "tactic_id": "TA0005",
        "tactic_name": "Defense Evasion",
        "description": "/var/log/auth.log 및 웹 접근 로그 삭제 또는 변조를 통한 관제 회피",
        "mitigation": "Wazuh 원격 중앙 집중식 로그 수집 및 WORM(Write Once Read Many) 스토리지 적용",
        "mapped_sids": [9020002],
        "hit_count": 1,
        "severity": "LOW",
        "active": False,
        "last_seen": "2026-09-30T08:50:00Z",
    },
    {
        "id": "T1027",
        "name": "Obfuscated Files or Information",
        "name_ko": "난독화된 파일 또는 스크립트 페이로드",
        "tactic_id": "TA0005",
        "tactic_name": "Defense Evasion",
        "description": "Base64 인코딩, eval 함수 중첩 등을 통한 IDS 시그니처 탐지 우회 시도",
        "mitigation": "Suricata HTTP 키워드 디코딩 검사(urldecode, base64_decode)",
        "mapped_sids": [9010002],
        "hit_count": 7,
        "severity": "HIGH",
        "active": True,
        "last_seen": "2026-09-30T10:15:20Z",
    },
    # 8. Credential Access (TA0006)
    {
        "id": "T1110.001",
        "name": "Password Guessing (Brute Force)",
        "name_ko": "비밀번호 사전 대입 공격",
        "tactic_id": "TA0006",
        "tactic_name": "Credential Access",
        "description": "포트 22(SSH)를 표적으로 root/admin 등 관리자 계정에 대한 초고빈도 무차별 대입",
        "mitigation": "fail2ban 자동 차단 연동, SSH 패스워드 로그인 금지 및 ED25519 공개키 인증 강제",
        "mapped_sids": [1000003],
        "hit_count": 82,
        "severity": "HIGH",
        "active": True,
        "last_seen": "2026-09-30T10:18:15Z",
    },
    {
        "id": "T1552",
        "name": "Unsecured Credentials",
        "name_ko": "비보호된 평문 자격증명 탐색",
        "tactic_id": "TA0006",
        "tactic_name": "Credential Access",
        "description": "웹루트 디렉터리 내 설정 파일에서 평문 DB 비밀번호 검색 및 추출",
        "mitigation": "환경 변수 기반 비밀번호 관리 및 웹 설정 파일 접근 권한 제한",
        "mapped_sids": [9010001],
        "hit_count": 2,
        "severity": "MEDIUM",
        "active": False,
        "last_seen": "2026-09-30T09:12:00Z",
    },
    # 9. Discovery (TA0007)
    {
        "id": "T1046",
        "name": "Network Service Discovery",
        "name_ko": "네트워크 서비스 및 포트 검색",
        "tactic_id": "TA0007",
        "tactic_name": "Discovery",
        "description": "타겟 서브넷(10.77.30.0/24) 내 활성 호스트 및 개방 포트 리스트 열거",
        "mitigation": "내부망 게이트웨이 nftables strict forward drop 정책 및 비인가 포트 필터링",
        "mapped_sids": [1000001, 9000001],
        "hit_count": 380,
        "severity": "HIGH",
        "active": True,
        "last_seen": "2026-09-30T10:02:11Z",
    },
    {
        "id": "T1082",
        "name": "System Information Discovery",
        "name_ko": "시스템 정보 검색 (uname/os-release)",
        "tactic_id": "TA0007",
        "tactic_name": "Discovery",
        "description": "운영체제 커널 버전, 아키텍처 및 릴리즈 정보 확인 명령어 실행",
        "mitigation": "시스템 정보 조회 유틸리티에 대한 일반 사용자 실행 권한 감사",
        "mapped_sids": [9000004],
        "hit_count": 8,
        "severity": "LOW",
        "active": True,
        "last_seen": "2026-09-30T10:17:00Z",
    },
    # 10. Lateral Movement (TA0008)
    {
        "id": "T1021.004",
        "name": "Remote Services: SSH",
        "name_ko": "원격 서비스 경유 횡적 이동(SSH)",
        "tactic_id": "TA0008",
        "tactic_name": "Lateral Movement",
        "description": "침해된 호스트에서 탈취한 키/패스워드를 악용하여 내부 다른 서버로 횡적 확산",
        "mitigation": "서브넷 간 SSH 통신 원천 차단(Zone Isolation) 및 점프 호스트(Bastion) 통제",
        "mapped_sids": [1000003],
        "hit_count": 0,
        "severity": "LOW",
        "active": False,
        "last_seen": None,
    },
    # 11. Collection (TA0009)
    {
        "id": "T1005",
        "name": "Data from Local System",
        "name_ko": "로컬 시스템 데이터 수집",
        "tactic_id": "TA0009",
        "tactic_name": "Collection",
        "description": "웹 설정 파일(config.php, /etc/passwd) 및 데이터베이스 덤프 수집",
        "mitigation": "데이터베이스 최소 권한 원칙(Least Privilege) 적용 및 중요 파일 퍼미션(chmod 600) 통제",
        "mapped_sids": [9010001],
        "hit_count": 4,
        "severity": "MEDIUM",
        "active": False,
        "last_seen": "2026-09-30T10:14:55Z",
    },
    # 12. Command and Control (TA0011)
    {
        "id": "T1571",
        "name": "Non-Standard Port (Reverse Shell C2)",
        "name_ko": "비표준 포트 역방향 셸 C2 연결",
        "tactic_id": "TA0011",
        "tactic_name": "Command and Control",
        "description": "타겟 호스트에서 외부 공격자(10.77.20.20:4444)로의 비표준 아웃바운드 세션 연결 시도",
        "mitigation": "아웃바운드 트래픽 엄격 통제 (Egress Filtering: 80, 443, 1514 외 전면 DROP)",
        "mapped_sids": [9000004],
        "hit_count": 14,
        "severity": "CRITICAL",
        "active": True,
        "last_seen": "2026-09-30T10:16:30Z",
    },
    {
        "id": "T1071",
        "name": "Application Layer Protocol (HTTP C2)",
        "name_ko": "애플리케이션 계층 프로토콜(HTTP C2) 활용",
        "tactic_id": "TA0011",
        "tactic_name": "Command and Control",
        "description": "HTTP 80/8080 포트를 위장하여 주기적인 비콘(Beacon) 신호 송수신",
        "mitigation": "Suricata HTTP 트래픽 검사 및 비인가 외부 웹 비콘 탐지 룰 적용",
        "mapped_sids": [9000004, 9010001],
        "hit_count": 11,
        "severity": "HIGH",
        "active": True,
        "last_seen": "2026-09-30T10:20:00Z",
    },
    # 13. Exfiltration (TA0010)
    {
        "id": "T1041",
        "name": "Exfiltration Over C2 Channel",
        "name_ko": "C2 채널을 통한 기밀 데이터 유출",
        "tactic_id": "TA0010",
        "tactic_name": "Exfiltration",
        "description": "수립된 C2 역방향 셸 터널을 통해 탈취한 데이터베이스 레코드 외부 전송",
        "mitigation": "네트워크 DLP 및 게이트웨이 Forward 체인 패킷 카운터 모니터링",
        "mapped_sids": [9000004],
        "hit_count": 0,
        "severity": "LOW",
        "active": False,
        "last_seen": None,
    },
    # 14. Impact (TA0040)
    {
        "id": "T1498.001",
        "name": "Direct Network Denial of Service (SYN Flood)",
        "name_ko": "직접 네트워크 서비스 거부(SYN 플러드)",
        "tactic_id": "TA0040",
        "tactic_name": "Impact",
        "description": "초당 15,000 pps 이상의 비정상 L4 TCP SYN 패킷 폭주로 서버 네트워크 고갈 유발",
        "mitigation": "Gateway nftables SYN Proxy 활성화 및 Conntrack 임계치 초과 시 자동 Rate Limit",
        "mapped_sids": [9000005],
        "hit_count": 15000,
        "severity": "CRITICAL",
        "active": True,
        "last_seen": "2026-09-30T10:30:15Z",
    },
    {
        "id": "T1486",
        "name": "Data Encrypted for Impact",
        "name_ko": "데이터 암호화를 통한 가용성 침해",
        "tactic_id": "TA0040",
        "tactic_name": "Impact",
        "description": "중요 업무 파일 및 데이터베이스를 무단 암호화하여 서비스 중단 유발",
        "mitigation": "오프라인/에어갭 백업 정책 유지 및 Wazuh 랜섬웨어 행위 기반 탐지 룰",
        "mapped_sids": [],
        "hit_count": 0,
        "severity": "INFO",
        "active": False,
        "last_seen": None,
    },
]


class MitreMatrixEngine:
    """Computes MITRE ATT&CK 14-Tactics coverage, real-time threat hit counts, and hotspots."""

    def __init__(self) -> None:
        tactic_ko_map = {t["id"]: t["name_ko"] for t in TACTIC_DEFINITIONS}
        self._techniques: dict[str, TechniqueInfo] = {}
        for t in TECHNIQUE_SEEDS:
            item = dict(t)
            if not item.get("tactic_name_ko"):
                item["tactic_name_ko"] = tactic_ko_map.get(item.get("tactic_id", ""), "")
            self._techniques[item["id"]] = TechniqueInfo.model_validate(item)

    def get_matrix_report(self) -> MitreMatrixReport:
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")

        # Group techniques by tactic
        tactic_map: dict[str, list[TechniqueInfo]] = {t["id"]: [] for t in TACTIC_DEFINITIONS}
        for tech in self._techniques.values():
            if tech.tactic_id in tactic_map:
                tactic_map[tech.tactic_id].append(tech)

        tactics_list: list[TacticInfo] = []
        covered_tactics_count = 0
        active_tech_count = 0
        total_detections = 0

        for t_def in sorted(TACTIC_DEFINITIONS, key=lambda x: x["order"]):
            t_id = t_def["id"]
            techs = tactic_map.get(t_id, [])
            tactic_hits = sum(t.hit_count for t in techs)
            has_active = any(t.active for t in techs)

            if len(techs) > 0:
                covered_tactics_count += 1

            for t in techs:
                if t.active:
                    active_tech_count += 1
                total_detections += t.hit_count

            t_info = TacticInfo(
                id=t_id,
                name=t_def["name"],
                name_ko=t_def["name_ko"],
                order=t_def["order"],
                techniques=techs,
                tactic_hit_count=tactic_hits,
                total_hits=tactic_hits,
                coverage_percentage=100.0 if len(techs) > 0 else 0.0,
                has_active_threat=has_active,
            )
            tactics_list.append(t_info)

        total_tactics = len(TACTIC_DEFINITIONS)
        coverage_pct = round((covered_tactics_count / total_tactics) * 100, 1)

        return MitreMatrixReport(
            framework_version="v19.2",
            tactics=tactics_list,
            total_tactics=total_tactics,
            covered_tactics=covered_tactics_count,
            total_techniques=len(self._techniques),
            active_techniques=active_tech_count,
            active_threat_techniques=active_tech_count,
            total_detections=total_detections,
            coverage_percentage=coverage_pct,
            generated_at=now_str,
        )

    def get_technique(self, technique_id: str) -> TechniqueInfo | None:
        return self._techniques.get(technique_id)

    def update_technique_hit(self, technique_id: str, count_delta: int = 1, severity: str | None = None) -> TechniqueInfo | None:
        tech = self._techniques.get(technique_id)
        if tech:
            tech.hit_count += count_delta
            tech.active = True
            tech.last_seen = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
            if severity:
                tech.severity = severity
        return tech


mitre_matrix_engine = MitreMatrixEngine()
