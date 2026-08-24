# AGENTS.md

> **Scope:** Repository-wide operating contract for AI coding agents and automation agents working on the **SOC Detection & Monitoring Lab**.
>
> **Applies to:** Codex, Claude Code, Gemini CLI, AGY, and any other agent that reads, modifies, validates, tests, documents, or automates this repository.

---

## 1. Project Mission

This repository exists to build and prove an **end-to-end SOC detection and investigation portfolio**, not to maximize the number of security tools installed.

The project MUST demonstrate this evidence-backed pipeline:

```text
Attacker
→ Gateway
→ Victim
→ Hyper-V Port Mirroring
→ Sensor
→ Suricata
→ Detection Rule
→ eve.json
→ Wazuh
→ Alert
→ SOC Investigation
→ PCAP / Raw Event / Rule
→ MITRE ATT&CK
→ Verdict
→ Detection Tuning
→ Re-test
→ Evidence
```

The project is complete only when the above flow is **implemented, tested, and supported by objective evidence**.

### Top-level rules

- **MUST:** Verify packet visibility before deploying IDS-dependent work.
- **MUST:** Every `PASS` requires objective test evidence.
- **MUST NOT:** Skip a failed or blocked completion gate.
- **MUST NOT:** Change the approved Architecture Baseline without a documented `DESIGN-ISSUE` and ADR decision.
- **MUST NOT:** Execute attack activity outside the isolated, authorized Lab environment.
- **MUST NOT:** Commit secrets, credentials, private keys, raw sensitive data, or unrestricted large PCAP/log datasets.
- **MUST NOT:** Claim completion for work that has not been directly validated.

---

## 2. Source of Truth

When instructions conflict, use this precedence:

1. `AGENTS.md`
2. Latest approved Implementation Plan
3. Latest approved LLD / Detailed Design
4. Latest approved HLD / Architecture
5. Requirements Definition
6. Approved ADRs
7. Runtime verification records
8. Test and Evidence records
9. `README.md`
10. Other documentation

### ADR exception

A **newer approved ADR** that explicitly changes HLD or LLD decisions takes precedence over the older baseline it replaces.

### Conflict rule

If two sources conflict and no approved ADR resolves the conflict:

```text
Status: BLOCKED
Reason: SOURCE-OF-TRUTH CONFLICT
```

Do not guess which source is correct.

---

## 3. Mandatory Read Before Work

Before changing the repository, the agent MUST read the documents relevant to the requested scope.

### Minimum project context

```text
AGENTS.md
README.md
docs/01-requirements/
docs/02-architecture/
docs/03-design/
docs/04-deployment/
```

### Area-specific context

| Work area | Read before modifying |
|---|---|
| Network / Hyper-V | `infrastructure/hyper-v/`, `infrastructure/network/`, related tests/evidence/ADR |
| Suricata | `suricata/`, related detection docs, tests, evidence, ADR |
| Snort | `snort/`, related PCAP metadata, comparison docs, tests |
| Wazuh | `wazuh/`, `infrastructure/docker/`, integration tests, deployment docs |
| Detection engineering | `suricata/rules/`, `snort/rules/`, `docs/06-detection/`, evidence |
| SOC investigation | `docs/07-investigation/`, `docs/08-incident/`, related EVE/PCAP metadata |
| Troubleshooting | `docs/09-troubleshooting/`, relevant runtime baselines and tests |

**MUST NOT** overwrite an existing configuration before reading its current source, test coverage, and rollback path.

---

## 4. Architecture Baseline

The following architecture is approved and **non-negotiable unless changed by approved change control**.

```text
Deployment Model:
Hybrid

Host:
Windows + Hyper-V

Container Runtime:
Docker Desktop + WSL2

VMs:
soc-attacker
soc-gateway
soc-victim
soc-sensor

Primary IDS:
Suricata 8.0.6

Secondary IDS:
Snort 3.12.2.0

Snort libDAQ:
3.0.27

Primary SIEM:
Wazuh 4.14.7

Primary Capture:
Hyper-V Port Mirroring

Suricata Capture:
AF_PACKET

Offline Validation:
PCAP

Threat Framework:
MITRE ATT&CK 19.2
```

### Approved VM roles

| VM | Role |
|---|---|
| `soc-attacker` | Authorized Lab traffic generation and test activity |
| `soc-gateway` | Routing and security boundary between Attack, Victim, and Management zones |
| `soc-victim` | Authorized isolated target |
| `soc-sensor` | Passive network sensor hosting Suricata, Snort validation tooling, packet capture, and Wazuh Agent |

### Prohibited architecture changes without ADR

The agent MUST NOT independently:

- replace Hyper-V;
- replace Suricata as Primary IDS;
- promote Snort to Primary IDS;
- replace Wazuh as SIEM;
- move the sensor into Docker;
- add Kubernetes, HA clusters, service mesh, Kafka, enterprise PKI, distributed Wazuh, multi-cloud, or other unrelated infrastructure;
- merge Attack and Management networks;
- change the project from passive IDS-first operation to inline IPS operation.

---

## 5. Network Baseline

### Zones

```text
ZONE-MGMT
10.77.10.0/24

ZONE-ATTACK
10.77.20.0/24

ZONE-VICTIM
10.77.30.0/24
```

### Fixed addressing baseline

| System | Address |
|---|---|
| Windows Host MGMT | `10.77.10.10` |
| Gateway MGMT | `10.77.10.1` |
| Gateway ATTACK | `10.77.20.1` |
| Gateway VICTIM | `10.77.30.1` |
| Attacker | `10.77.20.20` |
| Victim | `10.77.30.20` |
| Sensor MGMT | `10.77.10.20` |
| Sensor Monitor | **NO L3 IP** |

### Hyper-V vSwitch baseline

```text
soc-vsw-mgmt
soc-vsw-attack
soc-vsw-victim
```

### Port mirroring baseline

```text
Source:
soc-victim / nic-victim

Destination:
soc-sensor / nic-monitor
```

The agent MUST NOT change VM names, switch names, CIDRs, or fixed IP assignments without change control.

---

## 6. Technology Baseline

| Technology | Baseline |
|---|---|
| Suricata | `8.0.6` |
| Snort | `3.12.2.0` |
| libDAQ | `3.0.27` |
| Wazuh | `4.14.7` |
| MITRE ATT&CK | `19.2` |
| Capture | Hyper-V Port Mirroring + AF_PACKET |
| Packet analysis | `tcpdump`, `tshark`, Wireshark |
| SIEM mode | Docker single-node |
| Offline validation | PCAP |

### Version policy

- **MUST** use pinned versions where the baseline defines a version.
- **MUST NOT** replace pinned versions with `latest`.
- **MUST NOT** automatically upgrade because a newer stable version exists.
- **MUST** create a `VERSION-DRIFT-xxx` record when runtime or official stable versions differ from the baseline.

Template:

```text
VERSION-DRIFT-xxx

Baseline Version:
Detected Version:
Current Official Stable:
Compatibility Impact:
Security Impact:
Decision:
KEEP_BASELINE / UPGRADE_PROPOSAL
ADR Required:
YES / NO
```

---

## 7. Critical Implementation Order

# PACKET VISIBILITY BEFORE IDS

This order is mandatory:

```text
Connectivity
↓
Routing
↓
Firewall
↓
Port Mirroring
↓
Sensor tcpdump
↓
Suricata
↓
Detection
↓
EVE
↓
Wazuh
```

The agent MUST NOT invert this sequence by building Wazuh or IDS-dependent integration before packet visibility is validated.

### Hard dependency

If the sensor cannot observe the target traffic with `tcpdump`, all downstream IDS work is blocked.

---

## 8. Phase and Gate Policy

Approved phase order:

```text
Phase 0  Host Readiness
Phase 1  Repository Baseline
Phase 2  Hyper-V Virtual Network
Phase 3  VM Provisioning
Phase 4  Network Address Configuration
Phase 5  Gateway Routing
Phase 6  Gateway Firewall
Phase 7  Port Mirroring
Phase 8  Packet Visibility Validation
Phase 9  Suricata Deployment
Phase 10 Suricata Configuration
Phase 11 Detection Validation
Phase 12 PCAP Evidence
Phase 13 Snort Deployment
Phase 14 Snort Offline Validation
Phase 15 Wazuh Host Readiness
Phase 16 Wazuh Deployment
Phase 17 Sensor Wazuh Agent
Phase 18 Victim Wazuh Agent
Phase 19 Suricata-Wazuh Integration
Phase 20 Dashboard Validation
Phase 21 Attack Scenario
Phase 22 SOC Investigation
Phase 23 MITRE ATT&CK Mapping
Phase 24 False Positive Analysis
Phase 25 Detection Tuning
Phase 26 Re-test
Phase 27 End-to-End Validation
Phase 28 Evidence
Phase 29 Portfolio Documentation
Phase 30 Final Release Gate
```

### Gate result vocabulary

Only the following values are permitted:

```text
PASS
FAIL
BLOCKED
```

Do not use:

```text
Probably PASS
Mostly done
Should work
Looks okay
Assumed PASS
Likely successful
```

### Critical gates

```text
GATE-HOST-01
GATE-NET-01
GATE-FW-01
GATE-MIRROR-01
GATE-SURI-01
GATE-DETECT-01
GATE-PCAP-01
GATE-SNORT-01
GATE-WAZUH-01
GATE-SIEM-01
GATE-ANALYSIS-01
GATE-TUNE-01
GATE-E2E-01
GATE-PORTFOLIO-01
```

### GATE-NET-01 rule

For traffic:

```text
10.77.20.20
→
10.77.30.20
```

the same traffic MUST be visible on the sensor monitoring interface with `tcpdump`.

If not:

```text
GATE-NET-01 = FAIL
```

and IDS-dependent work MUST NOT continue.

---

## 9. Runtime Verification

Values marked `[RUNTIME VERIFICATION REQUIRED]` MUST be discovered, not guessed.

Typical runtime values include:

```text
Linux interface names
MAC addresses
Windows build
WSL version
Docker binding behavior
Service status
Container health
```

Required process:

```text
Observe
→ Command
→ Actual Value
→ Record
→ Test
→ Evidence
```

Example:

```text
Expected:
eth1

Actual:
ens224

Decision:
Use ens224

Evidence:
EV-RUNTIME-xxx
```

### Never invent runtime facts

The agent MUST NOT invent:

- Linux interface names;
- MAC addresses;
- container health;
- running service state;
- installed versions;
- dashboard status;
- test results;
- alerts;
- PCAP contents;
- Git commits;
- external connectivity.

If not verified, use:

```text
NOT VERIFIED
```

or:

```text
BLOCKED
```

---

## 10. Security Lab Scope

All offensive or suspicious test activity is restricted to:

```text
10.77.20.0/24
10.77.30.0/24
Approved Offline PCAP
```

The agent MUST NOT target public IPs or systems outside the explicitly authorized Lab.

### Prohibited activity

Without explicit authorization for a lawful target, the agent MUST NOT perform:

```text
Public IP scanning
Internet target exploitation
External brute force
Credential stuffing
Real malware execution
Destructive payload execution
Persistence outside the Lab
External lateral movement
```

### Malware policy

MVP testing SHOULD use:

```text
Approved PCAP
Sanitized sample
Synthetic traffic
Harmless marker
```

Actual malware execution is out of scope unless separately approved and safely isolated.

---

## 11. Network Security Rules

### Default posture

```text
DEFAULT DENY
```

### Allowed

```text
Attack → Victim
Authorized Lab test traffic

Victim → MGMT
Wazuh 1514/TCP and 1515/TCP only

Sensor → Wazuh
1514/TCP and 1515/TCP

Analyst → Dashboard
HTTPS
```

### Denied

```text
Attack → MGMT
ANY
```

### Firewall discipline

- **MUST NOT** leave the firewall in broad `ACCEPT` mode as a troubleshooting shortcut.
- **MUST** validate nftables syntax before reload.
- **MUST** retain rollback configuration before policy changes.

### Sensor monitoring NIC

```text
L3 IP:
NONE

Role:
Packet Capture Only
```

The agent MUST NOT add an IP address to the monitoring NIC for convenience.

---

## 12. Suricata Rules

### Operating contract

```text
Role:
Primary IDS

Mode:
Passive

Capture:
AF_PACKET

HOME_NET:
10.77.30.0/24

EXTERNAL_NET:
!$HOME_NET
```

### Primary event source

```text
/var/log/suricata/eve.json
```

### Rule paths

Managed runtime:

```text
/var/lib/suricata/rules/suricata.rules
```

Custom runtime:

```text
/etc/suricata/rules/
```

Repository source:

```text
suricata/rules/
```

Repository source and runtime deployment path MUST remain conceptually separate.

### Suricata SID allocation

```text
9000000–9099999
```

Subranges:

```text
9000000–9009999 Network
9010000–9019999 Web
9020000–9029999 Authentication
9030000–9039999 Lab
9090000–9099999 Reserved
```

Before adding a rule:

- **MUST** check for duplicate SID;
- **MUST** increment `rev` when behavior changes;
- **MUST** validate configuration before restart;
- **MUST** run targeted detection tests;
- **MUST** update evidence and documentation when the rule is portfolio-relevant.

---

## 13. Snort Rules

### Operating contract

Snort is NOT the primary real-time IDS.

```text
Role:
Secondary Validation
Offline PCAP Analysis
Rule Comparison
```

Primary workflow:

```text
PCAP
→ Snort
→ Alert
→ Suricata Comparison
```

### Snort SID allocation

```text
9100000–9199999
```

The agent MUST keep Snort custom SIDs separate from Suricata custom SID allocation.

### Validation

Snort changes SHOULD be validated with:

```text
snort -T
```

and, where relevant, against the same PCAP used for Suricata comparison.

---

## 14. Wazuh Rules

### Operating contract

```text
Version:
4.14.7

Deployment:
Docker Single-node
```

Expected components:

```text
soc-wazuh-manager
soc-wazuh-indexer
soc-wazuh-dashboard
```

Expected network:

```text
soc-wazuh-net
```

### Exposure policy

Externally exposed for the approved management path:

```text
1514/TCP
1515/TCP
443/TCP
```

Localhost only:

```text
55000/TCP
9200/TCP
```

The agent MUST NOT expose Dashboard, Indexer, or Manager API to the Attack network.

### Credential policy

Vendor default credentials MUST NOT remain in the final state.

The agent MUST NOT commit credentials to Git.

### Suricata integration

Expected pipeline:

```text
/var/log/suricata/eve.json
→ Wazuh Agent
→ Manager
→ Indexer
→ Dashboard
```

The agent MUST NOT claim `Wazuh Integration = PASS` unless the same Suricata event is traceable through the complete pipeline.

---

## 15. Version Policy

- Pin approved versions.
- Do not use floating `latest` tags.
- Do not perform silent upgrades.
- Record version drift.
- Treat version changes that affect architecture, ports, schemas, config format, or behavior as change-control items.
- Re-run relevant validation after any approved version change.

---

## 16. Secrets and Sensitive Data

### MUST NOT commit

```text
.env
*.key
*.pem
*.p12
*.pfx
credentials
password files
token files
private certificates
VM disks
raw sensitive logs
```

### Repository-safe pattern

```text
.env.example
```

MAY be committed when it contains placeholders only.

### Raw data policy

Do not commit by default:

```text
full eve.json
large PCAP collections
Wazuh index data
runtime logs
raw credentials
VHD/VHDX
```

Safe repository artifacts MAY include:

```text
sanitized event samples
small approved PCAP samples
PCAP metadata
SHA-256 hashes
custom rules
non-secret config examples
investigation reports
screenshots
evidence metadata
```

### Pre-commit security check

Before commit:

```bash
git status
git diff
git diff --cached
```

Review for:

```text
password
secret
token
api_key
private_key
credential
```

If a suspected secret is found, do not commit it.

---

## 17. Testing Rules

The agent MUST test the narrowest affected layer first.

Examples:

```text
Network change
→ Network test

Rule change
→ suricata -T
→ Target traffic
→ EVE verification

Wazuh change
→ docker compose config
→ Container health
→ Agent/integration test

Detection tuning
→ Normal traffic
→ Attack traffic
→ Before/after comparison
```

### Configuration validation before restart

Where validation exists, MUST run it before restart.

```text
Suricata:
suricata -T

Snort:
snort -T

Docker Compose:
docker compose config

nftables:
nft -c -f
```

Do not restart a service with known-invalid configuration.

### Evidence-required PASS

A `PASS` requires at least one objective artifact such as:

```text
command output
service status
packet capture
raw log
JSON event
test output
screenshot
PCAP
hash
git diff
git commit
dashboard result
```

No evidence means no `PASS`.

---

## 18. Evidence Rules

### Evidence naming

```text
EV-HOST-xxx
EV-NET-xxx
EV-MIRROR-xxx
EV-SURI-xxx
EV-PCAP-xxx
EV-SNORT-xxx
EV-WAZUH-xxx
EV-ANALYSIS-xxx
EV-TUNE-xxx
EV-E2E-xxx
```

### Suggested structure

```text
evidence/
└── EV-SURI-003/
    ├── metadata.md
    ├── screenshot.png
    ├── event.json
    ├── rule.rules
    └── pcap-reference.md
```

### Evidence metadata

At minimum:

```text
Evidence ID
Requirement
Design
Implementation Phase
Test
Scenario
Timestamp
Component
Expected
Actual
Result
PCAP
Rule
Incident
ATT&CK
Git Commit
```

### PCAP integrity

Preserved PCAPs MUST have a SHA-256 recorded.

```text
PCAP ID
Scenario ID
Timestamp
Source
Destination
SHA256
Related Alert
Related Incident
```

---

## 19. SOC Investigation Standard

Each alert investigation MUST follow, at minimum:

```text
Timestamp
↓
Source IP
↓
Destination IP
↓
Protocol / Port
↓
Signature
↓
SID
↓
Raw EVE
↓
PCAP
↓
Detection Rule
↓
Related Events
↓
MITRE ATT&CK
↓
Verdict
↓
Response
```

### Allowed verdicts

```text
TRUE_POSITIVE
FALSE_POSITIVE
BENIGN
UNRESOLVED
```

A verdict MUST include reasoning and linked evidence.

---

## 20. MITRE ATT&CK Policy

Do not force an ATT&CK mapping onto every event.

Mapping MUST be based on observed behavior that actually matches the official technique definition.

Baseline examples:

```text
Connectivity ping
→ Mapping may be unnecessary

Port / service scan
→ T1046

Password guessing
→ T1110.001
```

If uncertain:

```text
ATT&CK Mapping:
NOT VERIFIED
```

Do not invent technique IDs.

---

## 21. Detection Tuning

Detection tuning MUST be treated as an engineering validation loop, not a text edit.

Required sequence:

```text
Baseline Rule
↓
False Positive
↓
Raw Event
↓
PCAP
↓
Root Cause
↓
Rule Revision
↓
Config Validation
↓
Normal Traffic Re-test
↓
Attack Traffic Re-test
↓
Before/After Comparison
↓
Git Commit
↓
Evidence
```

### Tuning PASS criteria

Both conditions MUST hold:

```text
Normal Traffic:
False Positive reduced or removed

Attack Traffic:
Detection retained
```

If only one condition passes:

```text
GATE-TUNE-01 = FAIL
```

---

## 22. Git Rules

### Branches

Preferred lightweight structure:

```text
main
feature/network
feature/suricata
feature/snort
feature/wazuh
feature/detection
feature/evidence
```

Respect an existing simpler repository strategy. Do not introduce unnecessary Git-flow complexity.

### Commit convention

```text
feat(network):
feat(suricata):
feat(snort):
feat(wazuh):
feat(detection):
fix:
test:
docs:
chore:
```

### Commit scope

One commit SHOULD represent one coherent purpose.

Good:

```text
feat(network): configure victim port mirroring
```

Bad:

```text
fix everything
```

### Git safety

The agent MUST NOT use destructive Git operations casually:

```text
git reset --hard
git clean -fd
```

If unavoidable, clearly mark:

```text
[DESTRUCTIVE]
```

and verify impact first.

---

## 23. Documentation Rules

Documentation is part of the Definition of Done.

Successful implementation without these supporting artifacts is incomplete where applicable:

```text
Test
Evidence
Documentation
```

Repository responsibilities:

```text
docs/01-requirements/
Requirements

docs/02-architecture/
HLD / ADR

docs/03-design/
LLD

docs/04-deployment/
Implementation

docs/05-testing/
Tests

docs/06-detection/
Detection analysis

docs/07-investigation/
SOC investigations

docs/08-incident/
Incident reports

docs/09-troubleshooting/
Troubleshooting records
```

README SHOULD emphasize the SOC workflow and evidence chain, not just installation commands.

---

## 24. Troubleshooting

Do not change multiple unrelated settings at once.

Required troubleshooting discipline:

```text
Symptom
↓
Layer
↓
Observed Value
↓
Expected Value
↓
Single Change
↓
Re-test
↓
Evidence
```

### Troubleshooting IDs

```text
TRB-001
TRB-002
...
```

Record:

```text
Phase
Symptom
Environment
Expected
Actual
Root Cause
Resolution
Re-test
Evidence
```

### Key troubleshooting trees

#### No Suricata alert

```text
Traffic exists?
↓
Victim receives?
↓
Mirror configured?
↓
Sensor tcpdump?
↓
Suricata service?
↓
Correct monitor NIC?
↓
AF_PACKET?
↓
Rule loaded?
↓
Rule matches?
↓
EVE enabled?
```

#### Suricata alert exists but Wazuh event does not

```text
eve.json?
↓
Wazuh Agent?
↓
localfile?
↓
1514 reachable?
↓
Agent Active?
↓
Manager?
↓
Indexer?
↓
Dashboard query?
```

---

## 25. Change Management

Do not directly change the architecture or design baseline when implementation exposes a problem.

Create:

```text
DESIGN-ISSUE-xxx
```

with:

```text
Original Design
Observed Problem
Root Cause
Proposed Change
Requirement Impact
Security Impact
Test Impact
Migration Impact
```

If architecture-level impact exists, escalate to:

```text
ADR-CANDIDATE-xxx
```

Only an approved ADR may redefine the baseline.

---

## 26. Automation Rules

Initial implementation prioritizes manual observability.

```text
Manual Build
→ Manual Validation
→ Stable Baseline
→ Automation
```

Automation MUST NOT obscure network visibility or failure diagnosis.

### Approved automation candidates after baseline validation

```text
vSwitch creation
Port Mirroring
Health checks
Rule deployment
Rule validation
PCAP hashing
Evidence metadata generation
Wazuh health checks
```

Automation MUST preserve the same gates and evidence requirements as manual execution.

---

## 27. Agent Autonomy

The agent MAY perform without additional approval:

```text
Create files required by approved design
Add tests
Add documentation
Run safe configuration validation
Create evidence metadata
Fix lint/syntax issues
Perform non-destructive troubleshooting
Update runtime verification records
```

The agent MUST NOT independently:

```text
Change architecture
Change network CIDRs
Change VM topology
Replace IDS
Replace SIEM
Upgrade pinned versions
Relax firewall posture
Change secret-handling policy
Skip P0 gates
Perform destructive cleanup
Expose management services to the Attack network
Assign an IP to the sensor monitoring NIC
```

### Overengineering prohibition

Do not introduce without explicit requirement/ADR:

```text
Kubernetes
HA cluster
Service mesh
Kafka
Enterprise PKI
Complex SOAR
Distributed Wazuh
Cloud infrastructure
Terraform multi-cloud
```

### Priority discipline

```text
P0:
Network
Traffic
Suricata
Snort validation
Rules
PCAP
Analysis
Evidence

P1:
Wazuh
Dashboard
ATT&CK
False Positive Analysis
Tuning
Incident Report

P2:
Zeek
Sigma
YARA
Threat Intelligence
Detection-as-Code
Automation
```

Do not spend time on P2 while required P0/P1 gates remain incomplete.

---

## 28. Status Reporting

Every completed work segment or phase MUST end with a factual status report.

Use:

```markdown
## Phase Result

Phase:
Status: PASS / FAIL / BLOCKED

### Completed
- ...

### Runtime Values
- ...

### Tests
- ...

### Evidence
- ...

### Issues
- ...

### Changes
- ...

### Git
Branch:
Commit:
SHA:

### Gate
Gate:
Result:

### Next Phase
...
```

### No fake progress

Do not write:

```text
구축 완료
```

if only a package or service was installed.

Do not write:

```text
Wazuh Integration 완료
```

unless:

```text
eve.json
→ Agent
→ Manager
→ Indexer
→ Dashboard
```

was actually verified.

### Blocked reporting

```text
Status:
BLOCKED

Blocker:
...

Verified Cause:
...

Required Action:
...

Affected Gate:
...

Evidence:
...
```

---

## 29. Definition of Done

Project completion requires the following chain to be backed by real evidence:

```text
Attack
→ Traffic
→ Victim
→ Mirrored Packet
→ Suricata
→ Rule Match
→ EVE
→ Wazuh
→ Alert
→ Investigation
→ PCAP
→ ATT&CK
→ Verdict
→ False Positive Analysis
→ Rule Tuning
→ Re-test
→ Evidence
→ Portfolio Documentation
```

A running container, installed package, valid configuration, or visible dashboard alone is NOT sufficient.

---

## 30. Final Release Conditions

All required categories MUST pass:

```text
Host
Network
Routing
Firewall
Mirror
Packet Visibility
Suricata
Detection
PCAP
Snort
Wazuh
SIEM Integration
Attack Scenario
SOC Investigation
ATT&CK
False Positive
Tuning
Re-test
E2E
Evidence
Documentation
Secret Review
```

Only then may the agent declare:

```text
IMPLEMENTATION COMPLETE
```

Otherwise use:

```text
IMPLEMENTATION IN PROGRESS
```

or:

```text
IMPLEMENTATION BLOCKED
```

---

# Final Operating Principle

The priority of this repository is not:

```text
more tools
more automation
more code
```

The priority is:

```text
observable traffic
→ reproducible detection
→ defensible analysis
→ verified verdict
→ measured tuning
→ traceable evidence
```

**If a result cannot be verified, do not present it as fact.  
If a gate fails, fix or block it before moving forward.  
If a change alters the approved design, document and approve it before implementation.**
