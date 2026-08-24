from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any
from pydantic import BaseModel, Field

from analyzer.models import NormalizedAlert, Severity


class Incident(BaseModel):
    incident_id: str
    src_ip: str
    target_ips: list[str]
    attack_stages: list[str]
    alerts: list[NormalizedAlert]
    start_time: datetime
    last_seen: datetime
    highest_severity: Severity
    verdict: str
    playbook_ref: str | None = None


class CorrelationEngine:
    def __init__(self, window_minutes: int = 30):
        self.window = timedelta(minutes=window_minutes)
        self.ip_sessions: dict[str, list[NormalizedAlert]] = defaultdict(list)

    def classify_stage(self, alert: NormalizedAlert) -> str:
        sig = alert.signature.upper()
        if any(k in sig for k in ["SCAN", "RECON", "NULL", "XMAS", "FIN", "NIKTO", "DIRBUSTER", "PING"]):
            return "1. Reconnaissance"
        elif any(k in sig for k in ["SQL INJECTION", "XSS", "TRAVERSAL", "BRUTE FORCE", "LOG4J"]):
            return "2. Initial Access / Exploitation"
        elif any(k in sig for k in ["REVERSE SHELL", "METERPRETER", "COBALT", "BEACON", "TUNNELING"]):
            return "3. Command & Control / Execution"
        elif any(k in sig for k in ["EXFILTRATION", "CREDIT CARD", "LEAK"]):
            return "4. Exfiltration"
        return "Generic Security Activity"

    def process_alert(self, alert: NormalizedAlert) -> Incident | None:
        src = alert.src_ip
        now = alert.timestamp

        # Add to window
        self.ip_sessions[src].append(alert)
        # Expire older alerts
        self.ip_sessions[src] = [
            a for a in self.ip_sessions[src] if now - a.timestamp <= self.window
        ]

        alerts = self.ip_sessions[src]
        stages = list(sorted(set(self.classify_stage(a) for a in alerts)))
        
        # If at least 2 distinct attack stages or Critical severity alert detected -> Correlate as Incident
        if len(stages) >= 2 or any(a.severity == Severity.CRITICAL for a in alerts):
            severities = [a.severity for a in alerts]
            highest = Severity.CRITICAL if Severity.CRITICAL in severities else (
                Severity.HIGH if Severity.HIGH in severities else Severity.MEDIUM
            )
            
            targets = list(set(a.dst_ip for a in alerts))
            
            playbook = None
            if "3. Command & Control / Execution" in stages:
                playbook = "playbooks/04_malware_c2_investigation.md"
            elif "2. Initial Access / Exploitation" in stages:
                playbook = "playbooks/03_web_attack_investigation.md"
            elif "1. Reconnaissance" in stages:
                playbook = "playbooks/01_port_scan_investigation.md"

            verdict = (
                f"Multi-Stage Attack Chain Detected: {' -> '.join(stages)} "
                f"from {src} targeting {len(targets)} internal host(s)."
            )

            return Incident(
                incident_id=f"INC-{src}-{int(now.timestamp())}",
                src_ip=src,
                target_ips=targets,
                attack_stages=stages,
                alerts=alerts,
                start_time=alerts[0].timestamp,
                last_seen=alerts[-1].timestamp,
                highest_severity=highest,
                verdict=verdict,
                playbook_ref=playbook,
            )

        return None
