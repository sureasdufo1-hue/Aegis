# ELK Network Design & Port Matrix Specification (Phase ELK-1)

> **Document ID**: `ELK-NET-001`  
> **Status**: `APPROVED / BASELINE`  
> **Target Scope**: Network Segmentation, Ingestion Routing, and Port Conflict Resolution  
> **Classification**: Internal Engineering Baseline  

---

## 1. Network Topology & Zone Isolation

The ELK deployment strictly honors the three-zone network architecture defined in [AGENTS.md](file:///C:/Users/user/Documents/ChatGPT/Suricata-Snort-SOC-Lab/AGENTS.md) Section 5:

```text
               ZONE-ATTACK (Red Zone: 10.77.20.0/24)
                                 │
                                 ▼ [DENIED TO MGMT: nftables drop & log]
  +-----------------------------------------------------------------------------+
  | SOC GATEWAY (10.77.10.1 / 10.77.20.1 / 10.77.30.1)                          |
  +-----------------------------------------------------------------------------+
         │ (Mirrored via Hyper-V)                      │ (Management Route)
         ▼                                             ▼
  [ SOC SENSOR ]                             ZONE-MGMT (10.77.10.0/24)
  eth0: 10.77.10.20 (MGMT)                   Windows Host: 10.77.10.10
  eth1: NO L3 IP (Mirror)                               │
         │                                              ▼
         │ Ingest Stream (5044/TCP)          [ Docker Host & ELK Stack ]
         └─────────────────────────────────> soc-logstash: 10.77.10.10:5044
                                                        │
                                                        ▼
                                             soc-elasticsearch: 9201 (Host)
                                                        ▲
                                             ┌──────────┴──────────┐
                                             │                     │
                                     [ soc-kibana ]      [ FastAPI SOC Console ]
                                      Port: 5602            Port: 8000
```

---

## 2. Port Matrix & Port Conflict Resolution

During Phase ELK-0, a critical conflict was detected:
- Wazuh Indexer (OpenSearch) is allocated `127.0.0.1:9200`
- Wazuh Dashboard is allocated `5601` and `443`

To prevent port collision while keeping internal container services operating on standard ports:

| Service | Internal Container Port | Host Bound Port | Protocol | Binding Interface | Accessible From | Purpose |
|---|---|---|---|---|---|---|
| **Elasticsearch API** | `9200` | **`9201`** | HTTPS / TCP | `127.0.0.1` | Host, FastAPI Console, Kibana | REST API, Search, Ingest, Health Checks |
| **Kibana UI** | `5601` | **`5602`** | HTTP / HTTPS | `127.0.0.1`, `10.77.10.10` | Host Browser, Analyst Workstation | Threat Hunting, Dashboards, Discovery |
| **Logstash Beats Input** | `5044` | **`5044`** | TCP (TLS Opt) | `10.77.10.10` | Sensor VM (`10.77.10.20`), Host | Suricata EVE & Snort JSON stream ingestion |
| **Logstash Syslog Input**| `5514` | **`5514`** | UDP / TCP | `10.77.10.10` | SOC Gateway (`10.77.10.1`) | Gateway Firewall (nftables) drop/forward logs |
| **Logstash Monitoring** | `9600` | **`9600`** | HTTP / TCP | `127.0.0.1` | Host Local Only | Logstash pipeline metrics & telemetry |
| **FastAPI SOC Console** | `8000` | **`8000`** | HTTP / WS | `0.0.0.0` | Host Browser, Analyst Workstation | Primary Operational SOC Dashboard |
| *Wazuh Indexer (Legacy)*| `9200` | `9200` | HTTP / TCP | `127.0.0.1` | Wazuh Manager, Wazuh Dashboard | Wazuh FIM/Host Event Store (Preserved) |
| *Wazuh Dashboard (Legacy)*| `5601` | `5601` | HTTPS / TCP | `0.0.0.0` | Host Browser | Wazuh Host Security Dashboard (Preserved) |
| *Wazuh Agent Delivery* | `1514` | `1514` | TCP | `0.0.0.0` | Sensor VM, Victim VM | Wazuh Agent secure event delivery |

---

## 3. Network Access Control Rules (Firewall & nftables)

### 3.1 Gateway Firewall Rule Enforcement (`infrastructure/network/gateway_nftables.conf`)

The following firewall rules govern ELK network boundaries:

```nftables
# 1. Management Zone Isolation: Red Zone (10.77.20.0/24) cannot reach ELK ports
chain forward {
    # Existing rule: strictly log & drop all attack traffic to management zone
    ip saddr 10.77.20.0/24 ip daddr 10.77.10.0/24 log prefix "SOC-FW-DENY-ATTACK-TO-MGMT: " drop;

    # Explicit deny for ELK Ingestion & API Ports
    ip saddr 10.77.20.0/24 tcp dport { 9200, 9201, 5601, 5602, 5044, 9600 } drop;
    ip saddr 10.77.20.0/24 udp dport { 5514, 514 } drop;
}

# 2. Allow Sensor -> ELK Ingestion
chain forward {
    ip saddr 10.77.10.20 ip daddr 10.77.10.10 tcp dport 5044 accept;
}

# 3. Allow Gateway Syslog -> Logstash
chain output {
    ip daddr 10.77.10.10 udp dport 5514 accept;
}
```

### 3.2 Host-Level Network Binding Policy
- **Elasticsearch (`9201`)**: Bound exclusively to `127.0.0.1` (Host loopback). External attacker network probes receive no response.
- **Kibana (`5602`)**: Bound to `127.0.0.1` and `10.77.10.10`.
- **Logstash (`5044`, `5514`)**: Bound to `10.77.10.10` on the Management vSwitch.

---

## 4. Ingestion Data Paths & Bandwidth Control

```text
[ Data Source ]             [ Protocol ]     [ Target Endpoint ]       [ Expected Volume / EPS ]
Suricata EVE JSON           Beats / TCP      10.77.10.10:5044          50 ~ 250 EPS (Attack Peak: 1,500 EPS)
Snort 3 alert_json          Beats / TCP      10.77.10.10:5044          10 ~ 100 EPS
Gateway nftables syslog     Syslog / UDP     10.77.10.10:5514          20 ~ 150 EPS
Wazuh alerts.json           File / Beats     10.77.10.10:5044          5 ~ 50 EPS
```

- **Bandwidth Impact**: Average telemetry payload size is ~1.2 KB. At peak 2,000 EPS, network bandwidth consumption on `soc-vsw-mgmt` is **< 2.5 MB/s**, causing zero degradation to Hyper-V vSwitch performance.
