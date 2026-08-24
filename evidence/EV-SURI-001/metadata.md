# Evidence Record: EV-SURI-001

## 1. Metadata Summary

| Field | Value |
|---|---|
| **Evidence ID** | `EV-SURI-001` |
| **Requirement** | `REQ-IDS-01` (Primary IDS - Suricata 8.x Baseline & 9000-series Ruleset) |
| **Design Reference** | SOC Architecture HLD v1.0 (Section 1) / LLD v1.0 (Section 1.2) / Implementation Plan Phase 10 |
| **Implementation Phase** | Phase 10 (Suricata Baseline Configuration) |
| **Test** | Suricata YAML Configuration Parse & Rule File Loading Verification |
| **Scenario** | Suricata Engine Baseline & Custom Rule Provisioning |
| **Timestamp** | `2026-08-24T16:15:00+09:00` |
| **Component** | Suricata 8.0.6 (`suricata/config/suricata.yaml`, `suricata/rules/`) |
| **Expected** | `HOME_NET` set to `10.77.30.0/24`, `AF_PACKET` on `nic-monitor`, EVE JSON enabled, custom SIDs 9000000~9039999 loaded without duplicates |
| **Actual** | `suricata.yaml` configured with exact victim network variables, EVE JSON telemetry outputs, and 4 modular custom rule files |
| **Result** | `PASS` |
| **Completion Gate** | `GATE-SURI-01 = PASS` |

---

## 2. Verified Custom Rule Modules

| Category | File | SID Range | Techniques |
|---|---|---|---|
| **Reconnaissance** | `suricata/rules/9000-network-recon.rules` | 9000001–9000021 | T1046, T1595, T1498 |
| **Web Application** | `suricata/rules/9010-web-attacks.rules` | 9010001–9010040 | T1190, T1189, T1083, CVE-2021-44228 |
| **Authentication** | `suricata/rules/9020-auth-bruteforce.rules` | 9020001–9020010 | T1110, T1110.001 |
| **Malware & C2** | `suricata/rules/9030-malware-c2.rules` | 9030001–9030020 | T1071, T1059.004, T1048 |

---

## 3. Gate Assessment

| Gate ID | Condition | Status |
|---|---|---|
| **GATE-SURI-01** | Configuration parse valid, AF_PACKET configured, no duplicate SIDs | **PASS** |
