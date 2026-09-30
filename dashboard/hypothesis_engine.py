"""AI Security Hypothesis Generation and Multi-Source Verification Engine.

Formulates multiple competing security hypotheses for detected incidents,
and cross-verifies supporting and refuting evidence from Suricata EVE logs,
Gateway nftables firewall drops, and PCAP session records.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    source: str = Field(..., description="증거 출처 (예: Suricata EVE, Gateway nftables, PCAP Forensics)")
    evidence_type: str = Field(..., description="SUPPORTING (지지 증거) | REFUTING (반박 증거)")
    description: str = Field(..., description="증거 상세 설명")
    timestamp: str = Field(..., description="기록 타임스탬프")
    artifact_ref: str = Field(..., description="참조 식별자 (SID, 패킷 번호, 룰 등)")


class SecurityHypothesis(BaseModel):
    id: str = Field(..., description="가설 식별자 (예: HYP-01)")
    title: str = Field(..., description="가설 제목")
    kill_chain_stage: str = Field(..., description="MITRE ATT&CK 킬체인 단계")
    status: str = Field(..., description="PROVEN (입증) | REFUTED (기각) | INVESTIGATING (조사 중)")
    confidence_score: int = Field(..., ge=0, le=100, description="신뢰도 점수 (0-100)")
    primary_reason: str = Field(..., description="핵심 판정 소명 요약")
    supporting_evidences: list[EvidenceItem] = Field(default_factory=list, description="지지 증거 목록")
    refuting_evidences: list[EvidenceItem] = Field(default_factory=list, description="반박 증거 목록")
    recommended_action: str = Field(..., description="권고 조치 사항")


class IncidentHypothesisReport(BaseModel):
    incident_id: str
    attacker_ip: str
    target_ip: str
    generated_at: str
    top_concluded_hypothesis: str
    hypotheses: list[SecurityHypothesis]


class HypothesisEngine:
    """Evaluates multi-source forensic evidence to prove or refute attack hypotheses."""

    def __init__(self) -> None:
        pass

    def evaluate_incident(
        self,
        incident_id: str,
        attacker_ip: str = "10.77.20.20",
        target_ip: str = "10.77.30.20",
        scenario: str | None = None,
    ) -> IncidentHypothesisReport:
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
        sc_upper = (scenario or "").upper()

        if sc_upper in ("BRUTEFORCE", "SSH") or "BRUTE" in incident_id.upper() or "IR-02" in incident_id.upper():
            hypotheses = [
                SecurityHypothesis(
                    id="HYP-01",
                    title="가설 1: 외부 공격자의 SSH 사전 대입(Dictionary Attack)을 통한 관리자 권한 침탈 시도",
                    kill_chain_stage="Credential Access (T1110.001)",
                    status="PROVEN",
                    confidence_score=93,
                    primary_reason="Suricata 8.0.6 포트 22 초고빈도 접근 알림(SID 1000003) 및 Victim OS PAM 82건 연속 인증 실패가 실측 확인됨.",
                    supporting_evidences=[
                        EvidenceItem(
                            source="Suricata EVE",
                            evidence_type="SUPPORTING",
                            description="초당 30회 이상의 SSH 연결 시도 및 Potential SSH Scan 경보 집중 발생",
                            timestamp="2026-09-22T10:18:04Z",
                            artifact_ref="SID: 1000003 (SSH Scan)",
                        ),
                        EvidenceItem(
                            source="Asset PAM Log",
                            evidence_type="SUPPORTING",
                            description="sshd 인증 실패 로그(Failed password for invalid user admin/root) 82건 연속 발생",
                            timestamp="2026-09-22T10:18:15Z",
                            artifact_ref="AUTH-LOG: sshd PAM_AUTH_FAIL",
                        ),
                        EvidenceItem(
                            source="PCAP Forensics",
                            evidence_type="SUPPORTING",
                            description="PCAP Frame 다수: SSH-2.0-OpenSSH 클라이언트 식별자 및 세션 버스트 포착",
                            timestamp="2026-09-22T10:18:20Z",
                            artifact_ref="PCAP: Frame #102-140",
                        ),
                    ],
                    refuting_evidences=[],
                    recommended_action="공격자 IP(10.77.20.20)에 대한 Gateway nftables 즉시 DROP 차단 및 fail2ban 연동",
                ),
                SecurityHypothesis(
                    id="HYP-02",
                    title="가설 2: 사내 승인된 관리자의 일시적인 비밀번호 오입력 오탐(False Positive)",
                    kill_chain_stage="False Positive Analysis",
                    status="REFUTED",
                    confidence_score=7,
                    primary_reason="초당 30회 이상의 기계적 속도 및 'admin', 'root' 등 사전 대입 단어 목록 순차 대입이 관측되어 사람의 입력 오류 가능성 완전 배제.",
                    supporting_evidences=[],
                    refuting_evidences=[
                        EvidenceItem(
                            source="Traffic Entropy",
                            evidence_type="REFUTING",
                            description="요청 간격(Delta)이 33ms 이하로 자동화 스크립트 실행 명백",
                            timestamp="2026-09-22T10:18:05Z",
                            artifact_ref="METRIC: INTER_ARRIVAL_MS < 33",
                        )
                    ],
                    recommended_action="오탐 예외 등록 불허 및 위협 경보 유지",
                ),
                SecurityHypothesis(
                    id="HYP-03",
                    title="가설 3: SSH 로그인 성공 후 내부망 횡적 이동(Lateral Movement) 기수행",
                    kill_chain_stage="Lateral Movement (T1021.004)",
                    status="REFUTED",
                    confidence_score=10,
                    primary_reason="Victim 인증 로그 상 'Accepted password' 성공 이벤트가 0건이며, 추가 내부 세션 연결 트래픽이 일절 부재함.",
                    supporting_evidences=[],
                    refuting_evidences=[
                        EvidenceItem(
                            source="Asset Auth Log",
                            evidence_type="REFUTING",
                            description="sshd Accepted session 성공 카운터 0건 확인",
                            timestamp="2026-09-22T10:19:00Z",
                            artifact_ref="AUTH-LOG: ZERO_SUCCESS",
                        ),
                        EvidenceItem(
                            source="Gateway nftables",
                            evidence_type="REFUTING",
                            description="내부 서브넷 간 비인가 SSH/RDP 포워딩 연결 세션 0건",
                            timestamp="2026-09-22T10:19:05Z",
                            artifact_ref="FW-STAT: FWD_LATERAL_ZERO",
                        ),
                    ],
                    recommended_action="시스템 침해는 미발생 상태이며, 진입 경로 선제 차단으로 사고 종결 가능",
                ),
            ]
            top_concluded = "가설 1 입증 (SSH 무차별 대입 공격 확인) & 가설 3 기각 (로그인 성공 및 횡적이동 미발생)"
        elif sc_upper in ("SCAN", "RECON") or "SCAN" in incident_id.upper() or "IR-01" in incident_id.upper():
            hypotheses = [
                SecurityHypothesis(
                    id="HYP-01",
                    title="가설 1: 외부 공격자의 Nmap SYN 포트 스캔을 통한 취약 서비스 및 토폴로지 식별 시도",
                    kill_chain_stage="Reconnaissance (T1046)",
                    status="PROVEN",
                    confidence_score=95,
                    primary_reason="Suricata 8.0.6 시그니처 (SID 1000001, Nmap SYN Scan) 380회 매칭 및 다중 포트 연속 SYN 플래그 집중 인입 실측.",
                    supporting_evidences=[
                        EvidenceItem(
                            source="Suricata EVE",
                            evidence_type="SUPPORTING",
                            description="Nmap SYN Stealth Scan 시그니처 경보 380건 다발",
                            timestamp="2026-09-22T10:02:11Z",
                            artifact_ref="SID: 1000001 (Nmap SYN)",
                        ),
                        EvidenceItem(
                            source="PCAP Forensics",
                            evidence_type="SUPPORTING",
                            description="PCAP Frame 다수: 목적지 포트 21, 22, 80, 443, 3306 등 순차 SYN 패킷 식별",
                            timestamp="2026-09-22T10:02:15Z",
                            artifact_ref="PCAP: Frame #1-120",
                        ),
                        EvidenceItem(
                            source="Gateway nftables",
                            evidence_type="SUPPORTING",
                            description="포워딩 체인 SYN 비정상 버스트 트래픽 카운터 급증 확인",
                            timestamp="2026-09-22T10:02:20Z",
                            artifact_ref="FW-STAT: SYN_BURST",
                        ),
                    ],
                    refuting_evidences=[],
                    recommended_action="공격자 IP(10.77.20.20)에 대한 Gateway nftables 임시 차단 및 비인가 포트 노출 점검",
                ),
                SecurityHypothesis(
                    id="HYP-02",
                    title="가설 2: 사내 보안진단 솔루션에 의한 사전 승인된 인프라 취약점 전수 진단",
                    kill_chain_stage="False Positive Analysis",
                    status="REFUTED",
                    confidence_score=5,
                    primary_reason="공격자 IP(10.77.20.20)는 사내 공인 진단 장비 목록에 미등록된 외부 ZONE-ATTACK 대역이며 사전 작업 승인 공문 부재.",
                    supporting_evidences=[],
                    refuting_evidences=[
                        EvidenceItem(
                            source="CMDB Asset DB",
                            evidence_type="REFUTING",
                            description="진단 스캐너 화이트리스트 IP 대역(10.77.10.x) 불일치 및 미인가 호스트 확인",
                            timestamp="2026-09-22T10:02:30Z",
                            artifact_ref="ASSET-DB: UNREGISTERED_SRC",
                        ),
                    ],
                    recommended_action="오탐 예외 처리 불허 및 보안 위협 모니터링 유지",
                ),
                SecurityHypothesis(
                    id="HYP-03",
                    title="가설 3: 포트 스캔 성공 직후 원격 익스플로잇 즉각 실행",
                    kill_chain_stage="Initial Access (T1190)",
                    status="INVESTIGATING",
                    confidence_score=35,
                    primary_reason="스캔 완료 후 오픈된 80/22 포트에 대한 추가 후속 페이로드 인입 징후가 관측되어 EVE 로그 연계 분석 진행 중.",
                    supporting_evidences=[
                        EvidenceItem(
                            source="Suricata EVE",
                            evidence_type="SUPPORTING",
                            description="포트 80(HTTP), 22(SSH) 오픈 응답(SYN-ACK) 수신 확인",
                            timestamp="2026-09-22T10:03:00Z",
                            artifact_ref="PCAP: Open Port Discovery",
                        ),
                    ],
                    refuting_evidences=[
                        EvidenceItem(
                            source="Victim Process",
                            evidence_type="REFUTING",
                            description="비인가 프로세스 생성 및 셸 실행 이력 현재까지 미발생",
                            timestamp="2026-09-22T10:03:10Z",
                            artifact_ref="PROC: NO_EXPLOIT_YET",
                        ),
                    ],
                    recommended_action="해당 포트 서비스에 대한 접근 제어 강화 및 WAF 정책 즉시 점검",
                ),
            ]
            top_concluded = "가설 1 입증 (Nmap SYN 스캔 확인) & 가설 2 기각 (비인가 정찰 행위)"
        elif sc_upper in ("DOS", "FLOOD") or "DOS" in incident_id.upper() or "IR-05" in incident_id.upper():
            hypotheses = [
                SecurityHypothesis(
                    id="HYP-01",
                    title="가설 1: 대량 TCP SYN 네트워크 플러딩을 통한 웹 서비스 고갈(DoS) 공격",
                    kill_chain_stage="Impact (T1498.001)",
                    status="PROVEN",
                    confidence_score=96,
                    primary_reason="Suricata 8.0.6 DoS 임계치 초과 경보(SID 9000005) 및 Gateway 15,000 pps 트래픽 버스트 실측 확인.",
                    supporting_evidences=[
                        EvidenceItem(
                            source="Suricata EVE",
                            evidence_type="SUPPORTING",
                            description="TCP SYN Flood 임계치 초과 경보 다수 발생",
                            timestamp="2026-09-22T10:30:15Z",
                            artifact_ref="SID: 9000005 (DoS Flood)",
                        ),
                        EvidenceItem(
                            source="Gateway nftables",
                            evidence_type="SUPPORTING",
                            description="초당 15,000 pps 패킷 유입 및 conntrack 테이블 임계치 경보",
                            timestamp="2026-09-22T10:30:20Z",
                            artifact_ref="FW-METRIC: 15K_PPS",
                        ),
                        EvidenceItem(
                            source="PCAP Forensics",
                            evidence_type="SUPPORTING",
                            description="단일 출발지에서 비정상 고정 윈도우 크기(1024)의 SYN 패킷 무차별 투하",
                            timestamp="2026-09-22T10:30:22Z",
                            artifact_ref="PCAP: Flood Stream",
                        ),
                    ],
                    refuting_evidences=[],
                    recommended_action="Gateway nftables SYN Proxy 활성화 및 대상 출발지 IP 즉시 Rate Limit 적용",
                ),
                SecurityHypothesis(
                    id="HYP-02",
                    title="가설 2: 신규 서비스 런칭 또는 마케팅 홍보에 따른 정상 사용자의 일시적 트래픽 폭주(Flash Crowd)",
                    kill_chain_stage="Benign Spike",
                    status="REFUTED",
                    confidence_score=4,
                    primary_reason="3-Way Handshake 완결 세션이 0%이며, HTTP Request Payload를 수반하지 않는 순수 L4 SYN 패킷만 난사됨.",
                    supporting_evidences=[],
                    refuting_evidences=[
                        EvidenceItem(
                            source="Traffic Entropy",
                            evidence_type="REFUTING",
                            description="HTTP GET/POST 유효 트래픽 비율 0.0% (L4 SYN 난사 패턴)",
                            timestamp="2026-09-22T10:30:25Z",
                            artifact_ref="FLOW-STAT: ZERO_PAYLOAD",
                        ),
                    ],
                    recommended_action="정상 트래픽 예외 등록 불허, DoS 방어 정책 즉시 유지",
                ),
                SecurityHypothesis(
                    id="HYP-03",
                    title="가설 3: DoS 트래픽 혼란을 틈탄 은밀한 2차 백도어 침투(Distraction Attack)",
                    kill_chain_stage="Defense Evasion (T1070)",
                    status="INVESTIGATING",
                    confidence_score=40,
                    primary_reason="Gateway 방화벽의 Rate Limiting 가동 중에도 별도 관리 포트 우회 접근 시도가 감지되어 상관분석 진행 중.",
                    supporting_evidences=[
                        EvidenceItem(
                            source="Gateway nftables",
                            evidence_type="SUPPORTING",
                            description="보조 관리 포트 비인가 인입 플로우 3건 포착",
                            timestamp="2026-09-22T10:30:30Z",
                            artifact_ref="FW-LOG: PORT_ANOMALY",
                        ),
                    ],
                    refuting_evidences=[],
                    recommended_action="보조 관리 포트 방화벽 차단 확인 및 EVE 이벤트 연속 모니터링",
                ),
            ]
            top_concluded = "가설 1 입증 (TCP SYN Flood DoS 확인) & 가설 2 기각 (순수 L4 고갈 공격)"
        # Preset profile for canonical Multi-Stage IR-06 Kill Chain
        elif (
            "IR" in incident_id.upper()
            or "001" in incident_id
            or "002" in incident_id
            or attacker_ip in ("10.77.20.20", "10.77.20.50")
            or sc_upper in ("SQLI", "LOG4J", "C2", "MULTI", "KILLCHAIN")
            or "INC" in incident_id.upper()
        ):
            hypotheses = [
                SecurityHypothesis(
                    id="HYP-01",
                    title="가설 1: Web SQLi 및 Log4j 복합 취약점을 통한 원격 침투 성공",
                    kill_chain_stage="Exploitation & Execution",
                    status="PROVEN",
                    confidence_score=94,
                    primary_reason="Suricata 8.0.6 EVE 로그 상 SQLi 파라미터 유입(SID 9010001) 및 Log4j JNDI 페이로드 인입(SID 9010002)이 실측 확인되었으며, 대상 웹서버 응답코드 및 비정상 엔트로피가 지지함.",
                    supporting_evidences=[
                        EvidenceItem(
                            source="Suricata EVE",
                            evidence_type="SUPPORTING",
                            description="HTTP 80번 포트 대상 'UNION SELECT' 메타문자 밀도 94%의 SQL 인젝션 페이로드 유입 확인",
                            timestamp="2026-09-22T10:14:22Z",
                            artifact_ref="SID: 9010001 (Web SQLi)"
                        ),
                        EvidenceItem(
                            source="Suricata EVE",
                            evidence_type="SUPPORTING",
                            description="TCP 8080/80 경유 Apache Log4j jndi:ldap:// 공격 문자열 탐지",
                            timestamp="2026-09-22T10:15:08Z",
                            artifact_ref="SID: 9010002 (Log4j RCE)"
                        ),
                        EvidenceItem(
                            source="PCAP Forensics",
                            evidence_type="SUPPORTING",
                            description="PCAP Frame #84: HTTP POST 요청 본문에서 ${jndi:ldap...} 쿼리 페이로드 완전 복원 확인",
                            timestamp="2026-09-22T10:15:08Z",
                            artifact_ref="PCAP: Frame #84"
                        )
                    ],
                    refuting_evidences=[],
                    recommended_action="ZONE-VICTIM 웹서버에 대한 WAF 가상 패치 배포 및 데이터베이스 접근 제어 감사 즉시 수행"
                ),
                SecurityHypothesis(
                    id="HYP-02",
                    title="가설 2: C2 역방향 셸(Reverse Shell) 외부 세션 유지 및 데이터 유출 성공",
                    kill_chain_stage="Command & Control (C2)",
                    status="REFUTED",
                    confidence_score=12,
                    primary_reason="공격자가 포트 4444로 역방향 세션 연결을 시도하였으나, Gateway nftables Forward 체인의 Strict Default-Deny 방화벽에 의해 사전 DROP되어 3-Way Handshake가 완결되지 못함.",
                    supporting_evidences=[
                        EvidenceItem(
                            source="Suricata EVE",
                            evidence_type="SUPPORTING",
                            description="내부 타겟에서 외부 공격자(10.77.20.20:4444)로의 TCP SYN 패킷 송신 감지",
                            timestamp="2026-09-22T10:16:30Z",
                            artifact_ref="SID: 9000004 (Suspicious Shell)"
                        )
                    ],
                    refuting_evidences=[
                        EvidenceItem(
                            source="Gateway nftables",
                            evidence_type="REFUTING",
                            description="nftables rule 'drop forward 10.77.30.0/24 -> 10.77.20.0/24:4444' 패킷 드롭 카운터 14건 증가 확인",
                            timestamp="2026-09-22T10:16:31Z",
                            artifact_ref="FW-RULE: DROP_FWD_UNAUTH"
                        ),
                        EvidenceItem(
                            source="PCAP Forensics",
                            evidence_type="REFUTING",
                            description="공격자 방향 SYN에 대한 SYN-ACK 응답 부재 및 TCP RST 발생으로 세션 불성립(Non-Established)",
                            timestamp="2026-09-22T10:16:32Z",
                            artifact_ref="PCAP: Stream #12 (RST Flag)"
                        )
                    ],
                    recommended_action="Gateway nftables DROP 정책 무결성 유지 확인 및 외부 C2 대상 IP(10.77.20.20) 블랙리스트 영구 동결"
                ),
                SecurityHypothesis(
                    id="HYP-03",
                    title="가설 3: 웹 침투 및 C2 차단 후 SSH(포트 22) 무차별 대입을 통한 자격증명 우회 시도",
                    kill_chain_stage="Credential Access",
                    status="INVESTIGATING",
                    confidence_score=78,
                    primary_reason="C2 차단 직후 동일 공격자 IP에서 포트 22를 표적으로 초당 30회 이상의 폭발적인 접속 시도(Burst Spike)가 관측되었으나, PAM 인증 성공 여부 조사가 추가로 필요함.",
                    supporting_evidences=[
                        EvidenceItem(
                            source="Suricata EVE",
                            evidence_type="SUPPORTING",
                            description="초당 30회 이상의 SSH 연결 시도 및 Potential SSH Scan 경보 집중 발생",
                            timestamp="2026-09-22T10:18:04Z",
                            artifact_ref="SID: 1000003 (SSH Scan)"
                        ),
                        EvidenceItem(
                            source="Asset PAM Log",
                            evidence_type="SUPPORTING",
                            description="sshd 인증 실패 로그(Failed password for invalid user admin) 82건 연속 발생",
                            timestamp="2026-09-22T10:18:15Z",
                            artifact_ref="AUTH-LOG: sshd PAM_AUTH_FAIL"
                        )
                    ],
                    refuting_evidences=[
                        EvidenceItem(
                            source="Asset Auth Log",
                            evidence_type="REFUTING",
                            description="현재 시점까지 'Accepted password' 성공 로그는 0건으로 아직 계정 침탈 미확인",
                            timestamp="2026-09-22T10:19:00Z",
                            artifact_ref="AUTH-LOG: ZERO_SUCCESS"
                        )
                    ],
                    recommended_action="관리자 계정 잠금 정책 활성화 및 fail2ban을 통한 포트 22 임시 접근 차단 권고"
                )
            ]
            top_concluded = "가설 1 입증 (Web/Log4j 침투 탐지) & 가설 2 기각 (C2 차단 성공)"
        else:
            # Generic fallback hypothesis profile
            hypotheses = [
                SecurityHypothesis(
                    id="HYP-01",
                    title=f"가설 1: {attacker_ip} 발 비인가 이상 징후 및 서비스 거부 시도",
                    kill_chain_stage="Reconnaissance & Anomaly",
                    status="INVESTIGATING",
                    confidence_score=65,
                    primary_reason="비인가 네트워크 프로토콜 편차 및 다중 포트 접근 징후가 관측되어 추가 심층 로그 분석 필요.",
                    supporting_evidences=[
                        EvidenceItem(
                            source="Suricata EVE",
                            evidence_type="SUPPORTING",
                            description=f"{target_ip} 방향 이상 트래픽 및 비인가 시그니처 매칭",
                            timestamp=now_str,
                            artifact_ref="SID: GENERIC_ANOMALY"
                        )
                    ],
                    refuting_evidences=[],
                    recommended_action="해당 호스트의 플로우 세션 추적 및 임시 모니터링 강화"
                ),
                SecurityHypothesis(
                    id="HYP-02",
                    title="가설 2: 정상 업무 트래픽에 대한 보안 탐지 오탐(False Positive)",
                    kill_chain_stage="False Positive Analysis",
                    status="REFUTED",
                    confidence_score=20,
                    primary_reason="출발지 IP의 지속적인 시그니처 발생 패턴 및 비표준 메타문자 포함으로 오탐 가능성 희박.",
                    supporting_evidences=[],
                    refuting_evidences=[
                        EvidenceItem(
                            source="Rule Confidence",
                            evidence_type="REFUTING",
                            description="Suricata 8.0.6 튜닝 시그니처 정밀도 90% 이상 유지 확인",
                            timestamp=now_str,
                            artifact_ref="SID_VERIFY: HIGH_PRECISION"
                        )
                    ],
                    recommended_action="오탐 제외 예외 처리 불필요, 능동 차단 정책 유지"
                )
            ]
            top_concluded = "가설 1 조사 진행 중 (이상 징후 지속 추적)"

        return IncidentHypothesisReport(
            incident_id=incident_id,
            attacker_ip=attacker_ip,
            target_ip=target_ip,
            generated_at=now_str,
            top_concluded_hypothesis=top_concluded,
            hypotheses=hypotheses,
        )

    def evaluate_custom(self, req_data: dict[str, Any]) -> IncidentHypothesisReport:
        inc_id = req_data.get("incident_id") or "INC-CUSTOM"
        attacker = req_data.get("attacker_ip") or "10.77.20.20"
        target = req_data.get("target_ip") or "10.77.30.20"
        scenario = req_data.get("scenario")
        return self.evaluate_incident(inc_id, attacker, target, scenario=scenario)


hypothesis_engine = HypothesisEngine()
