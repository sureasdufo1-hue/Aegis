# EV-RUNTIME-LIVE-001: Live Infrastructure Closed-Loop SOC Telemetry & Detection Evidence

## 1. Executive Summary

| Attribute | Specification |
|---|---|
| **Evidence ID** | `EV-RUNTIME-LIVE-001` |
| **Validation Phase** | Runtime Infrastructure Live Pipeline Validation (Phases 0–27 Real Implementation) |
| **Execution Date** | 2026-09-30 (Live Runtime Verification) |
| **Status** | **PASS** |
| **Virtualization** | VMware Workstation Pro 17.5.2 (Host: Windows 11 Build 26100) |
| **Network Architecture** | Multi-Segment Private Virtual Networks (PVN / LAN Segments) |
| **Primary IDS** | Suricata 8.0.6 RELEASE (AF_PACKET Multi-Interface Mode: `ens37` + `ens38`) |
| **Primary SIEM** | Elasticsearch 8.19.20 & Kibana 5601 + Wazuh Manager 4.14.7 |
| **Forwarding Agent** | Filebeat 8.19.20 (TLS 1.3 encrypted transport to 10.77.10.30:9200) |
| **Host Sensor Agent** | Wazuh Agent 4.14.7 on `soc-victim` (`10.77.30.100`) |
| **AI Investigation** | AegisAI Orchestrator with Policy Validation & Dual-Control Human-in-the-Loop |

---

## 2. Infrastructure Baseline & Runtime Topology

### 2.1 Virtual Machine Inventory & Connectivity

| VM Name | Role | OS / Distro | Network Segment & Assigned IP | MAC Address | Services Verified |
|---|---|---|---|---|---|
| `soc-gateway` | SSH Jump Host / Perimeter | Ubuntu 24.04 LTS | VMnet8: `192.168.111.140/24`<br>MGMT PVN: `10.77.10.1/24` | `00:0c:29:1f:df:3c`<br>`00:0c:29:1f:df:46` | SSH (22), IP Forwarding, Static Routes |
| `soc-sensor` | Multi-Homed Network Sensor | Ubuntu 24.04 LTS | MGMT PVN: `10.77.10.20/24`<br>ATTACK PVN: `10.77.20.1/24`<br>VICTIM PVN: `10.77.30.1/24` | `00:0c:29:20:2a:a3`<br>`00:0c:29:20:2a:ad`<br>`00:0c:29:20:2a:b7` | Suricata 8.0.6 (AF_PACKET promiscuous), Filebeat 8.19.20 |
| `soc-victim` | Isolated Target Server | Ubuntu 24.04 LTS | VICTIM PVN: `10.77.30.100/24` | `00:0c:29:92:fa:65` | Python SimpleHTTP (Port 80), SSH (Port 22), Wazuh Agent 4.14.7 (Active) |
| `soc-attacker` | Red Team Traffic Generator | Kali Linux Rolling (Kernel 6.19.14) | ATTACK PVN: `10.77.20.50/24` | `00:0c:29:56:f4:4e` | Nmap, Curl, Hydra, Sqlmap, SSH (Port 22) |
| `soc-siem` | Central SIEM & Telemetry | Ubuntu 24.04 LTS | MGMT PVN: `10.77.10.30/24` | `00:0c:29:95:d7:97` | Elasticsearch 8.19.20 (Port 9200, Health: GREEN), Kibana (Port 5601), Wazuh Manager 4.14.7 (Ports 1514, 1515) |

---

## 3. Real-World Troubleshooting & Remediation Records

During the live deployment and validation, three critical operational issues were discovered, diagnosed root-caused, and remediated:

### 3.1 TRB-001: Sensor Filesystem Full (No Space Left on Device)
- **Symptom:** Suricata failed to write to `/var/log/suricata/eve.json` and `fast.log`, throwing `Error: logopenfile: No space left on device`.
- **Root Cause:** The default Ubuntu installer allocated only 10.00 GiB to the logical volume `ubuntu-lv` despite an 18.22 GiB physical volume (`ubuntu-vg`).
- **Remediation:**
  ```bash
  sudo lvextend -l +100%FREE /dev/ubuntu-vg/ubuntu-lv -r
  sudo journalctl --vacuum-size=50M
  sudo apt-get clean
  ```
- **Outcome:** Filesystem expanded live from 10.00 GiB (100% full) to 18.22 GiB (8.0 GiB available, 54% usage). Suricata logging restored with zero dropped packets.

### 3.2 TRB-002: Elasticsearch Service Token Access Denied
- **Symptom:** Elasticsearch 8.19.20 failed on boot with `AccessDeniedException: /etc/elasticsearch/service_tokens`.
- **Root Cause:** Root ownership with `600` permissions prevented the `elasticsearch` system daemon user from reading token definitions.
- **Remediation:**
  ```bash
  sudo chown -R elasticsearch:elasticsearch /etc/elasticsearch/
  sudo chmod 660 /etc/elasticsearch/service_tokens
  sudo systemctl restart elasticsearch
  ```
- **Outcome:** Elasticsearch initialized cleanly, all 51 active shards assigned, cluster health achieved `status: "green"`.

### 3.3 TRB-003: Filebeat Authentication Mismatch
- **Symptom:** `filebeat test output` failed with `HTTP 401 Unauthorized: unable to authenticate user [elastic]`.
- **Root Cause:** Password drift in `/etc/filebeat/filebeat.yml` (`[REDACTED_OLD_PW]` vs actual cluster password in `/etc/elasticsearch/es_pw.txt`).
- **Remediation:** Synchronized `/etc/filebeat/filebeat.yml` password and restarted `filebeat.service`.
- **Outcome:** TLS 1.3 handshake and authentication returned `talk to server... OK (version: 8.19.20)`.

---

## 4. End-to-End Evidence Chain

The complete evidence chain was executed and recorded using live network packets:

```text
[soc-attacker: 10.77.20.50]
      │
      │ (1) Nmap SYN scan, ICMP sweeps, HTTP /admin-test probe, SSH burst
      ▼
[soc-victim: 10.77.30.100] (Responds HTTP 404, SSH SYN-ACK)
      │
      │ (2) Network packets intercepted via PVN
      ▼
[soc-sensor: ens37 + ens38] (Promiscuous AF_PACKET capture)
      │
      │ (3) Rule evaluation (52,596 rules loaded)
      ▼
[Suricata 8.0.6: SID 1000001, 1000002, 1000003, 1000004, 1000005, 1000007]
      │
      │ (4) Structured JSON event emitted
      ▼
[/var/log/suricata/eve.json on soc-sensor]
      │
      │ (5) Filebeat 8.19.20 encrypted TLS 1.3 forwarding
      ▼
[soc-siem: Elasticsearch 8.19.20 on 10.77.10.30:9200]
      │ Index: .ds-filebeat-8.19.20-2026.09.30-000002 (611 hits for 10.77.20.50)
      │
      │ (6) Ingestion & Multi-Stage Correlation
      ▼
[AegisAI CorrelationEngine: Incident INC-10.77.20.50-1790738766]
      │ Classification: Reconnaissance -> Initial Access / Exploitation
      │
      │ (7) AI Orchestrator Automated Investigation
      ▼
[AI Analysis: Fact/Hypothesis Separation + Risk Assessment]
      │ Recommendation: BLOCK_IP (10.77.20.50), ISOLATE_HOST (10.77.30.100)
      │
      │ (8) Guardrail Validation & Dual-Control Creation
      ▼
[Dual-Control Approval Records: APR-90738766-236, APR-90738766-237]
      │ Policy: Allowed (Target validated not in Protected Management Subnet)
      │ Syntax: nft add rule inet filter input ip saddr 10.77.20.50 counter drop
      │ Status: PENDING (Human Authorization Required)
```

---

## 5. Artifact & Evidence Register

| File Name | Description | Hash / Verification |
|---|---|---|
| `topology_baseline.json` | Discovery baseline of VMs, MACs, routes, and VMware segments | Verified |
| `suricata_update.log` | Configuration validation (`suricata -T`) and service reload | Exit code 0 |
| `attacker_ip_check.txt` | Direct guest kernel query verifying `soc-attacker` network configuration | Verified |
| `live_eve_alert_sid1000005.json` | Raw Suricata EVE alert for HTTP Admin Probe | SID 1000005 |
| `live_eve_alerts_summary.json` | Multi-signature distinct alerts summary (ICMP, SSH, HTTP) | SIDs 1000001, 1000002, 1000005, 2034636 |
| `attacker_eve_alerts.json` | 24 alerts generated by `soc-attacker` (`10.77.20.50`) | Verified |
| `es_attacker_indexed_hits.json` | 611 documents retrieved from Elasticsearch cluster via REST API | Verified |
| `live_suricata_eve_sync.json` | Complete raw EVE log synchronized locally from `soc-sensor` | 230 events |
| `ai_investigation_evidence.json` | AegisAI Incident, AI analysis, fact separation, and Dual-Control approval records | Complete closed-loop |

---

## 6. Gate Determination

```text
Gate: GATE-E2E-01 (End-to-End Live Closed-Loop Validation)
Result: PASS

Gate: GATE-NET-01 (Packet Visibility on Sensor Interface)
Result: PASS

Gate: GATE-SURI-01 (Suricata Real-Time Detection & EVE Generation)
Result: PASS

Gate: GATE-SIEM-01 (SIEM Storage & Ingestion Verification)
Result: PASS

Gate: GATE-ANALYSIS-01 (AI Investigation & Dual-Control Human-in-the-Loop)
Result: PASS
```
