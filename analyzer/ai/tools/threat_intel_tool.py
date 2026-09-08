import time
from typing import Any

from analyzer.ai.tools.base import BaseInvestigationTool, ToolResult
from analyzer.detection.threat_intel import ThreatIntelEngine


class ThreatIntelLookupTool(BaseInvestigationTool):
    """
    Read-only Threat Intelligence Indicator Lookup Tool.
    Queries the known IOC database for malicious reputation.
    Invariant: A lookup miss is NOT treated as 'benign'; it is reported as UNKNOWN / UNMATCHED.
    """

    @property
    def name(self) -> str:
        return "lookup_threat_intel"

    @property
    def description(self) -> str:
        return "Queries verified IOC threat intelligence database for IP addresses or domain names."

    @property
    def parameter_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "indicator": {
                    "type": "string",
                    "description": "IP address or domain name to query (e.g. '198.51.100.44' or 'evil-c2.lab')",
                },
            },
            "required": ["indicator"],
        }

    def execute(self, **kwargs) -> ToolResult:
        start_time = time.perf_counter()
        indicator = kwargs.get("indicator", "").strip()

        if not indicator:
            return ToolResult(
                success=False,
                tool_name=self.name,
                data=[],
                error_message="Indicator cannot be empty.",
                latency_ms=(time.perf_counter() - start_time) * 1000,
            )

        # Check IP
        ip_match = ThreatIntelEngine.check_ip(indicator)
        if ip_match:
            return ToolResult(
                success=True,
                tool_name=self.name,
                data=[{
                    "indicator": ip_match.indicator,
                    "type": ip_match.indicator_type,
                    "threat_group": ip_match.threat_group,
                    "confidence": ip_match.confidence,
                    "description": ip_match.description,
                    "verdict": "KNOWN_MALICIOUS_IOC",
                }],
                records_returned=1,
                latency_ms=(time.perf_counter() - start_time) * 1000,
            )

        # Check Domain
        domain_match = ThreatIntelEngine.check_domain(indicator)
        if domain_match:
            return ToolResult(
                success=True,
                tool_name=self.name,
                data=[{
                    "indicator": domain_match.indicator,
                    "type": domain_match.indicator_type,
                    "threat_group": domain_match.threat_group,
                    "confidence": domain_match.confidence,
                    "description": domain_match.description,
                    "verdict": "KNOWN_MALICIOUS_IOC",
                }],
                records_returned=1,
                latency_ms=(time.perf_counter() - start_time) * 1000,
            )

        # No match - Must NOT declare benign
        return ToolResult(
            success=True,
            tool_name=self.name,
            data=[{
                "indicator": indicator,
                "verdict": "NO_RECORDED_IOC",
                "confidence": 0.0,
                "note": "Absence of threat intel hit does NOT prove benign behavior.",
            }],
            records_returned=1,
            latency_ms=(time.perf_counter() - start_time) * 1000,
        )
