# Log Source Inventory & Ingestion Specification (Phase ELK-1)

> **Document ID**: `ELK-LOG-001`  
> **Status**: `APPROVED / BASELINE`  
> **Target Scope**: Comprehensive Specification of All Security Telemetry Sources  
> **Classification**: Internal Engineering Baseline  

---

## 1. Master Log Source Registry

| Source ID | Originating Asset | File Path | Format | Transport | Importance | Ingest Pipeline / Target Data Stream |
|---|---|---|---|---|---|---|
| **SRC-SURI-01** | `soc-sensor` | `/var/log/suricata/eve.json` | JSON Lines | Elastic Agent / Filebeat -> 5044/TCP | **CRITICAL** | `pipeline-suricata` -> `logs-suricata.eve-default` |
| **SRC-SNORT-01**| `soc-sensor` | `/var/log/snort/alert_json.txt` | JSON Lines | Filebeat / Logstash -> 5044/TCP | **HIGH** | `pipeline-snort` -> `logs-snort.alert-default` |
| **SRC-WAZUH-01**| `soc-wazuh-manager`| `/var/ossec/logs/alerts/alerts.json` | JSON Lines | Logstash File Input / Bind | **HIGH** | `pipeline-wazuh` -> `logs-wazuh.alert-default` |
| **SRC-FW-01** | `soc-gateway` | `/var/log/nftables.log` | Syslog (RFC5424) | Syslog UDP -> 5514/UDP | **HIGH** | `pipeline-firewall` -> `logs-firewall.traffic-default` |
| **SRC-AUTH-01** | `soc-victim` / `soc-sensor` | `/var/log/auth.log` | Syslog | Filebeat -> 5044/TCP | **MEDIUM** | `pipeline-auth` -> `logs-linux.auth-default` |
| **SRC-AUDIT-01**| Host (FastAPI) | `dashboard/audit.py` (SQLite/Memory) | JSON / REST | Logstash REST / Agent Ingest | **MEDIUM** | `pipeline-audit` -> `logs-soc.audit-default` |

---

## 2. Detailed Telemetry Specifications

### 2.1 Suricata EVE JSON (`SRC-SURI-01`)
- **Origin**: `soc-sensor` via AF_PACKET sniffing on mirrored interface `eth1`.
- **Event Types Collected**:
  - `alert`: Detection signature matches (SID 9000000–9039999)
  - `dns`: Queries, responses, rcode, rdata, query type
  - `http`: Methods, URIs, user-agents, headers, response status codes
  - `tls`: Subject, issuer, SNI, TLS version, ja3/ja4 fingerprint
  - `ssh`: Client/server banners, key exchange parameters
  - `anomaly`: Protocol anomalies, stream reassembly failures
  - *Filtered Out at Source*: High-volume `flow` and `stats` are throttled or sampled to prevent storage saturation.
- **Key Raw Fields**: `timestamp`, `event_type`, `src_ip`, `src_port`, `dest_ip`, `dest_port`, `proto`, `alert.signature`, `alert.signature_id`, `alert.severity`, `alert.category`, `payload`, `community_id`.

### 2.2 Snort 3 JSON Alert (`SRC-SNORT-01`)
- **Origin**: `soc-sensor` via Snort 3 `alert_json` module.
- **Configuration Output**: Fields declared in [snort.lua](file:///C:/Users/user/Documents/ChatGPT/Suricata-Snort-SOC-Lab/snort/config/snort.lua) (34 standard fields).
- **Key Raw Fields**: `timestamp`, `action`, `class`, `dir`, `dst_addr`, `dst_port`, `src_addr`, `src_port`, `proto`, `gid`, `sid`, `rev`, `msg`, `b64_data`, `pkt_len`.

### 2.3 Wazuh Actionable Alerts (`SRC-WAZUH-01`)
- **Origin**: `soc-wazuh-manager` Docker container `/var/ossec/logs/alerts/alerts.json`.
- **Filtering Threshold**: Only events with `rule.level >= 3` or matching custom rules (100100–100111) are ingested.
- **Key Raw Fields**: `timestamp`, `rule.id`, `rule.level`, `rule.description`, `agent.id`, `agent.name`, `agent.ip`, `manager.name`, `data.srcip`, `data.dstip`, `rule.mitre.id`, `full_log`.

### 2.4 Gateway nftables Syslog (`SRC-FW-01`)
- **Origin**: `soc-gateway` kernel packet filter logging.
- **Prefix Matching**:
  - `SOC-FW-DENY-ATTACK-TO-MGMT:` (Unauthorized Red Zone traverse attempts)
  - `SOC-FW-FORWARD-ALLOW:` (Forwarded test traffic between Attacker and Victim)
- **Key Raw Fields**: `timestamp`, `hostname`, `IN`, `OUT`, `MAC`, `SRC`, `DST`, `LEN`, `TOS`, `PREC`, `TTL`, `ID`, `PROTO`, `SPT`, `DPT`.

---

## 3. Storage Ingestion Volume Estimation

Based on Lab benchmark traffic runs (1-hour attack simulations):

| Source | Baseline Idle EPS | Attack Burst EPS | Avg Doc Size | Daily Volume (Idle) | Daily Volume (Burst) |
|---|---|---|---|---|---|
| Suricata EVE | 5 EPS | 800 EPS | 1.4 KB | ~600 MB / day | ~2.5 GB / day |
| Snort 3 Alert| 0.5 EPS | 200 EPS | 0.8 KB | ~35 MB / day | ~300 MB / day |
| Gateway Firewall | 2 EPS | 400 EPS | 0.5 KB | ~86 MB / day | ~750 MB / day |
| Wazuh Alerts | 0.2 EPS | 50 EPS | 1.8 KB | ~30 MB / day | ~200 MB / day |
| **Total Estimated**| **~8 EPS** | **~1,450 EPS** | **~1.1 KB** | **~751 MB / day** | **~3.75 GB / day** |

*Capacity Headroom Evaluation*: With 1.27 TB SSD available, a 30-day retention window requires only **~30–110 GB**, utilizing less than 9% of available disk storage.
