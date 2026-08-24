# Evidence Record: EV-HOST-001

## 1. Metadata Summary

| Field | Value |
|---|---|
| **Evidence ID** | `EV-HOST-001` |
| **Requirement** | `REQ-HOST-01` (Host Virtualization, Container Runtime, Storage & Memory Readiness) |
| **Design Reference** | SOC Implementation Plan v1.0 (Phase 0) / LLD v1.0 |
| **Implementation Phase** | Phase 0 (Host Readiness) |
| **Test** | Host System Inspection (`verify_host_readiness.ps1`) |
| **Scenario** | Windows Host Prerequisites & Resource Validation |
| **Timestamp** | `2026-08-24T16:06:15+09:00` |
| **Component** | Windows 11 Host / Hyper-V / WSL2 / Docker Desktop |
| **Expected** | Hyper-V Enabled, WSL2 >= 2.1.5, Docker Operational, RAM >= 32GB, Storage Headroom Verified |
| **Actual** | Windows 10/11 Build 26100, Hyper-V Enabled, WSL 2.7.12.0, Docker Server 29.5.3, Total RAM 63.84 GB, Git 2.55.0 |
| **Result** | `PASS` |
| **Completion Gate** | `GATE-HOST-01 = PASS` |

---

## 2. Verified Host Metrics

```text
OS                 : Windows 10/11 Education (Build 26100)
Hyper-V            : Enabled (Feature Microsoft-Hyper-V-All active)
WSL Version        : WSL 2.7.12.0 (Kernel 6.6.x) [Meets >= 2.1.5 Requirement]
Docker Server      : 29.5.3 (Operational)
Docker Compose     : v2.x (Supports !override syntax)
Total Physical RAM : 63.84 GB (Exceeds >= 32 GB requirement)
Git Version        : 2.55.0.windows.2
```

---

## 3. Gate Assessment

| Gate ID | Condition | Result |
|---|---|---|
| **GATE-HOST-01** | All host readiness checks pass (Hyper-V, WSL2, Docker, RAM, Git) | **PASS** |
