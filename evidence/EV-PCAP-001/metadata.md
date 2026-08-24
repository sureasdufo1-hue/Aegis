# Evidence Record: EV-PCAP-001

## 1. Metadata Summary

| Field | Value |
|---|---|
| **Evidence ID** | `EV-PCAP-001` |
| **Requirement** | `REQ-IDS-04` (PCAP Evidence Pipeline & Cryptographic Integrity Verification) |
| **Design Reference** | SOC Implementation Plan v1.0 (Phase 12) / AGENTS.md Section 18 |
| **Implementation Phase** | Phase 12 (PCAP Evidence Pipeline) |
| **Test** | PCAP Generation & SHA-256 Checksum Calculation (`scripts/generate_pcap_samples.py`) |
| **Scenario** | 6 Core Attack Scenarios Real Packet Captures & Hash Verification |
| **Timestamp** | `2026-08-24T16:34:44+09:00` |
| **Component** | `pcaps/samples/`, `pcaps/metadata/pcap_manifest.json` |
| **Expected** | Real readable PCAPs exist for all attack vectors, source/destination IPs match architecture baseline, SHA-256 hashes recorded |
| **Actual** | 6 PCAP capture files generated with Layer 2/3/4/7 payload fidelity, SHA-256 manifest exported |
| **Result** | `PASS` |
| **Completion Gate** | `GATE-PCAP-01 = PASS` |

---

## 2. PCAP Inventory & Cryptographic Hash Manifest

| PCAP File | Attack Scenario | MITRE ATT&CK | Size (Bytes) | SHA-256 Checksum |
|---|---|---|---|---|
| `PCAP-20260824-ATK-001-ICMP.pcap` | ICMP Echo Request & Response | T1498 | 664 | `19b89af19a3717275199dbb005c2ef30bf9a087f4065b1aeabe8de4d6edf2e58` |
| `PCAP-20260824-ATK-002-SQLI.pcap` | Web SQL Injection UNION SELECT | T1190 | 607 | `a0ee7cc6d903c7f6b6dd42cb42b5c7c9bb3b672121e1221bbc4efd104ea87318` |
| `PCAP-20260824-ATK-003-SCAN.pcap` | Nmap Stealth NULL / XMAS / FIN Scan | T1046 | 374 | `6ca323167914187400f8661606c3452265096973d402f783e841646fb9633baa` |
| `PCAP-20260824-ATK-004-LOG4J.pcap` | Apache Log4j JNDI RCE Exploit | T1190 | 467 | `8892f82532ab94a86626a4fe517765d3c2d50473cea82cbc951a9273b24af577` |
| `PCAP-20260824-ATK-005-BRUTEFORCE.pcap` | SSH High-Frequency Brute Force | T1110 | 1950 | `988e13d00bef07014b533c9474ec351a42178ee07c95d79c6e34758eccf7fa6b` |
| `PCAP-20260824-ATK-006-C2REVERSESHELL.pcap` | DNS Tunneling & /bin/sh Reverse Shell | T1071, T1059 | 597 | `68e3332b20e2bdc34187d3193bd6861e04452d6e00012905a4f36c4e5b80db53` |

---

## 3. Gate Assessment

| Gate ID | Condition | Status |
|---|---|---|
| **GATE-PCAP-01** | PCAP exists, packets readable, source/dest correct (`10.77.20.20` ➔ `10.77.30.20`), SHA-256 recorded | **PASS** |
