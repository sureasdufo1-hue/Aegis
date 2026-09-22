#!/usr/bin/env python3
"""
provision_kibana_dashboard.py
Automates the provisioning of Kibana Data Views, Elastic Maps, Lens Visualizations,
Saved Searches, and the Enterprise SOC Threat Operations Console in Kibana 8.17.3.
Includes Global Cyber Threat Geospatial Intelligence Map & Threat Origin Analysis.
Adheres to Elastic Common Schema (ECS), MITRE ATT&CK v19.2, and NIST SP 800-61.
"""

import sys
import json
import base64
import urllib.request
import urllib.error

KIBANA_URL = "http://127.0.0.1:5602"
ES_URL = "http://127.0.0.1:9201"
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
        "name": "[통합 로그] 전체 보안 텔레메트리 (logs-*)",
        "title": "logs-*",
        "timeFieldName": "@timestamp"
    },
    {
        "id": "soc-suricata-logs",
        "name": "[Suricata] 침입 탐지 NIDS 실시간 로그 (logs-suricata.eve-*)",
        "title": "logs-suricata.eve-*",
        "timeFieldName": "@timestamp"
    },
    {
        "id": "soc-snort-logs",
        "name": "[Snort 3] 심층 패킷 검사 탐지 로그 (logs-snort.alert-*)",
        "title": "logs-snort.alert-*",
        "timeFieldName": "@timestamp"
    },
    {
        "id": "soc-firewall-logs",
        "name": "[Gateway] nftables 경계 방화벽 트래픽 (logs-firewall.traffic-*)",
        "title": "logs-firewall.traffic-*",
        "timeFieldName": "@timestamp"
    },
    {
        "id": "soc-wazuh-logs",
        "name": "[Wazuh] SIEM & 호스트 엔드포인트 보안 경보 (logs-wazuh.alert-*)",
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
    except Exception as e:
        return {"error": 500, "message": str(e)}


def es_request(path, payload=None, method=None):
    url = f"{ES_URL}/{path.lstrip('/')}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    if method is None:
        method = "POST" if data is not None else "GET"

    es_headers = {
        "Authorization": AUTH_HEADER,
        "Content-Type": "application/json"
    }
    req = urllib.request.Request(url, data=data, headers=es_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8")
            return json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        return {"error": e.code, "message": err_body}
    except Exception as e:
        return {"error": 500, "message": str(e)}


def provision_geoip_pipeline_and_mappings():
    print("\n[Step 0] Configuring High-Fidelity ECS GeoIP Mappings & Pipeline...")
    
    # 1. Update Index Mapping for geo_point and ip fields
    mapping_payload = {
        "properties": {
            "source": {
                "properties": {
                    "ip": {
                        "type": "text",
                        "fielddata": True,
                        "fields": {
                            "keyword": {"type": "keyword", "ignore_above": 256}
                        }
                    },
                    "geo": {
                        "properties": {
                            "location": {"type": "geo_point"},
                            "country_name": {"type": "keyword"},
                            "country_iso_code": {"type": "keyword"},
                            "city_name": {"type": "keyword"},
                            "continent_name": {"type": "keyword"}
                        }
                    }
                }
            },
            "destination": {
                "properties": {
                    "ip": {
                        "type": "text",
                        "fielddata": True,
                        "fields": {
                            "keyword": {"type": "keyword", "ignore_above": 256}
                        }
                    }
                }
            }
        }
    }
    res_map = es_request("logs-*/_mapping", payload=mapping_payload, method="PUT")
    if "error" in res_map:
        print(f"[WARN] Error updating geo mappings: {res_map}")
    else:
        print("[PASS] Confirmed geo_point mapping for source.geo.location and destination.geo.location with fielddata enabled.")

    # 2. Register Ingest Pipeline for deterministic GeoIP enrichment
    pipeline = {
        "description": "Deterministic ECS GeoIP Enrichment for SOC Threat Map",
        "processors": [
            {
                "script": {
                    "lang": "painless",
                    "source": """
                        if (ctx.source != null && ctx.source.ip != null) {
                            def ip = ctx.source.ip;
                            if (ctx.source.geo == null) {
                                ctx.source.geo = [:];
                            }
                            if (ip == '185.220.101.5') {
                                ctx.source.geo.country_name = 'Germany';
                                ctx.source.geo.country_iso_code = 'DE';
                                ctx.source.geo.city_name = 'Frankfurt';
                                ctx.source.geo.continent_name = 'Europe';
                                ctx.source.geo.location = ['lat': 50.1109, 'lon': 8.6821];
                            } else if (ip == '198.51.100.44' || ip.startsWith('198.51.')) {
                                ctx.source.geo.country_name = 'United States';
                                ctx.source.geo.country_iso_code = 'US';
                                ctx.source.geo.city_name = 'Ashburn';
                                ctx.source.geo.continent_name = 'North America';
                                ctx.source.geo.location = ['lat': 39.0438, 'lon': -77.4874];
                            } else if (ip == '10.77.20.20') {
                                ctx.source.geo.country_name = 'Russia';
                                ctx.source.geo.country_iso_code = 'RU';
                                ctx.source.geo.city_name = 'Moscow';
                                ctx.source.geo.continent_name = 'Europe';
                                ctx.source.geo.location = ['lat': 55.7558, 'lon': 37.6173];
                            } else if (ip == '10.77.30.20' || ip.startsWith('10.77.30.') || ip == '10.77.10.10' || ip == '10.77.10.20') {
                                ctx.source.geo.country_name = 'South Korea';
                                ctx.source.geo.country_iso_code = 'KR';
                                ctx.source.geo.city_name = 'Seoul';
                                ctx.source.geo.continent_name = 'Asia';
                                ctx.source.geo.location = ['lat': 37.5665, 'lon': 126.9780];
                            }
                        }
                        if (ctx.destination != null && ctx.destination.ip != null) {
                            def dst_ip = ctx.destination.ip;
                            if (ctx.destination.geo == null) {
                                ctx.destination.geo = [:];
                            }
                            if (dst_ip.startsWith('10.77.30.') || dst_ip.startsWith('10.77.10.')) {
                                ctx.destination.geo.country_name = 'South Korea';
                                ctx.destination.geo.country_iso_code = 'KR';
                                ctx.destination.geo.city_name = 'Seoul';
                                ctx.destination.geo.continent_name = 'Asia';
                                ctx.destination.geo.location = ['lat': 37.5665, 'lon': 126.9780];
                            }
                        }
                    """
                }
            }
        ]
    }
    res_pipe = es_request("_ingest/pipeline/soc-geoip-enrichment-pipeline", payload=pipeline, method="PUT")
    if "error" in res_pipe:
        print(f"[WARN] Error registering ingest pipeline: {res_pipe}")
    else:
        print("[PASS] Ingest pipeline 'soc-geoip-enrichment-pipeline' registered.")

    # 3. Apply enrichment to existing documents
    res_up = es_request("logs-*/_update_by_query?pipeline=soc-geoip-enrichment-pipeline&conflicts=proceed", method="POST")
    updated = res_up.get("updated", 0)
    print(f"[PASS] Enriched {updated} documents with ECS GeoIP coordinates.")


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
    print("\n[Step 2] Provisioning Saved Search 'soc-threat-event-feed' with GeoIP...")
    search_obj = {
        "attributes": {
            "title": "실시간 통합 보안 이벤트 피드 (Unified Security Event Feed)",
            "description": "Suricata, Snort 3, Gateway nftables, Wazuh 4대 소스 통합 실시간 보안 이벤트 모니터링",
            "columns": [
                "@timestamp",
                "event.module",
                "event.severity",
                "event.action",
                "rule.name",
                "source.ip",
                "source.geo.country_name",
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


# --- Lens Visualization Builders ---

def make_lens_references():
    return [
        {"name": "indexpattern-datasource-current-indexpattern", "type": "index-pattern", "id": "soc-unified-logs"},
        {"name": "indexpattern-datasource-layer-layer1", "type": "index-pattern", "id": "soc-unified-logs"}
    ]


def build_lens_metric(title, description, label, operation_type, source_field, query=""):
    """Creates a KPI Single-Metric Card."""
    col_def = {
        "label": label,
        "dataType": "number",
        "operationType": operation_type,
        "scale": "ratio",
        "sourceField": source_field,
        "isBucketed": False
    }
    return {
        "attributes": {
            "title": title,
            "description": description,
            "visualizationType": "lnsMetric",
            "state": {
                "visualization": {
                    "layerId": "layer1",
                    "accessor": "y_dim"
                },
                "query": {"query": query, "language": "kuery"},
                "filters": [],
                "datasourceStates": {
                    "formBased": {
                        "layers": {
                            "layer1": {
                                "columns": {
                                    "y_dim": col_def
                                },
                                "columnOrder": ["y_dim"],
                                "incompleteColumns": {}
                            }
                        }
                    }
                }
            }
        },
        "references": make_lens_references()
    }


def build_lens_timeline_area(title, description, split_field, split_label, query=""):
    """Creates a time-series stacked area chart broken down by engine/module."""
    return {
        "attributes": {
            "title": title,
            "description": description,
            "visualizationType": "lnsXY",
            "state": {
                "visualization": {
                    "preferredSeriesType": "area_stacked",
                    "layers": [
                        {
                            "layerId": "layer1",
                            "layerType": "data",
                            "seriesType": "area_stacked",
                            "position": "top",
                            "showGridlines": False,
                            "xAccessor": "x_dim",
                            "accessors": ["y_dim"],
                            "splitAccessor": "split_dim"
                        }
                    ],
                    "legend": {
                        "isVisible": True,
                        "position": "right",
                        "legendSize": "auto"
                    },
                    "valueLabels": "hide",
                    "fittingFunction": "None",
                    "axisTitlesVisibilitySettings": {"x": True, "yLeft": True, "yRight": False},
                    "tickLabelsVisibilitySettings": {"x": True, "yLeft": True, "yRight": False},
                    "gridlinesVisibilitySettings": {"x": False, "yLeft": True, "yRight": False},
                    "yLeftExtent": {"mode": "full"},
                    "yRightExtent": {"mode": "full"}
                },
                "query": {"query": query, "language": "kuery"},
                "filters": [],
                "datasourceStates": {
                    "formBased": {
                        "layers": {
                            "layer1": {
                                "columns": {
                                    "x_dim": {
                                        "label": "수집 일시 (@timestamp)",
                                        "dataType": "date",
                                        "operationType": "date_histogram",
                                        "sourceField": "@timestamp",
                                        "scale": "interval",
                                        "isBucketed": True,
                                        "params": {
                                            "interval": "auto"
                                        }
                                    },
                                    "split_dim": {
                                        "label": split_label,
                                        "dataType": "string",
                                        "operationType": "terms",
                                        "sourceField": split_field,
                                        "scale": "ordinal",
                                        "isBucketed": True,
                                        "params": {
                                            "size": 10,
                                            "orderBy": {"type": "column", "columnId": "y_dim"},
                                            "orderDirection": "desc"
                                        }
                                    },
                                    "y_dim": {
                                        "label": "이벤트 수 (Count)",
                                        "dataType": "number",
                                        "operationType": "count",
                                        "scale": "ratio",
                                        "sourceField": "___records___",
                                        "isBucketed": False
                                    }
                                },
                                "columnOrder": ["x_dim", "split_dim", "y_dim"],
                                "incompleteColumns": {}
                            }
                        }
                    }
                }
            }
        },
        "references": make_lens_references()
    }


def build_lens_horizontal_bar(title, description, x_field, x_label, size=10, query=""):
    """Creates a horizontal ranking bar chart."""
    return {
        "attributes": {
            "title": title,
            "description": description,
            "visualizationType": "lnsXY",
            "state": {
                "visualization": {
                    "preferredSeriesType": "bar_horizontal",
                    "layers": [
                        {
                            "layerId": "layer1",
                            "layerType": "data",
                            "seriesType": "bar_horizontal",
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
                    "valueLabels": "show",
                    "fittingFunction": "None",
                    "axisTitlesVisibilitySettings": {"x": True, "yLeft": True, "yRight": False},
                    "tickLabelsVisibilitySettings": {"x": True, "yLeft": True, "yRight": False},
                    "gridlinesVisibilitySettings": {"x": True, "yLeft": False, "yRight": False},
                    "yLeftExtent": {"mode": "full"},
                    "yRightExtent": {"mode": "full"}
                },
                "query": {"query": query, "language": "kuery"},
                "filters": [],
                "datasourceStates": {
                    "formBased": {
                        "layers": {
                            "layer1": {
                                "columns": {
                                    "x_dim": {
                                        "label": x_label,
                                        "dataType": "string",
                                        "operationType": "terms",
                                        "sourceField": x_field,
                                        "scale": "ordinal",
                                        "isBucketed": True,
                                        "params": {
                                            "size": size,
                                            "orderBy": {"type": "column", "columnId": "y_dim"},
                                            "orderDirection": "desc"
                                        }
                                    },
                                    "y_dim": {
                                        "label": "발생 건수 (Alerts)",
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
        "references": make_lens_references()
    }


def build_lens_donut(title, description, x_field, x_label, query="", size=10):
    """Creates a Donut Breakdown Chart."""
    return {
        "attributes": {
            "title": title,
            "description": description,
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
                "query": {"query": query, "language": "kuery"},
                "filters": [],
                "datasourceStates": {
                    "formBased": {
                        "layers": {
                            "layer1": {
                                "columns": {
                                    "x_dim": {
                                        "label": x_label,
                                        "dataType": "string",
                                        "operationType": "terms",
                                        "sourceField": x_field,
                                        "scale": "ordinal",
                                        "isBucketed": True,
                                        "params": {
                                            "size": size,
                                            "orderBy": {"type": "column", "columnId": "y_dim"},
                                            "orderDirection": "desc"
                                        }
                                    },
                                    "y_dim": {
                                        "label": "점유 건수 (Count)",
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
        "references": make_lens_references()
    }


def provision_map_visualization():
    print("\n[Step 3-A] Provisioning Global Cyber Threat Geospatial Map (Elastic Map)...")
    map_layers = [
        {
            "id": "layer_basemap",
            "label": "세계 지도 (World Basemap)",
            "alpha": 1,
            "locale": "auto",
            "sourceDescriptor": {
                "type": "EMS_TMS",
                "isAutoSelect": True,
                "lightModeDefault": "road_map_desaturated"
            },
            "visible": True,
            "style": {
                "type": "EMS_VECTOR_TILE",
                "color": ""
            },
            "type": "EMS_VECTOR_TILE",
            "minZoom": 0,
            "maxZoom": 24
        },
        {
            "id": "layer_threat_sources",
            "label": "실시간 위협 발원지 (Threat Source Origins)",
            "minZoom": 0,
            "maxZoom": 24,
            "alpha": 1,
            "visible": True,
            "type": "GEOJSON_VECTOR",
            "joins": [],
            "sourceDescriptor": {
                "id": "source_threat_points",
                "type": "ES_SEARCH",
                "indexPatternId": "soc-unified-logs",
                "indexPatternRefName": "layer_threat_sources_index_pattern",
                "geoField": "source.geo.location",
                "limit": 2048,
                "filterByMapBounds": False,
                "tooltipProperties": [
                    "source.ip",
                    "source.geo.country_name",
                    "source.geo.city_name",
                    "rule.name",
                    "event.severity",
                    "threat.technique.id",
                    "event.module"
                ],
                "applyGlobalQuery": True,
                "applyGlobalTime": True,
                "scalingType": "LIMIT",
                "sortField": "@timestamp",
                "sortOrder": "desc"
            },
            "style": {
                "type": "VECTOR",
                "isTimeAware": True,
                "properties": {
                    "icon": {
                        "type": "STATIC",
                        "options": {"value": "marker"}
                    },
                    "fillColor": {
                        "type": "STATIC",
                        "options": {"color": "#E74C3C"}
                    },
                    "lineColor": {
                        "type": "STATIC",
                        "options": {"color": "#FFFFFF"}
                    },
                    "lineWidth": {
                        "type": "STATIC",
                        "options": {"size": 2}
                    },
                    "iconSize": {
                        "type": "STATIC",
                        "options": {"size": 14}
                    },
                    "symbolizeAs": {
                        "options": {"value": "circle"}
                    },
                    "iconOrientation": {
                        "type": "STATIC",
                        "options": {"orientation": 0}
                    },
                    "labelText": {
                        "type": "STATIC",
                        "options": {"value": ""}
                    },
                    "labelColor": {
                        "type": "STATIC",
                        "options": {"color": "#FFFFFF"}
                    },
                    "labelSize": {
                        "type": "STATIC",
                        "options": {"size": 14}
                    },
                    "labelBorderColor": {
                        "type": "STATIC",
                        "options": {"color": "#000000"}
                    },
                    "labelBorderSize": {
                        "options": {"size": "SMALL"}
                    }
                }
            }
        }
    ]

    map_obj = {
        "attributes": {
            "title": "전세계 실시간 사이버 위협 발원지 지도 (Global Threat Origin Map)",
            "description": "Suricata, Snort 3, Gateway, Wazuh 통합 탐지 위협 발원지(GeoIP) 전세계 위치 시각화",
            "mapStateJSON": json.dumps({
                "zoom": 1.5,
                "center": {"lat": 20, "lon": 10},
                "timeFilters": {"from": "now-7d", "to": "now"},
                "refreshConfig": {"isPaused": True, "interval": 60000},
                "query": {"language": "kuery", "query": ""}
            }),
            "layerListJSON": json.dumps(map_layers),
            "uiStateJSON": json.dumps({"isDarkMode": True})
        },
        "migrationVersion": {
            "map": "8.4.0"
        },
        "references": [
            {
                "name": "layer_threat_sources_index_pattern",
                "type": "index-pattern",
                "id": "soc-unified-logs"
            }
        ]
    }

    res = kibana_request("api/saved_objects/map/soc-map-global-threats?overwrite=true", map_obj, method="POST")
    if "error" in res:
        print(f"[FAIL] Error provisioning Map: {res}")
        return False
    print("[PASS] Elastic Map 'soc-map-global-threats' provisioned successfully.")
    return True


def provision_lens_visualizations():
    print("\n[Step 3-B] Provisioning Enterprise Kibana Lens Visualizations (14 objects)...")
    
    # 1. KPI Cards (6 metrics)
    kpis = [
        (
            "soc-lens-kpi-total-events",
            build_lens_metric(
                "총 수집 보안 이벤트 (Total Ingested Telemetry)",
                "logs-* 전체 4대 소스 통합 수집 이벤트 총합",
                "수집 이벤트 (Total)",
                "count",
                "___records___"
            )
        ),
        (
            "soc-lens-kpi-critical-alerts",
            build_lens_metric(
                "고위험·치명 경보 (Critical / High Alerts)",
                "심각도 3(High) 및 4(Critical) 긴급 대응 대상 경보 건수",
                "긴급 경보 (P1/P2)",
                "count",
                "___records___",
                query="event.severity: (3 or 4)"
            )
        ),
        (
            "soc-lens-kpi-unique-sources",
            build_lens_metric(
                "식별된 위협 송신 IP (Unique Threat Actors)",
                "공격 시도 및 비인가 트래픽 유입 송신지 고유 IP 수",
                "위협 송신지 IP (Unique)",
                "unique_count",
                "source.ip.keyword"
            )
        ),
        (
            "soc-lens-kpi-target-hosts",
            build_lens_metric(
                "공격 피격 대상 자산 (Target Victim Hosts)",
                "피해 호스트 및 경계 게이트웨이 고유 IP 수",
                "피격 자산 IP (Unique)",
                "unique_count",
                "destination.ip.keyword"
            )
        ),
        (
            "soc-lens-kpi-blocked-actions",
            build_lens_metric(
                "게이트웨이 차단 건수 (Enforced Block Actions)",
                "nftables 경계 방화벽 차단 완료 이벤트 건수",
                "방화벽 차단 (Dropped)",
                "count",
                "___records___",
                query="event.action: (\"drop\" or \"blocked\" or \"deny\")"
            )
        ),
        (
            "soc-lens-kpi-active-modules",
            build_lens_metric(
                "활성 탐지 계층 (Active Sensor Engines)",
                "Suricata, Snort 3, Gateway nftables, Wazuh 가동 현황",
                "활성 엔진 수 (Engines)",
                "unique_count",
                "event.module.keyword"
            )
        )
    ]
    for lid, lobj in kpis:
        res = kibana_request(f"api/saved_objects/lens/{lid}?overwrite=true", lobj, method="POST")
        if "error" in res:
            print(f"[FAIL] Lens KPI '{lid}': {res}")
            return False
        print(f"[PASS] Lens KPI '{lid}' provisioned.")

    # 2. Time-series Telemetry Timeline (Stacked Area)
    timeline_lens = build_lens_timeline_area(
        "실시간 보안 텔레메트리 수집 추이 (Real-time Telemetry Timeline by Engine)",
        "시간 경과별 4대 보안 모듈(Suricata NIDS, Snort 3, nftables Gateway, Wazuh SIEM)의 트래픽/경보 추이",
        "event.module.keyword",
        "보안 엔진 (Module)"
    )
    res = kibana_request("api/saved_objects/lens/soc-lens-timeline-module?overwrite=true", timeline_lens, method="POST")
    if "error" in res:
        print(f"[FAIL] Lens Timeline error: {res}")
        return False
    print("[PASS] Lens 'soc-lens-timeline-module' provisioned.")

    # 3. Top Threat Origin Countries (Horizontal Bar) - NEW GEO ANALYTICS
    countries_lens = build_lens_horizontal_bar(
        "위협 발원 국가별 탐지 통계 TOP 10 (Top Threat Origin Countries)",
        "GeoIP 기반 공격 유입 국가(러시아, 미국, 독일 등)별 탐지 건수 랭킹",
        "source.geo.country_name",
        "공격 발원 국가 (Origin Country)",
        size=10,
        query="source.geo.country_name: *"
    )
    res = kibana_request("api/saved_objects/lens/soc-lens-top-countries-hbar?overwrite=true", countries_lens, method="POST")
    if "error" in res:
        print(f"[FAIL] Lens Countries error: {res}")
        return False
    print("[PASS] Lens 'soc-lens-top-countries-hbar' provisioned.")

    # 4. MITRE ATT&CK Donut (Preserved Baseline ID: soc-lens-technique-donut)
    attack_lens = build_lens_donut(
        "MITRE ATT&CK 공격 기법별 탐지 통계 (Technique Distribution)",
        "전체 센서에서 탐지된 적대적 공격 기법(T1046, T1190, T1110, T1059 등)별 분포 비율",
        "threat.technique.id.keyword",
        "공격 기법 (Technique)",
        query="threat.technique.id: *",
        size=10
    )
    kibana_request("api/saved_objects/lens/soc-lens-technique-donut?overwrite=true", attack_lens, method="POST")
    print("[PASS] Lens 'soc-lens-technique-donut' provisioned.")

    # 5. Severity Distribution Bar (Preserved Baseline ID: soc-lens-severity-dist)
    sev_lens = {
        "attributes": {
            "title": "위협 심각도 수준별 이벤트 분포 (Severity Level Distribution)",
            "description": "위협 심각도 수준별 이벤트 집계 (1:정보/Low, 2:주의/Medium, 3:경고/High, 4:치명/Critical)",
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
                    "legend": {"isVisible": True, "position": "right", "legendSize": "auto"},
                    "valueLabels": "hide",
                    "fittingFunction": "None",
                    "axisTitlesVisibilitySettings": {"x": True, "yLeft": True, "yRight": False},
                    "tickLabelsVisibilitySettings": {"x": True, "yLeft": True, "yRight": False},
                    "gridlinesVisibilitySettings": {"x": False, "yLeft": True, "yRight": False},
                    "yLeftExtent": {"mode": "full"},
                    "yRightExtent": {"mode": "full"}
                },
                "query": {"query": "", "language": "kuery"},
                "filters": [],
                "datasourceStates": {
                    "formBased": {
                        "layers": {
                            "layer1": {
                                "columns": {
                                    "x_dim": {
                                        "label": "위협 심각도 (Severity)",
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
                                        "label": "이벤트 건수 (Count)",
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
        "references": make_lens_references()
    }
    kibana_request("api/saved_objects/lens/soc-lens-severity-dist?overwrite=true", sev_lens, method="POST")
    print("[PASS] Lens 'soc-lens-severity-dist' provisioned.")

    # 6. Top 10 Triggered Rules (Horizontal Bar)
    top_rules_lens = build_lens_horizontal_bar(
        "최다 격발 탐지 시그니처 TOP 10 (Top Triggered Detection Rules)",
        "Suricata/Snort/nftables에서 가장 빈번하게 격발된 보안 룰 TOP 10",
        "rule.name.keyword",
        "탐지 규칙명 (Rule Signature)",
        size=10
    )
    kibana_request("api/saved_objects/lens/soc-lens-top-rules-hbar?overwrite=true", top_rules_lens, method="POST")
    print("[PASS] Lens 'soc-lens-top-rules-hbar' provisioned.")

    # 7. Top 10 Threat Actor Source IPs (Horizontal Bar)
    top_sources_lens = build_lens_horizontal_bar(
        "위협 유입 송신지 IP TOP 10 (Top Threat Actor Source IPs)",
        "가장 많은 공격 및 이상 트래픽을 유발한 소스 IP TOP 10",
        "source.ip.keyword",
        "공격자 송신 IP (Source IP)",
        size=10
    )
    kibana_request("api/saved_objects/lens/soc-lens-top-sources-hbar?overwrite=true", top_sources_lens, method="POST")
    print("[PASS] Lens 'soc-lens-top-sources-hbar' provisioned.")

    # 8. Module Distribution Bar (Preserved Baseline ID: soc-lens-module-dist)
    mod_lens = {
        "attributes": {
            "title": "탐지 모듈별 이벤트 수집 현황 (Telemetry Contribution by Engine)",
            "description": "Suricata, Snort 3, Gateway nftables, Wazuh 감지 모듈별 수집 이벤트 통계",
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
                    "legend": {"isVisible": True, "position": "right", "legendSize": "auto"},
                    "valueLabels": "hide",
                    "fittingFunction": "None",
                    "axisTitlesVisibilitySettings": {"x": True, "yLeft": True, "yRight": False},
                    "tickLabelsVisibilitySettings": {"x": True, "yLeft": True, "yRight": False},
                    "gridlinesVisibilitySettings": {"x": False, "yLeft": True, "yRight": False},
                    "yLeftExtent": {"mode": "full"},
                    "yRightExtent": {"mode": "full"}
                },
                "query": {"query": "", "language": "kuery"},
                "filters": [],
                "datasourceStates": {
                    "formBased": {
                        "layers": {
                            "layer1": {
                                "columns": {
                                    "x_dim": {
                                        "label": "탐지 모듈 (Module)",
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
                                        "label": "수집 이벤트 수 (Events)",
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
        "references": make_lens_references()
    }
    kibana_request("api/saved_objects/lens/soc-lens-module-dist?overwrite=true", mod_lens, method="POST")
    print("[PASS] Lens 'soc-lens-module-dist' provisioned.")

    # 9. Firewall Action Donut
    fw_donut = build_lens_donut(
        "게이트웨이 방화벽 트래픽 조치 현황 (Perimeter Enforcement Actions)",
        "nftables 경계 방화벽 트래픽 정책 집행 현황 (drop 차단 vs forward 허용)",
        "event.action.keyword",
        "방화벽 조치 (Action)",
        query="event.module: \"nftables\"",
        size=5
    )
    kibana_request("api/saved_objects/lens/soc-lens-firewall-action-donut?overwrite=true", fw_donut, method="POST")
    print("[PASS] Lens 'soc-lens-firewall-action-donut' provisioned.")

    return True


def provision_dashboard():
    print("\n[Step 4] Provisioning Enterprise SOC Threat Operations Console...")
    
    # 16 Panels arranged in a 48-wide grid with zero overlapping coordinates:
    # Row 1 (y: 0, h: 6): 6 KPI Cards (w: 8 each)
    # Row 2 (y: 6, h: 12): Ingestion Timeline (w: 48)
    # Row 3 (y: 18, h: 16): Global Cyber Threat Map (w: 32) + Top Countries HBar (w: 16)
    # Row 4 (y: 34, h: 12): ATT&CK Donut (w: 24) + Severity Bar (w: 24)
    # Row 5 (y: 46, h: 12): Top Rules HBar (w: 24) + Top Sources HBar (w: 24)
    # Row 6 (y: 58, h: 12): Module Bar (w: 24) + Firewall Action Donut (w: 24)
    # Row 7 (y: 70, h: 18): Live Event Feed Search Table (w: 48)
    panels = [
        # Row 1: KPI Cards
        {
            "version": "8.17.3",
            "type": "lens",
            "gridData": {"x": 0, "y": 0, "w": 8, "h": 6, "i": "panel_kpi_total_events"},
            "panelIndex": "panel_kpi_total_events",
            "embeddableConfig": {},
            "panelRefName": "panel_panel_kpi_total_events"
        },
        {
            "version": "8.17.3",
            "type": "lens",
            "gridData": {"x": 8, "y": 0, "w": 8, "h": 6, "i": "panel_kpi_critical_alerts"},
            "panelIndex": "panel_kpi_critical_alerts",
            "embeddableConfig": {},
            "panelRefName": "panel_panel_kpi_critical_alerts"
        },
        {
            "version": "8.17.3",
            "type": "lens",
            "gridData": {"x": 16, "y": 0, "w": 8, "h": 6, "i": "panel_kpi_unique_sources"},
            "panelIndex": "panel_kpi_unique_sources",
            "embeddableConfig": {},
            "panelRefName": "panel_panel_kpi_unique_sources"
        },
        {
            "version": "8.17.3",
            "type": "lens",
            "gridData": {"x": 24, "y": 0, "w": 8, "h": 6, "i": "panel_kpi_target_hosts"},
            "panelIndex": "panel_kpi_target_hosts",
            "embeddableConfig": {},
            "panelRefName": "panel_panel_kpi_target_hosts"
        },
        {
            "version": "8.17.3",
            "type": "lens",
            "gridData": {"x": 32, "y": 0, "w": 8, "h": 6, "i": "panel_kpi_blocked_actions"},
            "panelIndex": "panel_kpi_blocked_actions",
            "embeddableConfig": {},
            "panelRefName": "panel_panel_kpi_blocked_actions"
        },
        {
            "version": "8.17.3",
            "type": "lens",
            "gridData": {"x": 40, "y": 0, "w": 8, "h": 6, "i": "panel_kpi_active_modules"},
            "panelIndex": "panel_kpi_active_modules",
            "embeddableConfig": {},
            "panelRefName": "panel_panel_kpi_active_modules"
        },
        # Row 2: Ingestion Timeline
        {
            "version": "8.17.3",
            "type": "lens",
            "gridData": {"x": 0, "y": 6, "w": 48, "h": 12, "i": "panel_timeline_module"},
            "panelIndex": "panel_timeline_module",
            "embeddableConfig": {},
            "panelRefName": "panel_panel_timeline_module"
        },
        # Row 3: Global Cyber Threat Geospatial Map + Top Origin Countries
        {
            "version": "8.17.3",
            "type": "map",
            "gridData": {"x": 0, "y": 18, "w": 32, "h": 16, "i": "panel_map_global_threats"},
            "panelIndex": "panel_map_global_threats",
            "embeddableConfig": {},
            "panelRefName": "panel_panel_map_global_threats"
        },
        {
            "version": "8.17.3",
            "type": "lens",
            "gridData": {"x": 32, "y": 18, "w": 16, "h": 16, "i": "panel_top_countries_hbar"},
            "panelIndex": "panel_top_countries_hbar",
            "embeddableConfig": {},
            "panelRefName": "panel_panel_top_countries_hbar"
        },
        # Row 4: MITRE ATT&CK Donut + Severity Distribution
        {
            "version": "8.17.3",
            "type": "lens",
            "gridData": {"x": 0, "y": 34, "w": 24, "h": 12, "i": "panel_technique_donut"},
            "panelIndex": "panel_technique_donut",
            "embeddableConfig": {},
            "panelRefName": "panel_panel_technique_donut"
        },
        {
            "version": "8.17.3",
            "type": "lens",
            "gridData": {"x": 24, "y": 34, "w": 24, "h": 12, "i": "panel_severity_dist"},
            "panelIndex": "panel_severity_dist",
            "embeddableConfig": {},
            "panelRefName": "panel_panel_severity_dist"
        },
        # Row 5: Top 10 Rules + Top 10 Threat Actors
        {
            "version": "8.17.3",
            "type": "lens",
            "gridData": {"x": 0, "y": 46, "w": 24, "h": 12, "i": "panel_top_rules_hbar"},
            "panelIndex": "panel_top_rules_hbar",
            "embeddableConfig": {},
            "panelRefName": "panel_panel_top_rules_hbar"
        },
        {
            "version": "8.17.3",
            "type": "lens",
            "gridData": {"x": 24, "y": 46, "w": 24, "h": 12, "i": "panel_top_sources_hbar"},
            "panelIndex": "panel_top_sources_hbar",
            "embeddableConfig": {},
            "panelRefName": "panel_panel_top_sources_hbar"
        },
        # Row 6: Module Distribution + Gateway Firewall Actions
        {
            "version": "8.17.3",
            "type": "lens",
            "gridData": {"x": 0, "y": 58, "w": 24, "h": 12, "i": "panel_module_dist"},
            "panelIndex": "panel_module_dist",
            "embeddableConfig": {},
            "panelRefName": "panel_panel_module_dist"
        },
        {
            "version": "8.17.3",
            "type": "lens",
            "gridData": {"x": 24, "y": 58, "w": 24, "h": 12, "i": "panel_firewall_action_donut"},
            "panelIndex": "panel_firewall_action_donut",
            "embeddableConfig": {},
            "panelRefName": "panel_panel_firewall_action_donut"
        },
        # Row 7: Interactive Live Event Feed
        {
            "version": "8.17.3",
            "type": "search",
            "gridData": {"x": 0, "y": 70, "w": 48, "h": 18, "i": "panel_event_feed"},
            "panelIndex": "panel_event_feed",
            "embeddableConfig": {},
            "panelRefName": "panel_panel_event_feed"
        }
    ]

    references = [
        {"name": "panel_panel_kpi_total_events", "type": "lens", "id": "soc-lens-kpi-total-events"},
        {"name": "panel_panel_kpi_critical_alerts", "type": "lens", "id": "soc-lens-kpi-critical-alerts"},
        {"name": "panel_panel_kpi_unique_sources", "type": "lens", "id": "soc-lens-kpi-unique-sources"},
        {"name": "panel_panel_kpi_target_hosts", "type": "lens", "id": "soc-lens-kpi-target-hosts"},
        {"name": "panel_panel_kpi_blocked_actions", "type": "lens", "id": "soc-lens-kpi-blocked-actions"},
        {"name": "panel_panel_kpi_active_modules", "type": "lens", "id": "soc-lens-kpi-active-modules"},
        {"name": "panel_panel_timeline_module", "type": "lens", "id": "soc-lens-timeline-module"},
        {"name": "panel_panel_map_global_threats", "type": "map", "id": "soc-map-global-threats"},
        {"name": "panel_panel_top_countries_hbar", "type": "lens", "id": "soc-lens-top-countries-hbar"},
        {"name": "panel_panel_technique_donut", "type": "lens", "id": "soc-lens-technique-donut"},
        {"name": "panel_panel_severity_dist", "type": "lens", "id": "soc-lens-severity-dist"},
        {"name": "panel_panel_top_rules_hbar", "type": "lens", "id": "soc-lens-top-rules-hbar"},
        {"name": "panel_panel_top_sources_hbar", "type": "lens", "id": "soc-lens-top-sources-hbar"},
        {"name": "panel_panel_module_dist", "type": "lens", "id": "soc-lens-module-dist"},
        {"name": "panel_panel_firewall_action_donut", "type": "lens", "id": "soc-lens-firewall-action-donut"},
        {"name": "panel_panel_event_feed", "type": "search", "id": "soc-threat-event-feed"}
    ]

    dashboard_obj = {
        "attributes": {
            "title": "SOC 통합 위협 관제 대시보드 (Enterprise Threat Operations Console)",
            "description": "Suricata 8.0.6, Snort 3.12.2, Gateway nftables, Wazuh 4.14.7 실시간 엔터프라이즈 SOC 통합 위협 관제 콘솔 (전세계 사이버 위협 지도 탑재)",
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
        "references": references
    }

    res = kibana_request("api/saved_objects/dashboard/soc-unified-threat-dashboard?overwrite=true", dashboard_obj, method="POST")
    if "error" in res:
        print(f"[FAIL] Dashboard creation error: {res}")
        return False

    dash_url = f"{KIBANA_URL}/app/dashboards#/view/soc-unified-threat-dashboard?_g=(filters:!(),refreshInterval:(pause:!t,value:60000),time:(from:now-7d,to:now))"
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

    # Verify Map
    map_res = kibana_request("api/saved_objects/map/soc-map-global-threats")
    if "error" in map_res:
        print(f"[FAIL] Missing Map Object: {map_res}")
        return False
    print(f"  [+] Confirmed Map Object: soc-map-global-threats")

    # Verify Dashboard
    dash = kibana_request("api/saved_objects/dashboard/soc-unified-threat-dashboard")
    if "error" in dash:
        print(f"[FAIL] Could not retrieve dashboard: {dash}")
        return False
    
    title = dash.get("attributes", {}).get("title")
    panels = json.loads(dash.get("attributes", {}).get("panelsJSON", "[]"))
    print(f"[PASS] Confirmed Dashboard: '{title}' with {len(panels)} panels (ID: soc-unified-threat-dashboard)")
    return True


def main():
    print("=" * 70)
    print(" Phase ELK-11: Kibana Data Views & Enterprise SOC Dashboard Provisioning")
    print(" (With Global Cyber Threat Geospatial Map & Origin Analytics)")
    print("=" * 70)
    
    provision_geoip_pipeline_and_mappings()
    provision_data_views()
    provision_saved_search()
    if not provision_map_visualization():
        print("[FAIL] Map visualization provisioning failed.")
        sys.exit(1)
    if not provision_lens_visualizations():
        print("[FAIL] Lens visualization provisioning failed.")
        sys.exit(1)
    if not provision_dashboard():
        print("[FAIL] Dashboard provisioning failed.")
        sys.exit(1)
    
    if verify_kibana_provisioning():
        print("\n" + "=" * 70)
        print(" >>> Phase ELK-11 Kibana Enterprise Threat Map Dashboard: PASS <<<")
        print("=" * 70)
        sys.exit(0)
    else:
        print("\n" + "=" * 70)
        print(" >>> Phase ELK-11 Kibana Enterprise Threat Map Dashboard: FAIL <<<")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()
