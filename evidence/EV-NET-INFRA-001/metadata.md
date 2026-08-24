# Evidence Record: EV-NET-INFRA-001

## 1. Metadata Summary

| Field | Value |
|---|---|
| **Evidence ID** | `EV-NET-INFRA-001` |
| **Requirement** | `REQ-NET-01` (Network Segmentation & 3-Zone Virtual Infrastructure) |
| **Design Reference** | SOC Architecture HLD v1.0 (Section 1) / LLD v1.0 (Section 1.1) / Implementation Plan Phase 2 |
| **Implementation Phase** | Phase 2 (Hyper-V Virtual Network) |
| **Test** | Virtual Switch Configuration & Windows Host IP Binding Execution (`01_create_vswitches.ps1`) |
| **Scenario** | 3-Zone Virtual Switch Infrastructure Provisioning |
| **Timestamp** | `2026-08-24T16:03:49+09:00` |
| **Component** | Hyper-V Virtual Switch & Windows Host Management Network Adapter |
| **Expected** | `soc-vsw-mgmt` (Internal), `soc-vsw-attack` (Private), `soc-vsw-victim` (Private) created; `vEthernet (soc-vsw-mgmt)` assigned `10.77.10.10/24` |
| **Actual** | 3 vSwitches successfully created; Host adapter `vEthernet (soc-vsw-mgmt)` configured with static IPv4 `10.77.10.10/24` (DHCP Disabled); Host return route `10.77.30.0/24 via 10.77.10.1` added |
| **Result** | `PASS` |
| **Completion Gate** | `GATE-NET-INFRA-01 = PASS` |

---

## 2. Target Architecture Baseline

```text
+-------------------------------------------------------------------------+
|                              Windows Host                               |
|                     vEthernet (soc-vsw-mgmt): 10.77.10.10/24            |
|                     Route: 10.77.30.0/24 via 10.77.10.1                 |
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

## 3. Provisioning & Verification Execution Output

```text
============================================================
 [SOC LAB] Hyper-V Virtual Network Provisioning (Phase 2)
============================================================
[+] Creating Internal Switch: soc-vsw-mgmt...
[+] Creating Private Switch: soc-vsw-attack...
[+] Creating Private Switch: soc-vsw-victim...

[+] Configuring Host Adapter 'vEthernet (soc-vsw-mgmt)' with 10.77.10.10/24...
[+] Assigned IP 10.77.10.10/24 to 'vEthernet (soc-vsw-mgmt)'.

============================================================
 [GATE-NET-INFRA-01] Verification Summary
============================================================

Name           SwitchType
----           ----------
soc-vsw-mgmt     Internal
soc-vsw-attack    Private
soc-vsw-victim    Private

InterfaceAlias           IPAddress   PrefixLength
--------------           ---------   ------------
vEthernet (soc-vsw-mgmt) 10.77.10.10           24

[PASS] GATE-NET-INFRA-01: Virtual network infrastructure successfully created and verified.
```

---

## 4. Gate Assessment

| Gate ID | Condition | Status |
|---|---|---|
| **GATE-NET-INFRA-01** | `soc-vsw-mgmt` (Internal), `soc-vsw-attack` (Private), `soc-vsw-victim` (Private) active; Host IP `10.77.10.10/24` assigned | **PASS** |
