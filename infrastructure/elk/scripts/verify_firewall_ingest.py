#!/usr/bin/env python3
"""
verify_firewall_ingest.py
Validates Gateway nftables Firewall syslog ingestion into Logstash (UDP 5514)
and indexing into Elasticsearch (logs-firewall.traffic-default) with 100% ECS compliance.
"""

import sys
import time
import socket
import json
import base64
import urllib.request
import urllib.error

ELASTICSEARCH_URL = "http://127.0.0.1:9201"
LOGSTASH_UDP_HOST = "127.0.0.1"
LOGSTASH_UDP_PORT = 5514
INDEX_NAME = "logs-firewall.traffic-default"
AUTH_HEADER = "Basic " + base64.b64encode(b"elastic:changeme_soc_lab_strong_pass_2026").decode()

# Representative Gateway nftables syslog events
FIREWALL_TEST_EVENTS = [
    # 1. Blocked Attack Zone -> Management Zone (TCP probe to Elasticsearch port 9200)
    "<30>Sep 22 10:15:30 soc-gateway kernel: SOC-FW-DENY-ATTACK-TO-MGMT: IN=eth1 OUT=eth0 MAC=00:15:5d:01:14:02:00:15:5d:01:14:01:08:00 SRC=10.77.20.20 DST=10.77.10.10 LEN=60 TOS=0x00 PREC=0x00 TTL=63 ID=41235 DF PROTO=TCP SPT=49152 DPT=9200 WINDOW=64240 RES=0x00 SYN URGP=0",
    
    # 2. Blocked Attack Zone -> Management Zone (TCP probe to SSH port 22)
    "<30>Sep 22 10:15:31 soc-gateway kernel: SOC-FW-DENY-ATTACK-TO-MGMT: IN=eth1 OUT=eth0 MAC=00:15:5d:01:14:02:00:15:5d:01:14:01:08:00 SRC=10.77.20.20 DST=10.77.10.1 LEN=60 TOS=0x00 PREC=0x00 TTL=63 ID=41236 DF PROTO=TCP SPT=49153 DPT=22 WINDOW=64240 RES=0x00 SYN URGP=0",
    
    # 3. Blocked Attack Zone -> Management Zone (ICMP ping probe)
    "<30>Sep 22 10:15:32 soc-gateway kernel: SOC-FW-DENY-ATTACK-TO-MGMT: IN=eth1 OUT=eth0 MAC=00:15:5d:01:14:02:00:15:5d:01:14:01:08:00 SRC=10.77.20.20 DST=10.77.10.10 LEN=84 TOS=0x00 PREC=0x00 TTL=63 ID=12345 PROTO=ICMP TYPE=8 CODE=0",
    
    # 4. Blocked Attack Zone -> Management Zone (Raw format without syslog priority/header)
    "SOC-FW-DENY-ATTACK-TO-MGMT: IN=eth1 OUT=eth0 MAC=00:15:5d:01:14:02:00:15:5d:01:14:01:08:00 SRC=10.77.20.20 DST=10.77.10.20 LEN=60 TOS=0x00 PREC=0x00 TTL=63 ID=41237 DF PROTO=TCP SPT=49154 DPT=1514 WINDOW=64240 RES=0x00 SYN URGP=0",
    
    # 5. Blocked Attack Zone -> Management Zone (HTTPS probe)
    "<30>Sep 22 10:15:33 soc-gateway kernel: SOC-FW-DENY-ATTACK-TO-MGMT: IN=eth1 OUT=eth0 MAC=00:15:5d:01:14:02:00:15:5d:01:14:01:08:00 SRC=10.77.20.20 DST=10.77.10.10 LEN=60 TOS=0x00 PREC=0x00 TTL=63 ID=41238 DF PROTO=TCP SPT=49155 DPT=443 WINDOW=64240 RES=0x00 SYN URGP=0",
    
    # 6. Forward Allowed: Attack Zone -> Victim Zone (HTTP test traffic to port 80)
    "<30>Sep 22 10:15:34 soc-gateway kernel: SOC-FW-FORWARD-ALLOW: IN=eth1 OUT=eth2 MAC=00:15:5d:01:14:02:00:15:5d:01:14:03:08:00 SRC=10.77.20.20 DST=10.77.30.20 LEN=60 TOS=0x00 PREC=0x00 TTL=63 ID=23456 DF PROTO=TCP SPT=54321 DPT=80 WINDOW=64240 RES=0x00 SYN URGP=0",
    
    # 7. Forward Allowed: Attack Zone -> Victim Zone (JuiceShop test traffic to port 3000)
    "<30>Sep 22 10:15:35 soc-gateway kernel: SOC-FW-FORWARD-ALLOW: IN=eth1 OUT=eth2 MAC=00:15:5d:01:14:02:00:15:5d:01:14:03:08:00 SRC=10.77.20.20 DST=10.77.30.20 LEN=60 TOS=0x00 PREC=0x00 TTL=63 ID=23457 DF PROTO=TCP SPT=54322 DPT=3000 WINDOW=64240 RES=0x00 SYN URGP=0",
    
    # 8. Forward Allowed: Attack Zone -> Victim Zone (SSH test traffic to port 22)
    "<30>Sep 22 10:15:36 soc-gateway kernel: SOC-FW-FORWARD-ALLOW: IN=eth1 OUT=eth2 MAC=00:15:5d:01:14:02:00:15:5d:01:14:03:08:00 SRC=10.77.20.20 DST=10.77.30.20 LEN=60 TOS=0x00 PREC=0x00 TTL=63 ID=23458 DF PROTO=TCP SPT=54323 DPT=22 WINDOW=64240 RES=0x00 SYN URGP=0",
    
    # 9. Forward Allowed: Attack Zone -> Victim Zone (ICMP diagnostic ping)
    "<30>Sep 22 10:15:37 soc-gateway kernel: SOC-FW-FORWARD-ALLOW: IN=eth1 OUT=eth2 MAC=00:15:5d:01:14:02:00:15:5d:01:14:03:08:00 SRC=10.77.20.20 DST=10.77.30.20 LEN=84 TOS=0x00 PREC=0x00 TTL=63 ID=23459 PROTO=ICMP TYPE=8 CODE=0",
    
    # 10. Forward Allowed: Attack Zone -> Victim Zone (Alternative Web port 8080)
    "<30>Sep 22 10:15:38 soc-gateway kernel: SOC-FW-FORWARD-ALLOW: IN=eth1 OUT=eth2 MAC=00:15:5d:01:14:02:00:15:5d:01:14:03:08:00 SRC=10.77.20.20 DST=10.77.30.20 LEN=60 TOS=0x00 PREC=0x00 TTL=63 ID=23460 DF PROTO=TCP SPT=54324 DPT=8080 WINDOW=64240 RES=0x00 SYN URGP=0"
]


def send_firewall_syslog(messages):
    print(f"[*] Sending {len(messages)} nftables syslog messages to UDP {LOGSTASH_UDP_HOST}:{LOGSTASH_UDP_PORT}...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        for msg in messages:
            sock.sendto(msg.encode("utf-8") + b"\n", (LOGSTASH_UDP_HOST, LOGSTASH_UDP_PORT))
            time.sleep(0.05)
        print(f"[PASS] Sent {len(messages)} syslog messages successfully.")
    finally:
        sock.close()


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
            if docs_found >= len(FIREWALL_TEST_EVENTS):
                print(f"[PASS] Successfully retrieved {docs_found} documents from {INDEX_NAME}.")
                break
        except urllib.error.HTTPError as e:
            if e.code != 404:
                print(f"[WARN] HTTP Error: {e.code}")
        time.sleep(2)

    if docs_found == 0:
        print(f"[FAIL] No documents indexed in {INDEX_NAME} within timeout.")
        return False

    res = query_elasticsearch(f"{INDEX_NAME}/_search?size=50")
    hits = res.get("hits", {}).get("hits", [])

    print(f"[*] Verifying ECS normalization across {len(hits)} indexed firewall documents...")

    mandatory_fields = [
        "@timestamp",
        "event.module",
        "event.dataset",
        "event.kind",
        "event.category",
        "event.action",
        "event.outcome",
        "observer.name",
        "host.name",
        "source.ip",
        "destination.ip",
        "related.ip",
        "network.transport"
    ]

    all_passed = True
    deny_count = 0
    allow_count = 0

    for idx, hit in enumerate(hits):
        src = hit["_source"]
        
        # Flattened key getter for nested dictionaries
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

        action = get_nested(src, "event.action")
        outcome = get_nested(src, "event.outcome")
        rule_name = get_nested(src, "rule.name")
        src_ip = get_nested(src, "source.ip")
        dst_ip = get_nested(src, "destination.ip")
        proto = get_nested(src, "network.transport")
        
        if action == "drop":
            deny_count += 1
            if outcome != "denied":
                print(f"[FAIL] Doc {idx+1}: action is 'drop' but outcome is '{outcome}' (expected 'denied')")
                all_passed = False
        elif action == "forward":
            allow_count += 1
            if outcome != "success":
                print(f"[FAIL] Doc {idx+1}: action is 'forward' but outcome is '{outcome}' (expected 'success')")
                all_passed = False

        if idx < 5 or idx == len(hits) - 1:
            print(f"[PASS] Doc {idx+1}: rule='{rule_name}' action='{action}' outcome='{outcome}' {src_ip}->{dst_ip} ({proto})")

    print(f"[*] Total Verified: {deny_count} Dropped (Deny) events, {allow_count} Forwarded (Allow) events.")
    
    if deny_count == 0 or allow_count == 0:
        print("[FAIL] Missing either drop or forward events in dataset.")
        all_passed = False

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
    send_firewall_syslog(FIREWALL_TEST_EVENTS)
    if verify_ingestion():
        print("\n>>> Phase ELK-7 Firewall Ingest & ECS Normalization: PASS <<<")
        sys.exit(0)
    else:
        print("\n>>> Phase ELK-7 Firewall Ingest & ECS Normalization: FAIL <<<")
        sys.exit(1)
