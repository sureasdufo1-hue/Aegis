# Elastic Common Schema (ECS 8.x) Field Normalization Specification (Phase ELK-1)

> **Document ID**: `ELK-ECS-001`  
> **Status**: `APPROVED / BASELINE`  
> **Target Scope**: End-to-End Log Field Normalization for Unified Correlation & Threat Hunting  
> **Classification**: Internal Engineering Baseline  

---

## 1. Executive Purpose

A search query executed by an analyst:
```esql
FROM logs-* | WHERE source.ip == "10.77.20.20"
```
**MUST simultaneously return** Suricata network alerts, Snort detections, Gateway firewall drops, and Wazuh host authentication events across the complete kill chain without syntax friction.

This document defines the authoritative transformation matrix from raw vendor fields to **ECS (Elastic Common Schema) v8.x**.

---

## 2. Core Mandatory ECS Fields

Every normalized security document entering Elasticsearch MUST populate these baseline fields:

```text
@timestamp               : Date (ISO8601 UTC)
event.kind               : Keyword ("alert", "event")
event.category           : Keyword ("network", "intrusion_detection", "authentication")
event.type               : Keyword ("start", "info", "denied", "allowed")
event.action             : Keyword ("drop", "alert", "forward", "login")
event.outcome            : Keyword ("success", "failure", "unknown")
event.severity           : Long (1: Low, 2: Medium, 3: High, 4: Critical)

source.ip                : IP
source.port              : Long
destination.ip           : IP
destination.port         : Long

network.transport        : Keyword ("tcp", "udp", "icmp")
network.protocol         : Keyword ("http", "dns", "tls", "ssh")
network.community_id     : Keyword (Corelight Community ID string)

host.name                : Keyword ("soc-sensor", "soc-victim", "soc-gateway")
observer.name            : Keyword ("suricata", "snort", "nftables", "wazuh")
observer.type            : Keyword ("ids", "firewall", "siem")

rule.id                  : Keyword (e.g. "9010001", "100102")
rule.name                : Keyword (Signature description)
rule.category            : Keyword (Attack category)
rule.reference           : Keyword (CVE, URL, or MITRE technique)

threat.framework         : Keyword ("MITRE ATT&CK")
threat.tactic.id         : Keyword (e.g. "TA0001")
threat.technique.id      : Keyword (e.g. "T1190")

related.ip               : IP Array ([source.ip, destination.ip])
tags                     : Keyword Array
```

---

## 3. Telemetry Normalization Mapping Matrix

### 3.1 Suricata EVE JSON (`logs-suricata.eve-default`)

| Suricata Raw Field | Target ECS Field | Transformation / Extraction Logic |
|---|---|---|
| `timestamp` | `@timestamp` | Parse to ISO8601 UTC |
| `event_type` | `event.dataset` / `event.action` | Direct string copy |
| `"alert"` | `event.kind` | Static value `"alert"` |
| `src_ip` | `source.ip`, `related.ip` | IP validation & array append |
| `src_port` | `source.port` | Integer conversion |
| `dest_ip` | `destination.ip`, `related.ip` | IP validation & array append |
| `dest_port` | `destination.port` | Integer conversion |
| `proto` | `network.transport` | Lowercase string (`"tcp"`, `"udp"`) |
| `app_proto` | `network.protocol` | Lowercase string (`"http"`, `"dns"`) |
| `community_id` | `network.community_id` | Direct copy |
| `alert.signature` | `rule.name` | Direct copy |
| `alert.signature_id` | `rule.id` | Convert to string |
| `alert.severity` | `event.severity` | Map: 1 -> 4 (Crit), 2 -> 3 (High), 3 -> 2 (Med) |
| `alert.category` | `rule.category` | Direct copy |
| `alert.metadata.mitre_technique_id`| `threat.technique.id` | Extract e.g. `"T1190"` |
| `"soc-sensor"` | `observer.name` / `host.name` | Static sensor host identifier |

### 3.2 Snort 3 JSON Alert (`logs-snort.alert-default`)

| Snort 3 Raw Field | Target ECS Field | Transformation / Extraction Logic |
|---|---|---|
| `timestamp` | `@timestamp` | Parse Unix epoch/ISO string |
| `action` | `event.action` | `"allow"` or `"block"` |
| `"alert"` | `event.kind` | Static value `"alert"` |
| `src_addr` | `source.ip`, `related.ip` | IP mapping |
| `src_port` | `source.port` | Integer conversion |
| `dst_addr` | `destination.ip`, `related.ip` | IP mapping |
| `dst_port` | `destination.port` | Integer conversion |
| `proto` | `network.transport` | Lowercase string |
| `service` | `network.protocol` | Lowercase string |
| `msg` | `rule.name` | Direct copy |
| `sid` | `rule.id` | String formatted: `sid` |
| `class` | `rule.category` | Direct copy |
| `"snort"` | `observer.name` | Static observer name |

### 3.3 Wazuh Alert JSON (`logs-wazuh.alert-default`)

| Wazuh Raw Field | Target ECS Field | Transformation / Extraction Logic |
|---|---|---|
| `timestamp` | `@timestamp` | Parse ISO8601 string |
| `"alert"` | `event.kind` | Static value `"alert"` |
| `rule.level` | `event.severity` | Scale: 12-16 -> 4 (Crit), 7-11 -> 3 (High), 3-6 -> 2 (Med) |
| `rule.id` | `rule.id` | String e.g. `"100102"` |
| `rule.description` | `rule.name` | Direct copy |
| `rule.mitre.id` | `threat.technique.id` | Array / string copy e.g. `"T1046"` |
| `data.srcip` | `source.ip`, `related.ip` | Conditional copy if present |
| `data.dstip` | `destination.ip`, `related.ip` | Conditional copy if present |
| `agent.name` | `host.name` | Agent hostname e.g. `"soc-victim"` |
| `"wazuh"` | `observer.name` | Static observer name |

### 3.4 Gateway Firewall nftables (`logs-firewall.traffic-default`)

| nftables Syslog Field | Target ECS Field | Transformation / Extraction Logic |
|---|---|---|
| `timestamp` | `@timestamp` | Syslog timestamp |
| `"event"` | `event.kind` | Static value `"event"` |
| `SRC` | `source.ip`, `related.ip` | IP mapping |
| `SPT` | `source.port` | Integer conversion |
| `DST` | `destination.ip`, `related.ip` | IP mapping |
| `DPT` | `destination.port` | Integer conversion |
| `PROTO` | `network.transport` | Lowercase string |
| Prefix `SOC-FW-DENY` | `event.action` / `event.outcome` | Action: `"drop"`, Outcome: `"denied"` |
| `"soc-gateway"` | `observer.name` / `host.name` | Gateway node identifier |

---

## 4. Cross-Stream Search Demonstration

With this normalization, a single query retrieves the complete multi-source threat progression:

```text
[12:00:01] logs-firewall.traffic-default : DENIED packet to 10.77.10.10:9201 from 10.77.20.20
[12:00:02] logs-suricata.eve-default     : ALERT T1046 Nmap NULL/XMAS Scan against 10.77.30.20
[12:00:04] logs-snort.alert-default      : ALERT Snort 3 Stealth Scan Flag Anomaly
[12:00:10] logs-wazuh.alert-default      : ALERT T1110 SSH Brute Force Authentication Failure
```
All connected via `source.ip: 10.77.20.20` and `destination.ip: 10.77.30.20`.
