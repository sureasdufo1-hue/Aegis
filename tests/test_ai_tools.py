from analyzer.ai.tools.pcap_tool import PcapInspectionTool
from analyzer.ai.tools.registry import ToolRegistry
from analyzer.ai.tools.siem_tool import SiemQueryTool
from analyzer.ai.tools.threat_intel_tool import ThreatIntelLookupTool


def test_tool_registry_registration_and_declarations():
    registry = ToolRegistry(max_calls_per_session=3)
    registry.register(ThreatIntelLookupTool())
    registry.register(PcapInspectionTool())

    decls = registry.list_tool_declarations()
    assert len(decls) == 2
    tool_names = [d["name"] for d in decls]
    assert "lookup_threat_intel" in tool_names
    assert "inspect_pcap_flow" in tool_names


def test_tool_registry_bounded_call_limit():
    registry = ToolRegistry(max_calls_per_session=2)
    registry.register(ThreatIntelLookupTool())

    res1 = registry.execute_tool("lookup_threat_intel", {"indicator": "198.51.100.44"})
    assert res1.success is True

    res2 = registry.execute_tool("lookup_threat_intel", {"indicator": "8.8.8.8"})
    assert res2.success is True

    # 3rd call should hit bounded execution limit
    res3 = registry.execute_tool("lookup_threat_intel", {"indicator": "1.1.1.1"})
    assert res3.success is False
    assert "limit exceeded" in res3.error_message.lower()
    assert len(registry.audit_log) == 3


def test_threat_intel_tool_match_and_no_benign_assumption():
    ti_tool = ThreatIntelLookupTool()
    
    # Known malicious IOC
    res_hit = ti_tool.execute(indicator="198.51.100.44")
    assert res_hit.success is True
    assert res_hit.data[0]["threat_group"] == "CobaltStrike_C2"
    assert res_hit.data[0]["verdict"] == "KNOWN_MALICIOUS_IOC"

    # Miss: must not declare benign
    res_miss = ti_tool.execute(indicator="10.77.20.20")
    assert res_miss.success is True
    assert res_miss.data[0]["verdict"] == "NO_RECORDED_IOC"
    assert "not prove benign" in res_miss.data[0]["note"].lower()


def test_pcap_tool_manifest_verification_and_path_traversal_guard():
    pcap_tool = PcapInspectionTool()

    # Valid query matching sample
    res_valid = pcap_tool.execute(scenario_or_filename="PCAP-20260824-ATK-003-SCAN.pcap")
    assert res_valid.success is True
    assert res_valid.data[0]["integrity_verified"] is True
    assert res_valid.data[0]["primary_sid"] == 9000001

    # Path traversal attempt
    res_traversal = pcap_tool.execute(scenario_or_filename="../../windows/system32/cmd.exe")
    assert res_traversal.success is False
    assert "No matching verified PCAP" in res_traversal.error_message


def test_siem_query_tool_input_validation():
    siem_tool = SiemQueryTool()
    
    # Invalid IP format / injection attempt
    res_invalid = siem_tool.execute(ip="10.77.20.20; rm -rf /")
    assert res_invalid.success is False
    assert "Invalid IPv4 address format" in res_invalid.error_message
