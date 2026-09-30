import pytest
from analyzer.ai.rag.adaptive_threshold import (
    AdaptiveThresholdCalculator,
    AdaptiveThresholdResult,
)
from analyzer.ai.rag.knowledge_store import KnowledgeChunk


def test_base_query_threshold():
    calc = AdaptiveThresholdCalculator(base_threshold=0.50)
    result = calc.calculate("Investigate anomalous traffic and alert behavior")
    
    # Normal query with ~5 words, no CVE, no MITRE, no high-priority jargon
    assert result.effective_threshold == 0.50
    assert result.base_threshold == 0.50
    assert len(result.adjustments) == 0
    assert result.query_profile.has_cve is False
    assert result.query_profile.has_mitre is False


def test_cve_and_jargon_lowers_threshold():
    """
    Validates EVAL-GAP-008 resolution:
    Specific CVEs require lower thresholds so domain playbooks with exact technical
    relevance are not discarded by rigid thresholds.
    """
    calc = AdaptiveThresholdCalculator(base_threshold=0.50)
    result = calc.calculate("Remote code execution attempt via CVE-2021-44228 log4j header")

    assert result.query_profile.has_cve is True
    assert "CVE-2021-44228" in result.query_profile.cve_ids
    assert result.query_profile.has_jargon is True
    assert "log4j" in result.query_profile.detected_jargon
    # 0.50 - 0.15 (CVE) - 0.05 (Jargon) - 0.05 (Multi-token Context >= 8 words) = 0.25
    assert result.effective_threshold == pytest.approx(0.25, abs=0.01)
    assert any("CVE Detected" in adj for adj in result.adjustments)


def test_mitre_technique_adjustment():
    calc = AdaptiveThresholdCalculator(base_threshold=0.50)
    result = calc.calculate("Stealth network reconnaissance mapping T1046")

    assert result.query_profile.has_mitre is True
    assert "T1046" in result.query_profile.mitre_techniques
    # 0.50 - 0.10 (MITRE) = 0.40
    assert result.effective_threshold == pytest.approx(0.40, abs=0.01)


def test_short_query_ambiguity_guard():
    """Short ambiguous queries must raise the threshold to filter out noise."""
    calc = AdaptiveThresholdCalculator(base_threshold=0.50)
    result = calc.calculate("scan")

    assert result.query_profile.is_short is True
    # 0.50 + 0.10 = 0.60 (Guard against hallucinations)
    assert result.effective_threshold >= 0.55
    assert any("Short/Ambiguous Query Guard" in adj for adj in result.adjustments)


def test_threshold_safety_clamping():
    """Threshold cannot fall below min_threshold or exceed max_threshold."""
    calc = AdaptiveThresholdCalculator(base_threshold=0.50, min_threshold=0.25, max_threshold=0.80)
    
    # Query with multiple deductions that would drop below 0.25
    extreme_query = "Critical alert CVE-2023-12345 CVE-2024-99999 T1046 T1190 sqli log4j meterpreter traversal"
    result = calc.calculate(extreme_query)
    assert result.effective_threshold == 0.25  # Clamped to min_threshold


def test_filter_and_rank_resolution():
    calc = AdaptiveThresholdCalculator(base_threshold=0.50)
    chunk = KnowledgeChunk(
        chunk_id="test-sec1",
        document_title="Log4Shell Emergency Response Playbook",
        file_path="playbooks/06_log4shell.md",
        content="Incident response procedures for CVE-2021-44228 Log4j exploitation",
        sha256="abc123hash",
        keywords=["cve-2021-44228", "log4j", "exploit"],
    )

    scored_chunks = [(chunk, 0.35)]

    # 1. Under generic query: Score 0.35 is below base threshold 0.50 -> Rejected
    accepted_generic, res_gen = calc.filter_and_rank("investigate incident", scored_chunks)
    assert len(accepted_generic) == 0

    # 2. Under CVE-specific query: Score 0.35 is ABOVE adapted threshold ~0.30 -> Accepted!
    accepted_cve, res_cve = calc.filter_and_rank("Investigate CVE-2021-44228 log4j exploit", scored_chunks)
    assert len(accepted_cve) == 1
    assert accepted_cve[0][0].chunk_id == "test-sec1"
    assert accepted_cve[0][1] == 0.35
