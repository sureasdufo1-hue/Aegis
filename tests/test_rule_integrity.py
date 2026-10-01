"""
tests/test_rule_integrity.py
Unit tests verifying Detection-as-Code (DaC) ruleset syntax and integrity.
Ensures zero errors and zero warnings across canonical Suricata, Snort 3, and Wazuh rules.
"""

from pathlib import Path
from scripts.validate_rules import RuleValidator, REPO_ROOT


def test_canonical_rules_integrity():
    validator = RuleValidator(REPO_ROOT, include_legacy=False)
    suri_count = validator.parse_suricata_rules()
    snort_count = validator.parse_snort_rules()
    wazuh_count = validator.parse_wazuh_rules()

    assert suri_count >= 20, f"Expected at least 20 canonical Suricata rules, got {suri_count}"
    assert snort_count >= 10, f"Expected at least 10 canonical Snort rules, got {snort_count}"
    assert wazuh_count >= 5, f"Expected at least 5 Wazuh XML rules, got {wazuh_count}"

    errors = [f for f in validator.findings if f.severity == "ERROR"]
    warnings = [f for f in validator.findings if f.severity == "WARNING"]

    assert len(errors) == 0, f"Canonical rules contain errors: {errors}"
    assert len(warnings) == 0, f"Canonical rules contain warnings: {warnings}"


def test_suricata_sid_allocations():
    validator = RuleValidator(REPO_ROOT, include_legacy=False)
    validator.parse_suricata_rules()

    for sid in validator.suricata_sids:
        assert 9000000 <= sid <= 9099999, f"Suricata SID {sid} is outside 9000000-9099999 range"


def test_snort_sid_allocations():
    validator = RuleValidator(REPO_ROOT, include_legacy=False)
    validator.parse_snort_rules()

    for sid in validator.snort_sids:
        assert 9100000 <= sid <= 9199999, f"Snort SID {sid} is outside 9100000-9199999 range"
