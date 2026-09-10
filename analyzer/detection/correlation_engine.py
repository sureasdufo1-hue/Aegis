from collections import defaultdict
from datetime import datetime, timedelta

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
    activity_status: str = Field(default="SUSPICIOUS_ATTEMPT", description="ATTEMPT vs CONFIRMED_COMPROMISE")


class CorrelationEngine:
    def __init__(self, window_minutes: int = 30):
        self.window = timedelta(minutes=window_minutes)
        self.ip_sessions: dict[str, list[NormalizedAlert]] = defaultdict(list)

    def classify_stage(self, alert: NormalizedAlert) -> str:
        """
        Classifies an alert into Cyber Kill Chain stages using SID/technique metadata first,
        falling back to signature keyword analysis. Non-malicious diagnostic telemetry (Ping)
        is classified as Diagnostic and never escalates to an attack incident.
        """
        sid = alert.sid
        sig = alert.signature.upper()
        mitre = (alert.mitre_technique or "").upper()

        # 1. Non-attack diagnostic telemetry
        if sid in [9000020, 9100001] or ("PING" in sig and "FLOOD" not in sig and "SWEEP" not in sig and "ATTACK" not in sig):
            return "Diagnostic / Telemetry"

        # 2. Official SID / Technique / Category Allocations
        if (9000001 <= sid <= 9009999 or 9100020 <= sid <= 9100029 or sid in [9000021, 9100002] or 
                "T1046" in mitre or "T1595" in mitre or "T1498" in mitre):
            return "1. Reconnaissance"
        elif (9010000 <= sid <= 9029999 or 9100010 <= sid <= 9100019 or 
                "T1190" in mitre or "T1189" in mitre or "T1083" in mitre or "T1110" in mitre or
                any(k in sig for k in ["SQL INJECTION", "XSS", "TRAVERSAL", "BRUTE FORCE", "LOG4J"])):
            return "2. Initial Access / Exploitation"
        elif (9030010 <= sid <= 9039999 or 9100030 <= sid <= 9100039 or 
                "T1059" in mitre or "T1571" in mitre or "T1071.001" in mitre or
                any(k in sig for k in ["REVERSE SHELL", "METERPRETER", "COBALT", "BEACON"])):
            return "3. Command & Control / Execution"
        elif (9030001 <= sid <= 9030009 or "T1048" in mitre or "T1071.004" in mitre or
                any(k in sig for k in ["EXFILTRATION", "CREDIT CARD", "LEAK", "TUNNELING"])):
            return "4. Exfiltration"

        # 3. Fallback Heuristics on Signature text (strictly excluding bare 'PING')
        if any(k in sig for k in ["SCAN", "RECON", "NULL", "XMAS", "FIN", "NIKTO", "DIRBUSTER", "FLOOD"]):
            return "1. Reconnaissance"
        elif any(k in sig for k in ["SQL", "INJECTION", "EXPLOIT"]):
            return "2. Initial Access / Exploitation"
        elif any(k in sig for k in ["SHELL"]):
            return "3. Command & Control / Execution"

        return "Generic Security Activity"

    def process_alert(self, alert: NormalizedAlert) -> Incident | None:
        src = alert.src_ip
        now = alert.timestamp

        # Add to sliding window
        self.ip_sessions[src].append(alert)
        # Expire older alerts
        self.ip_sessions[src] = [
            a for a in self.ip_sessions[src] if now - a.timestamp <= self.window
        ]

        alerts = self.ip_sessions[src]
        
        # Classify stages, filtering out non-attack diagnostic events
        classified_stages = [self.classify_stage(a) for a in alerts]
        actionable_stages = sorted(set(
            s for s in classified_stages 
            if s not in ["Diagnostic / Telemetry", "Generic Security Activity"]
        ))
        
        # Escalation criteria:
        # 1. At least 2 distinct actionable attack stages, OR
        # 2. Any alert with CRITICAL severity that is an actionable attack stage
        has_critical = any(
            a.severity == Severity.CRITICAL for a in alerts 
            if self.classify_stage(a) not in ["Diagnostic / Telemetry", "Generic Security Activity"]
        )

        # 3. Cross-correlation: Connection Anomaly / Auth Failures followed by Auth Success
        has_auth_success = any(
            ("AUTHENTICATION SUCCESS" in a.signature.upper() or "ACCEPTED PASSWORD" in a.signature.upper() or a.sid == 5715)
            for a in alerts
        )
        has_brute_or_anomaly = any(
            ("BRUTE" in a.signature.upper() or "CONNECTION THRESHOLD" in a.signature.upper() or a.sid in [9020001, 5710, 5716, 5720])
            for a in alerts
        )
        has_auth_takeover = has_auth_success and has_brute_or_anomaly

        if len(actionable_stages) >= 2 or has_critical or has_auth_takeover:
            severities = [a.severity for a in alerts]
            highest = Severity.CRITICAL if (Severity.CRITICAL in severities or has_auth_takeover) else (
                Severity.HIGH if Severity.HIGH in severities else Severity.MEDIUM
            )
            
            targets = list(set(a.dst_ip for a in alerts))
            
            # Map Playbook
            playbook = None
            if "3. Command & Control / Execution" in actionable_stages or "4. Exfiltration" in actionable_stages:
                playbook = "playbooks/04_malware_c2_investigation.md"
            elif "2. Initial Access / Exploitation" in actionable_stages:
                # Distinguish web attack vs SSH brute force if possible
                if any("SSH" in a.signature.upper() or "BRUTE" in a.signature.upper() for a in alerts):
                    playbook = "playbooks/05_ssh_brute_force_investigation.md"
                else:
                    playbook = "playbooks/03_web_attack_investigation.md"
            elif "1. Reconnaissance" in actionable_stages:
                playbook = "playbooks/01_port_scan_investigation.md"

            # Determine Activity Status (Attempt vs Confirmed)
            has_auth_success = any(
                ("AUTHENTICATION SUCCESS" in a.signature.upper() or "ACCEPTED PASSWORD" in a.signature.upper() or a.sid == 5715)
                for a in alerts
            )
            has_brute_or_anomaly = any(
                ("BRUTE" in a.signature.upper() or "CONNECTION THRESHOLD" in a.signature.upper() or a.sid in [9020001, 5710, 5716, 5720])
                for a in alerts
            )

            is_confirmed = any(
                "3. Command & Control / Execution" in s or "4. Exfiltration" in s 
                for s in actionable_stages
            )

            if has_auth_success and has_brute_or_anomaly:
                is_confirmed = True
                highest = Severity.CRITICAL
                status = "CONFIRMED_COMPROMISE"
                status_text = "Confirmed Account Takeover (Brute Force Followed by Successful Login)"
                playbook = "playbooks/05_ssh_brute_force_investigation.md"
            else:
                status = "CONFIRMED_COMPROMISE" if is_confirmed else "SUSPICIOUS_ATTEMPT"
                status_text = "Confirmed Post-Exploitation Activity" if is_confirmed else "Suspicious Multi-Stage Exploit Attempt"

            verdict = (
                f"{status_text} Detected: {' -> '.join(actionable_stages)} "
                f"from {src} targeting {len(targets)} internal host(s)."
            )

            return Incident(
                incident_id=f"INC-{src}-{int(now.timestamp())}",
                src_ip=src,
                target_ips=targets,
                attack_stages=actionable_stages,
                alerts=alerts,
                start_time=alerts[0].timestamp,
                last_seen=alerts[-1].timestamp,
                highest_severity=highest,
                verdict=verdict,
                playbook_ref=playbook,
                activity_status=status,
            )

        return None
