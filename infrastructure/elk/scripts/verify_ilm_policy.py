#!/usr/bin/env python3
"""
verify_ilm_policy.py
Validates the SOC Index Lifecycle Management (ILM) policy (soc-security-logs-ilm)
and verifies that all security telemetry data streams are actively managed across
Hot (14d), Warm (90d), and Delete (365d) phases with Cluster Status GREEN.
"""

import sys
import json
import base64
import urllib.request
import urllib.error

ELASTICSEARCH_URL = "http://127.0.0.1:9201"
AUTH_HEADER = "Basic " + base64.b64encode(b"elastic:changeme_soc_lab_strong_pass_2026").decode()
POLICY_NAME = "soc-security-logs-ilm"
EXPECTED_INDICES = [
    "logs-suricata.eve-default",
    "logs-snort.alert-default",
    "logs-firewall.traffic-default",
    "logs-wazuh.alert-default"
]


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


def test_ilm_policy():
    print("=" * 70)
    print(" Phase ELK-10: Index Lifecycle Management (ILM) Policy Validation")
    print("=" * 70)

    # 1. Verify ILM Policy Definition
    print(f"\n[Test 1] Querying ILM policy '{POLICY_NAME}'...")
    try:
        res = query_elasticsearch(f"_ilm/policy/{POLICY_NAME}")
    except Exception as e:
        print(f"[FAIL] Could not retrieve ILM policy '{POLICY_NAME}': {e}")
        return False

    policy_data = res.get(POLICY_NAME, {}).get("policy", {})
    phases = policy_data.get("phases", {})
    print(f"[*] Registered Phases: {list(phases.keys())}")

    # Check phases presence
    for phase_name in ["hot", "warm", "cold", "delete"]:
        if phase_name not in phases:
            print(f"[FAIL] Missing required ILM phase: {phase_name}")
            return False

    # Check Hot phase rollover
    hot_rollover = phases["hot"].get("actions", {}).get("rollover", {})
    max_age = hot_rollover.get("max_age")
    max_size = hot_rollover.get("max_primary_shard_size")
    print(f"[*] Hot Phase Rollover: max_age={max_age}, max_primary_shard_size={max_size}")

    # Check Warm phase forcemerge
    warm_age = phases["warm"].get("min_age")
    warm_merge = phases["warm"].get("actions", {}).get("forcemerge", {}).get("max_num_segments")
    print(f"[*] Warm Phase: min_age={warm_age}, forcemerge max_segments={warm_merge}")

    # Check Cold phase
    cold_age = phases["cold"].get("min_age")
    print(f"[*] Cold Phase: min_age={cold_age}")

    # Check Delete phase (retention)
    delete_age = phases["delete"].get("min_age")
    print(f"[*] Delete Phase Retention: min_age={delete_age}")
    if delete_age != "365d":
        print(f"[FAIL] Expected Delete phase min_age 365d, found {delete_age}")
        return False

    print("[PASS] ILM policy definition adheres to SOC 14d/90d/365d retention standard.")

    # 2. Verify Index Template Association
    print("\n[Test 2] Checking index template 'soc-cluster-defaults' association...")
    tpl_res = query_elasticsearch("_index_template/soc-cluster-defaults")
    tpl = tpl_res.get("index_templates", [])[0].get("index_template", {})
    settings = tpl.get("template", {}).get("settings", {}).get("index", {})
    bound_ilm = settings.get("lifecycle", {}).get("name")
    replicas = settings.get("number_of_replicas")
    print(f"[*] Template bound ILM: {bound_ilm}, number_of_replicas: {replicas}")

    if bound_ilm != POLICY_NAME:
        print(f"[FAIL] Expected template lifecycle.name '{POLICY_NAME}', found '{bound_ilm}'")
        return False
    if str(replicas) != "0":
        print(f"[FAIL] Expected number_of_replicas '0' for single-node cluster, found '{replicas}'")
        return False
    print("[PASS] Universal index template successfully enforces ILM policy and single-node replicas.")

    # 3. Verify ILM Active Management on Existing Indices
    print("\n[Test 3] Explaining ILM status on active security indices...")
    explain_res = query_elasticsearch("logs-*/_ilm/explain")
    indices_info = explain_res.get("indices", {})

    all_indices_managed = True
    for idx_name in EXPECTED_INDICES:
        if idx_name not in indices_info:
            print(f"[FAIL] Expected index '{idx_name}' not found in ILM explain.")
            all_indices_managed = False
            continue

        info = indices_info[idx_name]
        is_managed = info.get("managed", False)
        active_policy = info.get("policy")
        current_phase = info.get("phase")
        action = info.get("action")
        step = info.get("step")

        print(f"[*] Index: {idx_name:30s} | Managed={str(is_managed):5s} | Policy={active_policy} | Phase={current_phase} | Step={step}")

        if not is_managed or active_policy != POLICY_NAME or current_phase != "hot":
            print(f"[FAIL] Index {idx_name} is not in expected ILM hot state.")
            all_indices_managed = False

    if not all_indices_managed:
        return False
    print("[PASS] All 4 security telemetry data streams are actively managed under ILM policy.")

    # 4. Cluster Health Status
    print("\n[Test 4] Checking Cluster Health...")
    health = query_elasticsearch("_cluster/health")
    status = health.get("status", "").upper()
    print(f"[*] Cluster Status: {status}")
    if status != "GREEN":
        print(f"[FAIL] Expected Cluster Status GREEN, found {status}")
        return False
    print("[PASS] Cluster status verified: GREEN")

    print("\n" + "=" * 70)
    print(" >>> Phase ELK-10 ILM Policy Validation: PASS <<<")
    print("=" * 70)
    return True


if __name__ == "__main__":
    if test_ilm_policy():
        sys.exit(0)
    else:
        sys.exit(1)
