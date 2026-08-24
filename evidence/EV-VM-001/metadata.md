# Evidence Record: EV-VM-001

## 1. Metadata Summary

| Field | Value |
|---|---|
| **Evidence ID** | `EV-VM-001` |
| **Requirement** | `REQ-VM-01` (VM Provisioning & Multi-NIC Interface Mapping) |
| **Design Reference** | SOC Architecture HLD v1.0 (Section 1) / LLD v1.0 (Section 1.1) / Implementation Plan Phase 3 |
| **Implementation Phase** | Phase 3 (VM Provisioning) |
| **Test** | Hyper-V VM Creation & Network Adapter Mapping Execution (`03_provision_vms.ps1`) |
| **Scenario** | 4 Isolated VMs Provisioning with Fixed Specs & Switch Connections |
| **Timestamp** | `2026-08-24T16:09:33+09:00` |
| **Component** | Hyper-V Virtual Machines (`soc-gateway`, `soc-victim`, `soc-sensor`, `soc-attacker`) |
| **Expected** | 4 Gen 2 VMs created with pinned resources and exact vSwitch connections |
| **Actual** | 4 VMs created (`soc-gateway`, `soc-victim`, `soc-sensor`, `soc-attacker`), 7 virtual network adapters configured and verified |
| **Result** | `PASS` |
| **Completion Gate** | `GATE-VM-01 = PASS` |

---

## 2. Verified VM & Network Adapter Inventory

```text
Name         State Generation MemoryGB
----         ----- ---------- --------
soc-attacker   Off          2        0
soc-gateway    Off          2        0
soc-sensor     Off          2        0
soc-victim     Off          2        0

VMName       Name        SwitchName     PortMirroringMode
------       ----        ----------     -----------------
soc-gateway  nic-mgmt    soc-vsw-mgmt   None
soc-gateway  nic-attack  soc-vsw-attack None
soc-gateway  nic-victim  soc-vsw-victim None
soc-victim   nic-victim  soc-vsw-victim None
soc-sensor   nic-mgmt    soc-vsw-mgmt   None
soc-sensor   nic-monitor soc-vsw-victim None
soc-attacker nic-attack  soc-vsw-attack None
```

---

## 3. Gate Assessment

| Gate ID | Condition | Status |
|---|---|---|
| **GATE-VM-01** | 4 VMs created with exact vCPU, RAM, VHDX, and vSwitch mappings | **PASS** |
| **RG-005** | Hyper-V MAC Mapping exported to `docs/04-deployment/hyperv-mac-map.csv` | **PASS** |
