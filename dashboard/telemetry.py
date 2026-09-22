import os
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from analyzer.detection.correlation_engine import CorrelationEngine, Incident
from analyzer.models import NormalizedAlert, Severity
from analyzer.parsers.eve_parser import stream_eve_log
from analyzer.parsers.snort_parser import stream_snort_log

SURICATA_LOG = Path(os.getenv("SURICATA_EVE_PATH", "logs/suricata/eve.json"))
SNORT_LOG = Path(os.getenv("SNORT_ALERT_PATH", "logs/snort/alert_json.txt"))

GEO_IP_LOOKUP: dict[str, dict[str, str]] = {
    "10.77.20.20": {"country": "공격 시뮬레이션 망 (Lab Red-Team)", "code": "LAB", "flag": "🔴"},
    "10.77.30.20": {"country": "피해자 격리망 (Target DMZ)", "code": "INT", "flag": "🛡️"},
    "10.77.10.20": {"country": "센서 관제망 (Sensor MGMT)", "code": "INT", "flag": "👁️"},
    "10.77.10.10": {"country": "SIEM 서버 (Wazuh MGMT)", "code": "INT", "flag": "💻"},
    "10.10.70.151": {"country": "대한민국 (분석관 콘솔)", "code": "KR", "flag": "🇰🇷"},
    "10.10.69.42": {"country": "대한민국 (운영 콘솔)", "code": "KR", "flag": "🇰🇷"},
    "198.51.100.44": {"country": "미국 (US Threat Intel)", "code": "US", "flag": "🇺🇸"},
    "208.103.161.2": {"country": "미국 (US External)", "code": "US", "flag": "🇺🇸"},
    "172.64.155.209": {"country": "미국 (Cloudflare)", "code": "US", "flag": "🇺🇸"},
    "104.18.32.47": {"country": "캐나다 (CDN Edge)", "code": "CA", "flag": "🇨🇦"},
    "121.125.60.240": {"country": "대한민국 (KT Ingress)", "code": "KR", "flag": "🇰🇷"},
    "185.220.101.5": {"country": "독일 (Tor Exit Node)", "code": "DE", "flag": "🇩🇪"},
    "45.154.255.89": {"country": "러시아 (Threat Actor)", "code": "RU", "flag": "🇷🇺"},
    "203.0.113.195": {"country": "싱가포르 (APNIC)", "code": "SG", "flag": "🇸🇬"},
    "192.0.2.88": {"country": "일본 (Tokyo DC)", "code": "JP", "flag": "🇯🇵"},
}


def get_geo_info(ip: str) -> dict[str, str]:
    if ip in GEO_IP_LOOKUP:
        return GEO_IP_LOOKUP[ip]
    if ip.startswith("10.77.20."):
        return {"country": "공격 시뮬레이션 망 (Lab Red-Team)", "code": "LAB", "flag": "🔴"}
    if ip.startswith(("10.77.", "10.10.")):
        return {"country": "내부 관제망 (Internal)", "code": "INT", "flag": "🔒"}
    if ip.startswith(("198.51.", "208.")):
        return {"country": "미국 (United States)", "code": "US", "flag": "🇺🇸"}
    return {"country": "미상 외부 (External WAN)", "code": "WAN", "flag": "🌐"}


def load_normalized_alerts() -> list[NormalizedAlert]:
    import hashlib
    alerts: list[NormalizedAlert] = []
    if SURICATA_LOG.exists():
        for i, a in enumerate(stream_eve_log(SURICATA_LOG)):
            key = f"suri_{i}_{a.sid}_{a.src_ip}_{a.dst_ip}_{a.src_port}_{a.dst_port}"
            a.id = f"EV-suri-{hashlib.md5(key.encode()).hexdigest()[:10]}"
            alerts.append(a)
    if SNORT_LOG.exists():
        for i, a in enumerate(stream_snort_log(SNORT_LOG)):
            key = f"snort_{i}_{a.sid}_{a.src_ip}_{a.dst_ip}_{a.src_port}_{a.dst_port}"
            a.id = f"EV-snort-{hashlib.md5(key.encode()).hexdigest()[:10]}"
            alerts.append(a)
    alerts.sort(key=lambda x: (x.timestamp, x.id), reverse=True)
    return alerts


def build_incidents(alerts: list[NormalizedAlert]) -> list[Incident]:
    engine = CorrelationEngine(window_minutes=60)
    incidents_by_id: dict[str, Incident] = {}
    for a in reversed(alerts):
        inc = engine.process_alert(a)
        if inc:
            incidents_by_id[inc.incident_id] = inc
    return list(incidents_by_id.values())


def get_dashboard_summary_telemetry() -> dict[str, Any]:
    alerts = load_normalized_alerts()
    incidents = build_incidents(alerts)

    total_alerts = len(alerts)
    critical_count = sum(1 for a in alerts if a.severity == Severity.CRITICAL)
    high_count = sum(1 for a in alerts if a.severity == Severity.HIGH)
    medium_count = sum(1 for a in alerts if a.severity == Severity.MEDIUM)
    low_count = sum(1 for a in alerts if a.severity in (Severity.LOW, Severity.INFO))
    blocked_count = 147  # From gateway nftables drop counter baseline

    # Engine counts
    engine_counts = Counter(a.engine.value for a in alerts)

    # Category counts
    category_counts = Counter(a.category for a in alerts)

    # Protocols
    proto_counts = Counter((a.protocol or "TCP").upper() for a in alerts)

    # Top attackers & targets
    top_src_ips = [
        {
            "ip": ip,
            "count": count,
            "geo": get_geo_info(ip),
            "pct": round(count / max(total_alerts, 1) * 100, 1),
        }
        for ip, count in Counter(a.src_ip for a in alerts).most_common(5)
    ]
    top_dst_ips = [
        {
            "ip": ip,
            "count": count,
            "geo": get_geo_info(ip),
            "pct": round(count / max(total_alerts, 1) * 100, 1),
        }
        for ip, count in Counter(a.dst_ip for a in alerts).most_common(5)
    ]

    # Recent critical alerts table
    recent_critical = []
    for a in alerts[:8]:
        recent_critical.append(
            {
                "id": a.id,
                "timestamp": a.timestamp.strftime("%m-%d %H:%M:%S") if hasattr(a.timestamp, "strftime") else str(a.timestamp)[5:19],
                "engine": a.engine.value.upper(),
                "severity": a.severity.value.upper(),
                "signature": a.signature,
                "src_ip": a.src_ip,
                "src_port": a.src_port,
                "dst_ip": a.dst_ip,
                "dst_port": a.dst_port,
                "category": a.category,
                "action": "BLOCK" if a.severity in (Severity.CRITICAL, Severity.HIGH) else "ALERT",
                "sid": a.sid,
            }
        )

    # Timeline buckets (last 10 time slices)
    timeline_series = generate_traffic_and_event_timeline(alerts)

    return {
        "kpis": {
            "critical_alerts": critical_count,
            "high_alerts": high_count,
            "medium_alerts": medium_count,
            "low_alerts": low_count,
            "open_incidents": len(incidents),
            "blocked_connections": blocked_count,
            "active_sensors": "4/4",
            "events_per_sec": 84,
            "total_alerts": total_alerts,
        },
        "system_telemetry": {
            "model": "Aegis Cloud-FW-Sensor (TG50B-Hybrid)",
            "serial": "224201022154",
            "policy_manager_ip": "10.10.30.130",
            "policy_manager_connected": True,
            "firmware": "3.1.1.15 (Build 1255-SOC)",
            "last_backup": "2026-09-13 01:00:01",
            "uptime": "10일 05시간 25분",
            "cpu_usage_pct": 18,
            "memory_usage_pct": 34,
            "disk_usage_pct": 42,
            "object_usage_pct": 39,
            "power_status": "NORMAL",
            "ports_active": [0, 1, 2, 3],
        },
        "policy_status": {
            "zero_hit_count": 2,
            "period_expired_count": 0,
            "total_policies": 14,
        },
        "threat_response_status": {
            "ips_detected": total_alerts,
            "ips_blocked": blocked_count,
            "app_control": 12,
            "anti_virus": 5,
            "malicious_site": 8,
            "web_filter": 24,
            "dns_filter": 16,
            "c2_block": 7,
            "data_leak_prevention": 3,
        },
        "engines": dict(engine_counts),
        "categories": dict(category_counts),
        "protocols": dict(proto_counts),
        "top_attackers": top_src_ips,
        "top_targets": top_dst_ips,
        "recent_alerts": recent_critical,
        "timeline": timeline_series,
    }


def generate_traffic_and_event_timeline(alerts: list[NormalizedAlert]) -> dict[str, Any]:
    # 12 intervals representing recent activity
    now = datetime.now(UTC)
    labels = []
    rx_traffic = [24.2, 38.5, 21.0, 58.4, 62.1, 74.0, 68.2, 32.1, 14.5, 48.0, 52.3, 31.8]
    tx_traffic = [18.4, 25.1, 15.2, 42.0, 47.3, 56.5, 51.0, 24.8, 11.2, 37.4, 40.1, 25.4]
    critical_events = [0, 1, 0, 2, 1, 0, 1, 0, 0, 1, 2, 1]
    high_events = [2, 3, 1, 4, 5, 2, 3, 1, 2, 4, 3, 2]
    blocked_events = [5, 8, 4, 12, 16, 9, 11, 6, 4, 14, 15, 8]

    for i in range(12):
        t = now - timedelta(minutes=(11 - i) * 5)
        labels.append(t.strftime("%H:%M"))

    return {
        "labels": labels,
        "rx_kbps": rx_traffic,
        "tx_kbps": tx_traffic,
        "critical_events": critical_events,
        "high_events": high_events,
        "blocked_events": blocked_events,
    }


def get_traffic_analysis_data(time_range: str = "1H") -> dict[str, Any]:
    # Ranking data matching Reference Image 3 (안랩 트래픽분석.jpg)
    return {
        "time_range": time_range,
        "total_rx_mbps": 42.8,
        "total_tx_mbps": 38.6,
        "total_mbps": 81.4,
        "top_sources": [
            {"ip": "10.77.20.20", "bytes": "48.2 MB", "packets": "128,450", "pct": 48.2, "flag": "🔴", "desc": "soc-attacker (Kali)"},
            {"10.10.70.151": {"bytes": "32.1 MB", "packets": "85,200", "pct": 32.1, "flag": "🇰🇷", "desc": "SOC Analyst Console"}},
            {"ip": "198.51.100.44", "bytes": "14.5 MB", "packets": "34,100", "pct": 14.5, "flag": "🇺🇸", "desc": "External SSH Scanner"},
            {"ip": "10.10.69.42", "bytes": "8.4 MB", "packets": "19,800", "pct": 8.4, "flag": "🇰🇷", "desc": "Gateway Admin"},
            {"ip": "185.220.101.5", "bytes": "5.2 MB", "packets": "12,400", "pct": 5.2, "flag": "🇩🇪", "desc": "Tor Exit Node"},
        ],
        "top_destinations": [
            {"ip": "10.77.30.20", "bytes": "52.4 MB", "packets": "142,000", "pct": 52.4, "flag": "🛡️", "desc": "soc-victim (JuiceShop/Target)"},
            {"ip": "208.103.161.2", "bytes": "24.1 MB", "packets": "62,300", "pct": 24.1, "flag": "🇺🇸", "desc": "External CDN Target"},
            {"ip": "10.77.10.10", "bytes": "18.6 MB", "packets": "48,900", "pct": 18.6, "flag": "💻", "desc": "soc-wazuh-siem (1514)"},
            {"ip": "172.64.155.209", "bytes": "12.3 MB", "packets": "31,400", "pct": 12.3, "flag": "🇺🇸", "desc": "Cloudflare DNS/Web"},
            {"ip": "10.77.10.20", "bytes": "9.5 MB", "packets": "24,500", "pct": 9.5, "flag": "👁️", "desc": "soc-sensor (Management)"},
        ],
        "top_services": [
            {"name": "syslog / wazuh", "port": 1514, "bytes": "28.4 MB", "pct": 34.0},
            {"name": "https", "port": 443, "bytes": "24.2 MB", "pct": 29.0},
            {"name": "http (target)", "port": 3000, "bytes": "16.8 MB", "pct": 20.1},
            {"name": "dns", "port": 53, "bytes": "8.5 MB", "pct": 10.2},
            {"name": "ssh", "port": 22, "bytes": "5.6 MB", "pct": 6.7},
        ],
        "top_protocols": [
            {"protocol": "TCP", "pct": 78.4, "bytes": "65.4 MB"},
            {"protocol": "UDP", "pct": 16.2, "bytes": "13.5 MB"},
            {"protocol": "ICMP", "pct": 4.1, "bytes": "3.4 MB"},
            {"protocol": "OTHER", "pct": 1.3, "bytes": "1.1 MB"},
        ],
        "top_dest_countries": [
            {"country": "미국 (US)", "code": "US", "flag": "🇺🇸", "pct": 46.5, "bytes": "38.8 MB"},
            {"country": "대한민국 (KR)", "code": "KR", "flag": "🇰🇷", "pct": 32.1, "bytes": "26.8 MB"},
            {"country": "일본 (JP)", "code": "JP", "flag": "🇯🇵", "pct": 9.8, "bytes": "8.2 MB"},
            {"country": "캐나다 (CA)", "code": "CA", "flag": "🇨🇦", "pct": 6.4, "bytes": "5.3 MB"},
            {"country": "싱가포르 (SG)", "code": "SG", "flag": "🇸🇬", "pct": 5.2, "bytes": "4.3 MB"},
        ],
        "top_policies": [
            {"id": "FW-004", "name": "Attack-to-Victim Permitted Test Services", "hits": 320, "bytes": "52.4 MB"},
            {"id": "FW-006", "name": "Sensor-to-Wazuh SIEM Event Forward", "hits": 480, "bytes": "28.4 MB"},
            {"id": "FW-007", "name": "Drop Attack-to-MGMT Violation Attempt", "hits": 147, "bytes": "9.2 MB"},
            {"id": "FW-001", "name": "Stateful Established / Related", "hits": 1420, "bytes": "112.5 MB"},
        ],
        "top_interfaces": [
            {"interface": "eth1 (soc-vsw-attack)", "rx": "48.2 MB", "tx": "12.4 MB", "total": "60.6 MB"},
            {"interface": "eth2 (soc-vsw-victim)", "rx": "14.1 MB", "tx": "52.4 MB", "total": "66.5 MB"},
            {"interface": "eth0 (soc-vsw-mgmt)", "rx": "28.6 MB", "tx": "18.2 MB", "total": "46.8 MB"},
            {"interface": "nic-monitor (Promiscuous)", "rx": "66.5 MB", "tx": "0 B", "total": "66.5 MB"},
        ],
    }


def get_network_interfaces_telemetry() -> list[dict[str, Any]]:
    # High density interface table matching Reference Image 4 (안랩 인터페이스.jpg)
    return [
        {
            "interface": "eth0",
            "device": "soc-gateway",
            "zone": "MGMT",
            "in_use": True,
            "status": "UP",
            "type": "고정 (Static)",
            "ipv4": "10.77.10.1 / 24",
            "ipv6": "fe80::1 / 64",
            "link": "1000 Full",
            "speed": "1000 Mbps",
            "rx_bps": "398.0 bps",
            "tx_bps": "31.2 Kbps",
            "rx_pps": "1.2 pps",
            "tx_pps": "12.0 pps",
            "rx_bytes": "14.9 KB",
            "tx_bytes": "1.2 MB",
            "rx_pkts": 225,
            "tx_pkts": 3800,
            "peak_rx": "468.0 bytes",
            "peak_tx": "90.0 KB",
            "avg_rx": "497.0 bytes",
            "avg_tx": "38.9 KB",
            "stp": False,
        },
        {
            "interface": "eth1",
            "device": "soc-gateway",
            "zone": "ATTACK",
            "in_use": True,
            "status": "UP",
            "type": "고정 (Static)",
            "ipv4": "10.77.20.1 / 24",
            "ipv6": "fe80::2 / 64",
            "link": "1000 Full",
            "speed": "1000 Mbps",
            "rx_bps": "36.3 Kbps",
            "tx_bps": "286.2 Kbps",
            "rx_pps": "14.0 pps",
            "tx_pps": "25.0 pps",
            "rx_bytes": "1.4 MB",
            "tx_bytes": "10.7 MB",
            "rx_pkts": 4500,
            "tx_pkts": 7800,
            "peak_rx": "2.2 KB",
            "peak_tx": "8.9 MB",
            "avg_rx": "44.8 KB",
            "avg_tx": "346.3 KB",
            "stp": False,
        },
        {
            "interface": "eth2",
            "device": "soc-gateway",
            "zone": "VICTIM",
            "in_use": True,
            "status": "UP",
            "type": "고정 (Static)",
            "ipv4": "10.77.30.1 / 24",
            "ipv6": "fe80::3 / 64",
            "link": "1000 Full",
            "speed": "1000 Mbps",
            "rx_bps": "242.1 Kbps",
            "tx_bps": "48.2 Kbps",
            "rx_pps": "28.0 pps",
            "tx_pps": "6.0 pps",
            "rx_bytes": "8.9 MB",
            "tx_bytes": "1.8 MB",
            "rx_pkts": 6200,
            "tx_pkts": 1400,
            "peak_rx": "14.2 MB",
            "peak_tx": "3.1 MB",
            "avg_rx": "280.4 KB",
            "avg_tx": "52.1 KB",
            "stp": False,
        },
        {
            "interface": "nic-monitor",
            "device": "soc-sensor",
            "zone": "NONE (Port Mirror)",
            "in_use": True,
            "status": "UP",
            "type": "무 L3 IP (Promiscuous)",
            "ipv4": "NO L3 IP (Capture Only)",
            "ipv6": "NO L3 IP",
            "link": "1000 Full",
            "speed": "1000 Mbps",
            "rx_bps": "278.4 Kbps",
            "tx_bps": "0.0 bps",
            "rx_pps": "34.0 pps",
            "tx_pps": "0.0 pps",
            "rx_bytes": "66.5 MB",
            "tx_bytes": "0 B",
            "rx_pkts": 14000,
            "tx_pkts": 0,
            "peak_rx": "28.4 MB",
            "peak_tx": "0 B",
            "avg_rx": "520.1 KB",
            "avg_tx": "0 B",
            "stp": False,
        },
        {
            "interface": "eth0",
            "device": "soc-sensor",
            "zone": "MGMT",
            "in_use": True,
            "status": "UP",
            "type": "고정 (Static)",
            "ipv4": "10.77.10.20 / 24",
            "ipv6": "fe80::20 / 64",
            "link": "1000 Full",
            "speed": "1000 Mbps",
            "rx_bps": "12.4 Kbps",
            "tx_bps": "48.2 Kbps",
            "rx_pps": "4.5 pps",
            "tx_pps": "16.2 pps",
            "rx_bytes": "2.4 MB",
            "tx_bytes": "18.6 MB",
            "rx_pkts": 3200,
            "tx_pkts": 9400,
            "peak_rx": "1.2 MB",
            "peak_tx": "8.5 MB",
            "avg_rx": "38.2 KB",
            "avg_tx": "142.1 KB",
            "stp": False,
        },
        {
            "interface": "eth0",
            "device": "soc-victim",
            "zone": "VICTIM",
            "in_use": True,
            "status": "UP",
            "type": "고정 (Static)",
            "ipv4": "10.77.30.20 / 24",
            "ipv6": "fe80::30 / 64",
            "link": "1000 Full",
            "speed": "1000 Mbps",
            "rx_bps": "184.2 Kbps",
            "tx_bps": "32.1 Kbps",
            "rx_pps": "22.0 pps",
            "tx_pps": "5.0 pps",
            "rx_bytes": "52.4 MB",
            "tx_bytes": "8.2 MB",
            "rx_pkts": 12800,
            "tx_pkts": 2400,
            "peak_rx": "16.4 MB",
            "peak_tx": "2.8 MB",
            "avg_rx": "340.5 KB",
            "avg_tx": "48.2 KB",
            "stp": False,
        },
        {
            "interface": "eth0",
            "device": "soc-attacker",
            "zone": "ATTACK",
            "in_use": True,
            "status": "UP",
            "type": "고정 (Static)",
            "ipv4": "10.77.20.20 / 24",
            "ipv6": "fe80::22 / 64",
            "link": "1000 Full",
            "speed": "1000 Mbps",
            "rx_bps": "32.1 Kbps",
            "tx_bps": "184.2 Kbps",
            "rx_pps": "5.0 pps",
            "tx_pps": "22.0 pps",
            "rx_bytes": "8.2 MB",
            "tx_bytes": "52.4 MB",
            "rx_pkts": 2400,
            "tx_pkts": 12800,
            "peak_rx": "2.8 MB",
            "peak_tx": "16.4 MB",
            "avg_rx": "48.2 KB",
            "avg_tx": "340.5 KB",
            "stp": False,
        },
    ]


def get_assets_telemetry() -> list[dict[str, Any]]:
    return [
        {
            "asset_id": "AST-VIC-01",
            "name": "soc-victim (WEB-01)",
            "ip": "10.77.30.20",
            "os": "Ubuntu 22.04 LTS (Kernel 5.15)",
            "zone": "ZONE-VICTIM (DMZ)",
            "role": "Target Web & App Server (JuiceShop 3000, SSH 22)",
            "risk_score": 88,
            "risk_level": "CRITICAL",
            "open_alerts": 14,
            "last_seen": "방금 전 (Active)",
            "status": "ONLINE",
            "mirror_status": "Mirrored to soc-sensor (nic-monitor)",
        },
        {
            "asset_id": "AST-GW-01",
            "name": "soc-gateway",
            "ip": "10.77.10.1 / 10.77.20.1 / 10.77.30.1",
            "os": "Ubuntu 22.04 LTS (nftables L3 Router)",
            "zone": "BOUNDARY (Gateway)",
            "role": "Tri-Zone Router & Stateful Firewall",
            "risk_score": 42,
            "risk_level": "MEDIUM",
            "open_alerts": 2,
            "last_seen": "방금 전 (Active)",
            "status": "ONLINE",
            "mirror_status": "N/A",
        },
        {
            "asset_id": "AST-SEN-01",
            "name": "soc-sensor",
            "ip": "10.77.10.20 (Monitor: NO IP)",
            "os": "Ubuntu 22.04 LTS (AF_PACKET)",
            "zone": "ZONE-MGMT / MONITOR",
            "role": "Suricata 8.0.6, Snort 3.12, Wazuh Agent 4.14.7",
            "risk_score": 15,
            "risk_level": "LOW",
            "open_alerts": 0,
            "last_seen": "방금 전 (Active)",
            "status": "ONLINE",
            "mirror_status": "Destination Promiscuous Sniffer",
        },
        {
            "asset_id": "AST-ATK-01",
            "name": "soc-attacker",
            "ip": "10.77.20.20",
            "os": "Kali Linux 2024.x Rolling",
            "zone": "ZONE-ATTACK",
            "role": "Red-Team Traffic Generator (Nmap, Hydra, C2)",
            "risk_score": 95,
            "risk_level": "CRITICAL",
            "open_alerts": 59,
            "last_seen": "방금 전 (Active)",
            "status": "MONITORED",
            "mirror_status": "Blocked from MGMT Network",
        },
        {
            "asset_id": "AST-SIEM-01",
            "name": "soc-wazuh-siem",
            "ip": "10.77.10.10",
            "os": "Docker Desktop + WSL2 (Windows Host)",
            "zone": "ZONE-MGMT",
            "role": "Wazuh Manager 4.14.7, OpenSearch 9200, Dashboard 443",
            "risk_score": 10,
            "risk_level": "LOW",
            "open_alerts": 0,
            "last_seen": "방금 전 (Active)",
            "status": "ONLINE",
            "mirror_status": "Target of Agent Events (Port 1514)",
        },
    ]


def get_sensors_telemetry() -> list[dict[str, Any]]:
    return [
        {
            "id": "SNS-SURI-01",
            "name": "Suricata IDS/IPS",
            "role": "Primary Real-time IDS",
            "version": "8.0.6",
            "capture_mode": "AF_PACKET (Hyper-V Port Mirroring)",
            "interface": "nic-monitor (eth1)",
            "status": "UP",
            "health": "OPTIMAL",
            "heartbeat": "< 3s ago",
            "last_event": "2026-09-16 17:08:42",
            "eps": 42.5,
            "active_rules": 128,
            "log_path": "/var/log/suricata/eve.json",
        },
        {
            "id": "SNS-SNRT-01",
            "name": "Snort 3",
            "role": "Secondary Validation & Offline PCAP Engine",
            "version": "3.12.2.0 (libDAQ 3.0.27)",
            "capture_mode": "Offline PCAP / Socket Mode",
            "interface": "pcap / eth1",
            "status": "UP",
            "health": "OPTIMAL",
            "heartbeat": "< 5s ago",
            "last_event": "2026-08-24 06:17:35",
            "eps": 18.2,
            "active_rules": 46,
            "log_path": "logs/snort/alert_json.txt",
        },
        {
            "id": "SNS-WAZUH-AGT",
            "name": "Wazuh Agent (Sensor)",
            "role": "EVE JSON Log Shipper & Host Telemetry",
            "version": "4.14.7",
            "capture_mode": "localfile JSON tailing",
            "interface": "eth0 (10.77.10.20 -> 10.77.10.10:1514)",
            "status": "UP",
            "health": "ACTIVE",
            "heartbeat": "< 10s ago",
            "last_event": "2026-09-16 17:06:19",
            "eps": 35.0,
            "active_rules": 0,
            "log_path": "/var/ossec/etc/ossec.conf",
        },
        {
            "id": "SNS-WAZUH-MGR",
            "name": "Wazuh Manager (Single-node)",
            "role": "Central SIEM & Alert Correlation Server",
            "version": "4.14.7",
            "capture_mode": "Docker Daemon (soc-wazuh-net)",
            "interface": "Port 1514/1515/55000",
            "status": "UP",
            "health": "OPTIMAL",
            "heartbeat": "< 4s ago",
            "last_event": "2026-09-16 17:09:12",
            "eps": 58.0,
            "active_rules": 86601,
            "log_path": "docker://soc-wazuh-manager",
        },
        {
            "id": "SNS-OPENSEARCH",
            "name": "Wazuh Indexer (OpenSearch)",
            "role": "SIEM Storage & Analytical Indexer",
            "version": "2.12.0 (Wazuh 4.14.7)",
            "capture_mode": "REST API (Port 9200)",
            "interface": "127.0.0.1:9200",
            "status": "UP",
            "health": "GREEN",
            "heartbeat": "< 2s ago",
            "last_event": "2026-09-16 17:09:30",
            "eps": 72.0,
            "active_rules": 0,
            "log_path": "wazuh-alerts-4.x-*",
        },
        {
            "id": "SNS-CORRELATION",
            "name": "Correlation Engine",
            "role": "Multi-Stage Kill Chain State Tracker",
            "version": "v1.2 (Window: 60m)",
            "capture_mode": "Sliding Window IP Session State",
            "interface": "In-Memory Stream",
            "status": "UP",
            "health": "RUNNING",
            "heartbeat": "Active",
            "last_event": "방금 전",
            "eps": 84.0,
            "active_rules": 4,
            "log_path": "analyzer/detection/correlation_engine.py",
        },
        {
            "id": "SNS-AI-COPILOT",
            "name": "AI Orchestrator & HITL",
            "role": "Evidence-Grounded Incident Analysis & Policy Gate",
            "version": "Qwen3.5 9B / Mock LLM",
            "capture_mode": "RAG + Deterministic Tool Calling",
            "interface": "FastAPI ASGI (Port 8000)",
            "status": "UP",
            "health": "READY",
            "heartbeat": "Active",
            "last_event": "방금 전",
            "eps": 1.0,
            "active_rules": 5,
            "log_path": "analyzer/ai/orchestrator.py",
        },
    ]


def get_security_policies_telemetry() -> list[dict[str, Any]]:
    # Policies matching Reference Image 5 (지역기반 차단정책.jpg) & Section 14
    return [
        {
            "policy_id": "FW-001",
            "name": "Stateful Connection Tracking (Established/Related)",
            "category": "FIREWALL_STATE",
            "source": "ANY",
            "destination": "ANY",
            "service": "ct state { established, related }",
            "action": "ACCEPT",
            "hits": 1420,
            "last_hit": "10초 전",
            "status": "ACTIVE",
            "is_zero_hit": False,
        },
        {
            "policy_id": "FW-002",
            "name": "ICMP Diagnostics (Management & Victim Ping)",
            "category": "FIREWALL_RULE",
            "source": "10.77.10.0/24, 10.77.30.0/24",
            "destination": "10.77.0.0/16",
            "service": "ICMP echo-request",
            "action": "ACCEPT",
            "hits": 84,
            "last_hit": "2분 전",
            "status": "ACTIVE",
            "is_zero_hit": False,
        },
        {
            "policy_id": "FW-003",
            "name": "SSH Management Access",
            "category": "FIREWALL_RULE",
            "source": "10.77.10.0/24 (ZONE-MGMT)",
            "destination": "10.77.10.1",
            "service": "TCP 22 (SSH)",
            "action": "ACCEPT",
            "hits": 26,
            "last_hit": "5분 전",
            "status": "ACTIVE",
            "is_zero_hit": False,
        },
        {
            "policy_id": "FW-004",
            "name": "Attack-to-Victim Lab Security Testing Channel",
            "category": "FIREWALL_RULE",
            "source": "10.77.20.20 (soc-attacker)",
            "destination": "10.77.30.20 (soc-victim)",
            "service": "TCP 80, 443, 3000, 22, 8080",
            "action": "ACCEPT",
            "hits": 320,
            "last_hit": "방금 전",
            "status": "ACTIVE",
            "is_zero_hit": False,
        },
        {
            "policy_id": "FW-005",
            "name": "Victim-to-Wazuh SIEM Agent Delivery",
            "category": "FIREWALL_RULE",
            "source": "10.77.30.20 (ZONE-VICTIM)",
            "destination": "10.77.10.10",
            "service": "TCP 1514, 1515",
            "action": "ACCEPT",
            "hits": 215,
            "last_hit": "1분 전",
            "status": "ACTIVE",
            "is_zero_hit": False,
        },
        {
            "policy_id": "FW-006",
            "name": "Sensor-to-Wazuh SIEM Event Forward",
            "category": "FIREWALL_RULE",
            "source": "10.77.10.20 (ZONE-MGMT)",
            "destination": "10.77.10.10",
            "service": "TCP 1514, 1515",
            "action": "ACCEPT",
            "hits": 480,
            "last_hit": "방금 전",
            "status": "ACTIVE",
            "is_zero_hit": False,
        },
        {
            "policy_id": "FW-007",
            "name": "Block & Log Attack Zone to Management Zone Violation",
            "category": "FIREWALL_RULE",
            "source": "10.77.20.0/24 (ZONE-ATTACK)",
            "destination": "10.77.10.0/24 (ZONE-MGMT)",
            "service": "ANY",
            "action": "DROP & LOG",
            "hits": 147,
            "last_hit": "3분 전",
            "status": "ACTIVE",
            "is_zero_hit": False,
        },
        {
            "policy_id": "GEO-001",
            "name": "IPv4 Regional Ingress Block (High-Risk Anonymizers)",
            "category": "GEO_BLOCKING",
            "source": "DE, RU, NL (High-Risk Tor/Proxy Subnets)",
            "destination": "10.77.30.0/24",
            "service": "ANY",
            "action": "DROP",
            "hits": 28,
            "last_hit": "18분 전",
            "status": "ACTIVE",
            "is_zero_hit": False,
        },
        {
            "policy_id": "IDS-9000001",
            "name": "SOC-SCAN: Nmap Stealth NULL Scan Detected",
            "category": "SURICATA_RULE",
            "source": "$EXTERNAL_NET",
            "destination": "$HOME_NET",
            "service": "TCP (flags: 0)",
            "action": "ALERT",
            "hits": 18,
            "last_hit": "방금 전",
            "status": "ENABLED",
            "is_zero_hit": False,
        },
        {
            "policy_id": "IDS-9010001",
            "name": "SOC-ATTACK: Web SQL Injection - UNION SELECT Pattern",
            "category": "SURICATA_RULE",
            "source": "$EXTERNAL_NET",
            "destination": "$HOME_NET",
            "service": "HTTP (Port 80/3000)",
            "action": "ALERT",
            "hits": 14,
            "last_hit": "방금 전",
            "status": "ENABLED",
            "is_zero_hit": False,
        },
        {
            "policy_id": "IDS-9030010",
            "name": "SOC-MALWARE: Interactive Reverse Shell Session Established",
            "category": "SURICATA_RULE",
            "source": "$HOME_NET",
            "destination": "$EXTERNAL_NET",
            "service": "TCP (Port 4444)",
            "action": "ALERT",
            "hits": 8,
            "last_hit": "방금 전",
            "status": "ENABLED",
            "is_zero_hit": False,
        },
        {
            "policy_id": "ZERO-001",
            "name": "Legacy Admin Interface (TCP 8443 Ingress)",
            "category": "ZERO_HIT_POLICY",
            "source": "10.77.10.0/24",
            "destination": "10.77.10.1",
            "service": "TCP 8443",
            "action": "ACCEPT",
            "hits": 0,
            "last_hit": "기록 없음 (Zero Hit)",
            "status": "EXPIRED_CANDIDATE",
            "is_zero_hit": True,
        },
        {
            "policy_id": "ZERO-002",
            "name": "Legacy Telnet Ingress Fallback (TCP 23)",
            "category": "ZERO_HIT_POLICY",
            "source": "ANY",
            "destination": "10.77.30.20",
            "service": "TCP 23",
            "action": "DROP",
            "hits": 0,
            "last_hit": "기록 없음 (Zero Hit)",
            "status": "EXPIRED_CANDIDATE",
            "is_zero_hit": True,
        },
    ]


def get_threats_countries_data() -> list[dict[str, Any]]:
    # Geo threat analysis matching Reference Image 5 & Section 9
    return [
        {
            "country": "미국 (United States)",
            "code": "US",
            "flag": "🇺🇸",
            "attack_count": 127,
            "blocked_count": 22,
            "critical_count": 8,
            "top_ip": "198.51.100.44",
            "top_rule": "SOC-ATTACK: SSH Brute Force Rate Exceeded",
            "severity": "CRITICAL",
            "lat": 37.0902,
            "lng": -95.7129,
        },
        {
            "country": "대한민국 (South Korea)",
            "code": "KR",
            "flag": "🇰🇷",
            "attack_count": 59,
            "blocked_count": 147,
            "critical_count": 12,
            "top_ip": "10.77.20.20 (Lab Red-Team)",
            "top_rule": "SOC-MALWARE: Interactive Reverse Shell Session Established",
            "severity": "CRITICAL",
            "lat": 35.9078,
            "lng": 127.7669,
        },
        {
            "country": "독일 (Germany)",
            "code": "DE",
            "flag": "🇩🇪",
            "attack_count": 18,
            "blocked_count": 18,
            "critical_count": 3,
            "top_ip": "185.220.101.5",
            "top_rule": "GEO-001: Regional High-Risk Anonymizer Ingress",
            "severity": "HIGH",
            "lat": 51.1657,
            "lng": 10.4515,
        },
        {
            "country": "러시아 (Russia)",
            "code": "RU",
            "flag": "🇷🇺",
            "attack_count": 14,
            "blocked_count": 14,
            "critical_count": 2,
            "top_ip": "45.154.255.89",
            "top_rule": "SOC-SCAN: Nmap Stealth NULL Scan Detected",
            "severity": "HIGH",
            "lat": 61.5240,
            "lng": 105.3188,
        },
        {
            "country": "일본 (Japan)",
            "code": "JP",
            "flag": "🇯🇵",
            "attack_count": 8,
            "blocked_count": 2,
            "critical_count": 1,
            "top_ip": "192.0.2.88",
            "top_rule": "SOC-ATTACK: Web SQL Injection - UNION SELECT",
            "severity": "MEDIUM",
            "lat": 36.2048,
            "lng": 138.2529,
        },
        {
            "country": "캐나다 (Canada)",
            "code": "CA",
            "flag": "🇨🇦",
            "attack_count": 6,
            "blocked_count": 1,
            "critical_count": 0,
            "top_ip": "104.18.32.47",
            "top_rule": "SOC-SCAN: Rapid Port Sweep Probe",
            "severity": "LOW",
            "lat": 56.1304,
            "lng": -106.3468,
        },
    ]
