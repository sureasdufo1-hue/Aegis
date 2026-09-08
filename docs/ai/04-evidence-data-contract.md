# Evidence & AI Schemas Data Contract Specification

## 1. Scope and Design Philosophy

This document defines the formal data contracts between the SOC detection pipeline, the AI investigation orchestrator, the policy engine, and the human-in-the-loop (HITL) approval system.

### Principles:
1. **Schema-Enforced Typing**: All contracts are defined using Pydantic v2 models with runtime validation.
2. **Provenance & Trust Levels**: Every piece of evidence carries an explicit trust level reflecting its point of origin.
3. **Epistemic Separation**: Observed facts, inferred hypotheses, and unknowns are stored in distinct top-level fields.

---

## 2. Core Evidence Schemas (`analyzer/ai/schemas/evidence.py`)

### 2.1 Trust Level Taxonomy

```python
class TrustLevel(StrEnum):
    RAW_CAPTURE = "RAW_CAPTURE"        # Byte-level PCAP or raw frame
    SENSOR_LOCAL = "SENSOR_LOCAL"      # Raw daemon log (eve.json, alert_json.txt)
    NORMALIZED = "NORMALIZED"          # Standardized NormalizedAlert
    CORRELATED = "CORRELATED"          # Multi-stage correlated Incident
    ENRICHED = "ENRICHED"              # Threat intelligence or reverse DNS lookup
    UNTRUSTED = "UNTRUSTED"            # Unsanitized payload or external header
```

### 2.2 Security Evidence Data Contract

```json
{
  "evidence_id": "EV-INC-01",
  "timestamp": "2026-09-07T11:11:23.036466Z",
  "source": {
    "system": "suricata",
    "index_or_path": "eve.json",
    "document_or_flow_id": "flow-2"
  },
  "network": {
    "src_ip": "10.77.20.20",
    "src_port": 49153,
    "dst_ip": "10.77.30.20",
    "dst_port": 3000,
    "protocol": "TCP"
  },
  "alert": {
    "signature": "SOC-ATTACK: Web SQL Injection - UNION SELECT Pattern Detected",
    "sid": 9010001,
    "category": "Web Application Attack",
    "severity": "HIGH",
    "mitre_technique": "T1190"
  },
  "trust_level": "NORMALIZED",
  "observed_facts": {
    "flow_id": 18293712,
    "http_uri": "/rest/products/search?q=apple'+UNION+SELECT+1,2,3,database()--",
    "mitre_technique": "T1190"
  }
}
```

---

## 3. Incident Analysis Schemas (`analyzer/ai/schemas/analysis.py`)

### 3.1 AI Incident Analysis Contract

| Field Name | Type | Description |
|---|---|---|
| `incident_id` | `str` | Reference ID of the investigated incident |
| `analysis_status` | `AnalysisStatus` | `TRIAGED` / `NEEDS_MORE_DATA` / `ESCALATED` / `SUPPRESSED` |
| `summary` | `str` | Concise executive summary of the triage verdict |
| `observed_facts` | `list[str]` | Objective, verifiable facts directly extracted from alerts/evidence |
| `hypotheses` | `list[str]` | Plausible attacker motives, next steps, or potential lateral movement paths |
| `unknowns` | `list[str]` | Missing visibility, unanswered forensic questions, or unverified endpoints |
| `risk_assessment` | `RiskAssessment` | Structured severity, confidence score (`0.0 - 1.0`), and impact scope |
| `attack_mapping` | `list[AttackTechniqueMapping]` | MITRE ATT&CK techniques with tactic, confidence, and evidence cross-references |
| `evidence_refs` | `list[str]` | List of `evidence_id` objects supporting the findings |
| `knowledge_refs` | `list[KnowledgeCitation]` | Retrieved RAG playbooks and documents with similarity score |
| `recommended_investigations` | `list[str]` | Suggested secondary investigative steps (e.g. host disk, auth logs) |
| `recommended_actions` | `list[str]` | Proposed containment recommendations (e.g. `BLOCK_IP 10.77.20.20`) |
| `model_info` | `dict[str, Any]` | Provider name, model identifier, latency in ms, and tool call count |
| `generated_at` | `datetime` | UTC timestamp of generation |

---

## 4. Action & Approval Contracts (`analyzer/ai/schemas/actions.py`)

### 4.1 Proposed Action Schema

```json
{
  "proposal_id": "PROP-87727348-01",
  "incident_id": "INC-10.77.20.20-1787727348",
  "action_type": "BLOCK_IP",
  "target": "10.77.20.20",
  "direction": "INBOUND",
  "duration_minutes": 60,
  "rule_syntax_preview": "nft add element inet filter blacklist { 10.77.20.20 }",
  "rationale": "Block attacker IP 10.77.20.20 engaged in multi-stage web exploit and reverse shell"
}
```

### 4.2 Policy Validation Result Schema

```json
{
  "target": "10.77.20.20",
  "is_valid": true,
  "verdict": "ALLOWED",
  "violations": [],
  "protected_asset_details": null,
  "validated_at": "2026-09-07T11:34:37.150000Z"
}
```

### 4.3 Action Approval Record Schema (Persistent HITL Object)

```json
{
  "approval_id": "APR-87727348-027",
  "incident_id": "INC-10.77.20.20-1787727348",
  "proposed_action": {
    "proposal_id": "PROP-87727348-01",
    "incident_id": "INC-10.77.20.20-1787727348",
    "action_type": "BLOCK_IP",
    "target": "10.77.20.20",
    "direction": "INBOUND",
    "duration_minutes": 60,
    "rule_syntax_preview": "nft add element inet filter blacklist { 10.77.20.20 }",
    "rationale": "Block attacker IP 10.77.20.20"
  },
  "policy_validation": {
    "target": "10.77.20.20",
    "is_valid": true,
    "verdict": "ALLOWED",
    "violations": []
  },
  "status": "EXECUTED",
  "execution_mode": "DRY_RUN",
  "created_at": "2026-09-07T11:34:30.000000Z",
  "expires_at": "2026-09-07T12:34:30.000000Z",
  "reviewed_by": "lead-analyst",
  "reviewed_at": "2026-09-07T11:34:37.155000Z",
  "review_notes": "Verified multi-stage exploit. Approving dry-run isolation.",
  "execution_output": "[DRY-RUN EXECUTION SIMULATION] 2026-09-07T11:34:37.157555+00:00\nAction Type: BLOCK_IP...",
  "executed_at": "2026-09-07T11:34:37.158000Z"
}
```
