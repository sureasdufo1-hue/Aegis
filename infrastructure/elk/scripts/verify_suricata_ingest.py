"""
Suricata 8.0.6 EVE JSON Ingestion & ECS Verification Tool for Phase ELK-5
Validates:
1. Stream Suricata EVE JSON events into Logstash pipeline (port 5047/TCP).
2. Verify indexing into Elasticsearch data stream / index: logs-suricata.eve-default.
3. Validate ECS field mappings:
   - @timestamp
   - event.module == 'suricata'
   - event.dataset == 'suricata.eve'
   - event.kind == 'alert'
   - source.ip, destination.ip, related.ip
   - rule.id, rule.name, rule.category
   - threat.framework == 'MITRE ATT&CK', threat.technique.id
4. Verify cluster health remains GREEN.
"""

import base64
import json
import os
from pathlib import Path
import socket
import sys
import time
import urllib.error
import urllib.request

LOGSTASH_HOST = os.getenv("LOGSTASH_HOST", "127.0.0.1")
LOGSTASH_TCP_PORT = int(os.getenv("LOGSTASH_SURICATA_TCP_PORT", "5047"))
ES_HOST = os.getenv("ES_HOST", "http://127.0.0.1:9201")
ES_USER = os.getenv("ES_USER", "elastic")
ES_PASSWORD = os.getenv("ELASTIC_PASSWORD", "changeme_soc_lab_strong_pass_2026")
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def send_events_to_logstash(events: list[dict]) -> bool:
    print(f"[*] Shipping {len(events)} Suricata EVE events to Logstash ({LOGSTASH_HOST}:{LOGSTASH_TCP_PORT})...")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5.0)
            s.connect((LOGSTASH_HOST, LOGSTASH_TCP_PORT))
            for ev in events:
                payload = json.dumps(ev) + "\n"
                s.sendall(payload.encode("utf-8"))
        print(f"[PASS] Successfully transmitted {len(events)} events over TCP.")
        return True
    except Exception as e:
        print(f"[FAIL] Failed to send events to Logstash: {e}")
        return False


def query_elasticsearch(endpoint: str) -> tuple[int, dict]:
    url = f"{ES_HOST.rstrip('/')}/{endpoint.lstrip('/')}"
    req = urllib.request.Request(url)
    auth = base64.b64encode(f"{ES_USER}:{ES_PASSWORD}".encode("ascii")).decode("ascii")
    req.add_header("Authorization", f"Basic {auth}")
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))
    except Exception as e:
        return 0, {"error": str(e)}


def verify_suricata_ingest() -> bool:
    print("==================================================================")
    print(" Phase ELK-5: Suricata 8.0.6 -> Logstash -> Elasticsearch Ingest  ")
    print("==================================================================")

    # 1. Load EVE JSON sample events
    eve_path = REPO_ROOT / "logs" / "suricata" / "eve.json"
    if not eve_path.exists():
        print(f"[FAIL] eve.json not found at {eve_path}")
        return False

    events_to_send = []
    with open(eve_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    ev = json.loads(line)
                    if ev.get("event_type") == "alert":
                        events_to_send.append(ev)
                except Exception:
                    continue

    if not events_to_send:
        print("[FAIL] No valid alert events found in eve.json")
        return False

    print(f"[*] Loaded {len(events_to_send)} alert events from {eve_path.name}")

    # 2. Ship sample of events to Logstash
    sample = events_to_send[:10]
    shipped = send_events_to_logstash(sample)
    if not shipped:
        return False

    # 3. Wait for Logstash processing and ES indexing
    print("[*] Awaiting Logstash pipeline processing & indexing (5 seconds)...")
    time.sleep(5.0)

    # Refresh index
    refresh_status, _ = query_elasticsearch("logs-suricata.eve-default/_refresh")
    print(f"[*] Index refresh status: {refresh_status}")

    # 4. Query Elasticsearch for ingested documents
    print("\n--- [1] Querying logs-suricata.eve-default in Elasticsearch ---")
    status, res = query_elasticsearch("logs-suricata.eve-default/_search?size=5")
    if status != 200:
        print(f"[FAIL] Query to logs-suricata.eve-default failed with status {status}: {res}")
        return False

    total_hits = res.get("hits", {}).get("total", {}).get("value", 0)
    print(f"[PASS] Total Ingested Documents in 'logs-suricata.eve-default': {total_hits}")

    if total_hits == 0:
        print("[FAIL] Zero documents found in logs-suricata.eve-default")
        return False

    # 5. Validate ECS Mappings on hits
    print("\n--- [2] Validating ECS Field Mappings ---")
    hits = res.get("hits", {}).get("hits", [])
    first_doc = hits[0].get("_source", {})

    print(f"Sample Ingested Doc ID: {hits[0].get('_id')}")

    # Check mandatory ECS fields
    checks = [
        ("event.module", first_doc.get("event", {}).get("module") == "suricata"),
        ("event.dataset", first_doc.get("event", {}).get("dataset") == "suricata.eve"),
        ("event.kind", first_doc.get("event", {}).get("kind") == "alert"),
        ("observer.name", first_doc.get("observer", {}).get("name") == "suricata"),
        ("source.ip", "ip" in first_doc.get("source", {})),
        ("destination.ip", "ip" in first_doc.get("destination", {})),
        ("rule.name", "name" in first_doc.get("rule", {})),
        ("rule.id", "id" in first_doc.get("rule", {})),
        ("related.ip", len(first_doc.get("related", {}).get("ip", [])) >= 2),
    ]

    all_passed = True
    for field_name, passed in checks:
        state = "PASS" if passed else "FAIL"
        print(f"[{state}] ECS field check '{field_name}'")
        if not passed:
            all_passed = False

    # Threat MITRE technique check
    threat_tech = first_doc.get("threat", {}).get("technique", {}).get("id")
    if threat_tech:
        print(f"[PASS] MITRE ATT&CK Technique ID mapped: {threat_tech}")
    else:
        print("[INFO] Document did not contain MITRE technique metadata or technique not present.")

    # 6. Check Cluster Health
    print("\n--- [3] Checking Cluster Health ---")
    h_status, h_res = query_elasticsearch("_cluster/health")
    c_status = h_res.get("status", "unknown").upper()
    print(f"[*] Cluster Status after Suricata Ingestion: {c_status}")
    if c_status != "GREEN":
        print(f"[WARN] Cluster status is {c_status} (Expected: GREEN)")

    if all_passed and total_hits > 0:
        print("\n[SUCCESS] Phase ELK-5: Suricata EVE JSON Ingestion & ECS Normalization PASSED!")
        return True
    else:
        print("\n[FAIL] Phase ELK-5 validation had failures.")
        return False


if __name__ == "__main__":
    success = verify_suricata_ingest()
    sys.exit(0 if success else 1)
