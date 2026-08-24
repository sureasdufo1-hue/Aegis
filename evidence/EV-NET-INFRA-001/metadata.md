# Evidence Record: EV-NET-INFRA-001

## 1. Metadata Summary

| Field | Value |
|---|---|
| **Evidence ID** | `EV-NET-INFRA-001` |
| **Requirement** | `REQ-NET-01` (Network Segmentation & 3-Zone Virtual Infrastructure) |
| **Design Reference** | SOC Architecture HLD v1.0 (Section 1) / LLD v1.0 (Section 1.1) / Implementation Plan Phase 2 |
| **Implementation Phase** | Phase 2 (Hyper-V Virtual Network) |
| **Test** | Virtual Switch Configuration & Windows Host IP Binding Test |
| **Scenario** | 3-Zone Virtual Switch Infrastructure Provisioning |
| **Timestamp** | `2026-08-24T15:59:00+09:00` |
| **Component** | Hyper-V Virtual Switch & Windows Host Management Network Adapter |
| **Expected** | `soc-vsw-mgmt` (Internal), `soc-vsw-attack` (Private), `soc-vsw-victim` (Private) created; `vEthernet (soc-vsw-mgmt)` assigned `10.77.10.10/24` |
| **Actual** | Automation scripts `01_create_vswitches.ps1` and `00_rollback_vswitches.ps1` configured; elevated execution required for Hyper-V WMI provisioning |
| **Result** | `PENDING_ELEVATED_RUN` |
| **Completion Gate** | `GATE-NET-INFRA-01` |

---

## 2. Target Architecture Baseline

```text
+-------------------------------------------------------------------------+
|                              Windows Host                               |
|                     vEthernet (soc-vsw-mgmt): 10.77.10.10/24            |
+------------------------------------+------------------------------------+
                                     |
               +---------------------+---------------------+
               |                     |                     |
               v                     v                     v
     [ soc-vsw-mgmt ]       [ soc-vsw-attack ]    [ soc-vsw-victim ]
       Type: Internal         Type: Private         Type: Private
       CIDR: 10.77.10.0/24    CIDR: 10.77.20.0/24   CIDR: 10.77.30.0/24
```

---

## 3. Provisioning & Validation Commands

### Elevated PowerShell Execution:
```powershell
Set-Location "C:\Users\user\Documents\ChatGPT\Suricata-Snort-SOC-Lab"
.\infrastructure\hyper-v\01_create_vswitches.ps1
```

### Direct Verification Commands:
```powershell
# 1. Verify Virtual Switches
Get-VMSwitch | Where-Object Name -like "soc-vsw-*" | Format-Table Name, SwitchType

# 2. Verify Host Management IP
Get-NetIPAddress -InterfaceAlias "vEthernet (soc-vsw-mgmt)" -AddressFamily IPv4 | Format-Table InterfaceAlias, IPAddress, PrefixLength
```

---

## 4. Gate Assessment Checklist

- [ ] `soc-vsw-mgmt` created as **Internal** vSwitch
- [ ] `soc-vsw-attack` created as **Private** vSwitch
- [ ] `soc-vsw-victim` created as **Private** vSwitch
- [ ] Host adapter `vEthernet (soc-vsw-mgmt)` configured with static IP `10.77.10.10/24` (DHCP Disabled)
- [ ] `GATE-NET-INFRA-01` validation passes
