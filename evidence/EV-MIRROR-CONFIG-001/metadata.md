# Evidence Record: EV-MIRROR-CONFIG-001

## 1. Metadata Summary

| Field | Value |
|---|---|
| **Evidence ID** | `EV-MIRROR-CONFIG-001` |
| **Requirement** | `REQ-NET-02` (Hyper-V Port Mirroring Configuration) |
| **Design Reference** | SOC Architecture HLD v1.0 (Section 1) / LLD v1.0 (Section 1.1) / Implementation Plan Phase 7 |
| **Implementation Phase** | Phase 7 (Port Mirroring Configuration) |
| **Test** | PowerShell Port Mirroring Mode Validation (`02_configure_port_mirroring.ps1`) |
| **Scenario** | Passive Traffic Mirroring from Victim to Sensor Monitor NIC |
| **Timestamp** | `2026-08-24T16:09:50+09:00` |
| **Component** | Hyper-V Network Adapters (`soc-victim\nic-victim`, `soc-sensor\nic-monitor`) |
| **Expected** | `soc-victim\nic-victim` PortMirroringMode=Source, `soc-sensor\nic-monitor` PortMirroringMode=Destination |
| **Actual** | `soc-victim\nic-victim` set to Source, `soc-sensor\nic-monitor` set to Destination on `soc-vsw-victim` |
| **Result** | `PASS` |
| **Completion Gate** | `GATE-MIRROR-CONFIG-01 = PASS` |

---

## 2. Verified Port Mirroring State

```text
VMName     Name        SwitchName     PortMirroringMode
------     ----        ----------     -----------------
soc-victim nic-victim  soc-vsw-victim            Source
soc-sensor nic-mgmt    soc-vsw-mgmt                None
soc-sensor nic-monitor soc-vsw-victim       Destination
```

---

## 3. Gate Assessment

| Gate ID | Condition | Status |
|---|---|---|
| **GATE-MIRROR-CONFIG-01** | Port Mirroring Source and Destination accurately configured on shared vSwitch | **PASS** |
