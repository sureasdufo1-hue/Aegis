"""Unit & Integration tests for E2E SOC Pipeline Demonstration Runner

and Master Release Gate (GATE-RELEASE-01) Verification.
"""

from pathlib import Path
from scripts.run_e2e_soc_demonstration import run_e2e_demonstration
from scripts.verify_master_release_gate import run_master_release_verification


def test_e2e_demonstration_runner_completes_all_stages(tmp_path: Path):
    """Verify that run_e2e_demonstration() executes all 8 stages successfully without regressions."""
    report = run_e2e_demonstration(output_dir=tmp_path)

    assert report["overall_status"] == "PASS"
    stages = report["stages"]
    assert len(stages) == 8

    # Stage 1: Network & Mirror NIC
    s1 = stages["1_network_telemetry"]
    assert s1["status"] == "PASS"
    assert "NO L3 IP" in s1["nic_monitor_ip"]

    # Stage 2: Attack Simulation
    s2 = stages["2_attack_simulation"]
    assert s2["status"] == "PASS"
    assert len(s2["injected_scenarios"]) == 3
    assert s2["total_alerts_emitted"] >= 6

    # Stage 3: Dual IDS Detection
    s3 = stages["3_dual_ids_detection"]
    assert s3["status"] == "PASS"
    assert s3["cross_match"] is True
    assert 9000001 in s3["suricata_sids"]
    assert 9100001 in s3["snort_sids"]

    # Stage 4: Sliding Window Correlation
    s4 = stages["4_correlation_escalation"]
    assert s4["status"] == "PASS"
    assert s4["window_minutes"] == 15
    assert s4["escalated_incident_id"] == "IR-06"
    assert s4["severity"] == "CRITICAL"

    # Stage 5: CTI Enrichment
    s5 = stages["5_cti_enrichment"]
    assert s5["status"] == "PASS"
    assert s5["reputation_score"] == 95
    assert s5["verdict"] == "MALICIOUS"
    assert s5["abuseipdb_score"] == 95

    # Stage 6: Incident Report Generation
    s6 = stages["6_incident_report"]
    assert s6["status"] == "PASS"
    assert s6["doc_number"].startswith("IR-")
    assert Path(s6["markdown_file"]).exists()
    assert Path(s6["html_file"]).exists()

    # Stage 7: SOAR HITL Action
    s7 = stages["7_soar_hitl_action"]
    assert s7["status"] == "PASS"
    assert s7["approval_status"] == "EXECUTED"
    assert s7["execution_status"] == "SUCCESS"

    # Stage 8: Sensor Monitoring Feedback Loop
    s8 = stages["8_sensor_feedback_loop"]
    assert s8["status"] == "PASS"
    assert s8["feedback_loop_verified"] is True


def test_master_release_gate_verification():
    """Verify that run_master_release_verification() passes all 6 release checks."""
    result = run_master_release_verification()
    assert result is True, "Master release gate (GATE-RELEASE-01) must pass 100%"
