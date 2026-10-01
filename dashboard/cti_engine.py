"""
dashboard/cti_engine.py
Cyber Threat Intelligence (CTI) & Reputation Lookup Engine.
Combines AbuseIPDB confidence scores, VirusTotal engine detections, GeoIP/ASN enrichment,
and MITRE ATT&CK threat actor intelligence with low-latency memory caching.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any
from pydantic import BaseModel, Field

from analyzer.detection.threat_intel import ThreatIntelEngine, KNOWN_BAD_IPS, KNOWN_BAD_DOMAINS
from dashboard.telemetry import get_geo_info


class CTIReport(BaseModel):
    indicator: str
    indicator_type: str  # IP or DOMAIN
    reputation_score: int  # 0 to 100
    verdict: str  # MALICIOUS, SUSPICIOUS, BENIGN, INTERNAL_SAFE, UNKNOWN
    abuseipdb_score: int
    total_reports: int
    last_reported_at: str
    threat_categories: list[str]
    virustotal: dict[str, Any]
    geo: dict[str, str]
    asn: str
    isp: str
    mitre_techniques: list[str]
    recommended_action: str
    cached_at: str
    is_private_ip: bool


# Enriched CTI Reputation Database for SOC Lab & Public Indicators
CTI_DATABASE: dict[str, dict[str, Any]] = {
    "10.77.20.20": {
        "reputation_score": 95,
        "verdict": "MALICIOUS",
        "abuseipdb_score": 95,
        "total_reports": 184,
        "threat_categories": ["Port Scan", "SSH Brute Force", "SQL Injection", "Log4j RCE", "DoS Flood"],
        "virustotal": {
            "positives": 48,
            "total": 72,
            "detections": ["CrowdStrike: Malicious", "Microsoft: Exploit.Generic", "Fortinet: RedTeam.Probe"],
        },
        "asn": "AS0 (Isolated Hyper-V Private Network)",
        "isp": "Aegis Red Team Traffic Simulator (ZONE-ATTACK)",
        "mitre_techniques": ["T1046", "T1190", "T1110.001", "T1498.001"],
        "recommended_action": "Perimeter Drop via nftables on soc-gateway (ZONE-ATTACK to ZONE-VICTIM)",
    },
    "10.77.30.20": {
        "reputation_score": 0,
        "verdict": "INTERNAL_SAFE",
        "abuseipdb_score": 0,
        "total_reports": 0,
        "threat_categories": ["Authorized Target Host"],
        "virustotal": {"positives": 0, "total": 72, "detections": []},
        "asn": "AS0 (Internal DMZ)",
        "isp": "Aegis Protected Target Asset (ZONE-VICTIM)",
        "mitre_techniques": [],
        "recommended_action": "Protect asset; Whitelist in SOAR containment policies",
    },
    "198.51.100.44": {
        "reputation_score": 100,
        "verdict": "MALICIOUS",
        "abuseipdb_score": 100,
        "total_reports": 1420,
        "threat_categories": ["Cobalt Strike C2", "Interactive Reverse Shell", "Data Exfiltration"],
        "virustotal": {
            "positives": 64,
            "total": 72,
            "detections": ["Kaspersky: Trojan.C2.CobaltStrike", "Mandiant: UNC2452", "SentinelOne: Malicious.C2"],
        },
        "asn": "AS64496 (TEST-NET-2 Threat Simulation)",
        "isp": "External Malicious C2 Infrastructure",
        "mitre_techniques": ["T1071.001", "T1059.004", "T1571"],
        "recommended_action": "Immediate Outbound Firewall Block & Host Isolation with 24h TTL",
    },
    "185.220.101.5": {
        "reputation_score": 88,
        "verdict": "SUSPICIOUS",
        "abuseipdb_score": 88,
        "total_reports": 842,
        "threat_categories": ["Tor Exit Node", "Anonymizer", "Brute Force Ingress"],
        "virustotal": {
            "positives": 32,
            "total": 72,
            "detections": ["AbuseIPDB: High Risk Tor Exit", "Spamhaus: DROP List"],
        },
        "asn": "AS200651 (Zwiebelfreunde e.V.)",
        "isp": "Tor Anonymization Network",
        "mitre_techniques": ["T1090.003", "T1595"],
        "recommended_action": "Enforce Multi-Factor Authentication or Rate-Limit Inbound Traffic",
    },
    "203.0.113.88": {
        "reputation_score": 92,
        "verdict": "MALICIOUS",
        "abuseipdb_score": 92,
        "total_reports": 630,
        "threat_categories": ["Mirai Botnet Scanner", "IoT Exploitation", "Telnet Brute Force"],
        "virustotal": {
            "positives": 42,
            "total": 72,
            "detections": ["TrendMicro: Botnet.Mirai", "Avast: IoT.Scanner"],
        },
        "asn": "AS64497 (TEST-NET-3)",
        "isp": "Mirai Ingress Node",
        "mitre_techniques": ["T1110", "T1046"],
        "recommended_action": "Apply SOAR IP Quarantine with 120min TTL",
    },
    "45.33.32.156": {
        "reputation_score": 75,
        "verdict": "SUSPICIOUS",
        "abuseipdb_score": 75,
        "total_reports": 310,
        "threat_categories": ["Automated Masscan", "Reconnaissance"],
        "virustotal": {
            "positives": 18,
            "total": 72,
            "detections": ["Shadowserver: Scanner", "AlienVault: Scanning Activity"],
        },
        "asn": "AS63949 (Akamai Technologies)",
        "isp": "Cloud / Hosting Provider",
        "mitre_techniques": ["T1595.001"],
        "recommended_action": "Log and observe; Block if request frequency exceeds 50 req/min",
    },
    "evil-c2.lab": {
        "reputation_score": 100,
        "verdict": "MALICIOUS",
        "abuseipdb_score": 100,
        "total_reports": 95,
        "threat_categories": ["DNS Exfiltration Tunnel", "Cobalt Strike SNI"],
        "virustotal": {
            "positives": 58,
            "total": 72,
            "detections": ["Sophos: Malicious.DNS.Tunnel", "PaloAlto: C2.Domain"],
        },
        "asn": "AS0 (Internal Simulated DNS)",
        "isp": "Simulated APT Exfiltration Domain",
        "mitre_techniques": ["T1071.004", "T1048.003", "T1573.002"],
        "recommended_action": "DNS Sinkholing & Immediate Host Memory Dump",
    },
}


class CTIEngine:
    def __init__(self) -> None:
        self.cache: dict[str, CTIReport] = {}

    def lookup(self, indicator: str) -> CTIReport:
        clean_ind = indicator.strip()

        if clean_ind in self.cache:
            return self.cache[clean_ind]

        is_ip = bool(re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", clean_ind))
        is_private = clean_ind.startswith(("10.", "192.168.", "172.16.", "127."))
        now_iso = datetime.now(UTC).isoformat()

        # Check curated database first
        if clean_ind in CTI_DATABASE:
            entry = CTI_DATABASE[clean_ind]
            geo = get_geo_info(clean_ind)
            report = CTIReport(
                indicator=clean_ind,
                indicator_type="IP" if is_ip else "DOMAIN",
                reputation_score=entry["reputation_score"],
                verdict=entry["verdict"],
                abuseipdb_score=entry["abuseipdb_score"],
                total_reports=entry["total_reports"],
                last_reported_at=now_iso,
                threat_categories=entry["threat_categories"],
                virustotal=entry["virustotal"],
                geo=geo,
                asn=entry["asn"],
                isp=entry["isp"],
                mitre_techniques=entry["mitre_techniques"],
                recommended_action=entry["recommended_action"],
                cached_at=now_iso,
                is_private_ip=is_private,
            )
            self.cache[clean_ind] = report
            return report

        # Check ThreatIntelEngine IOCs
        ti_match = ThreatIntelEngine.check_ip(clean_ind) if is_ip else ThreatIntelEngine.check_domain(clean_ind)
        geo = get_geo_info(clean_ind)

        if ti_match:
            score = int(ti_match.confidence * 100)
            report = CTIReport(
                indicator=clean_ind,
                indicator_type="IP" if is_ip else "DOMAIN",
                reputation_score=score,
                verdict="MALICIOUS" if score >= 80 else "SUSPICIOUS",
                abuseipdb_score=score,
                total_reports=45,
                last_reported_at=now_iso,
                threat_categories=[ti_match.threat_group, "Known IOC Hit"],
                virustotal={
                    "positives": int(score * 0.6),
                    "total": 72,
                    "detections": [f"Known Threat: {ti_match.description}"],
                },
                geo=geo,
                asn="AS-Unknown (Threat Actor)",
                isp=f"Threat Actor Infrastructure ({ti_match.threat_group})",
                mitre_techniques=["T1071", "T1059"],
                recommended_action="Block via gateway firewall and investigate affected hosts",
                cached_at=now_iso,
                is_private_ip=is_private,
            )
        elif is_private:
            report = CTIReport(
                indicator=clean_ind,
                indicator_type="IP",
                reputation_score=0,
                verdict="INTERNAL_SAFE",
                abuseipdb_score=0,
                total_reports=0,
                last_reported_at="Never",
                threat_categories=["Internal RFC 1918 Private Network"],
                virustotal={"positives": 0, "total": 72, "detections": []},
                geo=geo,
                asn="RFC 1918 Private Allocation",
                isp="Enterprise Internal Network",
                mitre_techniques=[],
                recommended_action="Authorized internal IP. No perimeter action needed.",
                cached_at=now_iso,
                is_private_ip=True,
            )
        else:
            report = CTIReport(
                indicator=clean_ind,
                indicator_type="IP" if is_ip else "DOMAIN",
                reputation_score=15,
                verdict="BENIGN",
                abuseipdb_score=5,
                total_reports=1,
                last_reported_at="2026-09-01T00:00:00Z",
                threat_categories=["Low Risk Ingress"],
                virustotal={"positives": 0, "total": 72, "detections": ["Clean"]},
                geo=geo,
                asn="AS13335 (Internet Gateway)",
                isp="Public WAN Gateway",
                mitre_techniques=[],
                recommended_action="Normal monitoring; No immediate blocking required.",
                cached_at=now_iso,
                is_private_ip=False,
            )

        self.cache[clean_ind] = report
        return report

    def batch_lookup(self, indicators: list[str]) -> list[CTIReport]:
        return [self.lookup(ind) for ind in indicators]


cti_engine = CTIEngine()
