# Evidence Record: EV-REPO-001

## 1. Metadata Summary

| Field | Value |
|---|---|
| **Evidence ID** | `EV-REPO-001` |
| **Requirement** | `REQ-REPO-01` (Repository Baseline & Standard Structure) |
| **Design Reference** | SOC Detection & Monitoring Lab Implementation Plan v1.0 (Phase 1) / LLD v1.0 |
| **Implementation Phase** | Phase 1 (Repository Baseline) |
| **Test** | Directory Tree Verification, `.gitignore` Rule Verification, `.env.example` Baseline Check, Pytest Suite Execution |
| **Scenario** | Repository Baseline Initialization |
| **Timestamp** | `2026-08-24T15:43:00+09:00` |
| **Component** | Repository Root / Git & Environment Configuration |
| **Expected** | 27 standard directories created, `.gitignore` protecting secrets/logs/raw pcaps, `.env.example` created with safe placeholders, all tests PASS |
| **Actual** | All 27 directories created with tracking, `.gitignore` active, `.env.example` in place, 10/10 pytest unit tests PASS |
| **Result** | `PASS` |
| **Git Commit** | `9d1ad7cf6a04d75149ea27d83b2d4b614873cb90` |
| **Completion Gate** | `GATE-REPO-01 = PASS` |

---

## 2. Directory Structure Verification

The following standard repository structure was initialized and verified:

```text
Suricata-Snort-SOC-Lab/
├── .env.example                  # Environment template with safe placeholders
├── .gitignore                    # Pinned security ignore rules (no keys, no secrets, no raw pcaps)
├── AGENTS.md                     # Agent operating contract & source of truth
├── README.md                     # Top-level portfolio documentation
├── pyproject.toml                # Build & pytest configuration (pythonpath configured)
├── requirements.txt              # Pinned Python dependencies
├── docs/                         # Requirements, Architecture, Design, Deployment docs
│   ├── 01-requirements/
│   ├── 02-architecture/
│   ├── 03-design/
│   ├── 04-deployment/
│   ├── 05-testing/
│   ├── 06-detection/comparisons/
│   ├── 07-investigation/
│   ├── 08-incident/
│   └── 09-troubleshooting/
├── infrastructure/               # Infrastructure-as-code & network scripts
│   ├── hyper-v/                  # Hyper-V switch & port mirroring scripts
│   ├── network/                  # Gateway nftables & sensor netplan
│   └── docker/                   # Wazuh docker compose
├── suricata/                     # Suricata IDS configurations, rules, and scripts
│   ├── config/
│   ├── rules/
│   └── scripts/
├── snort/                        # Snort 3 secondary IDS configs & rules
│   ├── config/
│   ├── rules/
│   └── scripts/
├── wazuh/                        # Wazuh SIEM rules and docker configs
│   ├── config/
│   ├── docker/
│   └── rules/
├── attack-lab/                   # Attack simulation scripts and scenarios
│   ├── scenarios/
│   └── scripts/
├── pcaps/                        # PCAP storage & metadata
│   ├── samples/
│   └── metadata/
├── analyzer/                     # Python real-time parser & correlation engine
├── dashboard/                    # SOC web console
├── evidence/                     # Evidence records per gate
│   └── EV-REPO-001/
│       └── metadata.md
└── tests/                        # Automated unit & integration tests
```

---

## 3. Security & Ignore Rule Checklist

- [x] `.env` excluded from version control
- [x] Private keys (`*.key`, `*.pem`, `*.p12`, `*.pfx`) excluded
- [x] Credentials and secrets directories excluded
- [x] Raw logs (`logs/`, `*.log`) excluded (except `.gitkeep`)
- [x] Large PCAP dumps (`*.pcap`, `*.pcapng`) excluded (except explicit samples)
- [x] Virtual machine disks (`*.vhdx`, `*.vhd`, `*.vmdk`) excluded

---

## 4. Test Execution Output

```text
============================= test session starts =============================
platform win32 -- Python 3.13.14, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\user\Documents\ChatGPT\Suricata-Snort-SOC-Lab
configfile: pyproject.toml
testpaths: tests
plugins: anyio-4.14.2, asyncio-1.4.0
collected 10 items

tests\test_correlation.py .                                              [ 10%]
tests\test_dashboard_api.py ....                                         [ 50%]
tests\test_parsers.py ..                                                 [ 70%]
tests\test_threat_intel.py ...                                           [100%]

======================== 10 passed, 1 warning in 0.59s ========================
```

---

## 5. Gate Assessment

| Gate ID | Condition | Status |
|---|---|---|
| **GATE-REPO-01** | Repository structure, `.gitignore`, `.env.example`, and baseline tests verified | **PASS** |
