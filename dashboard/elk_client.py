"""
elk_client.py
FastAPI backend integration client for Elasticsearch 8.17.3 and Kibana in SOC Detection Lab.
Provides real-time health checks, cross-stream search, timeline correlation, and threat statistics.
"""

import base64
import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://127.0.0.1:9201")
ELASTICSEARCH_USER = os.getenv("ELASTICSEARCH_USER", "elastic")
ELASTICSEARCH_PASSWORD = os.getenv("ELASTICSEARCH_PASSWORD", "changeme_soc_lab_strong_pass_2026")
KIBANA_URL = os.getenv("KIBANA_URL", "http://127.0.0.1:5602")

AUTH_TOKEN = base64.b64encode(f"{ELASTICSEARCH_USER}:{ELASTICSEARCH_PASSWORD}".encode()).decode()
AUTH_HEADER = f"Basic {AUTH_TOKEN}"
INDEX_PATTERN = "logs-*"


def es_request(path: str, payload: Optional[Dict[str, Any]] = None, method: Optional[str] = None, timeout: float = 5.0) -> Dict[str, Any]:
    url = f"{ELASTICSEARCH_URL}/{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    if method is None:
        method = "POST" if data is not None else "GET"

    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": AUTH_HEADER,
            "Content-Type": "application/json"
        },
        method=method
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content = resp.read().decode("utf-8")
            return json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        return {"error": e.code, "message": err_body}
    except Exception as e:
        return {"error": 503, "message": str(e)}


def kibana_status_check(timeout: float = 3.0) -> Dict[str, Any]:
    url = f"{KIBANA_URL}/api/status"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": AUTH_HEADER,
            "kbn-xsrf": "true"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            level = data.get("status", {}).get("overall", {}).get("level", "unavailable")
            return {"status": level, "available": level == "available"}
    except Exception as e:
        return {"status": "unavailable", "available": False, "error": str(e)}


def get_elk_cluster_health() -> Dict[str, Any]:
    es_health = es_request("_cluster/health")
    kib_health = kibana_status_check()

    if "error" in es_health:
        return {
            "status": "unavailable",
            "elasticsearch": {"status": "unavailable", "error": es_health.get("message")},
            "kibana": kib_health,
            "cluster_status": "RED",
            "kibana_dashboard_url": f"{KIBANA_URL}/app/dashboards#/view/soc-unified-threat-dashboard"
        }

    status = es_health.get("status", "unknown").upper()
    return {
        "status": "healthy" if status == "GREEN" and kib_health.get("available") else "degraded",
        "cluster_name": es_health.get("cluster_name", "soc-elk-cluster"),
        "cluster_status": status,
        "nodes": es_health.get("number_of_nodes", 0),
        "active_primary_shards": es_health.get("active_primary_shards", 0),
        "active_shards_percent": es_health.get("active_shards_percent_as_number", 0.0),
        "kibana": kib_health,
        "kibana_url": KIBANA_URL,
        "kibana_dashboard_url": f"{KIBANA_URL}/app/dashboards#/view/soc-unified-threat-dashboard"
    }


def get_elk_events(limit: int = 50, module: Optional[str] = None, severity: Optional[int] = None) -> Dict[str, Any]:
    must_clauses: List[Dict[str, Any]] = []
    if module:
        must_clauses.append({"term": {"event.module.keyword": module}})
    if severity is not None:
        must_clauses.append({"term": {"event.severity": severity}})

    query: Dict[str, Any] = {
        "size": min(limit, 100),
        "sort": [{"@timestamp": {"order": "desc"}}],
        "query": {"bool": {"must": must_clauses}} if must_clauses else {"match_all": {}}
    }

    res = es_request(f"{INDEX_PATTERN}/_search", query)
    if "error" in res:
        return {"total": 0, "events": [], "error": res.get("message")}

    hits = res.get("hits", {}).get("hits", [])
    total = res.get("hits", {}).get("total", {}).get("value", 0)

    events: List[Dict[str, Any]] = []
    for h in hits:
        src = h.get("_source", {})
        events.append({
            "id": h.get("_id"),
            "index": h.get("_index"),
            "timestamp": src.get("@timestamp"),
            "module": src.get("event", {}).get("module"),
            "dataset": src.get("event", {}).get("dataset"),
            "action": src.get("event", {}).get("action"),
            "severity": src.get("event", {}).get("severity"),
            "rule_name": src.get("rule", {}).get("name"),
            "rule_id": src.get("rule", {}).get("id"),
            "source_ip": src.get("source", {}).get("ip"),
            "source_port": src.get("source", {}).get("port"),
            "destination_ip": src.get("destination", {}).get("ip"),
            "destination_port": src.get("destination", {}).get("port"),
            "protocol": src.get("network", {}).get("transport"),
            "mitre_technique": src.get("threat", {}).get("technique", {}).get("id"),
            "host": src.get("host", {}).get("name")
        })

    return {"total": total, "count": len(events), "events": events}


def get_elk_timeline(ip: str, limit: int = 50) -> Dict[str, Any]:
    query = {
        "size": min(limit, 100),
        "sort": [{"@timestamp": {"order": "asc"}}],
        "query": {
            "term": {
                "related.ip.keyword": ip
            }
        }
    }

    res = es_request(f"{INDEX_PATTERN}/_search", query)
    if "error" in res:
        return {"ip": ip, "total": 0, "timeline": [], "error": res.get("message")}

    hits = res.get("hits", {}).get("hits", [])
    total = res.get("hits", {}).get("total", {}).get("value", 0)

    timeline: List[Dict[str, Any]] = []
    modules_involved = set()
    for h in hits:
        src = h.get("_source", {})
        mod = src.get("event", {}).get("module", "unknown")
        modules_involved.add(mod)
        timeline.append({
            "id": h.get("_id"),
            "index": h.get("_index"),
            "timestamp": src.get("@timestamp"),
            "module": mod,
            "action": src.get("event", {}).get("action"),
            "severity": src.get("event", {}).get("severity"),
            "rule_name": src.get("rule", {}).get("name"),
            "source_ip": src.get("source", {}).get("ip"),
            "destination_ip": src.get("destination", {}).get("ip"),
            "mitre_technique": src.get("threat", {}).get("technique", {}).get("id")
        })

    return {
        "ip": ip,
        "total": total,
        "modules_count": len(modules_involved),
        "modules": list(modules_involved),
        "timeline": timeline
    }


def get_elk_stats() -> Dict[str, Any]:
    query = {
        "size": 0,
        "aggs": {
            "by_module": {
                "terms": {"field": "event.module.keyword", "size": 10}
            },
            "by_severity": {
                "terms": {"field": "event.severity", "size": 5}
            },
            "by_technique": {
                "terms": {"field": "threat.technique.id.keyword", "size": 10}
            }
        }
    }

    res = es_request(f"{INDEX_PATTERN}/_search", query)
    if "error" in res:
        return {"error": res.get("message")}

    aggs = res.get("aggregations", {})
    total = res.get("hits", {}).get("total", {}).get("value", 0)

    return {
        "total_documents": total,
        "modules": {b["key"]: b["doc_count"] for b in aggs.get("by_module", {}).get("buckets", [])},
        "severities": {str(b["key"]): b["doc_count"] for b in aggs.get("by_severity", {}).get("buckets", [])},
        "top_techniques": {b["key"]: b["doc_count"] for b in aggs.get("by_technique", {}).get("buckets", [])}
    }
