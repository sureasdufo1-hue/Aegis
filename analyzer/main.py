import argparse
import sys
from pathlib import Path

# Enable UTF-8 output on Windows consoles
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console

from analyzer.alerting.notifier import print_alert_rich, print_incident_rich
from analyzer.detection.correlation_engine import CorrelationEngine
from analyzer.detection.threat_intel import ThreatIntelEngine
from analyzer.models import NormalizedAlert
from analyzer.parsers.eve_parser import stream_eve_log
from analyzer.parsers.snort_parser import stream_snort_log

console = Console()


def run_batch_analysis(eve_path: Path | None, snort_path: Path | None):
    console.print("\n[bold cyan]🛡️  SOC Lab Log Analyzer - Batch Processing Mode[/bold cyan]\n")
    
    correlation_engine = CorrelationEngine(window_minutes=60)
    alerts: list[NormalizedAlert] = []

    # 1. Ingest Suricata
    if eve_path and eve_path.exists():
        console.print(f"[green]✔[/green] Parsing Suricata EVE log: [bold]{eve_path}[/bold]")
        count = 0
        for alert in stream_eve_log(eve_path):
            alerts.append(alert)
            count += 1
        console.print(f"  └ Found {count} Suricata alerts")

    # 2. Ingest Snort
    if snort_path and snort_path.exists():
        console.print(f"[green]✔[/green] Parsing Snort 3 log: [bold]{snort_path}[/bold]")
        count = 0
        for alert in stream_snort_log(snort_path):
            alerts.append(alert)
            count += 1
        console.print(f"  └ Found {count} Snort alerts")

    # Sort chronologically
    alerts.sort(key=lambda x: x.timestamp)
    console.print(f"\n[bold yellow]🔍 Analyzing {len(alerts)} Total Security Events...[/bold yellow]\n")

    incidents = []
    for alert in alerts:
        # Check Threat Intel
        ti_match = ThreatIntelEngine.check_ip(alert.src_ip)
        if ti_match:
            alert.category += f" [TI: {ti_match.threat_group}]"

        print_alert_rich(alert)
        
        # Correlate
        incident = correlation_engine.process_alert(alert)
        if incident:
            incidents.append(incident)

    if incidents:
        console.print("\n[bold red]🔥 High Priority Correlated Incidents:[/bold red]\n")
        for inc in incidents:
            print_incident_rich(inc)
    else:
        console.print("\n[bold green]✅ No Multi-stage Critical Incidents Detected.[/bold green]\n")


def main():
    parser = argparse.ArgumentParser(description="SOC Lab Suricata & Snort Log Analyzer")
    parser.add_argument("--eve", type=Path, default=Path("logs/suricata/eve.json"), help="Path to eve.json")
    parser.add_argument("--snort", type=Path, default=Path("logs/snort/alert_json.txt"), help="Path to snort alert json")
    args = parser.parse_args()

    run_batch_analysis(args.eve, args.snort)


if __name__ == "__main__":
    main()
