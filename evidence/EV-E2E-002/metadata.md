# Evidence Record: EV-E2E-002

## 1. Metadata Summary

| Field | Value |
|---|---|
| **Evidence ID** | `EV-E2E-002` |
| **Requirement** | `REQ-SIEM-01` (Real-time Ingestion), `REQ-E2E-01` (Killchain Correlation & Web Console) |
| **Design Reference** | SOC Architecture HLD v1.0 / Implementation Plan Phase 31 / AGENTS.md Section 14 & 19 |
| **Implementation Phase** | Phase 31 (Real-time SIEM Ingestion & SOC Console E2E Validation) |
| **Test** | Real-time Ingestion, OpenSearch Indexing, Multi-Stage Correlation, and FastAPI Console E2E |
| **Scenario ID** | `SCN-PHASE31-001` (Multi-stage Killchain: Recon ➔ Initial Access ➔ C2) |
| **Timestamp** | `2026-08-26T15:56:35+09:00` |
| **Component** | Suricata EVE ➔ Wazuh Manager (4.14.7) ➔ Wazuh Indexer (OpenSearch 9200) ➔ Correlation Engine ➔ FastAPI SOC Console (:8501) |
| **Expected** | Suricata EVE events ingested in real time, decoded by Wazuh, indexed into OpenSearch, correlated into a CRITICAL Incident, and accessible via SOC Web Console |
| **Actual** | 100% verified: All 3 unique attack events indexed in OpenSearch, escalated to incident `INC-10.77.20.20-1787727443`, idempotency verified, all API endpoints returned HTTP 200 |
| **Result** | **`PASS`** |
| **Completion Gate** | `GATE-PHASE31-01 = PASS` |

---

## 2. Real-time Ingestion & Correlation Telemetry

### 2.1 Unique Test Execution Coordinates
- **Run ID**: `phase31_1787727383`
- **Attacker IP**: `10.77.20.20` (`soc-attacker`)
- **Target IP**: `10.77.30.20` (`soc-victim`)
- **Flow ID Base**: `920000000027384` ~ `920000000027386`

### 2.2 Ingestion & OpenSearch Document Mapping

| Stage | Suricata SID | Flow ID | Wazuh Alert ID | Rule Description | OpenSearch Index |
|---|---|---|---|---|---|
| **1. Reconnaissance** | `9000001` | `920000000027384` | `1787727385.25830` | Suricata: Alert - SOC-SCAN: Nmap Stealth NULL Scan Detected (Zero Flags) | `wazuh-alerts-4.x-2026.08.26` |
| **2. Initial Access** | `9010001` | `920000000027385` | `1787727385.27182` | Suricata: Alert - SOC-ATTACK: Web SQL Injection - UNION SELECT Pattern Detected | `wazuh-alerts-4.x-2026.08.26` |
| **3. C2 & Exfiltration** | `9030010` | `920000000027386` | `1787727385.24350` | Suricata: Alert - SOC-MALWARE: Interactive Reverse Shell Session Established (/bin/sh prompt detected) | `wazuh-alerts-4.x-2026.08.26` |

---

## 3. Correlated Incident Escalation

```json
{
  "incident_id": "INC-10.77.20.20-1787727443",
  "src_ip": "10.77.20.20",
  "target_ips": [
    "10.77.30.20"
  ],
  "attack_stages": [
    "1. Reconnaissance",
    "2. Initial Access / Exploitation",
    "3. Command & Control / Execution"
  ],
  "highest_severity": "CRITICAL",
  "verdict": "Multi-Stage Attack Chain Detected: 1. Reconnaissance -> 2. Initial Access / Exploitation -> 3. Command & Control / Execution from 10.77.20.20 targeting 1 internal host(s).",
  "playbook_ref": "playbooks/04_malware_c2_investigation.md"
}
```

---

## 4. FastAPI SOC Console API Validation

- **Endpoint `/api/health`**: `HTTP 200` (`status: healthy`, `service: soc-dashboard`)
- **Endpoint `/api/stats`**: `HTTP 200` (`total_alerts: 81`, `critical: 17`, `high: 36`, `incidents: 78`)
- **Endpoint `/api/alerts`**: `HTTP 200` (List of normalized telemetry records)
- **Endpoint `/api/incidents`**: `HTTP 200` (Active correlated multi-stage incidents)
- **Endpoint `/`**: `HTTP 200` (Live HTML & Chart.js Web Console)

---

## 5. Gate Assessment

| Gate ID | Condition | Status |
|---|---|---|
| **GATE-PHASE31-01** | Real-time Suricata EVE ➔ Wazuh Manager ➔ Indexer ➔ Correlation ➔ Console pipeline verified end-to-end with objective evidence | **PASS** |
