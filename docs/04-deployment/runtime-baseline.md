# 📊 Runtime Baseline & Verification Matrix

> **Environment**: Windows Host + Hyper-V + Docker Desktop (WSL2)  
> **Reference**: Implementation Plan v1.0 Section 36 & AGENTS.md Contract  
> **Last Verified**: 2026-08-24  

---

## 1. Runtime Verification Matrix

| Gate | Check Item | Verification Command | Actual Runtime Value | Status |
|---|---|---|---|---|
| **RG-001** | Windows Host Build | `Get-ComputerInfo` | `Windows 10 Education (Build 26100)` | **PASS** |
| **RG-002** | WSL Version | `wsl --version` | `WSL 2.7.12.0 (Kernel 6.6.x)` | **PASS** |
| **RG-003** | Gateway Interfaces | `ip -br link` (soc-gateway) | Defined via netplan (`eth0/1/2` mapped to Hyper-V MAC) | **PENDING_BOOT** |
| **RG-004** | Sensor Interfaces | `ip -br link` (soc-sensor) | `nic-mgmt` (eth0) / `nic-monitor` (eth1: NO IP) | **PENDING_BOOT** |
| **RG-005** | Hyper-V MAC Mapping | `Get-VMNetworkAdapter` | Exported to `docs/04-deployment/hyperv-mac-map.csv` | **PASS** |
| **RG-006** | Docker Engine & Bind | `docker version` / `docker compose` | `Docker Server 29.5.3` / `Compose v2.x` | **PASS** |

---

## 2. Fixed Network & Virtual Switch Baseline

```text
+---------------------------------------------------------------------------------------+
|                                    Windows Host                                       |
|                       vEthernet (soc-vsw-mgmt): 10.77.10.10/24                        |
|                       Static Route: 10.77.30.0/24 via 10.77.10.1                      |
+------------------------------------------+--------------------------------------------+
                                           |
                   +-----------------------+-----------------------+
                   |                       |                       |
                   v                       v                       v
         [ soc-vsw-mgmt ]         [ soc-vsw-attack ]      [ soc-vsw-victim ]
           Type: Internal           Type: Private           Type: Private
           CIDR: 10.77.10.0/24      CIDR: 10.77.20.0/24     CIDR: 10.77.30.0/24
```

---

## 3. Provisioned VM Hardware & Network Inventory

| VM Name | Generation | vCPU | RAM | Disk (VHDX) | Network Adapters | Switch Attachment | Mirroring Role |
|---|---|---|---|---|---|---|---|
| `soc-gateway` | Gen 2 | 1 | 1 GB | 16 GB | `nic-mgmt`<br>`nic-attack`<br>`nic-victim` | `soc-vsw-mgmt`<br>`soc-vsw-attack`<br>`soc-vsw-victim` | None |
| `soc-victim` | Gen 2 | 2 | 4 GB | 30 GB | `nic-victim` | `soc-vsw-victim` | **Source** |
| `soc-sensor` | Gen 2 | 4 | 8 GB | 80 GB | `nic-mgmt`<br>`nic-monitor` | `soc-vsw-mgmt`<br>`soc-vsw-victim` | **Destination** (`nic-monitor`) |
| `soc-attacker` | Gen 2 | 2 | 4 GB | 40 GB | `nic-attack` | `soc-vsw-attack` | None |

---

## 4. Hardware Resources Utilization

- **Host Total Physical RAM**: 63.84 GB
- **Lab VM Static Allocation**: 17.00 GB (Gateway: 1GB + Victim: 4GB + Sensor: 8GB + Attacker: 4GB)
- **Host Remaining Headroom**: ~46.84 GB (Well within safe operating limits)
