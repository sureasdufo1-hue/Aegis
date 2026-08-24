import json
import os
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from analyzer.models import NormalizedAlert, Severity
from analyzer.parsers.eve_parser import stream_eve_log
from analyzer.parsers.snort_parser import stream_snort_log
from analyzer.detection.correlation_engine import CorrelationEngine, Incident
from analyzer.detection.threat_intel import ThreatIntelEngine

app = FastAPI(title="SOC Lab - Suricata & Snort Real-Time Monitoring Center")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SURICATA_LOG = Path(os.getenv("SURICATA_EVE_PATH", "logs/suricata/eve.json"))
SNORT_LOG = Path(os.getenv("SNORT_ALERT_PATH", "logs/snort/alert_json.txt"))


def get_all_alerts() -> list[NormalizedAlert]:
    alerts: list[NormalizedAlert] = []
    if SURICATA_LOG.exists():
        alerts.extend(stream_eve_log(SURICATA_LOG))
    if SNORT_LOG.exists():
        alerts.extend(stream_snort_log(SNORT_LOG))
    alerts.sort(key=lambda x: x.timestamp, reverse=True)
    return alerts


@app.get("/api/stats")
def get_stats():
    alerts = get_all_alerts()
    total = len(alerts)
    critical = sum(1 for a in alerts if a.severity == Severity.CRITICAL)
    high = sum(1 for a in alerts if a.severity == Severity.HIGH)
    medium = sum(1 for a in alerts if a.severity == Severity.MEDIUM)
    low_info = total - (critical + high + medium)

    engine_counts = Counter(a.engine.value for a in alerts)
    category_counts = Counter(a.category for a in alerts)
    top_src_ips = Counter(a.src_ip for a in alerts).most_common(5)
    top_dst_ports = Counter(str(a.dst_port) for a in alerts if a.dst_port).most_common(5)

    # Correlation
    engine = CorrelationEngine(window_minutes=60)
    incidents = []
    for a in reversed(alerts):
        inc = engine.process_alert(a)
        if inc:
            incidents.append(inc)

    return {
        "total_alerts": total,
        "critical_alerts": critical,
        "high_alerts": high,
        "medium_alerts": medium,
        "low_info_alerts": low_info,
        "engine_distribution": dict(engine_counts),
        "category_distribution": dict(category_counts),
        "top_attackers": top_src_ips,
        "top_targeted_ports": top_dst_ports,
        "incident_count": len(incidents),
    }


@app.get("/api/alerts")
def get_alerts(limit: int = 50, severity: str | None = None):
    alerts = get_all_alerts()
    if severity:
        alerts = [a for a in alerts if a.severity.value == severity.upper()]
    return [a.model_dump() for a in alerts[:limit]]


@app.get("/api/incidents")
def get_incidents():
    alerts = get_all_alerts()
    engine = CorrelationEngine(window_minutes=60)
    incidents: list[Incident] = []
    for a in reversed(alerts):
        inc = engine.process_alert(a)
        if inc and not any(existing.incident_id == inc.incident_id for existing in incidents):
            incidents.append(inc)
    return [i.model_dump() for i in incidents]


@app.get("/", response_class=HTMLResponse)
def index():
    return """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SOC Security Operations Center | Suricata & Snort Lab</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Pretendard:wght@400;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Pretendard', sans-serif; background-color: #0b0f19; color: #e2e8f0; }
        .font-mono { font-family: 'JetBrains Mono', monospace; }
        .glow-red { box-shadow: 0 0 15px rgba(239, 68, 68, 0.25); }
        .glow-blue { box-shadow: 0 0 15px rgba(59, 130, 246, 0.25); }
        .glow-cyan { box-shadow: 0 0 15px rgba(6, 182, 212, 0.25); }
    </style>
</head>
<body class="min-h-screen">
    <!-- Top Header -->
    <header class="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50 px-6 py-4 flex items-center justify-between">
        <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center font-bold text-white shadow-lg">
                SOC
            </div>
            <div>
                <h1 class="text-xl font-bold text-white tracking-tight flex items-center gap-2">
                    Security Operations Center
                    <span class="text-xs px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">LIVE LAB</span>
                </h1>
                <p class="text-xs text-slate-400 font-mono">Suricata 7.x + Snort 3 Dual-Engine IDS/IPS Telemetry</p>
            </div>
        </div>
        <div class="flex items-center gap-3">
            <button onclick="refreshData()" class="px-4 py-2 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg transition">
                🔄 새로고침
            </button>
            <a href="/docs" target="_blank" class="px-4 py-2 text-xs font-semibold bg-blue-600 hover:bg-blue-500 text-white rounded-lg shadow transition">
                📚 API Docs
            </a>
        </div>
    </header>

    <!-- Main Container -->
    <main class="max-w-7xl mx-auto p-6 space-y-6">
        <!-- KPI Metrics Grid -->
        <section class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div class="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 glow-blue">
                <div class="flex justify-between items-center text-slate-400 text-xs font-medium mb-2">
                    <span>TOTAL ALERTS</span>
                    <span class="text-blue-400">전체 경보</span>
                </div>
                <div id="metric-total" class="text-3xl font-extrabold text-white font-mono">-</div>
                <div class="text-xs text-slate-500 mt-2">Suricata & Snort 집계</div>
            </div>

            <div class="bg-slate-900/60 border border-red-900/40 rounded-2xl p-5 glow-red">
                <div class="flex justify-between items-center text-red-400 text-xs font-medium mb-2">
                    <span>CRITICAL SEVERITY</span>
                    <span class="text-red-400 font-bold">긴급 대응</span>
                </div>
                <div id="metric-critical" class="text-3xl font-extrabold text-red-400 font-mono">-</div>
                <div class="text-xs text-slate-500 mt-2">RCE / C2 / Exploit</div>
            </div>

            <div class="bg-slate-900/60 border border-yellow-900/30 rounded-2xl p-5">
                <div class="flex justify-between items-center text-yellow-400 text-xs font-medium mb-2">
                    <span>HIGH & MEDIUM</span>
                    <span class="text-yellow-400">주의 / 경계</span>
                </div>
                <div id="metric-high-med" class="text-3xl font-extrabold text-yellow-400 font-mono">-</div>
                <div class="text-xs text-slate-500 mt-2">SQLi / XSS / Scan</div>
            </div>

            <div class="bg-slate-900/60 border border-cyan-900/40 rounded-2xl p-5 glow-cyan">
                <div class="flex justify-between items-center text-cyan-400 text-xs font-medium mb-2">
                    <span>CORRELATED INCIDENTS</span>
                    <span class="text-cyan-400 font-bold">복합 침해사고</span>
                </div>
                <div id="metric-incidents" class="text-3xl font-extrabold text-cyan-400 font-mono">-</div>
                <div class="text-xs text-slate-500 mt-2">킬체인 상관분석 탐지</div>
            </div>
        </section>

        <!-- Charts Grid -->
        <section class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div class="bg-slate-900/60 border border-slate-800 rounded-2xl p-5">
                <h3 class="text-sm font-bold text-slate-200 mb-4 flex items-center gap-2">
                    🎯 공격 유형별 분포 (Attack Categories)
                </h3>
                <div class="h-56">
                    <canvas id="categoryChart"></canvas>
                </div>
            </div>

            <div class="bg-slate-900/60 border border-slate-800 rounded-2xl p-5">
                <h3 class="text-sm font-bold text-slate-200 mb-4 flex items-center gap-2">
                    ⚡ 엔진별 탐지 비율 (Engine Detection)
                </h3>
                <div class="h-56">
                    <canvas id="engineChart"></canvas>
                </div>
            </div>

            <div class="bg-slate-900/60 border border-slate-800 rounded-2xl p-5">
                <h3 class="text-sm font-bold text-slate-200 mb-4 flex items-center gap-2">
                    🚨 주요 공격자 IP (Top Attackers)
                </h3>
                <div id="top-attackers-list" class="space-y-3 font-mono text-xs">
                    <p class="text-slate-500">데이터를 불러오는 중...</p>
                </div>
            </div>
        </section>

        <!-- Correlated Incidents Section -->
        <section class="bg-slate-900/70 border border-slate-800 rounded-2xl p-6">
            <div class="flex items-center justify-between mb-4">
                <div>
                    <h3 class="text-base font-bold text-white flex items-center gap-2">
                        🔥 상관분석 사고 사례 (Correlated Incidents)
                    </h3>
                    <p class="text-xs text-slate-400">정찰(Recon)부터 초기 침투, C2 비콘까지 이어진 공격 흐름을 탐지합니다.</p>
                </div>
            </div>
            <div id="incidents-container" class="space-y-3">
                <p class="text-slate-500 text-xs font-mono">침해 사고를 분석 중입니다...</p>
            </div>
        </section>

        <!-- Real-time Alerts Table -->
        <section class="bg-slate-900/70 border border-slate-800 rounded-2xl p-6">
            <div class="flex items-center justify-between mb-4">
                <div>
                    <h3 class="text-base font-bold text-white flex items-center gap-2">
                        📡 실시간 침입 탐지 경보 로그 (Live Alerts Stream)
                    </h3>
                    <p class="text-xs text-slate-400">Suricata EVE JSON 및 Snort 3 로그가 실시간 표준화되어 표시됩니다.</p>
                </div>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-left text-xs font-mono">
                    <thead class="text-slate-400 border-b border-slate-800 bg-slate-800/40">
                        <tr>
                            <th class="py-3 px-3">TIMESTAMP</th>
                            <th class="py-3 px-3">ENGINE</th>
                            <th class="py-3 px-3">SEVERITY</th>
                            <th class="py-3 px-3">SIGNATURE (RULE)</th>
                            <th class="py-3 px-3">SOURCE IP</th>
                            <th class="py-3 px-3">TARGET IP:PORT</th>
                            <th class="py-3 px-3">MITRE</th>
                        </tr>
                    </thead>
                    <tbody id="alerts-tbody" class="divide-y divide-slate-800/60 text-slate-300">
                        <tr>
                            <td colspan="7" class="py-8 text-center text-slate-500">로그를 불러오는 중입니다...</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </section>
    </main>

    <script>
        let catChartInstance = null;
        let engChartInstance = null;

        async function refreshData() {
            try {
                const statsRes = await fetch('/api/stats');
                const stats = await statsRes.json();

                document.getElementById('metric-total').textContent = stats.total_alerts;
                document.getElementById('metric-critical').textContent = stats.critical_alerts;
                document.getElementById('metric-high-med').textContent = (stats.high_alerts + stats.medium_alerts);
                document.getElementById('metric-incidents').textContent = stats.incident_count;

                // Render Top Attackers
                const atkList = document.getElementById('top-attackers-list');
                atkList.innerHTML = stats.top_attackers.length ? stats.top_attackers.map(([ip, cnt]) => `
                    <div class="flex items-center justify-between p-2 rounded-lg bg-slate-800/40 border border-slate-800">
                        <span class="text-red-400 font-semibold">${ip}</span>
                        <span class="px-2 py-0.5 rounded bg-red-500/10 text-red-400 border border-red-500/20">${cnt} alerts</span>
                    </div>
                `).join('') : '<p class="text-slate-500">감지된 공격자 IP가 없습니다.</p>';

                // Render Charts
                renderCharts(stats);

                // Fetch Incidents
                const incRes = await fetch('/api/incidents');
                const incidents = await incRes.json();
                renderIncidents(incidents);

                // Fetch Alerts
                const alertsRes = await fetch('/api/alerts?limit=25');
                const alerts = await alertsRes.json();
                renderAlerts(alerts);
            } catch (e) {
                console.error("Failed to fetch SOC data", e);
            }
        }

        function renderCharts(stats) {
            const catCtx = document.getElementById('categoryChart').getContext('2d');
            const engCtx = document.getElementById('engineChart').getContext('2d');

            const catLabels = Object.keys(stats.category_distribution);
            const catData = Object.values(stats.category_distribution);

            if (catChartInstance) catChartInstance.destroy();
            catChartInstance = new Chart(catCtx, {
                type: 'doughnut',
                data: {
                    labels: catLabels.length ? catLabels : ['대기중'],
                    datasets: [{
                        data: catData.length ? catData : [1],
                        backgroundColor: ['#ef4444', '#f59e0b', '#06b6d4', '#3b82f6', '#8b5cf6', '#10b981'],
                        borderWidth: 0
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8', font: { size: 10 } } } } }
            });

            const engLabels = Object.keys(stats.engine_distribution);
            const engData = Object.values(stats.engine_distribution);

            if (engChartInstance) engChartInstance.destroy();
            engChartInstance = new Chart(engCtx, {
                type: 'pie',
                data: {
                    labels: engLabels.length ? engLabels : ['Suricata', 'Snort'],
                    datasets: [{
                        data: engData.length ? engData : [0, 0],
                        backgroundColor: ['#06b6d4', '#f97316'],
                        borderWidth: 0
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8', font: { size: 10 } } } } }
            });
        }

        function renderIncidents(incidents) {
            const container = document.getElementById('incidents-container');
            if (!incidents.length) {
                container.innerHTML = '<div class="p-4 rounded-xl bg-slate-800/30 border border-slate-800 text-slate-500 text-xs">현재 진행 중인 다단계 복합 침해사고가 없습니다.</div>';
                return;
            }
            container.innerHTML = incidents.map(inc => `
                <div class="p-4 rounded-xl bg-gradient-to-r from-red-950/40 to-slate-900 border border-red-800/40 flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <div class="flex items-center gap-2 mb-1">
                            <span class="px-2 py-0.5 rounded text-xs font-bold bg-red-500/20 text-red-400 border border-red-500/30">${inc.highest_severity}</span>
                            <span class="text-xs text-slate-400 font-mono">${inc.incident_id}</span>
                            <span class="text-xs text-red-300 font-semibold font-mono">Attacker: ${inc.src_ip}</span>
                        </div>
                        <p class="text-xs text-slate-200">${inc.verdict}</p>
                        <div class="flex flex-wrap gap-2 mt-2">
                            ${inc.attack_stages.map(s => `<span class="px-2 py-0.5 rounded bg-slate-800 text-[10px] text-slate-300 border border-slate-700">⚡ ${s}</span>`).join('')}
                        </div>
                    </div>
                    ${inc.playbook_ref ? `<div class="text-xs text-cyan-400 font-semibold bg-cyan-950/40 border border-cyan-800 px-3 py-1.5 rounded-lg whitespace-nowrap">📖 ${inc.playbook_ref}</div>` : ''}
                </div>
            `).join('');
        }

        function renderAlerts(alerts) {
            const tbody = document.getElementById('alerts-tbody');
            if (!alerts.length) {
                tbody.innerHTML = '<tr><td colspan="7" class="py-8 text-center text-slate-500">수신된 경보 로그가 없습니다.</td></tr>';
                return;
            }
            tbody.innerHTML = alerts.map(a => {
                const sevBadge = a.severity === 'CRITICAL' ? 'bg-red-500/20 text-red-400 border-red-500/30' :
                               (a.severity === 'HIGH' ? 'bg-orange-500/20 text-orange-400 border-orange-500/30' :
                               (a.severity === 'MEDIUM' ? 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30' : 'bg-slate-800 text-slate-400 border-slate-700'));
                const engBadge = a.engine === 'SURICATA' ? 'text-cyan-400' : 'text-orange-400';
                const timeStr = a.timestamp.split('T')[1]?.substring(0, 8) || a.timestamp;
                return `
                    <tr class="hover:bg-slate-800/30 transition">
                        <td class="py-2.5 px-3 text-slate-400">${timeStr}</td>
                        <td class="py-2.5 px-3 font-bold ${engBadge}">${a.engine}</td>
                        <td class="py-2.5 px-3"><span class="px-2 py-0.5 rounded text-[10px] font-bold border ${sevBadge}">${a.severity}</span></td>
                        <td class="py-2.5 px-3 text-white font-medium">${a.signature}</td>
                        <td class="py-2.5 px-3 text-red-300">${a.src_ip}:${a.src_port || '-'}</td>
                        <td class="py-2.5 px-3 text-blue-300">${a.dst_ip}:${a.dst_port || '-'}</td>
                        <td class="py-2.5 px-3 text-magenta-400">${a.mitre_technique || '-'}</td>
                    </tr>
                `;
            }).join('');
        }

        // Initialize and auto refresh every 3 seconds
        refreshData();
        setInterval(refreshData, 3000);
    </script>
</body>
</html>
    """
