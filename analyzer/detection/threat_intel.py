from typing import Any
from pydantic import BaseModel


class ThreatIntelMatch(BaseModel):
    indicator: str
    indicator_type: str  # IP, DOMAIN, HASH
    threat_group: str
    confidence: float
    description: str


# Sample IOCs for Lab Practice
KNOWN_BAD_IPS = {
    "198.51.100.44": ("CobaltStrike_C2", 0.95, "Active Cobalt Strike Command & Control Server"),
    "203.0.113.88": ("Mirai_Botnet", 0.90, "Mirai Botnet Scanner & Brute Force Source"),
    "45.33.32.156": ("Masscan_Automated", 0.85, "Internet-wide Scanner Host"),
    "185.220.101.5": ("Tor_Exit_Node", 0.80, "Tor Anonymization Network Exit Node"),
}

KNOWN_BAD_DOMAINS = {
    "evil-c2.lab": ("APT_Exfil", 0.98, "Simulated DNS Data Exfiltration Tunnel Domain"),
    "miner.cryptopool.xyz": ("CoinMiner", 0.90, "Cryptocurrency Mining Pool Connection"),
}


class ThreatIntelEngine:
    @staticmethod
    def check_ip(ip: str) -> ThreatIntelMatch | None:
        if ip in KNOWN_BAD_IPS:
            group, conf, desc = KNOWN_BAD_IPS[ip]
            return ThreatIntelMatch(
                indicator=ip,
                indicator_type="IP",
                threat_group=group,
                confidence=conf,
                description=desc,
            )
        return None

    @staticmethod
    def check_domain(domain: str) -> ThreatIntelMatch | None:
        if domain in KNOWN_BAD_DOMAINS:
            group, conf, desc = KNOWN_BAD_DOMAINS[domain]
            return ThreatIntelMatch(
                indicator=domain,
                indicator_type="DOMAIN",
                threat_group=group,
                confidence=conf,
                description=desc,
            )
        return None
