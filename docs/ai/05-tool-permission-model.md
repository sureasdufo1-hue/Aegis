# Tool Permission Model & Execution Boundaries

## 1. Principles of Tool Governance

To protect the host operating system, production sensors, and management plane from abuse or unintended lateral activity, the AI-Orchestrated SOC Copilot enforces a strict **Least-Privilege Tool Execution Model**.

1. **Read-Only by Design**: Investigation tools executed during AI reasoning are strictly read-only. They cannot modify system states, iptables, disk contents, or configuration files.
2. **Schema & Argument Sanitization**: All tool arguments are validated before execution.
3. **Explicit Registration**: The orchestrator can only execute tools explicitly registered in `ToolRegistry`. Dynamically synthesized tool names or arbitrary shell commands are blocked.
4. **Session Call Budget**: A hard limit (default: 6–8 calls per session) prevents infinite reasoning loops, tool spamming, or resource exhaustion.
5. **Audited Invocations**: Every invocation, argument payload, result count, and latency is recorded in `ToolRegistry.audit_log`.

---

## 2. Tool Permission Matrix

| Tool Name | Permission Level | Allowed Operations | Guardrails & Constraints | Error State Behavior |
|---|---|---|---|---|
| **`query_siem_alerts`** | Read-Only | Query OpenSearch Wazuh Indexer (`:9200`) for historical alerts matching an IP or CIDR. | - IPv4/CIDR regex sanitization.<br>- Strictly restricted to HTTP GET / POST search.<br>- Max record limit: 25. | Returns `ToolResult(success=False, error_message=...)` if input is invalid or OpenSearch is offline. |
| **`lookup_threat_intel`** | Read-Only | Query curated Threat Intelligence feeds for IP, domain, or hash reputation. | - Strips leading/trailing whitespace.<br>- Misses return `matched: False`; system explicitly forbids assuming benign status. | Safe empty result returned on unrecognized format. |
| **`inspect_pcap_flow`** | Read-Only | Read and inspect packet flow summaries from approved sample PCAPs (`pcaps/samples/`). | - Resolves paths and verifies containment inside `pcaps/samples`.<br>- Validates against `pcap_manifest.json` SHA-256.<br>- Maximum packet inspection: 100 packets. | Rejects path traversal (`../`) and unauthorized files with explicit security error. |
| **`FirewallRuleAdapter`** | Simulation / Generation | Generate dry-run rule syntax (`nftables` / `iptables`). | - Operates purely in-memory.<br>- Does not invoke `nft` or `iptables` binary.<br>- Strictly controlled by `ActionType` and `Direction`. | Pure function; no OS interaction. |
| **`ActionExecutor`** | Controlled Execution | Simulate execution or create security tickets. | - **Zero live firewall modification without explicit code change and ADR**.<br>- Requires `record.status == APPROVED`.<br>- Requires `record.policy_validation.is_valid == True`. | Fail-closed: refuses execution if not approved or if policy failed. |

---

## 3. Prohibited Tool Classes

The following capabilities are **permanently prohibited** from the AI tool registry without an approved ADR and change control:

```text
[PROHIBITED CAPABILITIES]
├── Raw Bash / PowerShell Command Execution (e.g. subprocess.run(user_input, shell=True))
├── Arbitrary File Write / Delete (e.g. modifying /etc/suricata, /etc/nftables.conf)
├── Raw Socket / Packet Injection (e.g. scapy send(), raw packet crafting)
├── External Internet Web Fetching without domain whitelist
├── Lateral SSH / Telnet / WinRM execution to Lab VMs
└── Autonomous Database schema modification
```

---

## 4. Bounded Call Budget & Rate Limiting

The `ToolRegistry` tracks invocations via an atomic counter:

```python
if self.call_count > self.max_calls:
    err_res = ToolResult(
        success=False,
        tool_name=tool_name,
        data=[],
        error_message=f"Investigation tool call limit exceeded ({self.max_calls}). Bounded execution enforced.",
    )
    self._log_audit(tool_name, arguments, err_res, timestamp)
    return err_res
```

If an LLM enters an infinite reasoning loop or repeatedly calls tools, execution terminates cleanly, returning the bounded error to the orchestrator to preserve token budget and system responsiveness.
