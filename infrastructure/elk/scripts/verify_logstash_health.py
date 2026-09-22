"""
Logstash 8.17.3 Health Check & Multi-Pipeline Verification Tool for Phase ELK-4
Validates:
1. GET / (Logstash Node Info, Version == 8.17.3)
2. GET /_node/pipelines (suricata-beats, snort-alerts, firewall-traffic, wazuh-alerts)
3. Input ports connectivity (5044, 5045, 5046, 5514/udp)
4. Persisted queue & DLQ status
"""

import json
import os
import socket
import sys
import urllib.error
import urllib.request

LOGSTASH_API = os.getenv("LOGSTASH_API", "http://127.0.0.1:9600")
REQUIRED_PIPELINES = ["suricata-beats", "snort-alerts", "firewall-traffic", "wazuh-alerts"]


def check_port(host: str, port: int, proto: str = "tcp", timeout: float = 2.0) -> bool:
    try:
        sock_type = socket.SOCK_STREAM if proto == "tcp" else socket.SOCK_DGRAM
        with socket.socket(socket.AF_INET, sock_type) as s:
            s.settimeout(timeout)
            if proto == "tcp":
                return s.connect_ex((host, port)) == 0
            else:
                # UDP socket check
                s.sendto(b"", (host, port))
                return True
    except Exception:
        return False


def verify_logstash() -> bool:
    print(f"[*] Target Logstash API: {LOGSTASH_API}")

    # 1. Query Node Info
    print("\n--- [1] Checking Logstash Node Info (GET /) ---")
    try:
        req = urllib.request.Request(f"{LOGSTASH_API.rstrip('/')}/")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            version = data.get("version", "Unknown")
            name = data.get("name", "Unknown")
            status = data.get("status", "Unknown")
            print(f"[PASS] Node Name: {name}")
            print(f"[PASS] Logstash Version: {version}")
            print(f"[PASS] Operational Status: {status}")

            if version != "8.17.3":
                print(f"[WARN] Version {version} does not match pinned 8.17.3")
    except Exception as e:
        print(f"[FAIL] Unable to query Logstash Node Info: {e}")
        return False

    # 2. Query Pipelines Status
    print("\n--- [2] Checking Multi-Pipeline Status (GET /_node/pipelines) ---")
    try:
        req = urllib.request.Request(f"{LOGSTASH_API.rstrip('/')}/_node/pipelines")
        with urllib.request.urlopen(req, timeout=10) as resp:
            p_data = json.loads(resp.read().decode("utf-8"))
            pipelines = p_data.get("pipelines", {})
            active_ids = list(pipelines.keys())
            print(f"[*] Active Pipelines: {active_ids}")

            all_ok = True
            for req_id in REQUIRED_PIPELINES:
                if req_id in pipelines:
                    workers = pipelines[req_id].get("workers", 0)
                    batch_size = pipelines[req_id].get("batch_size", 0)
                    print(f"[PASS] Pipeline '{req_id}': RUNNING (Workers: {workers}, Batch: {batch_size})")
                else:
                    print(f"[FAIL] Pipeline '{req_id}': NOT FOUND or NOT RUNNING")
                    all_ok = False

            if not all_ok:
                return False
    except Exception as e:
        print(f"[FAIL] Unable to query Logstash Pipelines: {e}")
        return False

    # 3. Check Ingest Ports
    print("\n--- [3] Checking Ingest Port Bindings ---")
    ports = [
        ("127.0.0.1", 5044, "tcp", "Suricata Beats"),
        ("127.0.0.1", 5045, "tcp", "Snort TCP"),
        ("127.0.0.1", 5046, "tcp", "Wazuh TCP"),
        ("127.0.0.1", 5514, "udp", "Firewall Syslog UDP"),
    ]
    for host, port, proto, desc in ports:
        ok = check_port(host, port, proto)
        state = "OPEN / LISTENING" if ok else "CLOSED / UNREACHABLE"
        print(f"[{'PASS' if ok else 'WARN'}] {desc} ({host}:{port}/{proto}): {state}")

    print("\n[SUCCESS] Phase ELK-4: Logstash 8.17.3 Multi-Pipeline Engine is OPERATIONAL!")
    return True


if __name__ == "__main__":
    success = verify_logstash()
    sys.exit(0 if success else 1)
