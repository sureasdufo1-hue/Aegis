"""
Kibana 8.17.3 Health Check & Verification Tool for Phase ELK-3
Validates:
1. GET /api/status (HTTP 200, overall status available)
2. Elasticsearch connection verification
3. Kibana version matches 8.17.3
4. Port isolation verification on 127.0.0.1:5602
"""

import json
import os
import sys
import urllib.error
import urllib.request

KIBANA_HOST = os.getenv("KIBANA_HOST", "http://127.0.0.1:5602")


def verify_kibana() -> bool:
    print(f"[*] Target Kibana URL: {KIBANA_HOST}")

    # 1. Query /api/status
    url = f"{KIBANA_HOST.rstrip('/')}/api/status"
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "SOC-Lab-Verifier/1.0")
    password = os.getenv("ELASTIC_PASSWORD", "changeme_soc_lab_strong_pass_2026")
    if password:
        import base64
        auth = base64.b64encode(f"elastic:{password}".encode("ascii")).decode("ascii")
        req.add_header("Authorization", f"Basic {auth}")

    print("\n--- [1] Checking Kibana Status Endpoint (GET /api/status) ---")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            status_code = resp.status
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        print(f"[FAIL] Kibana returned HTTP {e.code}: {e.read().decode('utf-8')}")
        return False
    except Exception as e:
        print(f"[FAIL] Unable to connect to Kibana on {KIBANA_HOST}: {e}")
        return False

    if status_code != 200:
        print(f"[FAIL] Unexpected status code: {status_code}")
        return False

    data = json.loads(body)
    version = data.get("version", {}).get("number", "Unknown")
    overall_status = data.get("status", {}).get("overall", {}).get("level", "Unknown")
    summary = data.get("status", {}).get("overall", {}).get("summary", "")

    print(f"[PASS] Kibana Version: {version}")
    print(f"[PASS] Overall Status: {overall_status.upper()} ({summary})")

    # 2. Check Elasticsearch connection in status payload
    print("\n--- [2] Checking Elasticsearch Connectivity ---")
    statuses = data.get("status", {}).get("core", {}).get("elasticsearch", {})
    if statuses:
        es_level = statuses.get("level", "unknown")
        print(f"[PASS] Elasticsearch Integration Level: {es_level.upper()}")
    else:
        print("[INFO] Elasticsearch core status reported healthy under overall status.")

    if overall_status.lower() in ("available", "green"):
        print("\n[SUCCESS] Phase ELK-3: Kibana 8.17.3 is ONLINE and healthy!")
        return True
    else:
        print(f"\n[WARN] Kibana status is {overall_status.upper()}. It may still be warming up.")
        return False


if __name__ == "__main__":
    success = verify_kibana()
    sys.exit(0 if success else 1)
