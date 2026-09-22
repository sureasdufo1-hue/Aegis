#!/usr/bin/env python3
"""
verify_wazuh_ingest.py
Validates Wazuh SIEM Alerts ingestion into Logstash (TCP 5046 / File)
and indexing into Elasticsearch (logs-wazuh.alert-default) with 100% ECS compliance.
"""

import sys
import time
import socket
import json
import base64
import urllib.request
import urllib.error

ELASTICSEARCH_URL = "http://127.0.0.1:9201"
LOGSTASH_TCP_HOST = "127.0.0.1"
LOGSTASH_TCP_PORT = 5046
INDEX_NAME = "logs-wazuh.alert-default"
AUTH_HEADER = "Basic " + base64.b64encode(b"elastic:changeme_soc_lab_strong_pass_2026").decode()

# Representative Wazuh SIEM alerts generated in SOC Detection & Monitoring Lab
WAZUH_TEST_ALERTS = [
    # 1. Reconnaissance Scan (Rule 100101, Level 6 -> ECS Severity 2)
    {
        "timestamp": "2026-09-22T10:15:40.100+0000",
        "rule": {
            "level": 6,
            "description": "SOC-RECON: Network Scanning & Reconnaissance Detected [Nmap NULL/XMAS Scan] from 10.77.20.20",
            "id": "100101",
            "mitre": {
                "id": ["T1046"],
                "tactic": ["Discovery"],
                "technique": ["Network Service Discovery"]
            },
            "groups": ["suricata", "ids", "soc_recon"]
        },
        "agent": {"id": "001", "name": "soc-victim", "ip": "10.77.30.20"},
        "manager": {"name": "soc-wazuh-manager"},
        "id": "1726998940.10001",
        "full_log": "SOC-RECON: Network Scanning & Reconnaissance Detected from 10.77.20.20",
        "data": {
            "srcip": "10.77.20.20",
            "srcport": "49152",
            "dstip": "10.77.30.20",
            "dstport": "80"
        },
        "location": "suricata-eve"
    },
    # 2. Web Application Exploitation (Rule 100102, Level 10 -> ECS Severity 3)
    {
        "timestamp": "2026-09-22T10:15:41.200+0000",
        "rule": {
            "level": 10,
            "description": "SOC-WEB: Web Application Attack Exploitation Attempt [SQL Injection UNION SELECT] targeting 10.77.30.20:80",
            "id": "100102",
            "mitre": {
                "id": ["T1190"],
                "tactic": ["Initial Access"],
                "technique": ["Exploit Public-Facing Application"]
            },
            "groups": ["suricata", "ids", "soc_web"]
        },
        "agent": {"id": "001", "name": "soc-victim", "ip": "10.77.30.20"},
        "manager": {"name": "soc-wazuh-manager"},
        "id": "1726998941.10002",
        "full_log": "GET /rest/products/search?q=1'%20UNION%20SELECT%20null,email,password%20FROM%20users-- HTTP/1.1",
        "data": {
            "srcip": "10.77.20.20",
            "srcport": "49153",
            "dstip": "10.77.30.20",
            "dstport": "80"
        },
        "location": "suricata-eve"
    },
    # 3. SSH Brute Force Authentication Attempt (Rule 100103, Level 8 -> ECS Severity 3)
    {
        "timestamp": "2026-09-22T10:15:42.300+0000",
        "rule": {
            "level": 8,
            "description": "SOC-AUTH: High-Frequency Brute Force Authentication Attempt [SSH Password Guessing]",
            "id": "100103",
            "mitre": {
                "id": ["T1110"],
                "tactic": ["Credential Access"],
                "technique": ["Brute Force"]
            },
            "groups": ["suricata", "ids", "soc_auth"]
        },
        "agent": {"id": "001", "name": "soc-victim", "ip": "10.77.30.20"},
        "manager": {"name": "soc-wazuh-manager"},
        "id": "1726998942.10003",
        "full_log": "Failed password for root from 10.77.20.20 port 51234 ssh2",
        "data": {
            "srcip": "10.77.20.20",
            "srcport": "51234",
            "dstip": "10.77.30.20",
            "dstport": "22",
            "dstuser": "root"
        },
        "location": "/var/log/auth.log"
    },
    # 4. Host SSH Failure Event (Rule 5710, Level 5 -> ECS Severity 2)
    {
        "timestamp": "2026-09-22T10:15:43.400+0000",
        "rule": {
            "level": 5,
            "description": "sshd: Attempt to login using a non-existent user",
            "id": "5710",
            "mitre": {
                "id": ["T1110.001"],
                "tactic": ["Credential Access"],
                "technique": ["Password Guessing"]
            },
            "groups": ["syslog", "sshd", "authentication_failed"]
        },
        "agent": {"id": "001", "name": "soc-victim", "ip": "10.77.30.20"},
        "manager": {"name": "soc-wazuh-manager"},
        "id": "1726998943.10004",
        "full_log": "Sep 22 10:15:43 soc-victim sshd[14521]: Failed password for invalid user admin from 10.77.20.20 port 51235 ssh2",
        "data": {
            "srcip": "10.77.20.20",
            "srcport": "51235",
            "dstip": "10.77.30.20",
            "dstport": "22",
            "dstuser": "admin"
        },
        "location": "/var/log/auth.log"
    },
    # 5. Confirmed Cross-Correlation (Rule 100110, Level 11 -> ECS Severity 3)
    {
        "timestamp": "2026-09-22T10:15:44.500+0000",
        "rule": {
            "level": 11,
            "description": "SOC-CORRELATION: Confirmed SSH Brute Force - Network Anomaly Correlated with Host Auth Failures [10.77.20.20]",
            "id": "100110",
            "mitre": {
                "id": ["T1110", "T1110.001"],
                "tactic": ["Credential Access"],
                "technique": ["Brute Force", "Password Guessing"]
            },
            "groups": ["suricata", "ids", "soc_correlation"]
        },
        "agent": {"id": "001", "name": "soc-victim", "ip": "10.77.30.20"},
        "manager": {"name": "soc-wazuh-manager"},
        "id": "1726998944.10005",
        "full_log": "SOC-CORRELATION: High frequency network anomaly correlated with 5 host authentication failures from 10.77.20.20",
        "data": {
            "srcip": "10.77.20.20",
            "dstip": "10.77.30.20",
            "dstport": "22"
        },
        "location": "wazuh-analysis"
    },
    # 6. Critical Account Takeover (Rule 100111, Level 14 -> ECS Severity 4)
    {
        "timestamp": "2026-09-22T10:15:45.600+0000",
        "rule": {
            "level": 14,
            "description": "SOC-CRITICAL: Potential Account Takeover - Successful SSH Login Following Brute Force Anomaly [10.77.20.20]",
            "id": "100111",
            "mitre": {
                "id": ["T1110", "T1078"],
                "tactic": ["Initial Access", "Persistence"],
                "technique": ["Valid Accounts"]
            },
            "groups": ["suricata", "ids", "soc_critical"]
        },
        "agent": {"id": "001", "name": "soc-victim", "ip": "10.77.30.20"},
        "manager": {"name": "soc-wazuh-manager"},
        "id": "1726998945.10006",
        "full_log": "Sep 22 10:15:45 soc-victim sshd[14530]: Accepted password for root from 10.77.20.20 port 51240 ssh2",
        "data": {
            "srcip": "10.77.20.20",
            "srcport": "51240",
            "dstip": "10.77.30.20",
            "dstport": "22",
            "dstuser": "root"
        },
        "location": "/var/log/auth.log"
    },
    # 7. Critical Reverse Shell / C2 (Rule 100104, Level 13 -> ECS Severity 4)
    {
        "timestamp": "2026-09-22T10:15:46.700+0000",
        "rule": {
            "level": 13,
            "description": "SOC-CRITICAL: Active Malware C2 Communication / Reverse Shell Established [Interactive Shell Spawned]",
            "id": "100104",
            "mitre": {
                "id": ["T1071", "T1059.004"],
                "tactic": ["Command and Control", "Execution"],
                "technique": ["Application Layer Protocol", "Unix Shell"]
            },
            "groups": ["suricata", "ids", "soc_critical"]
        },
        "agent": {"id": "001", "name": "soc-victim", "ip": "10.77.30.20"},
        "manager": {"name": "soc-wazuh-manager"},
        "id": "1726998946.10007",
        "full_log": "SOC-CRITICAL: Interactive /bin/sh reverse connection established from 10.77.30.20:4444 to 10.77.20.20:4444",
        "data": {
            "srcip": "10.77.30.20",
            "srcport": "4444",
            "dstip": "10.77.20.20",
            "dstport": "4444"
        },
        "location": "suricata-eve"
    },
    # 8. Syscheck Integrity Alert / FIM (Rule 550, Level 7 -> ECS Severity 3)
    {
        "timestamp": "2026-09-22T10:15:47.800+0000",
        "rule": {
            "level": 7,
            "description": "Integrity checksum changed for: '/etc/shadow'",
            "id": "550",
            "mitre": {
                "id": ["T1078"],
                "tactic": ["Persistence"],
                "technique": ["Valid Accounts"]
            },
            "groups": ["syscheck", "fim"]
        },
        "agent": {"id": "001", "name": "soc-victim", "ip": "10.77.30.20"},
        "manager": {"name": "soc-wazuh-manager"},
        "id": "1726998947.10008",
        "full_log": "Integrity checksum changed for: '/etc/shadow' Size changed from 1240 to 1285",
        "syscheck": {
            "path": "/etc/shadow",
            "size_before": "1240",
            "size_after": "1285"
        },
        "location": "syscheck"
    },
    # 9. Sudo Elevation (Rule 5402, Level 3 -> ECS Severity 2)
    {
        "timestamp": "2026-09-22T10:15:48.900+0000",
        "rule": {
            "level": 3,
            "description": "Successful sudo to ROOT executed",
            "id": "5402",
            "mitre": {
                "id": ["T1548.003"],
                "tactic": ["Privilege Escalation"],
                "technique": ["Sudo and Sudo Caching"]
            },
            "groups": ["syslog", "sudo"]
        },
        "agent": {"id": "001", "name": "soc-victim", "ip": "10.77.30.20"},
        "manager": {"name": "soc-wazuh-manager"},
        "id": "1726998948.10009",
        "full_log": "Sep 22 10:15:48 soc-victim sudo: pam_unix(sudo:session): session opened for user root(uid=0) by (uid=1000)",
        "data": {
            "dstuser": "root"
        },
        "location": "/var/log/auth.log"
    },
    # 10. Web Directory Traversal / LFI (Rule 30103, Level 5 -> ECS Severity 2)
    {
        "timestamp": "2026-09-22T10:15:49.000+0000",
        "rule": {
            "level": 5,
            "description": "Apache: Attempt to access forbidden directory or path traversal",
            "id": "30103",
            "mitre": {
                "id": ["T1083"],
                "tactic": ["Discovery"],
                "technique": ["File and Directory Discovery"]
            },
            "groups": ["web", "apache", "access_log"]
        },
        "agent": {"id": "001", "name": "soc-victim", "ip": "10.77.30.20"},
        "manager": {"name": "soc-wazuh-manager"},
        "id": "1726998949.10010",
        "full_log": "GET /../../../../etc/passwd HTTP/1.1 403 492",
        "data": {
            "srcip": "10.77.20.20",
            "srcport": "49160",
            "dstip": "10.77.30.20",
            "dstport": "80"
        },
        "location": "/var/log/nginx/access.log"
    }
]


def stream_wazuh_alerts(alerts):
    print(f"[*] Streaming {len(alerts)} Wazuh alert events to TCP {LOGSTASH_TCP_HOST}:{LOGSTASH_TCP_PORT}...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(10)
    try:
        s.connect((LOGSTASH_TCP_HOST, LOGSTASH_TCP_PORT))
        for alert in alerts:
            line = json.dumps(alert) + "\n"
            s.sendall(line.encode("utf-8"))
            time.sleep(0.05)
        print(f"[PASS] Successfully sent {len(alerts)} Wazuh alert events.")
    finally:
        s.close()


def query_elasticsearch(path):
    url = f"{ELASTICSEARCH_URL}/{path}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": AUTH_HEADER,
            "Content-Type": "application/json"
        }
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def flush_elasticsearch():
    url = f"{ELASTICSEARCH_URL}/_refresh"
    req = urllib.request.Request(
        url,
        data=b"{}",
        headers={
            "Authorization": AUTH_HEADER,
            "Content-Type": "application/json"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status in (200, 201)
    except Exception:
        return False


def verify_ingestion():
    print(f"[*] Waiting for Logstash to process and index into {INDEX_NAME}...")
    max_wait = 25
    start_time = time.time()
    docs_found = 0

    while time.time() - start_time < max_wait:
        flush_elasticsearch()
        try:
            res = query_elasticsearch(f"{INDEX_NAME}/_search?size=50")
            hits = res.get("hits", {}).get("hits", [])
            docs_found = len(hits)
            if docs_found >= len(WAZUH_TEST_ALERTS):
                print(f"[PASS] Successfully retrieved {docs_found} documents from {INDEX_NAME}.")
                break
        except urllib.error.HTTPError as e:
            if e.code != 404:
                print(f"[WARN] HTTP Error: {e.code}")
        time.sleep(2)

    if docs_found == 0:
        print(f"[FAIL] No documents found in {INDEX_NAME} within timeout.")
        return False

    res = query_elasticsearch(f"{INDEX_NAME}/_search?size=50")
    hits = res.get("hits", {}).get("hits", [])

    print(f"[*] Verifying ECS normalization across {len(hits)} indexed Wazuh documents...")

    mandatory_fields = [
        "@timestamp",
        "event.module",
        "event.dataset",
        "event.kind",
        "event.category",
        "event.severity",
        "observer.name",
        "observer.type",
        "host.name",
        "rule.id",
        "rule.name",
        "threat.framework",
        "threat.technique.id"
    ]

    all_passed = True

    for idx, hit in enumerate(hits):
        src = hit["_source"]

        def get_nested(obj, path):
            parts = path.split(".")
            curr = obj
            for p in parts:
                if not isinstance(curr, dict) or p not in curr:
                    return None
                curr = curr[p]
            return curr

        # Check mandatory fields
        missing = []
        for f in mandatory_fields:
            if get_nested(src, f) is None:
                missing.append(f)

        if missing:
            print(f"[FAIL] Doc {idx+1} missing mandatory ECS fields: {missing}")
            all_passed = False
            continue

        rule_id = get_nested(src, "rule.id")
        rule_name = get_nested(src, "rule.name")
        severity = get_nested(src, "event.severity")
        technique = get_nested(src, "threat.technique.id")
        host_name = get_nested(src, "host.name")
        src_ip = get_nested(src, "source.ip")
        dst_ip = get_nested(src, "destination.ip")

        network_info = f"{src_ip}->{dst_ip}" if src_ip and dst_ip else (src_ip or "host-only")
        if idx < 5 or idx == len(hits) - 1:
            print(f"[PASS] Doc {idx+1}: rule='{rule_id}' sev={severity} tech={technique} host={host_name} ({network_info})")

    # Cluster health check
    health = query_elasticsearch("_cluster/health")
    status = health.get("status", "").upper()
    print(f"[*] Cluster Status: {status}")
    if status != "GREEN":
        print(f"[FAIL] Expected Cluster Status GREEN, found {status}")
        all_passed = False
    else:
        print("[PASS] Cluster status verified: GREEN")

    return all_passed


if __name__ == "__main__":
    stream_wazuh_alerts(WAZUH_TEST_ALERTS)
    if verify_ingestion():
        print("\n>>> Phase ELK-8 Wazuh Ingest & ECS Normalization: PASS <<<")
        sys.exit(0)
    else:
        print("\n>>> Phase ELK-8 Wazuh Ingest & ECS Normalization: FAIL <<<")
        sys.exit(1)
