# Evidence Record: EV-HYPERV-001

## 1. Metadata Summary

| Field | Value |
|---|---|
| **Evidence ID** | `EV-HYPERV-001` |
| **Requirement** | `REQ-NET-01` (3-Zone Hyper-V Isolation), `REQ-NET-02` (Port Mirroring), `REQ-VM-01` (4 Gen-2 VMs) |
| **Design Reference** | SOC Architecture HLD v1.0 / LLD v1.0 Section 2.1 & 4.2 / AGENTS.md Section 4 & 5 |
| **Implementation Phase** | Phase 32 (Hyper-V Segmented SOC Lab Provisioning & Live Sensor Integration) |
| **Test** | `TC-HOST-001`, `Test-SocHyperVPrerequisites.ps1`, `deploy_all.ps1 -DryRun` |
| **Timestamp** | `2026-08-26T16:31:20+09:00` |
| **Component** | Hyper-V Host (`DESKTOP-QIFELML`, Win11 26100, 63.8GB RAM, 1.2TB Disk), Virtual Switches, VM Templates, Port Mirroring Matrix |
| **Expected** | 3 Virtual Switches created, 4 Gen-2 VMs provisioned with ISOs, Port Mirroring configured from `soc-victim` to `soc-sensor`, and Host route added |
| **Actual** | Prerequisite analysis and Dry-Run validation successfully executed; Host resources verified (63.8GB RAM, 1.2TB free, ISOs present); Full execution requires Administrator elevation via `deploy_hyperv_admin.bat` and resolution of `VMnet10` subnet conflict (`10.77.10.1/24`) |
| **Result** | **`BLOCKED (ELEVATION & ROUTE CONFLICT ACTION REQUIRED)`** |
| **Completion Gate** | `GATE-HYPERV-01 = BLOCKED` |

---

## 2. Host Readiness & Resource Verification

- **OS / Hyper-V Service**: Windows 11 Education (Build 26100), `vmms` service is **Running**.
- **CPU & Memory**: 4 Cores (8 Logical Processors), **63.84 GB Total RAM**, **23.90 GB Free RAM** (Requirement: 17 GB).
- **Target Storage (`C:\SOC-Lab\vm`)**: **1,236.07 GB Free** (Requirement: 166 GB).
- **ISO Images Present in `C:\SOC-Lab\iso`**:
  - `ubuntu-22.04.5-live-server-amd64.iso` (SHA-256 verified)
  - `kali-linux-2026.2-installer-amd64.iso` (SHA-256 verified)

---

## 3. Dry Run Provisioning Plan & Resource Allocations

```text
========================================================================================================
VM Name       OS / Role                      Gen  vCPU  RAM (MB)  VHDX (GB)  Network Adapters / Switches
========================================================================================================
soc-gateway   Ubuntu 22.04 Router/Firewall    2     1     1024       16      nic-mgmt   -> soc-vsw-mgmt (10.77.10.1)
                                                                             nic-attack -> soc-vsw-attack (10.77.20.1)
                                                                             nic-victim -> soc-vsw-victim (10.77.30.1)
soc-victim    Ubuntu 22.04 + OWASP JuiceShop  2     2     4096       30      nic-victim -> soc-vsw-victim (10.77.30.20, Mirror: SOURCE)
soc-sensor    Ubuntu 22.04 + Suricata 8.0.6   2     4     8192       80      nic-mgmt   -> soc-vsw-mgmt (10.77.10.20)
                                                                             nic-monitor-> soc-vsw-victim (NO IP, Mirror: DESTINATION)
soc-attacker  Kali Linux 2026.2               2     2     4096       40      nic-attack -> soc-vsw-attack (10.77.20.20)
========================================================================================================
```

---

## 4. Blockers & Action Required

1. **UAC Elevation Required**:
   - Hyper-V cmdlets (`New-VMSwitch`, `New-VM`, `Set-VMNetworkAdapter`) require Administrator privileges.
   - Action: Execute [`deploy_hyperv_admin.bat`](file:///C:/Users/user/Documents/ChatGPT/Suricata-Snort-SOC-Lab/deploy_hyperv_admin.bat) via Windows "Run as Administrator".
2. **Subnet Conflict with `VMware Network Adapter VMnet10`**:
   - Host interface `VMware Network Adapter VMnet10` is currently bound to `10.77.10.1/24`.
   - Action: Disable `VMnet10` adapter or change its IP in VMware Virtual Network Editor before starting Hyper-V `vEthernet (soc-vsw-mgmt)`.

---

## 5. Artifacts & Supporting Files
- [`evidence/EV-HYPERV-001/prerequisites_report.json`](prerequisites_report.json)
- [`evidence/EV-HYPERV-001/dry_run_plan.json`](dry_run_plan.json)
- [`infrastructure/hyper-v/deploy_all.ps1`](../../infrastructure/hyper-v/deploy_all.ps1)
- [`infrastructure/hyper-v/Test-SocHyperVPrerequisites.ps1`](../../infrastructure/hyper-v/Test-SocHyperVPrerequisites.ps1)
- [`infrastructure/hyper-v/Test-SocHyperVTopology.ps1`](../../infrastructure/hyper-v/Test-SocHyperVTopology.ps1)
- [`infrastructure/hyper-v/Test-SocPortMirroring.ps1`](../../infrastructure/hyper-v/Test-SocPortMirroring.ps1)
