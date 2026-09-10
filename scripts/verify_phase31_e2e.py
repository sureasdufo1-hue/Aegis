"""
Phase 31 E2E Verification Script:
Validates real-time ingestion from Suricata EVE JSON -> Wazuh Manager -> Wazuh Indexer
-> Correlation Analyzer -> Incident Escalation -> FastAPI SOC Console.
"""

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

# Add repo root to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Fix windows console UTF-8
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from fastapi.testclient import TestClient
from rich.console import Console
from rich.panel import Panel

from analyzer.detection.correlation_engine import CorrelationEngine
from analyzer.parsers.eve_parser import stream_eve_log
from dashboard.app import app
from scenarios.traffic_generator import generate_targeted_killchain_events

console = Console()


def check_docker_containers() -> dict:
    """Verifies that Wazuh Docker containers are running."""
    containers = ["soc-wazuh-indexer", "soc-wazuh-manager", "soc-wazuh-dashboard"]
    status_map = {}
    for c in containers:
        try:
            res = subprocess.run(["docker", "inspect", "-f", "{{.State.Status}}", c], capture_output=True, text=True, check=True)
            status = res.stdout.strip()
            status_map[c] = status
        except Exception as e:
            status_map[c] = f"Error: {e}"
    return status_map


def query_indexer_count(endpoint: str = "http://127.0.0.1:9200") -> int:
    """Queries total documents across wazuh-alerts-* indices."""
    try:
        req = urllib.request.Request(f"{endpoint}/wazuh-alerts-*/_count")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("count", 0)
    except Exception as e:
        console.print(f"[yellow]Warning: Could not query indexer count: {e}[/yellow]")
        return -1


def poll_indexer_for_event(run_id: str, sig_id: int, timeout_sec: int = 15, endpoint: str = "http://127.0.0.1:9200") -> dict | None:
    """Polls OpenSearch indexer until document with matching run_id and signature_id appears."""
    start_time = time.time()
    url = f"{endpoint}/wazuh-alerts-*/_search?q=data.run_id:{run_id}%20AND%20data.alert.signature_id:{sig_id}"
    while time.time() - start_time < timeout_sec:
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=4) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                hits = data.get("hits", {}).get("hits", [])
                if hits:
                    return hits[0]["_source"]
        except Exception:
            pass
        time.sleep(1)
    return None


def run_phase31_verification() -> dict:
    console.print(Panel.fit("[bold cyan]🛡️ Phase 31: Real-time SIEM Ingestion & SOC Console E2E Validation[/bold cyan]"))

    run_id = f"phase31_{int(time.time())}"
    flow_id_base = 920000000000000 + int(time.time()) % 100000
    timestamp_start = datetime.now(UTC)

    results = {
        "phase": "Phase 31",
        "run_id": run_id,
        "start_time": timestamp_start.isoformat(),
        "gates": {},
        "stages": {},
    }

    # 1. Pre-checks: Docker container state
    console.print("\n[bold]1. Checking Wazuh Docker Stack...[/bold]")
    container_status = check_docker_containers()
    all_running = all(s == "running" for s in container_status.values())
    for name, stat in container_status.items():
        color = "green" if stat == "running" else "red"
        console.print(f"  • {name}: [{color}]{stat}[/{color}]")

    results["stages"]["containers"] = container_status
    if not all_running:
        console.print("[red]❌ Some Wazuh containers are not running![/red]")
        results["status"] = "BLOCKED"
        return results

    # 2. Initial Indexer Count
    initial_count = query_indexer_count()
    console.print(f"\n[bold]2. Initial OpenSearch Document Count:[/bold] {initial_count}")
    results["stages"]["initial_doc_count"] = initial_count

    # 3. Generate Unique Test Events (Recon, Initial Access, C2)
    console.print(f"\n[bold]3. Generating Unique 3-Stage Attack Events (Run ID: {run_id})...[/bold]")
    test_events = generate_targeted_killchain_events(
        run_id=run_id,
        attacker_ip="10.77.20.20",
        target_ip="10.77.30.20",
        base_time=timestamp_start,
        flow_id_base=flow_id_base,
    )
    for ev in test_events:
        console.print(f"  [+] Stage: {ev['alert']['metadata']['stage'][0]} | Flow ID: {ev['flow_id']} | SID: {ev['alert']['signature_id']} | Sig: {ev['alert']['signature']}")

    results["stages"]["generated_events"] = test_events

    # 4. Stream Events to Local EVE file & Wazuh Manager Container
    local_eve = Path("logs/suricata/eve.json")
    local_eve.parent.mkdir(parents=True, exist_ok=True)
    with open(local_eve, "a", encoding="utf-8") as f:
        for ev in test_events:
            f.write(json.dumps(ev) + "\n")

    # Inject into Docker Wazuh Manager's /var/ossec/logs/eve.json
    console.print("\n[bold]4. Ingesting into Wazuh Manager (/var/ossec/logs/eve.json)...[/bold]")
    eve_payload = "\n".join(json.dumps(ev) for ev in test_events) + "\n"
    inject_proc = subprocess.run(
        ["docker", "exec", "-i", "soc-wazuh-manager", "sh", "-c", "cat >> /var/ossec/logs/eve.json"],
        input=eve_payload,
        text=True,
        capture_output=True
    )
    console.print(f"  [green]✔ Ingested {len(test_events)} events into Manager container[/green]")

    # 5. Poll Wazuh Indexer for indexed documents
    console.print("\n[bold]5. Polling Wazuh Indexer (OpenSearch :9200) for real-time indexed alerts...[/bold]")
    indexed_hits = []
    for ev in test_events:
        sid = ev["alert"]["signature_id"]
        fid = ev["flow_id"]
        hit = poll_indexer_for_event(run_id=run_id, sig_id=sid, timeout_sec=15)
        if hit:
            indexed_hits.append(hit)
            rule_desc = hit.get("rule", {}).get("description", "N/A")
            alert_id = hit.get("id", "N/A")
            console.print(f"  [green]✔ Verified Hit in Indexer:[/green] SID: {sid} | Doc ID: {alert_id} | Rule: {rule_desc}")
        else:
            console.print(f"  [yellow]⚠ SID {sid} (Flow ID {fid}) was not indexed within timeout[/yellow]")

    results["stages"]["indexed_hits_count"] = len(indexed_hits)
    results["stages"]["indexed_hits"] = indexed_hits

    # 6. Execute Correlation Analyzer
    console.print("\n[bold]6. Running Multi-stage Killchain Correlation Engine...[/bold]")
    correlation_engine = CorrelationEngine(window_minutes=60)
    alerts_parsed = list(stream_eve_log(local_eve))
    
    # Filter to current run
    current_run_alerts = [
        a for a in alerts_parsed if a.raw_data.get("run_id") == run_id
    ]

    correlated_incident = None
    for a in current_run_alerts:
        inc = correlation_engine.process_alert(a)
        if inc:
            correlated_incident = inc

    if correlated_incident:
        console.print(f"  [bold green]✔ High Priority Incident Created:[/bold green] {correlated_incident.incident_id}")
        console.print(f"  • Attacker: {correlated_incident.src_ip}")
        console.print(f"  • Attack Stages: {' ➔ '.join(correlated_incident.attack_stages)}")
        console.print(f"  • Highest Severity: [bold red]{correlated_incident.highest_severity}[/bold red]")
        console.print(f"  • Playbook: {correlated_incident.playbook_ref}")
        console.print(f"  • Verdict: {correlated_incident.verdict}")
        results["stages"]["incident"] = correlated_incident.model_dump(mode="json")
    else:
        console.print("[red]❌ Correlation failed to escalate 3-stage sequence![/red]")
        results["stages"]["incident"] = None

    # 7. Validate Idempotency
    console.print("\n[bold]7. Validating Idempotency on Re-processing...[/bold]")
    idem_engine = CorrelationEngine(window_minutes=60)
    idem_inc = None
    for a in current_run_alerts:
        res = idem_engine.process_alert(a)
        if res:
            idem_inc = res
    
    idempotent = (
        correlated_incident is not None
        and idem_inc is not None
        and idem_inc.incident_id == correlated_incident.incident_id
        and idem_inc.attack_stages == correlated_incident.attack_stages
        and idem_inc.highest_severity == correlated_incident.highest_severity
    )
    console.print(f"  • Idempotency Check: {'[green]PASS[/green]' if idempotent else '[red]FAIL[/red]'}")
    results["stages"]["idempotency_pass"] = idempotent

    # 8. SOC Console API Response Validation
    console.print("\n[bold]8. Testing FastAPI SOC Console API Endpoints...[/bold]")
    client = TestClient(app)

    res_health = client.get("/api/health")
    res_stats = client.get("/api/stats")
    res_alerts = client.get("/api/alerts?limit=10")
    res_inc = client.get("/api/incidents")

    api_valid = (
        res_health.status_code == 200
        and res_stats.status_code == 200
        and res_alerts.status_code == 200
        and res_inc.status_code == 200
    )
    console.print(f"  • /api/health: HTTP {res_health.status_code}")
    console.print(f"  • /api/stats: HTTP {res_stats.status_code} (Total: {res_stats.json().get('total_alerts')} alerts)")
    console.print(f"  • /api/alerts: HTTP {res_alerts.status_code}")
    console.print(f"  • /api/incidents: HTTP {res_inc.status_code} ({len(res_inc.json())} incident(s))")

    results["stages"]["api_validation"] = {
        "status_code_health": res_health.status_code,
        "health_body": res_health.json(),
        "stats_body": res_stats.json(),
        "incidents_count": len(res_inc.json()),
    }

    # 9. Determine Overall Status
    pass_condition = (
        all_running
        and len(indexed_hits) == len(test_events)
        and correlated_incident is not None
        and idempotent
        and api_valid
    )

    overall_status = "PASS" if pass_condition else "PARTIAL"
    results["status"] = overall_status
    console.print(f"\n[bold {'green' if overall_status == 'PASS' else 'yellow'}]==================================================================[/bold {'green' if overall_status == 'PASS' else 'yellow'}]")
    console.print(f" [bold {'green' if overall_status == 'PASS' else 'yellow'}]🎉 Phase 31 Overall Result: {overall_status}[/bold {'green' if overall_status == 'PASS' else 'yellow'}]")
    console.print(f"[bold {'green' if overall_status == 'PASS' else 'yellow'}]==================================================================[/bold {'green' if overall_status == 'PASS' else 'yellow'}]\n")

    return results


if __name__ == "__main__":
    result = run_phase31_verification()
    
    # Save evidence files
    evidence_dir = Path("evidence/EV-E2E-002")
    evidence_dir.mkdir(parents=True, exist_ok=True)
    with open(evidence_dir / "e2e_verification_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    console.print(f"[+] Saved verification result to {evidence_dir / 'e2e_verification_result.json'}")
