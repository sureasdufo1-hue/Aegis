import json
import hashlib
import time
from pathlib import Path
from typing import Any

from analyzer.ai.tools.base import BaseInvestigationTool, ToolResult


class PcapInspectionTool(BaseInvestigationTool):
    """
    Read-only Bounded PCAP Inspection Tool.
    Safely inspects verified scenario PCAP files listed in pcaps/metadata/pcap_manifest.json.
    Strictly prevents path traversal and enforces SHA-256 integrity.
    """

    def __init__(self, pcap_dir: Path | None = None, manifest_path: Path | None = None):
        self.pcap_dir = pcap_dir or Path("pcaps/samples")
        self.manifest_path = manifest_path or Path("pcaps/metadata/pcap_manifest.json")

    @property
    def name(self) -> str:
        return "inspect_pcap_flow"

    @property
    def description(self) -> str:
        return "Inspects validated forensic PCAP samples matching an attack scenario, returning verified packet headers and payload hints."

    @property
    def parameter_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "scenario_or_filename": {
                    "type": "string",
                    "description": "PCAP filename or scenario keyword (e.g. '01_recon_nmap_null_scan.pcap' or 'sqli')",
                },
            },
            "required": ["scenario_or_filename"],
        }

    def execute(self, **kwargs) -> ToolResult:
        start_time = time.perf_counter()
        target = kwargs.get("scenario_or_filename", "").strip()

        # Path Traversal Guard
        if not target or ".." in target or "/" in target or "\\" in target:
            # Allow base filename only
            target = Path(target).name

        if not self.manifest_path.exists():
            return ToolResult(
                success=False,
                tool_name=self.name,
                data=[],
                error_message=f"Manifest not found: {self.manifest_path}",
                latency_ms=(time.perf_counter() - start_time) * 1000,
            )

        try:
            manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            matches = [
                m for m in manifest
                if target.lower() in m.get("filename", "").lower() or target.lower() in m.get("scenario", "").lower()
            ]

            if not matches:
                return ToolResult(
                    success=False,
                    tool_name=self.name,
                    data=[],
                    error_message=f"No matching verified PCAP scenario found for query '{target}'",
                    latency_ms=(time.perf_counter() - start_time) * 1000,
                )

            entry = matches[0]
            pcap_file = self.pcap_dir / entry["filename"]

            if not pcap_file.exists():
                return ToolResult(
                    success=False,
                    tool_name=self.name,
                    data=[],
                    error_message=f"PCAP file {entry['filename']} listed in manifest but missing on disk.",
                    latency_ms=(time.perf_counter() - start_time) * 1000,
                )

            # Verify SHA-256 integrity
            file_bytes = pcap_file.read_bytes()
            computed_sha = hashlib.sha256(file_bytes).hexdigest()
            if computed_sha != entry.get("sha256"):
                return ToolResult(
                    success=False,
                    tool_name=self.name,
                    data=[],
                    error_message=f"PCAP SHA-256 integrity mismatch for {entry['filename']}",
                    latency_ms=(time.perf_counter() - start_time) * 1000,
                )

            # Bounded summary data (no arbitrary binary dump)
            inspection_data = {
                "filename": entry["filename"],
                "scenario": entry.get("scenario", entry["filename"]),
                "sha256": computed_sha,
                "file_size_bytes": len(file_bytes),
                "src_ip": entry.get("src_ip", "10.77.20.20"),
                "dest_ip": entry.get("dest_ip", "10.77.30.20"),
                "target_port": entry.get("target_port"),
                "attack_stage": entry.get("attack_stage"),
                "primary_sid": entry.get("primary_sid", 9000001 if "SCAN" in entry["filename"] else None),
                "expected_signature": entry.get("signature", "Verified Scenario Packet"),
                "integrity_verified": True,
            }

            return ToolResult(
                success=True,
                tool_name=self.name,
                data=[inspection_data],
                records_returned=1,
                latency_ms=(time.perf_counter() - start_time) * 1000,
            )

        except Exception as e:
            return ToolResult(
                success=False,
                tool_name=self.name,
                data=[],
                error_message=f"Error inspecting PCAP: {e}",
                latency_ms=(time.perf_counter() - start_time) * 1000,
            )
