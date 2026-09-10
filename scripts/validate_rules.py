#!/usr/bin/env python3
"""
scripts/validate_rules.py
Detection-as-Code (DaC) Rule Syntax & Integrity Linter.
Validates Suricata, Snort 3, and Wazuh detection rules against repository baseline policies.
"""

from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import NamedTuple

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent

# Baseline Policies from AGENTS.md
SURICATA_SID_RANGE = (9000000, 9099999)
SNORT_SID_RANGE = (9100000, 9199999)

SURICATA_SUBRANGES = {
    "Network": (9000000, 9009999),
    "Web": (9010000, 9019999),
    "Authentication": (9020000, 9029999),
    "Lab / C2": (9030000, 9039999),
    "Reserved": (9090000, 9099999),
}


class RuleFinding(NamedTuple):
    file: str
    line: int
    rule_type: str
    sid: int
    severity: str
    message: str


class RuleValidator:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root
        self.findings: list[RuleFinding] = []
        self.suricata_sids: dict[int, tuple[str, int]] = {}
        self.snort_sids: dict[int, tuple[str, int]] = {}
        self.wazuh_rule_ids: dict[int, tuple[str, int]] = {}

    def parse_suricata_rules(self) -> int:
        count = 0
        suricata_dirs = [
            self.repo_root / "suricata" / "rules",
            self.repo_root / "rules" / "suricata",
        ]
        for sdir in suricata_dirs:
            if not sdir.exists():
                continue
            for rpath in sorted(sdir.glob("*.rules")):
                rel_path = rpath.relative_to(self.repo_root).as_posix()
                with open(rpath, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, raw_line in enumerate(f, start=1):
                        line = raw_line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if not line.startswith(("alert", "drop", "pass", "reject")):
                            continue

                        count += 1
                        # Extract sid
                        sid_match = re.search(r"\bsid\s*:\s*(\d+)\s*;", line)
                        rev_match = re.search(r"\brev\s*:\s*(\d+)\s*;", line)
                        msg_match = re.search(r'\bmsg\s*:\s*"([^"]+)"\s*;', line)

                        if not msg_match:
                            self.findings.append(RuleFinding(
                                rel_path, line_num, "Suricata", 0, "ERROR", "Missing required 'msg' option"
                            ))

                        if not rev_match:
                            self.findings.append(RuleFinding(
                                rel_path, line_num, "Suricata", 0, "WARNING", "Missing 'rev' revision option"
                            ))

                        if not sid_match:
                            self.findings.append(RuleFinding(
                                rel_path, line_num, "Suricata", 0, "ERROR", "Missing required 'sid' option"
                            ))
                            continue

                        sid = int(sid_match.group(1))

                        # Check range (unless it's an upstream standard rule like 2000000)
                        if not (SURICATA_SID_RANGE[0] <= sid <= SURICATA_SID_RANGE[1]):
                            if sid < 10000000:  # Allow standard ET Open SIDs if bundled
                                self.findings.append(RuleFinding(
                                    rel_path, line_num, "Suricata", sid, "WARNING",
                                    f"SID {sid} is outside baseline custom allocation {SURICATA_SID_RANGE[0]}-{SURICATA_SID_RANGE[1]}"
                                ))

                        # Check duplication
                        if sid in self.suricata_sids:
                            prev_file, prev_line = self.suricata_sids[sid]
                            # If it's the exact same file or mirrored directory, note it
                            if prev_file != rel_path:
                                self.findings.append(RuleFinding(
                                    rel_path, line_num, "Suricata", sid, "INFO",
                                    f"Duplicate SID {sid} also defined in {prev_file}:{prev_line}"
                                ))
                        else:
                            self.suricata_sids[sid] = (rel_path, line_num)

        return count

    def parse_snort_rules(self) -> int:
        count = 0
        snort_dirs = [
            self.repo_root / "snort" / "rules",
            self.repo_root / "rules" / "snort",
        ]
        for sdir in snort_dirs:
            if not sdir.exists():
                continue
            for rpath in sorted(sdir.glob("*.rules")):
                rel_path = rpath.relative_to(self.repo_root).as_posix()
                with open(rpath, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, raw_line in enumerate(f, start=1):
                        line = raw_line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if not line.startswith(("alert", "drop", "pass", "block")):
                            continue

                        count += 1
                        sid_match = re.search(r"\bsid\s*:\s*(\d+)\s*;", line)
                        msg_match = re.search(r'\bmsg\s*:\s*"([^"]+)"\s*;', line)

                        if not msg_match:
                            self.findings.append(RuleFinding(
                                rel_path, line_num, "Snort", 0, "ERROR", "Missing required 'msg' option"
                            ))

                        if not sid_match:
                            self.findings.append(RuleFinding(
                                rel_path, line_num, "Snort", 0, "ERROR", "Missing required 'sid' option"
                            ))
                            continue

                        sid = int(sid_match.group(1))

                        if not (SNORT_SID_RANGE[0] <= sid <= SNORT_SID_RANGE[1]):
                            self.findings.append(RuleFinding(
                                rel_path, line_num, "Snort", sid, "WARNING",
                                f"SID {sid} is outside Snort custom allocation {SNORT_SID_RANGE[0]}-{SNORT_SID_RANGE[1]}"
                            ))

                        if sid in self.snort_sids:
                            prev_file, prev_line = self.snort_sids[sid]
                            if prev_file != rel_path:
                                self.findings.append(RuleFinding(
                                    rel_path, line_num, "Snort", sid, "INFO",
                                    f"Duplicate SID {sid} also defined in {prev_file}:{prev_line}"
                                ))
                        else:
                            self.snort_sids[sid] = (rel_path, line_num)

        return count

    def parse_wazuh_rules(self) -> int:
        count = 0
        wazuh_dir = self.repo_root / "wazuh" / "rules"
        if not wazuh_dir.exists():
            return 0

        for xml_file in sorted(wazuh_dir.glob("*.xml")):
            rel_path = xml_file.relative_to(self.repo_root).as_posix()
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                for rule_elem in root.findall(".//rule"):
                    count += 1
                    rule_id_str = rule_elem.get("id")
                    if not rule_id_str:
                        self.findings.append(RuleFinding(
                            rel_path, 0, "Wazuh", 0, "ERROR", "Wazuh rule missing 'id' attribute"
                        ))
                        continue

                    rule_id = int(rule_id_str)
                    desc_elem = rule_elem.find("description")
                    if desc_elem is None or not (desc_elem.text or "").strip():
                        self.findings.append(RuleFinding(
                            rel_path, 0, "Wazuh", rule_id, "ERROR", f"Rule {rule_id} missing <description>"
                        ))

                    if rule_id in self.wazuh_rule_ids:
                        prev_file, _ = self.wazuh_rule_ids[rule_id]
                        self.findings.append(RuleFinding(
                            rel_path, 0, "Wazuh", rule_id, "ERROR", f"Duplicate Wazuh rule id {rule_id} found in {prev_file}"
                        ))
                    else:
                        self.wazuh_rule_ids[rule_id] = (rel_path, 0)

            except ET.ParseError as e:
                self.findings.append(RuleFinding(
                    rel_path, 0, "Wazuh", 0, "ERROR", f"XML syntax parse error: {e}"
                ))

        return count

    def validate_all(self) -> bool:
        suri_count = self.parse_suricata_rules()
        snort_count = self.parse_snort_rules()
        wazuh_count = self.parse_wazuh_rules()

        print("==================================================")
        print(" Aegis Detection-as-Code (DaC) Rule Integrity Report")
        print("==================================================")
        print(f"• Suricata Detection Rules Parsed : {suri_count}")
        print(f"• Snort Secondary Rules Parsed    : {snort_count}")
        print(f"• Wazuh SIEM XML Rules Parsed     : {wazuh_count}")
        print("--------------------------------------------------")

        errors = [f for f in self.findings if f.severity == "ERROR"]
        warnings = [f for f in self.findings if f.severity == "WARNING"]
        infos = [f for f in self.findings if f.severity == "INFO"]

        if errors:
            print(f"\n[!] ERRORS DETECTED ({len(errors)}):")
            for e in errors:
                print(f"  ❌ [{e.rule_type}] {e.file}:{e.line} (SID {e.sid}): {e.message}")

        if warnings:
            print(f"\n[!] WARNINGS ({len(warnings)}):")
            for w in warnings:
                print(f"  ⚠️ [{w.rule_type}] {w.file}:{w.line} (SID {w.sid}): {w.message}")

        if infos:
            print(f"\n[*] NOTICES ({len(infos)}):")
            for i in infos:
                print(f"  ℹ️ [{i.rule_type}] {i.file}:{i.line}: {i.message}")

        print("\n--------------------------------------------------")
        if not errors:
            print(f"✓ RESULT: ALL DETECTION RULES PASSED VALIDATION! (Errors: 0, Warnings: {len(warnings)})")
            print("==================================================")
            return True
        else:
            print(f"✗ RESULT: RULE INTEGRITY VALIDATION FAILED! (Errors: {len(errors)})")
            print("==================================================")
            return False


def main() -> int:
    validator = RuleValidator(REPO_ROOT)
    success = validator.validate_all()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
