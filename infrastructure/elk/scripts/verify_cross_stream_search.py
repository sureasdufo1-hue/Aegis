#!/usr/bin/env python3
"""
verify_cross_stream_search.py
Automated validation of Multi-Source ECS cross-stream search and correlation
across Suricata, Snort, Gateway nftables, and Wazuh in Elasticsearch (logs-*).
"""

import sys
import json
import base64
import urllib.request
import urllib.error

ELASTICSEARCH_URL = "http://127.0.0.1:9201"
AUTH_HEADER = "Basic " + base64.b64encode(b"elastic:changeme_soc_lab_strong_pass_2026").decode()
INDEX_PATTERN = "logs-*"
ATTACKER_IP = "10.77.20.20"


def query_elasticsearch(path, payload=None):
    url = f"{ELASTICSEARCH_URL}/{path}"
    data = json.dumps(payload).encode("utf-8") if payload else None
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": AUTH_HEADER,
            "Content-Type": "application/json"
        }
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def test_cross_stream_search():
    print("=" * 70)
    print(" Phase ELK-9: Multi-Source Cross-Stream Search & Unified ECS Validation")
    print("=" * 70)

    # 1. Total Document Count & Shard Health across logs-*
    print(f"\n[Test 1] Querying wildcard pattern '{INDEX_PATTERN}'...")
    res = query_elasticsearch(f"{INDEX_PATTERN}/_search?size=0")
    total_docs = res.get("hits", {}).get("total", {}).get("value", 0)
    shards = res.get("_shards", {})
    print(f"[*] Shards: total={shards.get('total')}, successful={shards.get('successful')}, failed={shards.get('failed')}")
    print(f"[*] Total Indexed Telemetry Documents across all streams: {total_docs}")
    if total_docs < 40:
        print(f"[FAIL] Expected at least 40 documents across 4 streams, found {total_docs}")
        return False
    print("[PASS] Multi-stream wildcard query resolved across all shards.")

    # 2. Module Distribution Aggregation
    print("\n[Test 2] Validating Module Distribution across logs-*...")
    mod_query = {
        "size": 0,
        "aggs": {
            "by_module": {
                "terms": {
                    "field": "event.module.keyword",
                    "size": 10
                }
            }
        }
    }
    res = query_elasticsearch(f"{INDEX_PATTERN}/_search", mod_query)
    buckets = res.get("aggregations", {}).get("by_module", {}).get("buckets", [])
    modules_found = {b["key"]: b["doc_count"] for b in buckets}
    print(f"[*] Discovered Modules: {modules_found}")
    
    expected_modules = ["suricata", "snort", "nftables", "wazuh"]
    missing_modules = [m for m in expected_modules if m not in modules_found or modules_found[m] == 0]
    if missing_modules:
        print(f"[FAIL] Missing expected modules in logs-*: {missing_modules}")
        return False
    print(f"[PASS] All 4 security modules verified in unified index pattern: {list(modules_found.keys())}")

    # 3. Attacker Timeline Correlation Query (related.ip == 10.77.20.20)
    print(f"\n[Test 3] Executing Attacker Timeline Correlation for {ATTACKER_IP}...")
    timeline_query = {
        "size": 50,
        "sort": [{"@timestamp": {"order": "asc"}}],
        "query": {
            "term": {
                "related.ip.keyword": ATTACKER_IP
            }
        }
    }
    res = query_elasticsearch(f"{INDEX_PATTERN}/_search", timeline_query)
    hits = res.get("hits", {}).get("hits", [])
    print(f"[*] Attacker {ATTACKER_IP} correlated events count: {len(hits)}")
    if len(hits) < 15:
        print(f"[FAIL] Expected at least 15 correlated events for {ATTACKER_IP}, found {len(hits)}")
        return False

    timeline_modules = set()
    for idx, hit in enumerate(hits):
        src = hit["_source"]
        mod = src.get("event", {}).get("module", "unknown")
        timeline_modules.add(mod)
        ts = src.get("@timestamp", "N/A")
        rule_name = src.get("rule", {}).get("name", "N/A")
        act = src.get("event", {}).get("action", "N/A")
        if idx < 6 or idx == len(hits) - 1:
            print(f"  [{ts}] [{mod.upper():8s}] action={act:7s} rule={rule_name[:50]}")

    print(f"[*] Modules participating in {ATTACKER_IP} timeline: {timeline_modules}")
    if set(expected_modules) != timeline_modules:
        print(f"[FAIL] Timeline missing events from some modules. Expected {expected_modules}, found {timeline_modules}")
        return False
    print(f"[PASS] Single query successfully reconstructed 4-source end-to-end incident timeline.")

    # 4. Multi-Source MITRE ATT&CK Technique Aggregation
    print("\n[Test 4] Validating Unified MITRE ATT&CK Technique Aggregation...")
    tech_query = {
        "size": 0,
        "aggs": {
            "techniques": {
                "terms": {
                    "field": "threat.technique.id.keyword",
                    "size": 20
                }
            }
        }
    }
    res = query_elasticsearch(f"{INDEX_PATTERN}/_search", tech_query)
    tech_buckets = res.get("aggregations", {}).get("techniques", {}).get("buckets", [])
    tech_summary = {b["key"]: b["doc_count"] for b in tech_buckets}
    print(f"[*] Discovered ATT&CK Techniques: {tech_summary}")

    key_techniques = ["T1110", "T1190", "T1046", "T1059.004"]
    for kt in key_techniques:
        if kt not in tech_summary:
            print(f"[FAIL] Expected key ATT&CK technique '{kt}' not found in aggregation.")
            return False
    print(f"[PASS] Multi-Source MITRE ATT&CK aggregation confirmed across all security detectors.")

    # 5. Severity Distribution Aggregation
    print("\n[Test 5] Validating Severity Distribution Aggregation...")
    sev_query = {
        "size": 0,
        "aggs": {
            "severities": {
                "terms": {
                    "field": "event.severity"
                }
            }
        }
    }
    res = query_elasticsearch(f"{INDEX_PATTERN}/_search", sev_query)
    sev_buckets = res.get("aggregations", {}).get("severities", {}).get("buckets", [])
    sev_summary = {b["key"]: b["doc_count"] for b in sev_buckets}
    print(f"[*] Severity Buckets (1:Low, 2:Med, 3:High, 4:Crit): {sev_summary}")
    
    if 4 not in sev_summary or 3 not in sev_summary:
        print("[FAIL] Missing Critical or High severity buckets in aggregation.")
        return False
    print(f"[PASS] Unified severity distribution verified: Critical={sev_summary.get(4)}, High={sev_summary.get(3)}, Med={sev_summary.get(2)}")

    # 6. Cluster Health Status
    print("\n[Test 6] Checking Cluster Health...")
    health = query_elasticsearch("_cluster/health")
    status = health.get("status", "").upper()
    print(f"[*] Cluster Status: {status}")
    if status != "GREEN":
        print(f"[FAIL] Expected Cluster Status GREEN, found {status}")
        return False
    print("[PASS] Cluster status verified: GREEN")

    print("\n" + "=" * 70)
    print(" >>> Phase ELK-9 Multi-Source Cross-Stream Search: PASS <<<")
    print("=" * 70)
    return True


if __name__ == "__main__":
    if test_cross_stream_search():
        sys.exit(0)
    else:
        sys.exit(1)
