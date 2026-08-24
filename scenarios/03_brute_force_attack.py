"""
Scenario 03: SSH & Web Authentication Brute Force Attack
Triggers:
- SSH Brute Force High Frequency Connection (sid: 1000120)
"""

import sys
import time
import socket


def run_ssh_brute_force(target_ip: str = "127.0.0.1", port: int = 22, attempts: int = 10):
    print(f"[*] Simulating High-Frequency SSH Brute Force against {target_ip}:{port} ({attempts} connections)...")

    for i in range(1, attempts + 1):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            s.connect((target_ip, port))
            # Send fake SSH authentication attempt
            s.sendall(b"SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.6\r\n")
            s.close()
            print(f"  -> Attempt {i}/{attempts} sent")
        except Exception:
            pass
        time.sleep(0.1)

    print("[+] SSH brute force scenario completed!")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    run_ssh_brute_force(target)
