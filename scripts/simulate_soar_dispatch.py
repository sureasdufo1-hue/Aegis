#!/usr/bin/env python3
"""
scripts/simulate_soar_dispatch.py
SOAR Tier-1 Real-Time Incident Notification Simulation Tool.
Generates multi-stage synthetic incidents and dispatches alerts via Slack, Discord, and Webhook.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import UTC, datetime
from pathlib import Path

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from analyzer.alerting.dispatcher import NotificationConfig, NotificationDispatcher
from analyzer.detection.correlation_engine import Incident
from analyzer.models import EngineType, NormalizedAlert, Severity

console = Console()


def create_scenario_incident(scenario: str) -> Incident:
    now_utc = datetime.now(UTC)

    if scenario == "account_takeover":
        alert_recon = NormalizedAlert(
            id=f"ALT-{int(now_utc.timestamp())}-1",
            timestamp=now_utc,
            engine=EngineType.SURICATA,
            sid=9000001,
            rev=1,
            signature="SCAN Nmap TCP SYN Port Scan Detected",
            category="Reconnaissance",
            severity=Severity.MEDIUM,
            src_ip="10.77.20.20",
            dst_ip="10.77.30.20",
            src_port=49812,
            dst_port=22,
            protocol="TCP",
            mitre_technique="T1046",
        )
        alert_brute = NormalizedAlert(
            id=f"ALT-{int(now_utc.timestamp())}-2",
            timestamp=now_utc,
            engine=EngineType.SURICATA,
            sid=9020001,
            rev=1,
            signature="AUTH SSH Brute Force Login Attempt Threshold Exceeded",
            category="Authentication Anomaly",
            severity=Severity.HIGH,
            src_ip="10.77.20.20",
            dst_ip="10.77.30.20",
            src_port=49813,
            dst_port=22,
            protocol="TCP",
            mitre_technique="T1110.001",
        )
        alert_success = NormalizedAlert(
            id=f"ALT-{int(now_utc.timestamp())}-3",
            timestamp=now_utc,
            engine=EngineType.WAZUH,
            sid=5715,
            rev=1,
            signature="sshd: Authentication Success (Accepted password for root)",
            category="Authentication Success",
            severity=Severity.CRITICAL,
            src_ip="10.77.20.20",
            dst_ip="10.77.30.20",
            src_port=49814,
            dst_port=22,
            protocol="TCP",
            mitre_technique="T1078",
        )
        return Incident(
            incident_id=f"INC-ATO-{int(now_utc.timestamp())}",
            src_ip="10.77.20.20",
            target_ips=["10.77.30.20"],
            attack_stages=["1. Reconnaissance", "2. Initial Access / Exploitation"],
            alerts=[alert_recon, alert_brute, alert_success],
            start_time=now_utc,
            last_seen=now_utc,
            highest_severity=Severity.CRITICAL,
            verdict="Confirmed Account Takeover: SSH Brute Force Followed by Successful Login",
            playbook_ref="playbooks/05_ssh_brute_force_investigation.md",
            activity_status="CONFIRMED_COMPROMISE",
        )
    elif scenario == "c2_beacon":
        alert_exploit = NormalizedAlert(
            id=f"ALT-{int(now_utc.timestamp())}-1",
            timestamp=now_utc,
            engine=EngineType.SURICATA,
            sid=9010001,
            rev=1,
            signature="WEB-ATTACK SQL Injection Attempt Detected (UNION SELECT)",
            category="Web Application Attack",
            severity=Severity.HIGH,
            src_ip="10.77.20.20",
            dst_ip="10.77.30.20",
            src_port=51020,
            dst_port=80,
            protocol="TCP",
            mitre_technique="T1190",
        )
        alert_shell = NormalizedAlert(
            id=f"ALT-{int(now_utc.timestamp())}-2",
            timestamp=now_utc,
            engine=EngineType.SURICATA,
            sid=9030010,
            rev=1,
            signature="MALWARE-CNC Cobalt Strike Beacon / Reverse Shell Activity Detected",
            category="Command and Control",
            severity=Severity.CRITICAL,
            src_ip="10.77.20.20",
            dst_ip="10.77.30.20",
            src_port=51022,
            dst_port=4444,
            protocol="TCP",
            mitre_technique="T1059.004",
        )
        return Incident(
            incident_id=f"INC-C2-{int(now_utc.timestamp())}",
            src_ip="10.77.20.20",
            target_ips=["10.77.30.20"],
            attack_stages=["2. Initial Access / Exploitation", "3. Command & Control / Execution"],
            alerts=[alert_exploit, alert_shell],
            start_time=now_utc,
            last_seen=now_utc,
            highest_severity=Severity.CRITICAL,
            verdict="Confirmed Post-Exploitation Activity: Web Exploit Followed by Reverse Shell C2 Connection",
            playbook_ref="playbooks/04_malware_c2_investigation.md",
            activity_status="CONFIRMED_COMPROMISE",
        )
    else:
        # Default web scan & exploit
        alert1 = NormalizedAlert(
            id=f"ALT-{int(now_utc.timestamp())}-1",
            timestamp=now_utc,
            engine=EngineType.SURICATA,
            sid=9000001,
            rev=1,
            signature="SCAN Nmap TCP SYN Port Scan Detected",
            category="Reconnaissance",
            severity=Severity.MEDIUM,
            src_ip="10.77.20.20",
            dst_ip="10.77.30.20",
            src_port=48910,
            dst_port=80,
            protocol="TCP",
            mitre_technique="T1046",
        )
        alert2 = NormalizedAlert(
            id=f"ALT-{int(now_utc.timestamp())}-2",
            timestamp=now_utc,
            engine=EngineType.SURICATA,
            sid=9010001,
            rev=1,
            signature="WEB-ATTACK SQL Injection Attempt Detected",
            category="Web Application Attack",
            severity=Severity.HIGH,
            src_ip="10.77.20.20",
            dst_ip="10.77.30.20",
            src_port=48911,
            dst_port=80,
            protocol="TCP",
            mitre_technique="T1190",
        )
        return Incident(
            incident_id=f"INC-WEB-{int(now_utc.timestamp())}",
            src_ip="10.77.20.20",
            target_ips=["10.77.30.20"],
            attack_stages=["1. Reconnaissance", "2. Initial Access / Exploitation"],
            alerts=[alert1, alert2],
            start_time=now_utc,
            last_seen=now_utc,
            highest_severity=Severity.CRITICAL,
            verdict="Suspicious Multi-Stage Exploit Attempt: Reconnaissance -> Web Exploitation",
            playbook_ref="playbooks/03_web_attack_investigation.md",
            activity_status="SUSPICIOUS_ATTEMPT",
        )


async def main() -> None:
    parser = argparse.ArgumentParser(description="Simulate SOAR Real-Time Incident Notification Dispatch")
    parser.add_argument("--scenario", choices=["account_takeover", "c2_beacon", "web_exploit"], default="account_takeover",
                        help="Attack scenario to simulate")
    parser.add_argument("--force", action="store_true", help="Bypass cooldown throttling")
    parser.add_argument("--dry-run", action="store_true", help="Force dry-run mode (print payload, no HTTP POST)")
    args = parser.parse_args()

    console.print(Panel.fit(
        "[bold cyan]Aegis SOC Lab - SOAR Notification Dispatcher Simulator[/bold cyan]\n"
        "[white]Real-Time Multi-Channel Incident Alerting & Actionable Payload Verification[/white]",
        border_style="cyan",
    ))

    config = NotificationConfig.from_env()
    if args.dry_run:
        config.dry_run = True

    dispatcher = NotificationDispatcher(config=config)
    masked = dispatcher.get_masked_config()

    table_cfg = Table(title="Notification Channel Configuration", border_style="dim")
    table_cfg.add_column("Channel", style="bold green")
    table_cfg.add_column("Status", style="bold")
    table_cfg.add_column("Endpoint", style="white")

    table_cfg.add_row("Slack Block Kit", "Active" if masked["slack_configured"] else "Dry Run / Disabled", masked["slack_url_masked"] or "(None)")
    table_cfg.add_row("Discord Embed", "Active" if masked["discord_configured"] else "Dry Run / Disabled", masked["discord_url_masked"] or "(None)")
    table_cfg.add_row("Generic Webhook", "Active" if masked["webhook_configured"] else "Dry Run / Disabled", masked["webhook_url_masked"] or "(None)")
    table_cfg.add_row("Cooldown Window", f"{masked['cooldown_minutes']} minutes", "-")
    console.print(table_cfg)

    incident = create_scenario_incident(args.scenario)

    console.print(f"\n[bold yellow]Generated Synthetic Incident:[/bold yellow] [bold white]{incident.incident_id}[/bold white]")
    console.print(f"• Attacker: [bold red]{incident.src_ip}[/bold red] ➔ Target: [bold green]{incident.target_ips}[/bold green]")
    console.print(f"• Severity: [bold red]{incident.highest_severity.value}[/bold red] ({incident.activity_status})")
    console.print(f"• Verdict:  {incident.verdict}")
    console.print(f"• Recommended Isolation: [bold magenta]nft add element inet filter blocklist {{ {incident.src_ip} }}[/bold magenta]\n")

    console.print("[bold cyan]Dispatching notification across configured channels...[/bold cyan]")
    dispatch_result = await dispatcher.dispatch_incident(incident, force=args.force)

    table_res = Table(title="Dispatch Results", border_style="bold cyan")
    table_res.add_column("Channel", style="bold")
    table_res.add_column("Result Status", style="bold")

    if dispatch_result["status"] in ("throttled", "suppressed"):
        table_res.add_row("All Channels", f"[bold yellow]{dispatch_result['status'].upper()}[/bold yellow]")
    else:
        for ch in dispatch_result.get("dispatched_channels", []):
            st = ch["status"]
            color = "green" if st == "success" else ("yellow" if st == "dry_run" else "red")
            table_res.add_row(ch["channel"].upper(), f"[{color}]{st.upper()}[/{color}]")

    console.print(table_res)
    console.print("\n[bold green]✓ SOAR Dispatch simulation completed successfully.[/bold green]")


if __name__ == "__main__":
    asyncio.run(main())
