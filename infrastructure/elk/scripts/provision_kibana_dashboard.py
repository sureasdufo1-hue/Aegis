#!/usr/bin/env python3
"""
provision_kibana_dashboard.py
Automates the provisioning of Kibana Data Views, Lens Visualizations,
Saved Searches, and the Unified SOC Threat Operations Dashboard in Kibana 8.17.3.
"""

import sys
import json
import base64
import urllib.request
import urllib.error

KIBANA_URL = "http://127.0.0.1:5602"
AUTH_HEADER = "Basic " + base64.b64encode(b"elastic:changeme_soc_lab_strong_pass_2026").decode()
HEADERS = {
    "Authorization": AUTH_HEADER,
    "Content-Type": "application/json",
    "kbn-xsrf": "true"
}

# 1. Data Views Definitions
DATA_VIEWS = [
    {
        "id": "soc-unified-logs",
        "name": "SOC Unified Security Telemetry (logs-*)",
        "title": "logs-*",
        "timeFieldName": "@timestamp"
    },
    {
        "id": "soc-suricata-logs",
        "name": "Suricata IDS (logs-suricata.eve-*)",
        "title": "logs-suricata.eve-*",
        "timeFieldName": "@timestamp"
    },
    {
        "id": "soc-snort-logs",
        "name": "Snort 3 IDS (logs-snort.alert-*)",
        "title": "logs-snort.alert-*",
        "timeFieldName": "@timestamp"
    },
    {
        "id": "soc-firewall-logs",
        "name": "Gateway nftables Firewall (logs-firewall.traffic-*)",
        "title": "logs-firewall.traffic-*",
        "timeFieldName": "@timestamp"
    },
    {
        "id": "soc-wazuh-logs",
        "name": "Wazuh SIEM (logs-wazuh.alert-*)",
        "title": "logs-wazuh.alert-*",
        "timeFieldName": "@timestamp"
    }
]


def kibana_request(path, payload=None, method=None):
    url = f"{KIBANA_URL}/{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    if method is None:
        method = "POST" if data is not None else "GET"

    req = urllib.request.Request(url, data=data, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8")
            return json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        return {"error": e.code, "message": err_body}


def provision_data_views():
    print("\n[Step 1] Provisioning Kibana Data Views...")
    for dv in DATA_VIEWS:
        body = {
            "data_view": {
                "id": dv["id"],
                "name": dv["name"],
                "title": dv["title"],
                "timeFieldName": dv["timeFieldName"]
            },
            "override": True
        }
        res = kibana_request("api/data_views/data_view", body, method="POST")
        if "error" in res:
            print(f"[WARN] Error provisioning {dv['id']}: {res}")
        else:
            print(f"[PASS] Provisioned Data View: {dv['id']} ({dv['title']})")

    # Set Default Index Pattern to soc-unified-logs
    kibana_request("api/kibana/settings", {"changes": {"defaultIndex": "soc-unified-logs"}}, method="POST")
    print("[PASS] Default Data View configured to 'soc-unified-logs'.")


def provision_saved_search():
    print("\n[Step 2] Provisioning Saved Search 'soc-threat-event-feed'...")
    search_obj = {
        "attributes": {
            "title": "SOC Unified Security Event Feed",
            "description": "Chronological real-time feed across Suricata, Snort, Gateway, and Wazuh",
            "columns": [
                "@timestamp",
                "event.module",
                "event.severity",
                "rule.name",
                "source.ip",
                "destination.ip",
                "threat.technique.id"
            ],
            "sort": [["@timestamp", "desc"]],
            "kibanaSavedObjectMeta": {
                "searchSourceJSON": json.dumps({
                    "highlightAll": True,
                    "version": True,
                    "query": {"query": "", "language": "kuery"},
                    "filter": [],
                    "indexRefName": "kibanaSavedObjectMeta.searchSourceJSON.index"
                })
            }
        },
        "references": [
            {
                "name": "kibanaSavedObjectMeta.searchSourceJSON.index",
                "type": "index-pattern",
                "id": "soc-unified-logs"
            }
        ]
    }
    res = kibana_request("api/saved_objects/search/soc-threat-event-feed?overwrite=true", search_obj, method="POST")
    if "error" in res:
        print(f"[FAIL] Saved Search creation error: {res}")
        return False
    print("[PASS] Saved Search 'soc-threat-event-feed' provisioned successfully.")
    return True


def provision_lens_visualizations():
    print("\n[Step 3] Provisioning Kibana Lens Visualizations...")
    
    # 1. Module Distribution Bar Chart
    mod_lens = {
        "attributes": {
            "title": "Security Telemetry by Module",
            "description": "Event distribution across Suricata, Snort 3, Gateway nftables, and Wazuh",
            "visualizationType": "lnsXY",
            "state": {
                "visualization": {
                    "preferredSeriesType": "bar",
                    "layers": [
                        {
                            "layerId": "layer1",
                            "layerType": "data",
                            "seriesType": "bar",
                            "position": "top",
                            "showGridlines": False,
                            "xAccessor": "x_dim",
                            "accessors": ["y_dim"]
                        }
                    ],
                    "legend": {
                        "isVisible": True,
                        "position": "right",
                        "legendSize": "auto"
                    },
                    "valueLabels": "hide",
                    "fittingFunction": "None",
                    "axisTitlesVisibilitySettings": {
                        "x": True,
                        "yLeft": True,
                        "yRight": False
                    },
                    "tickLabelsVisibilitySettings": {
                        "x": True,
                        "yLeft": True,
                        "yRight": False
                    },
                    "gridlinesVisibilitySettings": {
                        "x": False,
                        "yLeft": True,
                        "yRight": False
                    },
                    "yLeftExtent": {
                        "mode": "full"
                    },
                    "yRightExtent": {
                        "mode": "full"
                    }
                },
                "query": {"query": "", "language": "kuery"},
                "filters": [],
                "datasourceStates": {
                    "formBased": {
                        "layers": {
                            "layer1": {
                                "columns": {
                                    "x_dim": {
                                        "label": "Detector Module",
                                        "dataType": "string",
                                        "operationType": "terms",
                                        "sourceField": "event.module.keyword",
                                        "scale": "ordinal",
                                        "isBucketed": True,
                                        "params": {
                                            "size": 10,
                                            "orderBy": {"type": "column", "columnId": "y_dim"},
                                            "orderDirection": "desc"
                                        }
                                    },
                                    "y_dim": {
                                        "label": "Total Events",
                                        "dataType": "number",
                                        "operationType": "count",
                                        "scale": "ratio",
                                        "sourceField": "___records___",
                                        "isBucketed": False
                                    }
                                },
                                "columnOrder": ["x_dim", "y_dim"],
                                "incompleteColumns": {}
                            }
                        }
                    }
                }
            }
        },
        "references": [
            {"name": "indexpattern-datasource-current-indexpattern", "type": "index-pattern", "id": "soc-unified-logs"},
            {"name": "indexpattern-datasource-layer-layer1", "type": "index-pattern", "id": "soc-unified-logs"}
        ]
    }
    kibana_request("api/saved_objects/lens/soc-lens-module-dist?overwrite=true", mod_lens, method="POST")
    print("[PASS] Lens 'soc-lens-module-dist' provisioned.")

    # 2. MITRE ATT&CK Distribution Donut Chart
    attack_lens = {
        "attributes": {
            "title": "MITRE ATT&CK Technique Distribution",
            "description": "Categorization of detected adversary techniques across all sensors",
            "visualizationType": "lnsPie",
            "state": {
                "visualization": {
                    "shape": "donut",
                    "layers": [
                        {
                            "layerId": "layer1",
                            "layerType": "data",
                            "primaryGroups": ["x_dim"],
                            "metrics": ["y_dim"],
                            "numberDisplay": "percent",
                            "categoryDisplay": "default",
                            "legendDisplay": "default",
                            "legendPosition": "right",
                            "nestedLegend": False
                        }
                    ]
                },
                "query": {"query": "threat.technique.id: *", "language": "kuery"},
                "filters": [],
                "datasourceStates": {
                    "formBased": {
                        "layers": {
                            "layer1": {
                                "columns": {
                                    "x_dim": {
                                        "label": "MITRE ATT&CK Technique",
                                        "dataType": "string",
                                        "operationType": "terms",
                                        "sourceField": "threat.technique.id.keyword",
                                        "scale": "ordinal",
                                        "isBucketed": True,
                                        "params": {
                                            "size": 10,
                                            "orderBy": {"type": "column", "columnId": "y_dim"},
                                            "orderDirection": "desc"
                                        }
                                    },
                                    "y_dim": {
                                        "label": "Alert Count",
                                        "dataType": "number",
                                        "operationType": "count",
                                        "scale": "ratio",
                                        "sourceField": "___records___",
                                        "isBucketed": False
                                    }
                                },
                                "columnOrder": ["x_dim", "y_dim"],
                                "incompleteColumns": {}
                            }
                        }
                    }
                }
            }
        },
        "references": [
            {"name": "indexpattern-datasource-current-indexpattern", "type": "index-pattern", "id": "soc-unified-logs"},
            {"name": "indexpattern-datasource-layer-layer1", "type": "index-pattern", "id": "soc-unified-logs"}
        ]
    }
    kibana_request("api/saved_objects/lens/soc-lens-technique-donut?overwrite=true", attack_lens, method="POST")
    print("[PASS] Lens 'soc-lens-technique-donut' provisioned.")

    # 3. Severity Distribution
    sev_lens = {
        "attributes": {
            "title": "Events by Severity Level",
            "description": "Severity breakdown (1:Low, 2:Medium, 3:High, 4:Critical)",
            "visualizationType": "lnsXY",
            "state": {
                "visualization": {
                    "preferredSeriesType": "bar",
                    "layers": [
                        {
                            "layerId": "layer1",
                            "layerType": "data",
                            "seriesType": "bar",
                            "position": "top",
                            "showGridlines": False,
                            "xAccessor": "x_dim",
                            "accessors": ["y_dim"]
                        }
                    ],
                    "legend": {
                        "isVisible": True,
                        "position": "right",
                        "legendSize": "auto"
                    },
                    "valueLabels": "hide",
                    "fittingFunction": "None",
                    "axisTitlesVisibilitySettings": {
                        "x": True,
                        "yLeft": True,
                        "yRight": False
                    },
                    "tickLabelsVisibilitySettings": {
                        "x": True,
                        "yLeft": True,
                        "yRight": False
                    },
                    "gridlinesVisibilitySettings": {
                        "x": False,
                        "yLeft": True,
                        "yRight": False
                    },
                    "yLeftExtent": {
                        "mode": "full"
                    },
                    "yRightExtent": {
                        "mode": "full"
                    }
                },
                "query": {"query": "", "language": "kuery"},
                "filters": [],
                "datasourceStates": {
                    "formBased": {
                        "layers": {
                            "layer1": {
                                "columns": {
                                    "x_dim": {
                                        "label": "Severity",
                                        "dataType": "number",
                                        "operationType": "terms",
                                        "sourceField": "event.severity",
                                        "scale": "ordinal",
                                        "isBucketed": True,
                                        "params": {
                                            "size": 5,
                                            "orderBy": {"type": "alphabetical"},
                                            "orderDirection": "asc"
                                        }
                                    },
                                    "y_dim": {
                                        "label": "Count",
                                        "dataType": "number",
                                        "operationType": "count",
                                        "scale": "ratio",
                                        "sourceField": "___records___",
                                        "isBucketed": False
                                    }
                                },
                                "columnOrder": ["x_dim", "y_dim"],
                                "incompleteColumns": {}
                            }
                        }
                    }
                }
            }
        },
        "references": [
            {"name": "indexpattern-datasource-current-indexpattern", "type": "index-pattern", "id": "soc-unified-logs"},
            {"name": "indexpattern-datasource-layer-layer1", "type": "index-pattern", "id": "soc-unified-logs"}
        ]
    }
    kibana_request("api/saved_objects/lens/soc-lens-severity-dist?overwrite=true", sev_lens, method="POST")
    print("[PASS] Lens 'soc-lens-severity-dist' provisioned.")

    return True


def provision_dashboard():
    print("\n[Step 4] Provisioning Unified SOC Threat Dashboard...")
    panels = [
        {
            "version": "8.17.3",
            "type": "lens",
            "gridData": {"x": 0, "y": 0, "w": 24, "h": 12, "i": "panel_module_dist"},
            "panelIndex": "panel_module_dist",
            "embeddableConfig": {},
            "panelRefName": "panel_panel_module_dist"
        },
        {
            "version": "8.17.3",
            "type": "lens",
            "gridData": {"x": 24, "y": 0, "w": 24, "h": 12, "i": "panel_technique_donut"},
            "panelIndex": "panel_technique_donut",
            "embeddableConfig": {},
            "panelRefName": "panel_panel_technique_donut"
        },
        {
            "version": "8.17.3",
            "type": "lens",
            "gridData": {"x": 0, "y": 12, "w": 24, "h": 10, "i": "panel_severity_dist"},
            "panelIndex": "panel_severity_dist",
            "embeddableConfig": {},
            "panelRefName": "panel_panel_severity_dist"
        },
        {
            "version": "8.17.3",
            "type": "search",
            "gridData": {"x": 0, "y": 22, "w": 48, "h": 16, "i": "panel_event_feed"},
            "panelIndex": "panel_event_feed",
            "embeddableConfig": {},
            "panelRefName": "panel_panel_event_feed"
        }
    ]

    dashboard_obj = {
        "attributes": {
            "title": "SOC Threat Operations & Monitoring Dashboard",
            "description": "Unified Multi-Source Real-time Security Monitoring across Suricata 8.0.6, Snort 3.12.2, Gateway nftables, and Wazuh 4.14.7",
            "hits": 0,
            "panelsJSON": json.dumps(panels),
            "timeRestore": True,
            "timeFrom": "now-7d",
            "timeTo": "now",
            "kibanaSavedObjectMeta": {
                "searchSourceJSON": json.dumps({
                    "query": {"query": "", "language": "kuery"},
                    "filter": []
                })
            }
        },
        "references": [
            {
                "name": "panel_panel_module_dist",
                "type": "lens",
                "id": "soc-lens-module-dist"
            },
            {
                "name": "panel_panel_technique_donut",
                "type": "lens",
                "id": "soc-lens-technique-donut"
            },
            {
                "name": "panel_panel_severity_dist",
                "type": "lens",
                "id": "soc-lens-severity-dist"
            },
            {
                "name": "panel_panel_event_feed",
                "type": "search",
                "id": "soc-threat-event-feed"
            }
        ]
    }

    res = kibana_request("api/saved_objects/dashboard/soc-unified-threat-dashboard?overwrite=true", dashboard_obj, method="POST")
    if "error" in res:
        print(f"[FAIL] Dashboard creation error: {res}")
        return False

    dash_url = f"{KIBANA_URL}/app/dashboards#/view/soc-unified-threat-dashboard"
    print(f"[PASS] Dashboard 'soc-unified-threat-dashboard' provisioned successfully!")
    print(f"[*] Access URL: {dash_url}")
    return True


def verify_kibana_provisioning():
    print("\n[Step 5] Verifying Provisioned Objects...")
    # Verify Data Views
    dvs = kibana_request("api/data_views")
    dv_list = dvs.get("data_view", [])
    print(f"[*] Total Data Views: {len(dv_list)}")
    dv_ids = [d["id"] for d in dv_list]
    for exp in ["soc-unified-logs", "soc-suricata-logs", "soc-snort-logs", "soc-firewall-logs", "soc-wazuh-logs"]:
        if exp not in dv_ids:
            print(f"[FAIL] Missing Data View: {exp}")
            return False
        print(f"  [+] Confirmed Data View: {exp}")

    # Verify Dashboard
    dash = kibana_request("api/saved_objects/dashboard/soc-unified-threat-dashboard")
    if "error" in dash:
        print(f"[FAIL] Could not retrieve dashboard: {dash}")
        return False
    
    title = dash.get("attributes", {}).get("title")
    print(f"[PASS] Confirmed Dashboard: '{title}' (ID: soc-unified-threat-dashboard)")
    return True


def main():
    print("=" * 70)
    print(" Phase ELK-11: Kibana Data Views & Unified SOC Dashboard Provisioning")
    print("=" * 70)
    
    provision_data_views()
    provision_saved_search()
    provision_lens_visualizations()
    provision_dashboard()
    
    if verify_kibana_provisioning():
        print("\n" + "=" * 70)
        print(" >>> Phase ELK-11 Kibana Data Views & Dashboard: PASS <<<")
        print("=" * 70)
        sys.exit(0)
    else:
        print("\n" + "=" * 70)
        print(" >>> Phase ELK-11 Kibana Data Views & Dashboard: FAIL <<<")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()
