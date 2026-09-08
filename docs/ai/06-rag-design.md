# RAG Knowledge Grounding & Playbook Retrieval Design

## 1. Overview & Objective

To prevent LLM hallucination and ensure that triage recommendations adhere to approved SOC standard operating procedures (SOP), the orchestrator incorporates a **Retrieval-Augmented Generation (RAG)** engine.

The RAG engine indexes incident playbooks and detection engineering rules. When an incident is analyzed, relevant playbook guidance is retrieved and injected into the prompt context along with strict citation metadata.

---

## 2. Knowledge Corpus & Provenance

The knowledge store indexes the following authoritative operational documents:

| Document Path | Scope & Focus | Keywords & Signatures |
|---|---|---|
| `playbooks/01_port_scan_investigation.md` | Port scan, reconnaissance triage, Nmap flags | `SCAN`, `RECON`, `NULL`, `XMAS`, `FIN`, `T1046` |
| `playbooks/02_ssh_brute_force_investigation.md` | SSH brute force, credential guessing | `SSH`, `BRUTE FORCE`, `AUTH`, `T1110` |
| `playbooks/03_web_attack_investigation.md` | SQLi, XSS, Path Traversal, Log4j | `SQL INJECTION`, `UNION SELECT`, `XSS`, `T1190` |
| `playbooks/04_malware_c2_investigation.md` | Reverse shells, C2 beacons, interactive shells | `REVERSE SHELL`, `METERPRETER`, `BEACON`, `T1059` |
| `playbooks/05_containment_procedures.md` | Host isolation, IP blocking, rule tuning | `CONTAINMENT`, `ISOLATE`, `BLOCK`, `QUARANTINE` |
| `docs/06-detection/README.md` | Custom Suricata/Snort rule definitions & SIDs | `9000001`, `9010001`, `9020001`, `9030010` |

### Integrity Tracking
Each source document is hashed using SHA-256 upon ingestion:
```python
file_sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
```
This guarantees that chunk provenance can be audited back to an exact file revision in Git.

---

## 3. Chunking & Indexing Pipeline

1. **Document Loading**: Scans `playbooks/` and `docs/06-detection/`.
2. **Section-Based Splitting**: Markdown documents are split along section headers (`## `). This preserves logical coherence:
   - Summary
   - Identification & Signatures
   - Verification Steps
   - Containment & Remediation Actions
3. **Keyword Indexing**: Extracts tokens of length ≥ 3 characters to form an inverted token set for fast overlap evaluation.

---

## 4. Retrieval & Scoring Algorithm

The `KnowledgeStore` employs a normalized token overlap similarity metric:

$$\text{Score}(Q, C) = \frac{|W_Q \cap W_C|}{|W_Q|}$$

Where:
- $W_Q$ is the set of alphanumeric keyword tokens in the query (composed of incident signatures and attack stages).
- $W_C$ is the keyword token set of the candidate chunk $C$.

The top $K$ chunks (default: $K=2$) are returned, sorted descending by relevance score.

### Incident Signature Resolution
The `KnowledgeRetriever.retrieve_for_incident(...)` method synthesizes a targeted search query combining:
1. All alert signatures associated with the correlated incident.
2. The identified attack stages (e.g., `1. Reconnaissance`, `3. Command & Control / Execution`).

---

## 5. Grounding Prompt Assembly & Token Budget

To ensure the combined prompt does not exceed the model's 8,192 context budget, RAG chunks are truncated to 1,200 characters each:

```text
[RAG KNOWLEDGE PLAYBOOK REFERENCES]
--- Reference 1 ---
Title: C2 & Malware Incident Investigation Playbook
Chunk ID: 04_malware_c2_investigation-sec2
Relevance Score: 0.75
Content:
## Containment Procedures
1. Isolate the target host from the internal network while maintaining SIEM visibility...
```

The LLM is explicitly instructed to cite the document title and chunk ID in its structured analysis output.
