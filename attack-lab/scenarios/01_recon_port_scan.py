"""
Scenario 01: Reconnaissance & Port Scan Attack Simulation
Triggers:
- Nmap NULL Scan (sid: 1000101 / 2000020)
- Nmap XMAS Scan (sid: 1000102 / 2000021)
- Nmap FIN Scan (sid: 1000103 / 2000022)
- ICMP Ping Sweep (sid: 1000301 / 2000001)
"""

import sys
import time
from scapy.all import IP, TCP, ICMP, send


def run_recon_scans(target_ip: str = "127.0.0.1"):
    print(f"[*] Starting Reconnaissance & Stealth Port Scans against {target_ip}...")

    # 1. ICMP Ping Sweep
    print(" -> Sending ICMP Ping requests...")
    pkt_ping = IP(dst=target_ip) / ICMP()
    send(pkt_ping, count=3, verbose=0)
    time.sleep(0.5)

    # 2. Stealth NULL Scan (Flags = 0)
    print(" -> Sending TCP Stealth NULL Scans...")
    for port in [21, 22, 80, 443, 3306, 8080]:
        pkt_null = IP(dst=target_ip) / TCP(dport=port, flags="")
        send(pkt_null, verbose=0)
    time.sleep(0.5)

    # 3. Stealth XMAS Scan (Flags = FPU)
    print(" -> Sending TCP Stealth XMAS Scans (FIN, PSH, URG)...")
    for port in [22, 80, 8080]:
        pkt_xmas = IP(dst=target_ip) / TCP(dport=port, flags="FPU")
        send(pkt_xmas, verbose=0)
    time.sleep(0.5)

    # 4. Stealth FIN Scan (Flags = F)
    print(" -> Sending TCP Stealth FIN Scans...")
    for port in [80, 443]:
        pkt_fin = IP(dst=target_ip) / TCP(dport=port, flags="F")
        send(pkt_fin, verbose=0)

    print("[+] Reconnaissance scan simulation complete!")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    run_recon_scans(target)
