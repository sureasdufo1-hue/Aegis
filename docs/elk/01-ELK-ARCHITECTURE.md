# ELK Architecture Design Specification (Phase ELK-1)

> **Document ID**: `ELK-ARCH-001`  
> **Status**: `APPROVED / BASELINE`  
> **Target Scope**: SOC Detection & Monitoring Lab — Central Security Data & Threat Hunting Layer  
> **Classification**: Internal Engineering Baseline  

---

## 1. Executive Summary & Mission

The objective of the ELK Stack integration in this SOC Lab is not merely installing Elasticsearch and Kibana, but establishing an **authoritative, normalized Security Data Lake, Correlation Engine, and Threat Hunting Layer** that bridges:
1. **Network Sensors** (Suricata 8.0.6, Snort 3.12.2.0, Gateway nftables)
2. **Endpoint & Host Telemetry** (Wazuh 4.14.7 alerts)
3. **Application & Operational Consoles** (FastAPI Enterprise SOC Console, REST API)
4. **Future AI Security Layer** (Evidence Retrievable Layer for LLM / SOC Copilot)

```text
[ Network / Endpoint / Security Telemetry ]
       │ (Suricata / Snort / Gateway Firewall / Wazuh)
       ▼
[ Ingestion & Normalization Layer ]
       │ (Elastic Agent / Filebeat / Logstash Pipelines)
       ▼
[ Elasticsearch 8.17.3 Single-Node Engine ]
       │ (ECS Normalization / Data Streams / ILM / RBAC)
       ├─────────────────────────────────┬─────────────────────────────────┐
       ▼                                 ▼                                 ▼
[ Kibana 8.17.3 ]              [ FastAPI SOC Console ]           [ Future AI Copilot ]
- Threat Hunting                - Live Triage & Alerting          - RAG Context Retrieval
- Multi-source Correlation      - Human-in-the-Loop Actions       - Automated Evidence Triage
- Forensic Deep-Dive            - Incident Management             - Root Cause Explanation
```

---

## 2. Technology & Version Baseline

To ensure absolute cross-component compatibility, long-term stability, and adherence to [AGENTS.md](file:///C:/Users/user/Documents/ChatGPT/Suricata-Snort-SOC-Lab/AGENTS.md) version pinning rules, the following stack versions are designated:

| Component | Pinned Version | License / Distribution | Role in SOC Architecture |
|---|---|---|---|
| **Elasticsearch** | `8.17.3` | Elastic Basic (Free / Security Enabled) | Central Security Event Store, Vector & Text Search, Correlation Backend |
| **Logstash** | `8.17.3` | Elastic Basic / Apache 2.0 | Multi-pipeline Ingestion, Snort 3/Firewall/Wazuh Parsing, ECS Field Transformation |
| **Kibana** | `8.17.3` | Elastic Basic (Free) | Tactical Dashboards, Visual Threat Hunting, Timeline Pivot Analysis |
| **Elastic Agent / Filebeat** | `8.17.3` | Elastic Basic | Zero-overhead Suricata EVE JSON streaming from Sensor VM |
| **Wazuh (Preserved)** | `4.14.7` | Open Source (GPLv2 / Apache 2.0) | Endpoint Integrity, Host FIM, Vulnerability Scanning (Alert-only forward) |
| **Suricata (Preserved)** | `8.0.6` | Open Source (GPLv2) | Primary Real-time Network IDS (`AF_PACKET` on `eth1`) |
| **Snort (Preserved)** | `3.12.2.0` | Open Source (GPLv2) | Secondary IDS & Offline PCAP Verification Engine |
| **FastAPI SOC Console** | Host Native (3.13) | Internal | High-density Operational SOC Screen (`http://0.0.0.0:8000`) |

---

## 3. Host Topology & Deployment Model

### 3.1 Single-Node Isolation Architecture

Per requirements (Section 7), the Lab operates as an optimized **Single-Node Elasticsearch** deployment. A multi-node cluster is explicitly avoided to preserve host memory and disk headroom.

- **Host Platform**: Windows 11 Education (Xeon E-2374G, 64 GB RAM, 1.27 TB Free NVMe SSD)
- **Container Network**: `soc-elk-net` (Bridge, Isolated from Attack Network)
- **Persistence Strategy**: Named Docker Volumes with Host Bind-Mount backups for configuration and certificates.

```text
+---------------------------------------------------------------------------------------------------+
| PHYSICAL HOST: Intel Xeon E-2374G (4C/8T) | Total RAM: 64 GB (Free: ~40 GB) | Disk Free: 1.27 TB  |
+---------------------------------------------------------------------------------------------------+
  │
  ├── [ ZONE-MGMT: 10.77.10.0/24 ]
  │     ├── Windows Host Management Interface : 10.77.10.10 (Host Loopback & VMnet10: 10.77.10.1)
  │     ├── Gateway Management Interface      : 10.77.10.1
  │     ├── Sensor Management Interface       : 10.77.10.20
  │     └── FastAPI SOC Console               : 0.0.0.0:8000 (Active, PID 26400)
  │
  ├── [ DOCKER ENGINE / WSL2: soc-elk-net Bridge ]
  │     │
  │     ├── soc-elasticsearch (8.17.3)
  │     │     ├── Container IP   : 172.28.0.10
  │     │     ├── Internal Port  : 9200/TCP (TLS Encrypted)
  │     │     ├── Host Exposure  : 127.0.0.1:9201 -> 9200 (ISOLATED from Wazuh 9200)
  │     │     ├── JVM Heap       : 4 GB (Xms4g Xmx4g)
  │     │     └── Volume         : soc-elk-es-data (SSD persistent)
  │     │
  │     ├── soc-kibana (8.17.3)
  │     │     ├── Container IP   : 172.28.0.11
  │     │     ├── Internal Port  : 5601/TCP (HTTPS/HTTP)
  │     │     ├── Host Exposure  : 127.0.0.1:5602 -> 5601 (ISOLATED from Wazuh 5601)
  │     │     └── Dependency     : soc-elasticsearch
  │     │
  │     └── soc-logstash (8.17.3)
  │           ├── Container IP   : 172.28.0.12
  │           ├── Ingest Ports   : 10.77.10.10:5044 (Beats), 10.77.10.10:5514/udp (Syslog)
  │           ├── JVM Heap       : 2 GB (Xms2g Xmx2g)
  │           ├── Queue Type     : Persisted (`queue.type: persisted`, max 4 GB)
  │           └── Pipelines      : Suricata, Snort, Firewall, Wazuh Alerts
  │
  └── [ EXISTING PRESERVED STACK: soc-wazuh-net Bridge ]
        ├── soc-wazuh-indexer   : 127.0.0.1:9200 (OpenSearch based, Zero Port Collision)
        ├── soc-wazuh-manager   : 1514/1515/tcp, 127.0.0.1:55000
        └── soc-wazuh-dashboard : 443, 5601 (Wazuh UI, Zero Port Collision)
```

---

## 4. Hardware Resource Allocation Budget

Based on the actual physical resource baseline established in Phase ELK-0 (64 GB RAM, 40 GB Free, 1.27 TB SSD):

| Component | Minimum vCPU | Allocated RAM (JVM / Heap) | Container Limit | Persistent Storage Budget |
|---|---|---|---|---|
| **Elasticsearch** | 2 vCPU | 4 GB JVM Heap (`-Xms4g -Xmx4g`) | 6 GB RAM Limit | 100 GB SSD (Hot/Warm ILM managed) |
| **Logstash** | 2 vCPU | 2 GB JVM Heap (`-Xms2g -Xmx2g`) | 3 GB RAM Limit | 10 GB SSD (Persistent Queue) |
| **Kibana** | 1 vCPU | 1 GB NodeJS Memory | 2 GB RAM Limit | 2 GB SSD |
| **Elastic Agent (Sensor)** | 1 vCPU | 256 MB (Go Binary) | N/A (On Sensor VM) | Temporary Spool (500 MB) |
| **Total ELK Budget** | **4 vCPU** | **7.25 GB Effective** | **11 GB Cap** | **112 GB SSD Total** |
| **Remaining Host Headroom** | 4 Logical Cores | **~29.0 GB Free RAM** | Unconstrained | **> 1.15 TB Free SSD** |

*Verdict*: The allocation is well within host safety thresholds, leaving over 29 GB RAM for Hyper-V Lab VMs and the operating system.

---

## 5. Architectural Separation of Concerns (Wazuh vs. ELK)

To prevent duplication and comply with Section 3 of the mandate:

```text
┌──────────────────────────────────────────────┐     ┌──────────────────────────────────────────────┐
│             WAZUH SIEM DOMAIN                │     │               ELK STACK DOMAIN               │
│         (Endpoint & Host Focused)            │     │         (Network & Correlation Focused)      │
├──────────────────────────────────────────────┤     ├──────────────────────────────────────────────┤
│ - Linux Host File Integrity Monitoring (FIM) │     │ - Suricata 8.0.6 Real-Time Network IDS       │
│ - Host Rootcheck & System Anomaly Detection  │     │ - Snort 3.12.2.0 Secondary IDS & PCAP Replay │
│ - Host Package Vulnerability Assessment      │     │ - Gateway Firewall (nftables) Drop / Allow   │
│ - Local Host Auth Logs (sshd auth failures)  │     │ - Full Network Flow, DNS, HTTP, TLS, SSH     │
│ - Endpoint Active Response Execution         │     │ - Unified Multi-Source Correlation Matrix    │
│ - Raw Security Log Archiving                 │     │ - FastAPI SOC Console Telemetry Source       │
└──────────────────────┬───────────────────────┘     └──────────────────────▲───────────────────────┘
                       │                                                    │
                       │ Forward Detection Alerts Only (alerts.json)        │
                       └────────────────────────────────────────────────────┘
```

1. **No Raw Event Duplication**: Wazuh internal agent heartbeats and un-alerted system logs are NOT copied to Elasticsearch.
2. **Selective Alert Ingestion**: Only actionable alerts (`rule.level >= 3` in `/var/ossec/logs/alerts/alerts.json`) are forwarded via Logstash to `logs-wazuh.alert-default`.
3. **Correlation Synergy**: High-fidelity correlation rules in ELK combine Suricata network alerts with Wazuh host alerts (e.g. Network Exploit -> Host Shell Execution).
