# Phase AI-0: Current Baseline Assessment

## 1. System Inventory & Baseline State

- **Date**: 2026-09-07
- **Host**: Windows 11 Education (Build 26100), Intel(R) Core CPU, 63.84 GB Total RAM, 23.9 GB Free RAM.
- **Python**: 3.13.14 (Environment: `.venv` / global Python)
- **Local AI / GPU**: Intel(R) UHD Graphics P750 (Integrated, 2GB shared memory, no CUDA). Ollama CLI is **Not Installed** locally; default provider must support deterministic Mock mode and external/local Ollama endpoint abstraction.
- **Docker Stack**:
  - `soc-wazuh-indexer`: Up (Port 9200 OpenSearch REST API)
  - `soc-wazuh-manager`: Up (Ports 1514/1515 TCP, 55000 API)
  - `soc-wazuh-dashboard`: Up (Ports 443/5601 HTTPS)
- **FastAPI SOC Console**: Running on `http://127.0.0.1:8501` (`/api/health` status: `healthy`).
- **Regression Suite**: `pytest tests/` -> **22/22 PASS (100%)** in 0.82s.

---

## 2. Existing SOC Assets & Integration Points

| Component | Repository Path / Port | Role |
|---|---|---|
| **EVE Parser** | `analyzer/parsers/eve_parser.py` | Suricata EVE JSON event normalizer |
| **Snort Parser** | `analyzer/parsers/snort_parser.py` | Snort 3 alert JSON normalizer |
| **Data Models** | `analyzer/models.py` | `NormalizedAlert`, `Severity`, `EngineType` |
| **Correlation Engine** | `analyzer/detection/correlation_engine.py` | 4-stage killchain classifier & 30-min window correlation |
| **Threat Intel** | `analyzer/detection/threat_intel.py` | Known bad IPs/domains IOC matching |
| **SOC Console** | `dashboard/app.py` | FastAPI app serving dashboard & REST API on port 8501 |
| **Playbooks** | `playbooks/*.md` | Incident investigation SOPs (5 playbooks) |
| **PCAPs & Manifest** | `pcaps/metadata/pcap_manifest.json` | 6 verified attack scenario PCAPs with SHA-256 |

---

## 3. Network Boundaries & Protected Assets

```text
ZONE-MGMT:   10.77.10.0/24 (Host: 10.77.10.10, Gateway: 10.77.10.1, Sensor: 10.77.10.20, SIEM)
ZONE-ATTACK: 10.77.20.0/24 (Attacker: 10.77.20.20, Gateway: 10.77.20.1)
ZONE-VICTIM: 10.77.30.0/24 (Victim: 10.77.30.20 / 10.77.30.100, Gateway: 10.77.30.1)
```

**CRITICAL RULE**: The Gateway (`10.77.10.1`), DNS server, SIEM Indexer/Manager, Sensor MGMT, and Host MGMT adapter MUST NEVER be recommended for blocking or isolation. A deterministic protected asset whitelist is enforced outside the LLM.
