import json
import logging
import sys
from typing import Any
import httpx

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from analyzer.models import NormalizedAlert, Severity
from analyzer.detection.correlation_engine import Incident

logger = logging.getLogger("soc.notifier")
console = Console()


def print_alert_rich(alert: NormalizedAlert) -> None:
    color = "red" if alert.severity in [Severity.CRITICAL, Severity.HIGH] else (
        "yellow" if alert.severity == Severity.MEDIUM else "cyan"
    )
    
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_row("[bold]Engine:[/bold]", f"[{color}]{alert.engine}[/{color}]")
    table.add_row("[bold]Severity:[/bold]", f"[{color}]{alert.severity}[/{color}]")
    table.add_row("[bold]SID / Rev:[/bold]", f"{alert.sid}:{alert.rev}")
    table.add_row("[bold]Source:[/bold]", f"{alert.src_ip}:{alert.src_port or '-'}")
    table.add_row("[bold]Destination:[/bold]", f"{alert.dst_ip}:{alert.dst_port or '-'}")
    table.add_row("[bold]Category:[/bold]", f"{alert.category}")
    if alert.mitre_technique:
        table.add_row("[bold]MITRE ATT&CK:[/bold]", f"[magenta]{alert.mitre_technique}[/magenta]")
    if alert.http_uri:
        table.add_row("[bold]HTTP URI:[/bold]", f"{alert.http_uri}")

    console.print(Panel(table, title=f"🚨 [bold {color}]{alert.signature}[/bold {color}]", border_style=color))


def print_incident_rich(incident: Incident) -> None:
    table = Table(title=f"🔥 INCIDENT ESCALATION: {incident.incident_id}", border_style="bold red")
    table.add_column("Property", style="cyan")
    table.add_column("Details", style="white")

    table.add_row("Attacker IP", incident.src_ip)
    table.add_row("Target IPs", ", ".join(incident.target_ips))
    table.add_row("Attack Stages", " ➔ ".join(incident.attack_stages))
    table.add_row("Alert Count", str(len(incident.alerts)))
    table.add_row("Severity", f"[bold red]{incident.highest_severity}[/bold red]")
    table.add_row("Verdict", incident.verdict)
    if incident.playbook_ref:
        table.add_row("Recommended Playbook", f"[bold green]{incident.playbook_ref}[/bold green]")

    console.print(table)


async def send_webhook_alert(webhook_url: str, alert: NormalizedAlert) -> None:
    if not webhook_url:
        return
    payload = {
        "text": f"🚨 *[SOC Alert]* {alert.signature}\n"
                f"• Engine: {alert.engine} | Severity: {alert.severity}\n"
                f"• Flow: `{alert.src_ip}` -> `{alert.dst_ip}:{alert.dst_port}`\n"
                f"• Category: {alert.category}"
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(webhook_url, json=payload)
    except Exception as e:
        logger.error(f"Failed to send webhook: {e}")
