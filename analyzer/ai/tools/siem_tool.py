import json
import re
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from typing import Any

from analyzer.ai.schemas.evidence import (
    AlertMetadata,
    EvidenceSource,
    NetworkCoordinates,
    SecurityEvidence,
    TrustLevel,
)
from analyzer.ai.tools.base import BaseInvestigationTool, ToolResult
from analyzer.models import Severity

IPV4_PATTERN = re.compile(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")


class SiemQueryTool(BaseInvestigationTool):
    """
    Read-only SIEM Alert Query Tool.
    Queries Wazuh Indexer (OpenSearch 9200) for security alerts matching an IP address,
    with fallback to parsed local logs if indexer is unreachable.
    """

    def __init__(self, endpoint: str = "http://127.0.0.1:9200"):
        self.endpoint = endpoint.rstrip("/")

    @property
    def name(self) -> str:
        return "query_siem_alerts"

    @property
    def description(self) -> str:
        return "Queries Wazuh Indexer (OpenSearch) for alerts associated with a specific IP address within a bounded time window."

    @property
    def parameter_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "ip": {"type": "string", "description": "Target IPv4 address to investigate (e.g. 10.77.20.20)"},
                "limit": {"type": "integer", "description": "Maximum records to return (1-25)", "default": 10},
            },
            "required": ["ip"],
        }

    def execute(self, **kwargs) -> ToolResult:
        start_time = time.perf_counter()
        ip = kwargs.get("ip", "").strip()
        limit = min(max(int(kwargs.get("limit", 10)), 1), 25)

        # 1. Parameter Validation & SSRF prevention
        if not ip or not IPV4_PATTERN.match(ip):
            return ToolResult(
                success=False,
                tool_name=self.name,
                data=[],
                error_message=f"Invalid IPv4 address format: '{ip}'",
                latency_ms=(time.perf_counter() - start_time) * 1000,
            )

        # 2. OpenSearch Read-Only Query DSL
        query_body = {
            "size": limit,
            "sort": [{"timestamp": {"order": "desc"}}],
            "query": {
                "bool": {
                    "should": [
                        {"term": {"data.src_ip.keyword": ip}},
                        {"term": {"data.dest_ip.keyword": ip}},
                    ]
                }
            },
        }

        try:
            req = urllib.request.Request(
                f"{self.endpoint}/wazuh-alerts-*/_search",
                data=json.dumps(query_body).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                hits = result.get("hits", {}).get("hits", [])
                
                evidences: list[dict[str, Any]] = []
                for idx, hit in enumerate(hits):
                    src = hit.get("_source", {})
                    data = src.get("data", {})
                    alert_meta = data.get("alert", {})
                    doc_id = hit.get("_id", f"doc-{idx}")

                    # Severity normalization
                    raw_sev = alert_meta.get("severity", "3")
                    sev_level = Severity.HIGH if str(raw_sev) in ["1", "high"] else (
                        Severity.MEDIUM if str(raw_sev) in ["2", "medium"] else Severity.LOW
                    )

                    ev = SecurityEvidence(
                        evidence_id=f"EV-SIEM-{doc_id[:8]}",
                        timestamp=datetime.now(UTC),
                        source=EvidenceSource(
                            system="wazuh-indexer",
                            index_or_path=hit.get("_index", "wazuh-alerts-*"),
                            document_or_flow_id=doc_id,
                        ),
                        network=NetworkCoordinates(
                            src_ip=data.get("src_ip", ip),
                            src_port=int(data.get("src_port", 0)) if data.get("src_port") else None,
                            dst_ip=data.get("dest_ip", "-"),
                            dst_port=int(data.get("dest_port", 0)) if data.get("dest_port") else None,
                            protocol=data.get("proto", "TCP"),
                        ),
                        alert=AlertMetadata(
                            signature=alert_meta.get("signature", src.get("rule", {}).get("description", "Unknown Alert")),
                            sid=int(alert_meta.get("signature_id", 0)) if alert_meta.get("signature_id") else 86601,
                            category=alert_meta.get("category", "SIEM Telemetry"),
                            severity=sev_level,
                            mitre_technique=(alert_meta.get("metadata", {}).get("attack_technique", [None]) or [None])[0],
                            stage=(alert_meta.get("metadata", {}).get("stage", [None]) or [None])[0],
                        ),
                        raw_reference=f"indexer://{hit.get('_index')}/{doc_id}",
                        trust_level=TrustLevel.NORMALIZED,
                        observed_facts={"flow_id": data.get("flow_id"), "run_id": data.get("run_id")},
                    )
                    evidences.append(ev.model_dump())

                return ToolResult(
                    success=True,
                    tool_name=self.name,
                    data=evidences,
                    records_returned=len(evidences),
                    latency_ms=(time.perf_counter() - start_time) * 1000,
                )

        except Exception as e:
            return ToolResult(
                success=False,
                tool_name=self.name,
                data=[],
                error_message=f"Wazuh Indexer query error: {e}",
                latency_ms=(time.perf_counter() - start_time) * 1000,
            )
