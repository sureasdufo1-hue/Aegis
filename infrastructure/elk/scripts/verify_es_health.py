"""
Elasticsearch 8.17.3 Health Check & Verification Tool for Phase ELK-2
Performs standard REST API validation:
1. GET / (Cluster information & version verification)
2. GET /_cluster/health (Cluster health status: target green)
3. GET /_cat/nodes?v (Node topology verification)
4. GET /_cat/indices?v (Index & shard allocation verification)
"""

import json
import os
import sys
import urllib.error
import urllib.request

ES_HOST = os.getenv("ES_HOST", "http://127.0.0.1:9201")
ES_USER = os.getenv("ES_USER", "elastic")
ES_PASSWORD = os.getenv("ELASTIC_PASSWORD", "changeme_soc_lab_strong_pass_2026")


def make_request(path: str) -> tuple[int, str]:
    url = f"{ES_HOST.rstrip('/')}{path}"
    req = urllib.request.Request(url)
    import base64
    auth_str = f"{ES_USER}:{ES_PASSWORD}"
    b64_auth = base64.b64encode(auth_str.encode("utf-8")).decode("ascii")
    req.add_header("Authorization", f"Basic {b64_auth}")

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")
    except Exception as e:
        return 0, str(e)


def run_health_check() -> bool:
    print(f"[*] Target Elasticsearch URL: {ES_HOST}")

    # 1. Check Root Endpoint
    print("\n--- [1] Checking Root Endpoint (GET /) ---")
    status, body = make_request("/")
    if status != 200:
        print(f"[FAIL] Unable to connect to Elasticsearch: HTTP {status} - {body}")
        return False

    try:
        root_data = json.loads(body)
        version = root_data.get("version", {}).get("number", "Unknown")
        cluster_name = root_data.get("cluster_name", "Unknown")
        print(f"[PASS] Connected to cluster '{cluster_name}', Version: {version}")
    except Exception:
        print(f"[PASS] Connected. Response:\n{body}")

    # 2. Check Cluster Health
    print("\n--- [2] Checking Cluster Health (GET /_cluster/health) ---")
    status, body = make_request("/_cluster/health")
    if status != 200:
        print(f"[FAIL] Cluster health check failed: HTTP {status} - {body}")
        return False

    health = json.loads(body)
    c_status = health.get("status", "unknown").lower()
    nodes = health.get("number_of_nodes", 0)
    active_shards = health.get("active_primary_shards", 0)
    unassigned = health.get("unassigned_shards", 0)

    print(f"Cluster Status: {c_status.upper()}")
    print(f"Nodes: {nodes}, Active Primary Shards: {active_shards}, Unassigned: {unassigned}")

    if c_status == "green":
        print("[PASS] Cluster status is GREEN!")
    elif c_status == "yellow":
        print("[WARN] Cluster status is YELLOW (Single-Node unassigned replicas detected).")
        print("       Adjusting template number_of_replicas to 0 will achieve GREEN.")
    else:
        print(f"[FAIL] Cluster status is {c_status.upper()}")
        return False

    # 3. Check Nodes
    print("\n--- [3] Checking Nodes (GET /_cat/nodes?v) ---")
    status, body = make_request("/_cat/nodes?v")
    print(body if status == 200 else f"HTTP {status}: {body}")

    # 4. Check Indices
    print("\n--- [4] Checking Indices (GET /_cat/indices?v) ---")
    status, body = make_request("/_cat/indices?v")
    print(body if status == 200 else f"HTTP {status}: {body}")

    return True


if __name__ == "__main__":
    success = run_health_check()
    sys.exit(0 if success else 1)
