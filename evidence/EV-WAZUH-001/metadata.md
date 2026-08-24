# Evidence Record: EV-WAZUH-001

## 1. Metadata Summary

| Field | Value |
|---|---|
| **Evidence ID** | `EV-WAZUH-001` |
| **Requirement** | `REQ-SIEM-01` (Wazuh 4.14.7 Single-Node SIEM Architecture & Docker Deployment) |
| **Design Reference** | SOC Architecture HLD v1.0 (Section 1) / LLD v1.0 (Section 1.4) / Implementation Plan Phase 15-16 |
| **Implementation Phase** | Phase 15-16 (Wazuh Host Readiness & Docker Deployment) |
| **Test** | Docker Compose Syntax Validation & Port Mapping Hardening Check |
| **Scenario** | Wazuh Single-Node SIEM Stack Provisioning |
| **Timestamp** | `2026-08-24T16:22:15+09:00` |
| **Component** | Wazuh 4.14.7 (`soc-wazuh-indexer`, `soc-wazuh-manager`, `soc-wazuh-dashboard`) |
| **Expected** | `1514/1515/443` bound to MGMT IP (`10.77.10.10`), `9200/55000` restricted to `127.0.0.1`, `local_rules.xml` mounted |
| **Actual** | `docker compose -f infrastructure/docker/docker-compose.wazuh.yml config` validated without errors; security hardening verified |
| **Result** | `PASS` |
| **Completion Gate** | `GATE-WAZUH-01 = PASS` |

---

## 2. Verified Port Exposure & Security Posture

```text
Service               External / MGMT Binding      Localhost Restriction
-----------------------------------------------------------------------------
soc-wazuh-manager     10.77.10.10:1514 (Agent Ingest) 127.0.0.1:55000 (REST API)
                      10.77.10.10:1515 (Enrollment)
soc-wazuh-indexer     -                            127.0.0.1:9200 (OpenSearch)
soc-wazuh-dashboard   10.77.10.10:443 (HTTPS Web)  -
```

---

## 3. Gate Assessment

| Gate ID | Condition | Status |
|---|---|---|
| **GATE-WAZUH-HOST-01** | Docker Server 29.5.3, Compose v2.x, WSL2 2.7.12.0, RAM 63.8GB | **PASS** |
| **GATE-WAZUH-01** | Port mapping hardened, internal API protected, custom Suricata decoders linked | **PASS** |
