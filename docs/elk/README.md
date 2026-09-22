# 🛡️ SOC Detection & Monitoring Lab — ELK Stack Architecture Index

> **Master Guide**: Central Security Data, Search, Threat Hunting & Correlation Layer  
> **Status**: `IMPLEMENTATION COMPLETE` (All 14 Phases & 8 Critical Release Gates Passed)  

---

## Document Index & Specifications

| Spec ID | Title | Summary |
|---|---|---|
| [01-ELK-ARCHITECTURE.md](file:///C:/Users/user/Documents/ChatGPT/Suricata-Snort-SOC-Lab/docs/elk/01-ELK-ARCHITECTURE.md) | **ELK Architecture Design** | Single-Node Elasticsearch 8.17.3, Logstash, Kibana topology, hardware budgets, and Wazuh separation. |
| [02-ELK-NETWORK-DESIGN.md](file:///C:/Users/user/Documents/ChatGPT/Suricata-Snort-SOC-Lab/docs/elk/02-ELK-NETWORK-DESIGN.md) | **Network & Port Matrix Design** | Port conflict resolution (9201/5602 vs. 9200/5601), Zone access controls, and nftables boundary rules. |
| [03-LOG-SOURCE-INVENTORY.md](file:///C:/Users/user/Documents/ChatGPT/Suricata-Snort-SOC-Lab/docs/elk/03-LOG-SOURCE-INVENTORY.md) | **Log Source Inventory** | Suricata EVE, Snort 3 JSON, Wazuh alerts, and nftables syslog ingestion paths and volume estimates. |
| [04-DATA-STREAM-DESIGN.md](file:///C:/Users/user/Documents/ChatGPT/Suricata-Snort-SOC-Lab/docs/elk/04-DATA-STREAM-DESIGN.md) | **Data Stream & ILM Design** | Elastic Data Streams (`logs-*-*`), Single-node replica policy (`0`), and Hot/Warm/Cold ILM retention. |
| [05-ECS-MAPPING.md](file:///C:/Users/user/Documents/ChatGPT/Suricata-Snort-SOC-Lab/docs/elk/05-ECS-MAPPING.md) | **ECS Normalization Matrix** | Universal Elastic Common Schema (ECS 8.x) mapping across Suricata, Snort, Wazuh, and Firewall. |

---

## Operational Verification & Verification Scripts

| Script | Location | Purpose |
|---|---|---|
| `verify_cross_stream_search.py` | `infrastructure/elk/scripts/` | Cross-stream wildcard timeline & ATT&CK aggregation validation |
| `verify_ilm_policy.py` | `infrastructure/elk/scripts/` | Validates ILM hot/warm/delete policy & index template management |
| `verify_correlation_rules.py` | `infrastructure/elk/scripts/` | Validates Query DSL campaign & EQL sequence detection engine |
| `verify_elk_final_release.py` | `infrastructure/elk/scripts/` | Final release gate evaluating all 8 operational and security gates |

---

## Kibana Operational Artifacts

- **SOC Threat Operations Dashboard**: `http://127.0.0.1:5602/app/dashboards#/view/soc-unified-threat-dashboard`
- **Data Views**:
  - `soc-unified-logs` (`logs-*`): Cross-telemetry search & hunting
  - `soc-suricata-logs` (`logs-suricata.*-*`): Suricata EVE telemetry
  - `soc-snort-logs` (`logs-snort.*-*`): Snort 3 alerts
  - `soc-firewall-logs` (`logs-firewall.*-*`): Gateway nftables audit logs
  - `soc-wazuh-logs` (`logs-wazuh.*-*`): Wazuh SIEM alerts

---

## Architectural Principles Quick Reference

1. **No Port Collisions**: Elasticsearch exposed on `9201` and Kibana on `5602`, completely preserving Wazuh OpenSearch on `9200` and Wazuh Dashboard on `5601`.
2. **Single-Node Optimization**: Replica shards strictly pinned to `0` to guarantee green cluster health on single-node Lab hardware.
3. **Strict AI Evidence Separation**: Raw evidence streams (`logs-*`) remain immutable; AI Copilot analysis results are routed to isolated `soc-ai.analysis-default`.
4. **Defensive Hardening**: Native Elasticsearch TLS and RBAC with granular API Keys for FastAPI read operations, barring raw `elastic` superuser access from client apps.
