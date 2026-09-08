# Evidence Record: EV-HYPERV-002

## 1. Metadata Summary

| Field | Value |
|---|---|
| **Evidence ID** | `EV-HYPERV-002` |
| **Requirement** | `REQ-NET-01` (3-Zone Hyper-V Isolation), `REQ-NET-02` (Port Mirroring), `REQ-VM-01` (4 Gen-2 VMs) |
| **Design Reference** | SOC Architecture HLD v1.0 / LLD v1.0 Section 2.1 & 4.2 / AGENTS.md Section 4 & 5 |
| **Implementation Phase** | Phase 32A (Hyper-V Elevated Provisioning & Live Sensor E2E Validation) |
| **Test** | `TC-HOST-001`, `Test-SocHyperVPrerequisites.ps1`, `pytest tests/` (22/22 PASS), `vmnet10_dependency_check` |
| **Timestamp** | `2026-08-27T12:23:30+09:00` |
| **Component** | Host (`DESKTOP-QIFELML`, Win11 26100, 63.8GB RAM, 1.2TB Disk), VMware Workstation 17.5.2, Hyper-V Subsystem |
| **Expected** | Administrator session verifies host, resolves VMnet10 collision, provisions Hyper-V 3-zone switches & 4 Gen-2 VMs, and executes Live Sensor E2E validation |
| **Actual** | Session is elevated (Administrator = True), Phase 31 regression test passed (22/22 PASS). However, execution is **BLOCKED** due to two critical environmental constraints: (1) Active VMware VMs (`soc-gateway` PID 22752, `soc-victim` PID 12956, `soc-sensor` PID 5200, `soc-attacker` PID 21612, `soc-siem` PID 24264) are currently running and actively bound to `VMware Network Adapter VMnet10` (`10.77.10.1/24`); (2) Windows Optional Feature `Microsoft-Hyper-V-All` is currently `Disabled` on the host, requiring Windows Feature enablement and a reboot before Hyper-V cmdlets (`New-VMSwitch`, `New-VM`) can function |
| **Result** | **`BLOCKED (ACTIVE VMWARE VMS & HYPER-V FEATURE DISABLED)`** |
| **Completion Gate** | `GATE-HYPERV-01 = BLOCKED` |

---

## 2. Elevation & Privilege Status
- **Process Identity**: `DESKTOP-QIFELML\user`
- **Windows Built-in Administrator Role**: `True` (Elevated)
- **Token Elevation**: High IL

---

## 3. Host State & Active Workload Audit

### 3.1 Active VMware Workstation Instances (Conflict Investigation)
All 5 VMware SOC lab virtual machines are actively executing on the host with active file locks (`*.lck`):
- `soc-gateway` (PID: 22752, `soc-gateway.vmx`, NIC 0 bound to `VMnet10`)
- `soc-victim` (PID: 12956, `soc-victim.vmx`)
- `soc-sensor` (PID: 5200, `soc-sensor.vmx`)
- `soc-attacker` (PID: 21612, `soc-attacker.vmx`)
- `soc-siem` (PID: 24264, `soc-siem.vmx`)

### 3.2 Subnet Collision Analysis (`10.77.10.0/24`)
- Adapter `VMware Network Adapter VMnet10` is **Up** with IP `10.77.10.1/24`.
- VMware DHCP & NAT services (`vmnat.exe`, `vmnetdhcp.exe`) are actively bound to `VMnet10`.
- Active host routes for `10.77.10.0/24` are pointing to `VMnet10`.
- Disabling `VMnet10` while `soc-gateway` (PID 22752) is running would immediately disrupt active VMware lab communications.

### 3.3 Windows Hyper-V Optional Features Status
- `Microsoft-Hyper-V-All`: **State = Disabled**
- `Microsoft-Hyper-V`: **State = Disabled**
- `Microsoft-Hyper-V-Hypervisor`: **State = Disabled**
- `Microsoft-Hyper-V-Services`: **State = Disabled**
- `Microsoft-Hyper-V-Management-PowerShell`: **State = Disabled**
- `vmms` Service: **Not installed/active**

---

## 4. Phase 31 Regression Validation
- `pytest tests/`: **`22 passed in 32.03s` (100% PASS)**
- Verification includes: `test_correlation.py`, `test_dashboard_api.py`, `test_detection_tuning.py`, `test_parsers.py`, `test_pcap_manifest.py`, `test_phase31_e2e.py`, `test_threat_intel.py`.

---

## 5. Artifacts in Evidence EV-HYPERV-002
- `prechange_network_state.json`: Full dump of NetAdapters, IPAddresses, NetRoutes, and DNS servers.
- `prechange_hyperv_state.json`: Hyper-V switches, VMs, and service state snapshot.
- `vmnet10_dependency_check.txt`: Process list, active `.lck` files, and VMnet10 bindings.
- `phase32a_verification_report.json`: Structured phase report.
