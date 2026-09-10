import os
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from analyzer.ai.actions.executor import ActionExecutor
from analyzer.ai.approvals.repository import ApprovalRepository
from analyzer.ai.localization import (
    ACTION_TYPE_MAP,
    APPROVAL_STATUS_MAP,
    ATTACK_STAGE_MAP,
    COMMON_UI_KO,
    ENGINE_MAP,
    EXECUTION_MODE_MAP,
    MITRE_TECHNIQUE_MAP,
    POLICY_VERDICT_MAP,
    SEVERITY_MAP,
    SIGNATURE_MAP,
    SecurityEventInterpreter,
)
from analyzer.ai.orchestrator import AIOrchestrator
from analyzer.ai.policy.protected_assets import PROTECTED_IPS, PROTECTED_NETWORKS
from analyzer.ai.schemas.actions import ApprovalStatus, ExecutionMode
from analyzer.alerting.dispatcher import NotificationDispatcher
from analyzer.detection.correlation_engine import CorrelationEngine, Incident
from analyzer.models import NormalizedAlert, Severity
from analyzer.parsers.eve_parser import stream_eve_log
from analyzer.parsers.snort_parser import stream_snort_log

app = FastAPI(title="SOC Lab - Suricata, Snort & AI Copilot Monitoring Center")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

SURICATA_LOG = Path(os.getenv("SURICATA_EVE_PATH", "logs/suricata/eve.json"))
SNORT_LOG = Path(os.getenv("SNORT_ALERT_PATH", "logs/snort/alert_json.txt"))

from analyzer.ai.providers.mock_provider import MockLLMProvider
from analyzer.ai.providers.ollama_provider import OllamaProvider

# Core AI Components
approval_repo = ApprovalRepository()
action_executor = ActionExecutor(mode=ExecutionMode.DRY_RUN)
notification_dispatcher = NotificationDispatcher()

llm_provider_env = os.getenv("LLM_PROVIDER", "mock").lower()
if llm_provider_env in ("ollama", "live"):
    initial_provider = OllamaProvider(
        endpoint=os.getenv("LLM_BASE_URL", "http://127.0.0.1:11434"),
        model=os.getenv("LLM_MODEL", "qwen3.5:9b"),
        timeout_seconds=float(os.getenv("LLM_TIMEOUT", "180.0")),
        enable_fallback=os.getenv("LLM_ENABLE_FALLBACK", "false").lower() in ("true", "1"),
    )
else:
    initial_provider = MockLLMProvider()

orchestrator = AIOrchestrator(provider=initial_provider, approval_repo=approval_repo)
interpreter = SecurityEventInterpreter()
incident_ai_analyses: dict[str, dict[str, Any]] = {}


class ReviewActionRequest(BaseModel):
    reviewer: str = Field(default="soc-analyst", description="Username or ID of reviewing analyst")
    notes: str | None = Field(default=None, description="Analyst review notes or justification")
    auto_execute: bool = Field(default=True, description="Execute action immediately upon approval")


class InterpretRequest(BaseModel):
    target_type: str = Field(default="alert", description="'alert' or 'incident'")
    signature: str | None = None
    category: str | None = None
    severity: str | None = None
    mitre_id: str | None = None
    incident_id: str | None = None


@app.get("/api/health")
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "soc-dashboard",
        "timestamp": datetime.now().isoformat(),
        "eve_log_exists": SURICATA_LOG.exists(),
        "snort_log_exists": SNORT_LOG.exists(),
        "ai_copilot_ready": True,
    }


def get_all_alerts() -> list[NormalizedAlert]:
    alerts: list[NormalizedAlert] = []
    if SURICATA_LOG.exists():
        alerts.extend(stream_eve_log(SURICATA_LOG))
    if SNORT_LOG.exists():
        alerts.extend(stream_snort_log(SNORT_LOG))
    alerts.sort(key=lambda x: x.timestamp, reverse=True)
    return alerts


def get_current_incidents() -> list[Incident]:
    alerts = get_all_alerts()
    engine = CorrelationEngine(window_minutes=60)
    incidents_by_id: dict[str, Incident] = {}
    for a in reversed(alerts):
        inc = engine.process_alert(a)
        if inc:
            incidents_by_id[inc.incident_id] = inc
    return list(incidents_by_id.values())


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

    incidents = get_current_incidents()
    pending_approvals = sum(1 for r in approval_repo.list_all() if r.status == ApprovalStatus.PENDING)

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
        "pending_approvals": pending_approvals,
    }


@app.get("/api/alerts")
def get_alerts(limit: int = 50, severity: str | None = None):
    alerts = get_all_alerts()
    if severity:
        alerts = [a for a in alerts if a.severity.value == severity.upper()]
    return [a.model_dump() for a in alerts[:limit]]


@app.get("/api/incidents")
def get_incidents():
    incidents = get_current_incidents()
    return [i.model_dump() for i in incidents]


# -------------------------------------------------------------
# SOAR Tier-1 Real-Time Alert Dispatcher API Endpoints
# -------------------------------------------------------------

@app.get("/api/notifications/config")
def get_notification_config():
    return notification_dispatcher.get_masked_config()


@app.get("/api/notifications/history")
def get_notification_history(limit: int = 50):
    records = notification_dispatcher.history
    return [r.model_dump() for r in records[-limit:]]


class NotificationTestRequest(BaseModel):
    channel: str | None = Field(default=None, description="Optional channel filter: 'slack', 'discord', 'webhook'")


@app.post("/api/notifications/test")
async def send_test_notification_endpoint(req: NotificationTestRequest | None = None):
    channel = req.channel if req else None
    result = await notification_dispatcher.send_test_notification(channel=channel)
    return result


class ManualDispatchRequest(BaseModel):
    incident_id: str
    force: bool = Field(default=True, description="Bypass cooldown throttling")


@app.post("/api/notifications/dispatch")
async def manual_dispatch_incident(req: ManualDispatchRequest):
    incidents = get_current_incidents()
    target_inc = next((i for i in incidents if i.incident_id == req.incident_id), None)
    if not target_inc:
        raise HTTPException(status_code=404, detail=f"Incident '{req.incident_id}' not found")
    result = await notification_dispatcher.dispatch_incident(target_inc, force=req.force)
    return result


# -------------------------------------------------------------
# AI Copilot, Localization & HITL Approval API Endpoints
# -------------------------------------------------------------

@app.get("/api/localization/dictionary")
def get_localization_dictionary():
    return {
        "common_ui": COMMON_UI_KO,
        "severities": SEVERITY_MAP,
        "engines": ENGINE_MAP,
        "attack_stages": ATTACK_STAGE_MAP,
        "signatures": SIGNATURE_MAP,
        "mitre_techniques": MITRE_TECHNIQUE_MAP,
        "policy_verdicts": POLICY_VERDICT_MAP,
        "approval_statuses": APPROVAL_STATUS_MAP,
        "action_types": ACTION_TYPE_MAP,
        "execution_modes": EXECUTION_MODE_MAP,
    }


@app.post("/api/ai/interpret")
def interpret_event(req: InterpretRequest):
    if req.target_type == "incident" and req.incident_id:
        incidents = get_current_incidents()
        matched = next(
            (i for i in incidents if i.incident_id == req.incident_id or req.incident_id.startswith(f"INC-{i.src_ip}")),
            None
        )
        if not matched:
            return JSONResponse(status_code=404, content={"error": f"Incident '{req.incident_id}' not found."})
        return interpreter.interpret_incident(matched.model_dump())
    elif req.signature:
        return interpreter.interpret_alert(
            signature=req.signature,
            category=req.category or "",
            severity=req.severity or "MEDIUM",
            mitre_id=req.mitre_id
        )
    else:
        return JSONResponse(status_code=400, content={"error": "Either signature or incident_id must be provided."})


@app.get("/api/ai/health")
def get_ai_health():
    records = approval_repo.list_all()
    is_mock = "mock" in orchestrator.provider.provider_name.lower()
    return {
        "status": "healthy",
        "provider": orchestrator.provider.provider_name,
        "provider_model": orchestrator.provider.model_name,
        "is_mock_provider": is_mock,
        "provider_status_label": "모의 분석 결과 (Mock Baseline - 실제 LLM 아님)" if is_mock else "로컬 LLM (Ollama 활성)",
        "tools_available": len(orchestrator.tools.list_tools()),
        "tools": orchestrator.tools.list_tools(),
        "rag_documents_loaded": len(set(c.file_path for c in orchestrator.retriever.store.chunks)),
        "rag_chunks_loaded": len(orchestrator.retriever.store.chunks),
        "approval_stats": {
            "total": len(records),
            "pending": sum(1 for r in records if r.status == ApprovalStatus.PENDING),
            "approved": sum(1 for r in records if r.status == ApprovalStatus.APPROVED),
            "rejected": sum(1 for r in records if r.status == ApprovalStatus.REJECTED),
            "executed": sum(1 for r in records if r.status == ApprovalStatus.EXECUTED),
            "expired": sum(1 for r in records if r.status == ApprovalStatus.EXPIRED),
        },
        "protected_assets_count": len(PROTECTED_IPS) + len(PROTECTED_NETWORKS),
    }


class ProviderSelectRequest(BaseModel):
    provider: str = Field(default="ollama", description="'ollama', 'real' or 'mock'")
    provider_type: str | None = Field(default=None, description="Alias for provider")
    model: str = Field(default="qwen3.5:9b", description="Model name, e.g. qwen3.5:9b or qwen3.5:4b")
    model_name: str | None = Field(default=None, description="Alias for model")
    timeout_seconds: float = Field(default=180.0)


@app.post("/api/ai/provider/select")
def select_ai_provider(req: ProviderSelectRequest):
    prov = (req.provider_type or req.provider or "").lower()
    mod = req.model_name or req.model or "qwen3.5:9b"
    if prov in ("ollama", "live", "real"):
        new_provider = OllamaProvider(
            endpoint=os.getenv("LLM_BASE_URL", "http://127.0.0.1:11434"),
            model=mod,
            timeout_seconds=req.timeout_seconds,
            enable_fallback=False,
        )
        if not new_provider.health_check():
            raise HTTPException(status_code=503, detail=f"Ollama endpoint unreachable or model '{mod}' not installed")
    else:
        new_provider = MockLLMProvider()

    orchestrator.provider = new_provider
    is_mock = "mock" in new_provider.provider_name.lower()
    return {
        "status": "success",
        "provider": new_provider.provider_name,
        "provider_model": new_provider.model_name,
        "is_mock_provider": is_mock,
        "provider_status_label": "모의 분석 결과 (Mock Baseline - 실제 LLM 아님)" if is_mock else f"로컬 LLM ({new_provider.model_name} 활성)",
    }


@app.get("/api/ai/protected-assets")
def get_ai_protected_assets():
    return {
        "protected_ips": PROTECTED_IPS,
        "protected_networks": [str(n) for n in PROTECTED_NETWORKS],
    }


@app.post("/api/incidents/{incident_id}/ai-investigate")
def ai_investigate_incident(incident_id: str):
    incidents = get_current_incidents()
    matched_incident = next(
        (i for i in incidents if i.incident_id == incident_id or incident_id.startswith(f"INC-{i.src_ip}")),
        None
    )

    if not matched_incident:
        return JSONResponse(status_code=404, content={"error": f"Incident '{incident_id}' not found."})

    analysis, approval_records = orchestrator.investigate_incident(matched_incident)
    analysis_dict = analysis.model_dump()
    incident_ai_analyses[incident_id] = analysis_dict

    return {
        "status": "success",
        "incident_id": incident_id,
        "analysis": analysis_dict,
        "approval_requests": [r.model_dump(mode="json") for r in approval_records],
    }


@app.get("/api/incidents/{incident_id}/ai-analysis")
def get_incident_ai_analysis(incident_id: str):
    if incident_id in incident_ai_analyses:
        return incident_ai_analyses[incident_id]
    return JSONResponse(
        status_code=404,
        content={"error": f"No AI analysis found for incident '{incident_id}'. Please trigger investigation first."}
    )


@app.get("/api/action-proposals")
def get_action_proposals(incident_id: str | None = None):
    records = approval_repo.list_all(incident_id=incident_id)
    return [r.model_dump(mode="json") for r in records]


@app.get("/api/action-proposals/{approval_id}")
def get_single_action_proposal(approval_id: str):
    rec = approval_repo.get(approval_id)
    if not rec:
        return JSONResponse(status_code=404, content={"error": f"Approval record '{approval_id}' not found."})
    return rec.model_dump(mode="json")


@app.post("/api/action-proposals/{approval_id}/approve")
def approve_action_proposal(approval_id: str, req: ReviewActionRequest | None = None):
    reviewer = req.reviewer if req else "soc-analyst"
    notes = req.notes if req else None
    auto_execute = req.auto_execute if req else True

    ok, rec_or_err = approval_repo.review_approval(
        approval_id=approval_id,
        decision=ApprovalStatus.APPROVED,
        reviewer=reviewer,
        notes=notes,
    )
    if not ok:
        return JSONResponse(status_code=400, content={"error": rec_or_err})

    exec_output = None
    if auto_execute:
        _, exec_output = action_executor.execute_approved_action(rec_or_err)
        approval_repo._save()

    return {
        "status": "success",
        "approval_id": approval_id,
        "record": rec_or_err.model_dump(mode="json"),
        "execution_output": exec_output,
    }


@app.post("/api/action-proposals/{approval_id}/reject")
def reject_action_proposal(approval_id: str, req: ReviewActionRequest | None = None):
    reviewer = req.reviewer if req else "soc-analyst"
    notes = req.notes if req else None

    ok, rec_or_err = approval_repo.review_approval(
        approval_id=approval_id,
        decision=ApprovalStatus.REJECTED,
        reviewer=reviewer,
        notes=notes,
    )
    if not ok:
        return JSONResponse(status_code=400, content={"error": rec_or_err})

    return {
        "status": "success",
        "approval_id": approval_id,
        "record": rec_or_err.model_dump(mode="json"),
    }


@app.post("/api/action-proposals/{approval_id}/execute")
def execute_action_proposal(approval_id: str):
    rec = approval_repo.get(approval_id)
    if not rec:
        return JSONResponse(status_code=404, content={"error": f"Approval record '{approval_id}' not found."})

    ok, output = action_executor.execute_approved_action(rec)
    if not ok:
        return JSONResponse(status_code=400, content={"error": output})
    approval_repo._save()

    return {
        "status": "success",
        "approval_id": approval_id,
        "output": output,
        "record": rec.model_dump(mode="json"),
    }


# -------------------------------------------------------------
# Frontend Dashboard HTML (Professional SOC Console)
# -------------------------------------------------------------

@app.get("/threat-matrix", response_class=HTMLResponse)
def threat_matrix_page():
    html_path = Path(__file__).parent / "static" / "threat_matrix.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="Threat Matrix visualization file not found")
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@app.get("/", response_class=HTMLResponse)
def index():
    return """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SOC Security Operations Center | Suricata & Snort Lab | AI Copilot</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Pretendard:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif; background-color: #0b0f19; color: #e2e8f0; }
        .font-mono { font-family: 'JetBrains Mono', monospace; }
        /* Custom subtle focus and surface styles */
        .soc-surface { background-color: rgba(15, 23, 42, 0.75); border: 1px solid rgba(30, 41, 59, 0.9); }
        .soc-surface-card { background-color: rgba(15, 23, 42, 0.6); border: 1px solid rgba(51, 65, 85, 0.5); }
        .soc-highlight { border-color: rgba(6, 182, 212, 0.4); }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #0f172a; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: #475569; }
    </style>
</head>
<body class="min-h-screen flex flex-col">
    <!-- Top Enterprise Navigation -->
    <header class="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-40 px-6 py-3.5 flex flex-wrap items-center justify-between gap-4">
        <div class="flex items-center gap-3.5">
            <div class="w-9 h-9 rounded-lg bg-gradient-to-tr from-cyan-600 via-blue-600 to-indigo-700 flex items-center justify-center font-extrabold text-white text-sm shadow-md">
                SOC
            </div>
            <div>
                <div class="flex items-center gap-2.5">
                    <h1 class="text-base font-bold text-white tracking-tight">
                        보안관제 센터 (SOC Operations Center)
                    </h1>
                    <span class="text-[11px] px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-mono font-semibold">
                        LIVE MONITORING
                    </span>
                </div>
                <p class="text-xs text-slate-400 font-mono">
                    Suricata & Snort Lab | Suricata 8.x + Snort 3 Dual-Engine IDS/IPS & Evidence-Grounded AI Copilot
                </p>
            </div>
        </div>

            <!-- Interactive AI Engine Selector & Status Badge -->
            <div class="flex items-center gap-2 bg-slate-800/90 border border-slate-700/80 rounded-lg px-2.5 py-1 text-xs">
                <label for="provider-select" class="text-slate-400 font-medium flex items-center gap-1.5 whitespace-nowrap">
                    <span class="text-indigo-400">🤖</span>
                    <span>AI 엔진:</span>
                </label>
                <select id="provider-select" onchange="switchAiProvider(this.value)" class="bg-slate-900 border border-slate-700 rounded-md px-2 py-1 text-xs font-mono font-semibold text-white focus:outline-none focus:border-cyan-500 cursor-pointer transition" title="분석관 전용 실시간 AI 추론 엔진 전환기">
                    <option value="mock">⚡ 모의 엔진 (Mock Baseline · 0s)</option>
                    <option value="qwen3.5:4b">🚀 Qwen3.5 4B (고속 분석 · ~120s)</option>
                    <option value="qwen3.5:9b" selected>🧠 Qwen3.5 9B (정밀 분석 · ~180s)</option>
                </select>
                <div id="provider-badge" class="text-xs px-2 py-0.5 rounded-md bg-amber-500/10 text-amber-300 border border-amber-500/30 flex items-center gap-1.5 font-mono">
                    <span id="provider-status-dot" class="w-2 h-2 rounded-full bg-amber-400"></span>
                    <span id="provider-status-text">AI 상태 확인 중...</span>
                </div>
            </div>

            <!-- View Mode Segmented Control -->
            <div class="flex items-center rounded-lg bg-slate-800/80 p-0.5 border border-slate-700 text-xs">
                <button onclick="setViewMode('original')" id="btn-mode-orig" class="px-2.5 py-1 rounded-md font-medium transition text-slate-400 hover:text-white">
                    원문 (EN)
                </button>
                <button onclick="setViewMode('korean')" id="btn-mode-ko" class="px-2.5 py-1 rounded-md font-medium transition text-slate-400 hover:text-white">
                    한국어 (KO)
                </button>
                <button onclick="setViewMode('split')" id="btn-mode-split" class="px-2.5 py-1 rounded-md font-medium transition bg-blue-600 text-white font-semibold">
                    나란히 보기 (Split)
                </button>
            </div>

            <button onclick="refreshData()" class="px-3 py-1.5 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg transition flex items-center gap-1.5">
                <span>🔄</span> 새로고침
            </button>
            <a href="/threat-matrix" target="_blank" class="px-3 py-1.5 text-xs font-semibold bg-gradient-to-r from-cyan-950 via-slate-900 to-blue-950 hover:from-cyan-900 hover:to-blue-900 text-cyan-300 border border-cyan-500/40 rounded-lg transition flex items-center gap-1.5 shadow-[0_0_12px_rgba(6,182,212,0.25)]" title="새 창에서 3D 실시간 위협 요격 매트릭스 열기">
                <span>🛡️</span> 3D 위협 요격 매트릭스
            </a>
            <a href="/docs" target="_blank" class="px-3 py-1.5 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-slate-700 rounded-lg transition">
                📚 API 명세
            </a>
        </div>
    </header>

    <!-- Main Workspace Container -->
    <main class="flex-1 max-w-7xl w-full mx-auto p-6 space-y-6">
        <!-- 1. 시각적 중심 허브 (Holographic Shield & AI Core) -->
        <section id="central-shield-hub" class="soc-surface rounded-2xl border border-cyan-500/30 bg-slate-950/90 relative overflow-hidden shadow-[0_0_35px_rgba(6,182,212,0.18)]">
            <!-- Central Hub Header Bar -->
            <div class="px-6 py-3.5 border-b border-slate-800/90 bg-gradient-to-r from-slate-900 via-slate-900/90 to-blue-950/40 flex flex-wrap items-center justify-between gap-4">
                <div class="flex items-center gap-3.5">
                    <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500/20 to-blue-600/20 border border-cyan-400/40 flex items-center justify-center text-xl shadow-[0_0_16px_rgba(6,182,212,0.3)]">
                        🛡️
                    </div>
                    <div>
                        <div class="flex items-center gap-2">
                            <span class="text-[10px] px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-mono font-bold tracking-wider border border-cyan-500/30">
                                VISUAL CENTRAL HUB
                            </span>
                            <h2 class="text-sm font-bold text-white tracking-tight">
                                시각적 중심 허브 // Holographic Shield & AI Core (실시간 위협 요격 매트릭스)
                            </h2>
                        </div>
                        <p class="text-xs text-slate-400 mt-0.5">
                            외부 침투 위협(Coral Red Vector) 실시간 요격·차단 ➔ 중앙 3D 홀로그램 실드 & AI 코어 충격파 분산 ➔ 우측 내부 안전 데이터(Cyan Stream) 정화
                        </p>
                    </div>
                </div>

                <!-- Hub Quick Telemetry & Fullscreen Controls -->
                <div class="flex items-center gap-3">
                    <div class="hidden sm:flex items-center gap-3 text-xs font-mono bg-slate-900/90 border border-slate-800 rounded-lg px-3 py-1.5">
                        <div class="flex items-center gap-1.5">
                            <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                            <span class="text-slate-400">실드 무결성:</span>
                            <span class="text-emerald-400 font-bold">100% OPTIMAL</span>
                        </div>
                        <span class="text-slate-700">|</span>
                        <div class="flex items-center gap-1.5">
                            <span class="text-slate-400">실시간 방어율:</span>
                            <span class="text-cyan-400 font-bold">99.9%</span>
                        </div>
                    </div>
                    <a href="/threat-matrix" target="_blank" class="px-3.5 py-1.5 text-xs font-bold bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 rounded-lg transition-all shadow-[0_0_15px_rgba(6,182,212,0.3)] flex items-center gap-1.5" title="새 탭에서 3D 전술관제 전체화면 열기">
                        <span>전체화면 3D 전술관제</span>
                        <span>↗</span>
                    </a>
                </div>
            </div>

            <!-- Embedded Interactive 3D WebGL Shield Viewport -->
            <div class="relative w-full h-[520px] bg-[#050811] overflow-hidden">
                <iframe id="threat-matrix-iframe" src="/threat-matrix?embed=true" class="w-full h-full border-0 select-none" title="AEGIS AI Holographic Shield Interactive Viewport"></iframe>
            </div>
        </section>

        <!-- KPI Metrics Grid -->
        <section class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            <div class="soc-surface rounded-xl p-4 flex flex-col justify-between">
                <div class="flex justify-between items-center text-xs text-slate-400 font-medium mb-2">
                    <span class="font-mono">TOTAL ALERTS</span>
                    <span class="text-blue-400">전체 경보</span>
                </div>
                <div id="metric-total" class="text-3xl font-bold text-white font-mono">-</div>
                <div class="text-[11px] text-slate-500 mt-2">Suricata & Snort 집계</div>
            </div>

            <div class="soc-surface rounded-xl p-4 border-l-4 border-l-red-500 flex flex-col justify-between">
                <div class="flex justify-between items-center text-xs text-slate-400 font-medium mb-2">
                    <span class="font-mono">CRITICAL SEVERITY</span>
                    <span class="text-red-400 font-semibold">긴급 대응</span>
                </div>
                <div id="metric-critical" class="text-3xl font-bold text-red-400 font-mono">-</div>
                <div class="text-[11px] text-slate-500 mt-2">RCE / C2 역방향 셸</div>
            </div>

            <div class="soc-surface rounded-xl p-4 border-l-4 border-l-yellow-500 flex flex-col justify-between">
                <div class="flex justify-between items-center text-xs text-slate-400 font-medium mb-2">
                    <span class="font-mono">HIGH & MEDIUM</span>
                    <span class="text-yellow-400">주의 / 경계</span>
                </div>
                <div id="metric-high-med" class="text-3xl font-bold text-yellow-400 font-mono">-</div>
                <div class="text-[11px] text-slate-500 mt-2">SQLi / 무차별 대입 / 스캔</div>
            </div>

            <div class="soc-surface rounded-xl p-4 border-l-4 border-l-cyan-500 flex flex-col justify-between">
                <div class="flex justify-between items-center text-xs text-slate-400 font-medium mb-2">
                    <span class="font-mono">CORRELATED INCIDENTS</span>
                    <span class="text-cyan-400 font-semibold">복합 침해사고</span>
                </div>
                <div id="metric-incidents" class="text-3xl font-bold text-cyan-400 font-mono">-</div>
                <div class="text-[11px] text-slate-500 mt-2">다단계 킬체인 상관분석</div>
            </div>

            <div class="soc-surface rounded-xl p-4 border-l-4 border-l-amber-500 flex flex-col justify-between">
                <div class="flex justify-between items-center text-xs text-slate-400 font-medium mb-2">
                    <span class="font-mono">HITL APPROVALS</span>
                    <span class="text-amber-400 font-semibold">승인 대기 조치</span>
                </div>
                <div id="metric-approvals" class="text-3xl font-bold text-amber-400 font-mono">-</div>
                <div class="text-[11px] text-slate-500 mt-2">분석가 검토 필요 (Dry-Run)</div>
            </div>
        </section>

        <!-- Charts & Top Attackers Grid -->
        <section class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div class="soc-surface rounded-xl p-5">
                <h3 class="text-xs font-bold text-slate-200 mb-3 flex items-center justify-between">
                    <span>🎯 공격 유형별 분포 (Attack Categories)</span>
                </h3>
                <div class="h-52">
                    <canvas id="categoryChart"></canvas>
                </div>
            </div>

            <div class="soc-surface rounded-xl p-5">
                <h3 class="text-xs font-bold text-slate-200 mb-3 flex items-center justify-between">
                    <span>⚡ 탐지 엔진 점유율 (Detection Engines)</span>
                </h3>
                <div class="h-52">
                    <canvas id="engineChart"></canvas>
                </div>
            </div>

            <div class="soc-surface rounded-xl p-5 flex flex-col justify-between">
                <h3 class="text-xs font-bold text-slate-200 mb-3 flex items-center justify-between">
                    <span>🚨 주요 공격자 IP (Top Threat Actors)</span>
                </h3>
                <div id="top-attackers-list" class="space-y-2.5 font-mono text-xs flex-1">
                    <p class="text-slate-500 text-[11px]">데이터를 불러오는 중...</p>
                </div>
            </div>
        </section>

        <!-- Correlated Incidents Section & Investigation -->
        <section class="soc-surface rounded-xl p-6 space-y-4">
            <div class="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-slate-800 pb-3">
                <div>
                    <h2 class="text-sm font-bold text-white flex items-center gap-2">
                        <span>🔥 다단계 복합 침해사고 (Correlated Incidents)</span>
                        <span class="text-[10px] px-2 py-0.5 rounded bg-red-500/10 text-red-400 border border-red-500/20 font-normal">
                            우선 대응 필요
                        </span>
                    </h2>
                    <p class="text-xs text-slate-400 mt-0.5">
                        정찰(Recon)부터 초기 침투, C2 비콘 수립까지 이어진 킬체인 공격을 단계별로 시각화하고 AI 정밀 분석을 제공합니다.
                    </p>
                </div>
            </div>
            <div id="incidents-container" class="space-y-4">
                <p class="text-slate-500 text-xs font-mono">침해 사고를 분석 중입니다...</p>
            </div>
        </section>

        <!-- HITL Containment Proposals Queue (Human Approval Gate) -->
        <section class="soc-surface rounded-xl p-6 space-y-4">
            <div class="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-slate-800 pb-3">
                <div>
                    <h2 class="text-sm font-bold text-amber-300 flex items-center gap-2">
                        <span>🛡️ AI 대응 조치 검토 및 인간 승인 (HITL Approval Gate)</span>
                    </h2>
                    <p class="text-xs text-slate-400 mt-0.5">
                        AI 권고 조치는 게이트웨이 및 SIEM 보호 정책 검증을 거치며, 분석가의 승인 없이는 결코 단독 적용되지 않습니다.
                    </p>
                </div>
                <div class="flex items-center gap-2">
                    <span class="text-[11px] px-2.5 py-1 rounded bg-slate-800 text-slate-300 border border-slate-700 font-mono">
                        기본 실행 모드: <span class="text-cyan-400 font-semibold">모의 실행 (Dry-Run / 호스트 불변)</span>
                    </span>
                </div>
            </div>

            <div class="overflow-x-auto">
                <table class="w-full text-left text-xs font-mono">
                    <thead class="text-slate-400 border-b border-slate-800 bg-slate-800/40">
                        <tr>
                            <th class="py-2.5 px-3">승인 번호 (ID)</th>
                            <th class="py-2.5 px-3">사고 식별자</th>
                            <th class="py-2.5 px-3">제안 조치 및 대상</th>
                            <th class="py-2.5 px-3">정책 검증 상태</th>
                            <th class="py-2.5 px-3">규칙 구문 프리뷰</th>
                            <th class="py-2.5 px-3">승인 상태</th>
                            <th class="py-2.5 px-3 text-center">분석가 의사결정</th>
                        </tr>
                    </thead>
                    <tbody id="approvals-tbody" class="divide-y divide-slate-800/60 text-slate-300">
                        <tr>
                            <td colspan="7" class="py-6 text-center text-slate-500">대응 조치 제안 내역을 불러오는 중입니다...</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </section>

        <!-- Real-time Alerts Stream Section -->
        <section class="soc-surface rounded-xl p-6 space-y-4">
            <div class="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-slate-800 pb-3">
                <div>
                    <h2 class="text-sm font-bold text-white flex items-center gap-2">
                        <span>📡 실시간 침입 탐지 경보 스트림 (Live Alert Telemetry)</span>
                    </h2>
                    <p class="text-xs text-slate-400 mt-0.5">
                        Suricata 8.x EVE JSON 및 Snort 3 로그가 실시간 표준화되어 표시됩니다. 각 경보의 한국어 해석과 원본 패킷 증적을 열람할 수 있습니다.
                    </p>
                </div>
                <!-- Table Search & Severity Filter -->
                <div class="flex items-center gap-2 flex-wrap">
                    <input type="text" id="alert-search-input" onkeyup="filterAlerts()" placeholder="IP, 규칙명, SID 검색..." class="px-3 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-mono w-48">
                    <select id="alert-severity-select" onchange="filterAlerts()" class="px-2.5 py-1.5 text-xs bg-slate-900 border border-slate-700 rounded-lg text-slate-300 focus:outline-none focus:border-cyan-500 font-mono">
                        <option value="ALL">모든 위험도 (All)</option>
                        <option value="CRITICAL">심각 (Critical)</option>
                        <option value="HIGH">높음 (High)</option>
                        <option value="MEDIUM">보통 (Medium)</option>
                        <option value="LOW">낮음 (Low)</option>
                    </select>
                </div>
            </div>

            <div class="overflow-x-auto">
                <table class="w-full text-left text-xs font-mono">
                    <thead class="text-slate-400 border-b border-slate-800 bg-slate-800/40">
                        <tr>
                            <th class="py-2.5 px-3">발생 시각 (KST / UTC)</th>
                            <th class="py-2.5 px-3">엔진</th>
                            <th class="py-2.5 px-3">위험도</th>
                            <th class="py-2.5 px-3">탐지 규칙 (시그니처)</th>
                            <th class="py-2.5 px-3">출발지 (Attacker)</th>
                            <th class="py-2.5 px-3">목적지 (Target)</th>
                            <th class="py-2.5 px-3">MITRE 기법</th>
                            <th class="py-2.5 px-3 text-center">조치 / 해석</th>
                        </tr>
                    </thead>
                    <tbody id="alerts-tbody" class="divide-y divide-slate-800/60 text-slate-300">
                        <tr>
                            <td colspan="8" class="py-8 text-center text-slate-500">로그를 불러오는 중입니다...</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </section>
    </main>

    <!-- General Modal for Details & Interpretation -->
    <div id="generalModal" class="hidden fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div class="bg-slate-900 border border-slate-700 rounded-2xl max-w-2xl w-full p-6 space-y-4 shadow-2xl">
            <div class="flex justify-between items-center border-b border-slate-800 pb-3">
                <h4 id="modalTitle" class="text-sm font-bold text-white font-mono">Modal Title</h4>
                <button onclick="closeModal()" class="text-slate-400 hover:text-white p-1">✕</button>
            </div>
            <div id="modalBody" class="text-xs text-slate-300 max-h-96 overflow-y-auto space-y-3"></div>
            <div class="flex justify-end pt-2 border-t border-slate-800">
                <button onclick="closeModal()" class="px-4 py-2 text-xs bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition font-medium">닫기</button>
            </div>
        </div>
    </div>

    <!-- AI Investigation Progress & Elapsed Timer Modal -->
    <div id="investigationModal" class="hidden fixed inset-0 bg-black/85 backdrop-blur-md z-50 flex items-center justify-center p-4">
        <div class="bg-slate-900 border border-slate-700/80 rounded-2xl max-w-xl w-full p-6 space-y-5 shadow-2xl relative overflow-hidden">
            <!-- Ambient Glow -->
            <div class="absolute -right-16 -top-16 w-48 h-48 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none"></div>
            <div class="absolute -left-16 -bottom-16 w-48 h-48 bg-cyan-600/10 rounded-full blur-3xl pointer-events-none"></div>

            <!-- Modal Header -->
            <div class="flex items-start justify-between border-b border-slate-800 pb-3">
                <div>
                    <div class="flex items-center gap-2">
                        <span class="w-2.5 h-2.5 rounded-full bg-indigo-400 animate-ping"></span>
                        <h3 class="text-sm font-bold text-white flex items-center gap-1.5 font-mono">
                            <span>🤖 AI 심층 침해사고 조사 파이프라인</span>
                        </h3>
                    </div>
                    <p id="inv-modal-subtitle" class="text-xs text-slate-400 mt-1 font-mono">
                        사고 ID: <span id="inv-modal-inc-id" class="text-cyan-400 font-semibold">-</span> | 
                        공격자: <span id="inv-modal-src-ip" class="text-red-400 font-semibold">-</span>
                    </p>
                </div>
                <button onclick="minimizeInvestigationModal()" class="text-slate-400 hover:text-white text-xs font-mono bg-slate-800 hover:bg-slate-700 rounded-lg px-2.5 py-1 transition flex items-center gap-1" title="백그라운드 진행으로 전환">
                    <span>▼</span> 최소화
                </button>
            </div>

            <!-- Stopwatch & Active Model Info Card -->
            <div class="bg-slate-950/80 p-4 rounded-xl border border-slate-800/90 space-y-3">
                <div class="flex items-center justify-between">
                    <div>
                        <span class="text-[11px] text-slate-400 block font-medium">경과 시간 (Elapsed Timer)</span>
                        <div id="inv-timer-display" class="text-3xl font-extrabold text-cyan-400 font-mono tracking-wider">
                            00:00.0
                        </div>
                    </div>
                    <div class="text-right">
                        <span class="text-[11px] text-slate-400 block font-medium">활성 추론 엔진</span>
                        <div id="inv-model-display" class="text-xs font-mono font-bold text-purple-300 bg-purple-950/40 border border-purple-800/50 px-2.5 py-1 rounded-md mt-0.5">
                            Qwen3.5 9B
                        </div>
                    </div>
                </div>

                <!-- Animated Progress Bar -->
                <div class="space-y-1">
                    <div class="flex justify-between text-[11px] font-mono text-slate-400">
                        <span id="inv-progress-label">증적 수집 및 도구 실행 중...</span>
                        <span id="inv-progress-pct" class="text-cyan-400 font-bold">15%</span>
                    </div>
                    <div class="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                        <div id="inv-progress-bar" class="bg-gradient-to-r from-cyan-500 via-blue-500 to-indigo-600 h-2 rounded-full transition-all duration-300 ease-out" style="width: 15%"></div>
                    </div>
                </div>

                <div class="text-[11px] text-slate-500 font-mono flex items-center gap-1.5 pt-1 border-t border-slate-900">
                    <span>⚡</span>
                    <span id="inv-hw-hint">Intel Xeon 4C/8T AVX2 CPU 전용 연산 (Strict Localhost 127.0.0.1:11434)</span>
                </div>
            </div>

            <!-- Stepper: 4-Stage Visual Pipeline -->
            <div class="space-y-2.5">
                <div class="text-xs font-semibold text-slate-300 flex items-center gap-1">
                    <span>📋</span> 단계별 분석 파이프라인 상태:
                </div>
                
                <div class="space-y-2 text-xs font-mono">
                    <!-- Step 1 -->
                    <div id="inv-step-1" class="p-2.5 rounded-lg bg-slate-800/80 border border-cyan-500/80 flex items-center justify-between transition shadow-md shadow-cyan-950/40">
                        <div class="flex items-center gap-2">
                            <span id="inv-step-1-icon" class="text-cyan-400 animate-spin">🌀</span>
                            <div>
                                <div class="font-semibold text-white">1단계. 보안 증적 수집 및 읽기 도구 실행</div>
                                <div id="inv-step-1-desc" class="text-[11px] text-slate-400">Suricata EVE 로그, Snort 경보 및 Threat Intel 평판 조회</div>
                            </div>
                        </div>
                        <span id="inv-step-1-badge" class="text-[10px] px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-bold animate-pulse">진행 중</span>
                    </div>

                    <!-- Step 2 -->
                    <div id="inv-step-2" class="p-2.5 rounded-lg bg-slate-950/40 border border-slate-800 flex items-center justify-between transition opacity-60">
                        <div class="flex items-center gap-2">
                            <span id="inv-step-2-icon" class="text-slate-500">⏳</span>
                            <div>
                                <div class="font-semibold text-slate-300">2단계. RAG 보안 플레이북 검색 및 컨텍스트 바운딩</div>
                                <div id="inv-step-2-desc" class="text-[11px] text-slate-500">MITRE ATT&CK v19.2 매핑 및 침해대응 플레이북 800자 청크 추출</div>
                            </div>
                        </div>
                        <span id="inv-step-2-badge" class="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-bold">대기 중</span>
                    </div>

                    <!-- Step 3 -->
                    <div id="inv-step-3" class="p-2.5 rounded-lg bg-slate-950/40 border border-slate-800 flex items-center justify-between transition opacity-60">
                        <div class="flex items-center gap-2">
                            <span id="inv-step-3-icon" class="text-slate-500">⏳</span>
                            <div>
                                <div class="font-semibold text-slate-300">3단계. 로컬 LLM 인과관계 추론 및 구조화 생성</div>
                                <div id="inv-step-3-desc" class="text-[11px] text-slate-500">프롬프트 토큰 평가 및 Structured JSON (Pydantic) 생성</div>
                            </div>
                        </div>
                        <span id="inv-step-3-badge" class="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-bold">대기 중</span>
                    </div>

                    <!-- Step 4 -->
                    <div id="inv-step-4" class="p-2.5 rounded-lg bg-slate-950/40 border border-slate-800 flex items-center justify-between transition opacity-60">
                        <div class="flex items-center gap-2">
                            <span id="inv-step-4-icon" class="text-slate-500">⏳</span>
                            <div>
                                <div class="font-semibold text-slate-300">4단계. 독립 정책 검증(PolicyValidator) 및 인간 승인 큐 등록</div>
                                <div id="inv-step-4-desc" class="text-[11px] text-slate-500">차단 대상 IP 정책 검증 및 Dry-Run 모의 실행 승인 레코드 생성</div>
                            </div>
                        </div>
                        <span id="inv-step-4-badge" class="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-bold">대기 중</span>
                    </div>
                </div>
            </div>

            <!-- Modal Footer Actions -->
            <div id="inv-modal-footer" class="flex items-center justify-between pt-2 border-t border-slate-800">
                <span class="text-[11px] text-slate-500 font-mono">
                    * 창을 최소화해도 백그라운드 조사는 중단 없이 계속 진행됩니다.
                </span>
                <div class="flex items-center gap-2">
                    <button onclick="minimizeInvestigationModal()" class="px-3.5 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition font-medium">
                        백그라운드로 계속
                    </button>
                    <button id="inv-btn-view-result" onclick="closeInvestigationModalAndScroll()" class="hidden px-4 py-1.5 text-xs bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-lg transition shadow flex items-center gap-1.5">
                        <span>✅</span> 결과 확인하기
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- Floating Minimized Pill when modal is minimized -->
    <div id="inv-minimized-pill" class="hidden fixed bottom-6 right-6 z-50 bg-slate-900/95 border border-indigo-500/50 shadow-2xl rounded-xl p-3.5 flex items-center gap-3.5 backdrop-blur cursor-pointer hover:border-indigo-400 transition" onclick="restoreInvestigationModal()">
        <span class="w-2.5 h-2.5 rounded-full bg-indigo-400 animate-ping"></span>
        <div class="font-mono text-xs">
            <div class="font-bold text-white flex items-center gap-2">
                <span>🤖 AI 조사 진행 중</span>
                <span id="pill-timer" class="text-cyan-400 font-bold">00:00.0</span>
            </div>
            <div id="pill-status" class="text-[11px] text-slate-400 mt-0.5">로컬 LLM 추론 연산 중...</div>
        </div>
        <span class="text-xs text-slate-300 bg-slate-800 hover:bg-slate-700 px-2.5 py-1 rounded-md border border-slate-700">열기 ▲</span>
    </div>

    <!-- Toast Notification Container -->
    <div id="toast-container" class="fixed top-16 right-6 z-50 space-y-2 pointer-events-none"></div>

    <script>
        let currentViewMode = localStorage.getItem('soc_view_mode') || 'split';
        let localizationDict = null;
        let catChartInstance = null;
        let engChartInstance = null;
        let rawAlertsCache = [];
        let rawIncidentsCache = [];
        let invTimerInterval = null;
        let invStartTime = 0;
        let currentInvestigatingId = null;
        let isSwitchingProvider = false;

        function showToastNotification(message, type = 'info') {
            const container = document.getElementById('toast-container');
            if (!container) return;
            const toast = document.createElement('div');
            
            const borderBg = type === 'success' ? 'border-emerald-500/80 bg-slate-900/95 text-emerald-300' :
                            (type === 'error' ? 'border-red-500/80 bg-slate-900/95 text-red-300' : 'border-cyan-500/80 bg-slate-900/95 text-cyan-300');
            const icon = type === 'success' ? '✅' : (type === 'error' ? '❌' : 'ℹ️');

            toast.className = `p-3 rounded-xl border ${borderBg} shadow-2xl flex items-center gap-2.5 text-xs font-mono backdrop-blur pointer-events-auto transform transition-all duration-300 ease-out translate-y-2 opacity-0`;
            toast.innerHTML = `<span>${icon}</span><span class="flex-1">${escapeHTML(message)}</span>`;

            container.appendChild(toast);
            requestAnimationFrame(() => {
                toast.classList.remove('translate-y-2', 'opacity-0');
            });

            setTimeout(() => {
                toast.classList.add('opacity-0', '-translate-y-2');
                setTimeout(() => toast.remove(), 300);
            }, 4000);
        }

        async function switchAiProvider(selectedKey) {
            if (isSwitchingProvider) return;
            isSwitchingProvider = true;

            const provSelect = document.getElementById('provider-select');
            const provDot = document.getElementById('provider-status-dot');
            const provText = document.getElementById('provider-status-text');

            if (provSelect) provSelect.disabled = true;
            if (provText) provText.textContent = '엔진 전환 중...';
            if (provDot) provDot.className = 'w-2 h-2 rounded-full bg-amber-400 animate-spin';

            let payload = {};
            if (selectedKey === 'mock') {
                payload = { provider: 'mock' };
            } else {
                payload = { provider: 'ollama', model: selectedKey };
            }

            try {
                const res = await fetch('/api/ai/provider/select', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await res.json();
                if (data.status === 'success') {
                    showToastNotification(`AI 엔진이 '${data.provider_model || data.provider}'(으)로 즉각 전환되었습니다.`, 'success');
                } else {
                    showToastNotification(`엔진 전환 실패: ${data.detail || data.error}`, 'error');
                }
            } catch(e) {
                console.error("Provider switch failed", e);
                showToastNotification("엔진 전환 중 네트워크 오류 발생", 'error');
            } finally {
                if (provSelect) provSelect.disabled = false;
                isSwitchingProvider = false;
                await refreshData();
            }
        }

        function updateInvStepState(stepNum, state, descText = null) {
            const stepEl = document.getElementById(`inv-step-${stepNum}`);
            const iconEl = document.getElementById(`inv-step-${stepNum}-icon`);
            const badgeEl = document.getElementById(`inv-step-${stepNum}-badge`);
            const descEl = document.getElementById(`inv-step-${stepNum}-desc`);

            if (!stepEl || !iconEl || !badgeEl) return;
            if (descText && descEl) descEl.textContent = descText;

            if (state === 'active') {
                stepEl.className = "p-2.5 rounded-lg bg-slate-800/80 border border-cyan-500/80 flex items-center justify-between transition shadow-md shadow-cyan-950/40";
                iconEl.textContent = "🌀";
                iconEl.className = "text-cyan-400 animate-spin";
                badgeEl.className = "text-[10px] px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-bold animate-pulse";
                badgeEl.textContent = "진행 중";
            } else if (state === 'done') {
                stepEl.className = "p-2.5 rounded-lg bg-slate-900/90 border border-emerald-500/40 flex items-center justify-between transition";
                iconEl.textContent = "✅";
                iconEl.className = "text-emerald-400";
                badgeEl.className = "text-[10px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-bold";
                badgeEl.textContent = "완료";
            } else if (state === 'error') {
                stepEl.className = "p-2.5 rounded-lg bg-red-950/40 border border-red-500/50 flex items-center justify-between transition";
                iconEl.textContent = "❌";
                iconEl.className = "text-red-400";
                badgeEl.className = "text-[10px] px-2 py-0.5 rounded bg-red-500/20 text-red-300 border border-red-500/40 font-bold";
                badgeEl.textContent = "오류";
            } else {
                stepEl.className = "p-2.5 rounded-lg bg-slate-950/40 border border-slate-800 flex items-center justify-between transition opacity-60";
                iconEl.textContent = "⏳";
                iconEl.className = "text-slate-500";
                badgeEl.className = "text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-bold";
                badgeEl.textContent = "대기 중";
            }
        }

        function formatTimerDisplay(ms) {
            const totalSec = ms / 1000;
            const m = Math.floor(totalSec / 60);
            const s = Math.floor(totalSec % 60);
            const d = Math.floor((ms % 1000) / 100);
            return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}.${d}`;
        }

        function minimizeInvestigationModal() {
            document.getElementById('investigationModal').classList.add('hidden');
            document.getElementById('inv-minimized-pill').classList.remove('hidden');
        }

        function restoreInvestigationModal() {
            document.getElementById('inv-minimized-pill').classList.add('hidden');
            document.getElementById('investigationModal').classList.remove('hidden');
        }

        function closeInvestigationModalAndScroll() {
            document.getElementById('investigationModal').classList.add('hidden');
            document.getElementById('inv-minimized-pill').classList.add('hidden');
            if (currentInvestigatingId) {
                const target = document.getElementById(`ai-res-${currentInvestigatingId}`);
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    target.classList.add('ring-2', 'ring-cyan-400');
                    setTimeout(() => target.classList.remove('ring-2', 'ring-cyan-400'), 2500);
                }
            }
        }

        // Safe HTML text escaper to prevent XSS
        function escapeHTML(str) {
            if (!str) return '';
            return String(str)
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#039;');
        }

        // Format ISO UTC to KST
        function formatKST(isoStr) {
            if (!isoStr) return '-';
            try {
                const date = new Date(isoStr);
                return date.toLocaleString('ko-KR', { timeZone: 'Asia/Seoul', hour12: false });
            } catch(e) {
                return isoStr;
            }
        }

        function setViewMode(mode) {
            currentViewMode = mode;
            localStorage.setItem('soc_view_mode', mode);

            // Update button styles
            ['orig', 'ko', 'split'].forEach(m => {
                const btn = document.getElementById(`btn-mode-${m}`);
                if (!btn) return;
                if ((m === 'orig' && mode === 'original') || (m === 'ko' && mode === 'korean') || (m === 'split' && mode === 'split')) {
                    btn.className = "px-2.5 py-1 rounded-md font-semibold transition bg-blue-600 text-white shadow";
                } else {
                    btn.className = "px-2.5 py-1 rounded-md font-medium transition text-slate-400 hover:text-white";
                }
            });

            // Re-render components
            renderIncidents(rawIncidentsCache);
            filterAlerts();
        }

        async function fetchLocalizationDict() {
            try {
                const res = await fetch('/api/localization/dictionary');
                localizationDict = await res.json();
            } catch(e) {
                console.error("Failed to load localization dictionary", e);
            }
        }

        function getLocalizedSignature(sig) {
            if (!sig) return '-';
            if (!localizationDict || !localizationDict.signatures || !localizationDict.signatures[sig]) {
                return escapeHTML(sig);
            }
            const info = localizationDict.signatures[sig];
            const koTitle = info.ko_title;

            if (currentViewMode === 'original') {
                return escapeHTML(sig);
            } else if (currentViewMode === 'korean') {
                return `<span class="text-white font-medium">${escapeHTML(koTitle)}</span>`;
            } else {
                // Split View
                return `<div class="space-y-0.5">
                    <span class="text-white font-medium">${escapeHTML(koTitle)}</span>
                    <span class="block text-[11px] text-slate-400 font-mono">↳ ${escapeHTML(sig)}</span>
                </div>`;
            }
        }

        function getLocalizedStage(stage) {
            if (!stage) return '-';
            const stInfo = localizationDict?.attack_stages?.[stage];
            if (!stInfo) return escapeHTML(stage);

            if (currentViewMode === 'original') return escapeHTML(stInfo.en);
            if (currentViewMode === 'korean') return escapeHTML(stInfo.ko);
            return `${escapeHTML(stInfo.short)}`;
        }

        function getLocalizedSeverity(sev) {
            const sevInfo = localizationDict?.severities?.[sev];
            const badgeClass = sevInfo ? sevInfo.badge_class : 'bg-slate-800 text-slate-400';
            const koText = sevInfo ? sevInfo.ko : sev;
            const label = currentViewMode === 'original' ? sev : `${koText} (${sev})`;
            return `<span class="px-2 py-0.5 rounded text-[10px] font-bold border ${badgeClass}">${label}</span>`;
        }

        function getLocalizedPolicyVerdict(verdict) {
            const vInfo = localizationDict?.policy_verdicts?.[verdict];
            if (vInfo) {
                const isAllow = verdict === 'ALLOWED';
                const icon = isAllow ? '✅' : '🛑';
                return `<span class="px-2 py-0.5 rounded text-[10px] font-bold border ${vInfo.badge_class}">${icon} ${currentViewMode === 'original' ? verdict : vInfo.ko}</span>`;
            }
            return `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-400">${escapeHTML(verdict)}</span>`;
        }

        async function refreshData() {
            try {
                if (!localizationDict) await fetchLocalizationDict();

                // 1. Fetch AI Health & Provider status
                const aiHealthRes = await fetch('/api/ai/health');
                const aiHealth = await aiHealthRes.json();
                const provSelect = document.getElementById('provider-select');
                const provBadge = document.getElementById('provider-badge');
                const provDot = document.getElementById('provider-status-dot');
                const provText = document.getElementById('provider-status-text');

                if (!isSwitchingProvider && provSelect) {
                    if (aiHealth.is_mock_provider) {
                        provSelect.value = 'mock';
                    } else if (aiHealth.provider_model?.includes('4b')) {
                        provSelect.value = 'qwen3.5:4b';
                    } else if (aiHealth.provider_model?.includes('9b')) {
                        provSelect.value = 'qwen3.5:9b';
                    }
                }

                if (aiHealth.is_mock_provider) {
                    if (provBadge) provBadge.className = "text-xs px-2.5 py-1 rounded-md bg-amber-500/10 text-amber-300 border border-amber-500/30 flex items-center gap-1.5 font-mono";
                    if (provDot) provDot.className = "w-2 h-2 rounded-full bg-amber-400";
                    if (provText) provText.textContent = `모의 분석 기준선 (Mock Baseline - 실제 LLM 아님)`;
                } else if (aiHealth.provider_model?.includes('4b')) {
                    if (provBadge) provBadge.className = "text-xs px-2.5 py-1 rounded-md bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 flex items-center gap-1.5 font-mono";
                    if (provDot) provDot.className = "w-2 h-2 rounded-full bg-cyan-400 animate-pulse";
                    if (provText) provText.textContent = `로컬 LLM 연동 (${aiHealth.provider_model} 고속 활성)`;
                } else {
                    if (provBadge) provBadge.className = "text-xs px-2.5 py-1 rounded-md bg-purple-500/10 text-purple-300 border border-purple-500/30 flex items-center gap-1.5 font-mono";
                    if (provDot) provDot.className = "w-2 h-2 rounded-full bg-purple-400 animate-pulse";
                    if (provText) provText.textContent = `로컬 LLM 연동 (${aiHealth.provider_model} 정밀 활성)`;
                }

                // 2. Fetch Stats
                const statsRes = await fetch('/api/stats');
                const stats = await statsRes.json();
                document.getElementById('metric-total').textContent = stats.total_alerts.toLocaleString();
                document.getElementById('metric-critical').textContent = stats.critical_alerts.toLocaleString();
                document.getElementById('metric-high-med').textContent = (stats.high_alerts + stats.medium_alerts).toLocaleString();
                document.getElementById('metric-incidents').textContent = stats.incident_count.toLocaleString();
                document.getElementById('metric-approvals').textContent = (stats.pending_approvals ?? 0).toLocaleString();

                // Top Attackers
                const atkList = document.getElementById('top-attackers-list');
                atkList.innerHTML = stats.top_attackers.length ? stats.top_attackers.map(([ip, cnt]) => `
                    <div class="flex items-center justify-between p-2 rounded-lg bg-slate-800/40 border border-slate-800">
                        <span class="text-red-400 font-semibold font-mono flex items-center gap-1.5">
                            <span class="w-1.5 h-1.5 rounded-full bg-red-400"></span>
                            ${escapeHTML(ip)}
                        </span>
                        <span class="px-2 py-0.5 rounded bg-red-500/10 text-red-400 border border-red-500/20 text-[11px] font-mono font-semibold">${cnt} alerts</span>
                    </div>
                `).join('') : '<p class="text-slate-500 text-xs">감지된 공격자 IP가 없습니다.</p>';

                // Render Charts
                renderCharts(stats);

                // 3. Fetch Incidents
                const incRes = await fetch('/api/incidents');
                rawIncidentsCache = await incRes.json();
                renderIncidents(rawIncidentsCache);

                // 4. Fetch Action Proposals
                const propRes = await fetch('/api/action-proposals');
                const proposals = await propRes.json();
                renderProposals(proposals);

                // 5. Fetch Alerts
                const alertsRes = await fetch('/api/alerts?limit=50');
                rawAlertsCache = await alertsRes.json();
                filterAlerts();

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
            if (!incidents || !incidents.length) {
                container.innerHTML = '<div class="p-6 rounded-xl bg-slate-800/30 border border-slate-800 text-slate-500 text-xs text-center font-mono">현재 진행 중인 다단계 복합 침해사고가 없습니다.</div>';
                return;
            }

            container.innerHTML = incidents.map(inc => {
                const sevBadge = getLocalizedSeverity(inc.highest_severity);
                const startTimeKST = formatKST(inc.start_time);
                const lastSeenKST = formatKST(inc.last_seen);

                // Build Attack Stages Timeline
                const stagesHtml = inc.attack_stages.map((stage, idx) => {
                    const stText = getLocalizedStage(stage);
                    const isC2 = stage.includes('3.') || stage.includes('C2');
                    const isExploit = stage.includes('2.');
                    const stageColor = isC2 ? 'text-red-400 border-red-500/40 bg-red-950/30' :
                                      (isExploit ? 'text-orange-400 border-orange-500/40 bg-orange-950/30' : 'text-cyan-400 border-cyan-500/40 bg-cyan-950/30');

                    return `
                        <div class="flex items-center gap-1.5">
                            <div class="px-2.5 py-1 rounded text-[11px] font-semibold border ${stageColor} flex items-center gap-1">
                                <span>⚡</span>
                                <span>${escapeHTML(stText)}</span>
                            </div>
                            ${idx < inc.attack_stages.length - 1 ? '<span class="text-slate-600 text-xs">➔</span>' : ''}
                        </div>
                    `;
                }).join('');

                return `
                    <div class="soc-surface-card rounded-xl p-5 space-y-3.5 hover:border-slate-700 transition">
                        <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
                            <div>
                                <div class="flex items-center gap-2 mb-1 flex-wrap">
                                    ${sevBadge}
                                    <span class="text-xs text-slate-300 font-mono font-semibold">${escapeHTML(inc.incident_id)}</span>
                                    <span class="text-xs text-red-400 font-mono font-bold">공격자 IP: ${escapeHTML(inc.src_ip)}</span>
                                    <span class="text-xs text-slate-400 font-mono">대상: ${escapeHTML(inc.target_ips.join(', '))}</span>
                                </div>
                                <p class="text-xs text-slate-300 mt-1">
                                    ${currentViewMode === 'korean' ? '다단계 킬체인 공격 흐름이 상관분석에 의해 입증되었습니다.' : escapeHTML(inc.verdict)}
                                </p>
                                <div class="text-[11px] text-slate-500 font-mono mt-1">
                                    최초 탐지: ${startTimeKST} | 최근 활동: ${lastSeenKST} (총 ${inc.alerts.length}개 연관 경보)
                                </div>
                            </div>
                            <div class="flex items-center gap-2 flex-wrap">
                                <button onclick="interpretIncident('${inc.incident_id}')" class="px-3 py-1.5 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-cyan-800/60 rounded-lg transition flex items-center gap-1.5 shadow">
                                    <span>📖</span> 한국어 해석
                                </button>
                                <button onclick="investigateIncident('${inc.incident_id}')" id="btn-investigate-${inc.incident_id}" class="px-3.5 py-1.5 text-xs font-bold bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg shadow transition flex items-center gap-1.5">
                                    <span>🤖</span> AI 심층 조사
                                </button>
                            </div>
                        </div>

                        <!-- Visual Timeline -->
                        <div class="bg-slate-950/40 p-3 rounded-lg border border-slate-800/60 flex items-center gap-2 overflow-x-auto">
                            <span class="text-[11px] text-slate-400 font-medium whitespace-nowrap mr-1">공격 진행 단계:</span>
                            <div class="flex items-center gap-2">
                                ${stagesHtml}
                            </div>
                        </div>

                        <!-- AI Investigation Expansion Container -->
                        <div id="ai-res-${inc.incident_id}" class="hidden pt-2 border-t border-slate-800"></div>
                    </div>
                `;
            }).join('');
        }

        async function interpretIncident(incidentId) {
            try {
                const res = await fetch('/api/ai/interpret', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ target_type: 'incident', incident_id: incidentId })
                });
                const data = await res.json();
                openInterpretationModal("사고 분석 한국어 해석", data);
            } catch(e) {
                console.error("Interpretation failed", e);
                alert("한국어 해석 조회 중 오류가 발생했습니다.");
            }
        }

        async function interpretAlert(signature, category, severity, mitreId) {
            try {
                const res = await fetch('/api/ai/interpret', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        target_type: 'alert',
                        signature: signature,
                        category: category,
                        severity: severity,
                        mitre_id: mitreId
                    })
                });
                const data = await res.json();
                openInterpretationModal("단일 경보 한국어 해석", data);
            } catch(e) {
                console.error("Alert interpretation failed", e);
                alert("경보 해석 조회 실패");
            }
        }

        async function investigateIncident(incidentId) {
            currentInvestigatingId = incidentId;
            const btn = document.getElementById(`btn-investigate-${incidentId}`);
            const resContainer = document.getElementById(`ai-res-${incidentId}`);
            
            // 1. Get incident details
            const inc = rawIncidentsCache.find(i => i.incident_id === incidentId);
            const srcIp = inc ? inc.src_ip : '알 수 없음';
            const targets = inc ? inc.target_ips.join(', ') : '알 수 없음';

            document.getElementById('inv-modal-inc-id').textContent = incidentId;
            document.getElementById('inv-modal-src-ip').textContent = srcIp;

            // 2. Identify active model
            const selectedProv = document.getElementById('provider-select')?.value || 'mock';
            const modelDisplay = document.getElementById('inv-model-display');
            const hwHint = document.getElementById('inv-hw-hint');
            const progBar = document.getElementById('inv-progress-bar');
            const progPct = document.getElementById('inv-progress-pct');
            const progLabel = document.getElementById('inv-progress-label');
            const viewResultBtn = document.getElementById('inv-btn-view-result');

            viewResultBtn.classList.add('hidden');
            progBar.className = "bg-gradient-to-r from-cyan-500 via-blue-500 to-indigo-600 h-2 rounded-full transition-all duration-300 ease-out";
            progBar.style.width = '5%';
            progPct.textContent = '5%';
            progLabel.textContent = '보안 증적 수집 및 도구 실행 준비 중...';

            if (selectedProv === 'mock') {
                modelDisplay.textContent = '모의 기준선 (Mock)';
                modelDisplay.className = 'text-xs font-mono font-bold text-amber-300 bg-amber-950/40 border border-amber-800/50 px-2.5 py-1 rounded-md mt-0.5';
                hwHint.textContent = '결정론적 규칙 모의 엔진 (즉시 응답 · 0s)';
            } else if (selectedProv.includes('4b')) {
                modelDisplay.textContent = 'Qwen3.5 4B (고속 분석)';
                modelDisplay.className = 'text-xs font-mono font-bold text-cyan-300 bg-cyan-950/40 border border-cyan-800/50 px-2.5 py-1 rounded-md mt-0.5';
                hwHint.textContent = 'Intel Xeon 4C/8T AVX2 CPU 연산 중 (예상 소요시간: 약 120초)';
            } else {
                modelDisplay.textContent = 'Qwen3.5 9B (정밀 분석)';
                modelDisplay.className = 'text-xs font-mono font-bold text-purple-300 bg-purple-950/40 border border-purple-800/50 px-2.5 py-1 rounded-md mt-0.5';
                hwHint.textContent = 'Intel Xeon 4C/8T AVX2 CPU 연산 중 (예상 소요시간: 약 180초)';
            }

            // 3. Reset Stepper
            updateInvStepState(1, 'active', 'Suricata EVE 로그, Snort 경보 및 Threat Intel 평판 조회 중...');
            updateInvStepState(2, 'waiting', 'MITRE ATT&CK v19.2 매핑 및 침해대응 플레이북 800자 청크 추출 대기');
            updateInvStepState(3, 'waiting', '프롬프트 토큰 평가 및 Structured JSON 생성 대기');
            updateInvStepState(4, 'waiting', '차단 대상 IP 정책 검증 및 Dry-Run 모의 실행 승인 레코드 생성 대기');

            // 4. Open Modal
            document.getElementById('investigationModal').classList.remove('hidden');
            document.getElementById('inv-minimized-pill').classList.add('hidden');

            if (btn) {
                btn.disabled = true;
                btn.innerHTML = '<span>🌀</span> 심층 분석 중...';
            }

            // 5. Start Elapsed Stopwatch Timer
            if (invTimerInterval) clearInterval(invTimerInterval);
            invStartTime = Date.now();
            document.getElementById('inv-timer-display').textContent = '00:00.0';
            document.getElementById('pill-timer').textContent = '00:00.0';

            invTimerInterval = setInterval(() => {
                const elapsed = Date.now() - invStartTime;
                const timeStr = formatTimerDisplay(elapsed);
                document.getElementById('inv-timer-display').textContent = timeStr;
                document.getElementById('pill-timer').textContent = timeStr;

                if (selectedProv === 'mock') {
                    progBar.style.width = '85%';
                    progPct.textContent = '85%';
                    progLabel.textContent = '모의 기준선 규칙 분석 중...';
                    document.getElementById('pill-status').textContent = '모의 분석 중...';
                } else {
                    if (elapsed < 3500) {
                        progBar.style.width = '15%';
                        progPct.textContent = '15%';
                        progLabel.textContent = '1단계: Suricata/Snort 로그 및 Threat Intel 조회 중...';
                        document.getElementById('pill-status').textContent = '증적 수집 중...';
                    } else if (elapsed < 11000) {
                        updateInvStepState(1, 'done', 'Suricata EVE 로그, Snort 경보 및 Threat Intel 평판 조회 완료');
                        updateInvStepState(2, 'active', 'RAG 지식 검색 및 800자 컨텍스트 바운딩 추출 중...');
                        const p = Math.min(32, 15 + Math.floor((elapsed - 3500) / 7500 * 17));
                        progBar.style.width = `${p}%`;
                        progPct.textContent = `${p}%`;
                        progLabel.textContent = '2단계: RAG 플레이북 검색 및 ATT&CK 매핑 중...';
                        document.getElementById('pill-status').textContent = 'RAG 지식 검색 중...';
                    } else {
                        updateInvStepState(1, 'done');
                        updateInvStepState(2, 'done', '침해대응 플레이북 800자 청크 추출 및 증적 바운딩 완료');
                        updateInvStepState(3, 'active', `로컬 LLM AVX2 CPU 추론 연산 중 (${Math.floor(elapsed/1000)}초 경과)...`);
                        const progressFraction = Math.min(0.94, 0.32 + 0.62 * (1 - Math.exp(-(elapsed - 11000) / 70000)));
                        const pctVal = Math.floor(progressFraction * 100);
                        progBar.style.width = `${pctVal}%`;
                        progPct.textContent = `${pctVal}%`;
                        progLabel.textContent = `3단계: 로컬 LLM 추론 연산 중 (${Math.floor(elapsed/1000)}s 경과 · CPU 연산)...`;
                        document.getElementById('pill-status').textContent = `LLM 추론 연산 중 (${Math.floor(elapsed/1000)}s)...`;
                    }
                }
            }, 60);

            // 6. Execute Investigation Request
            try {
                const res = await fetch(`/api/incidents/${incidentId}/ai-investigate`, { method: 'POST' });
                const data = await res.json();
                
                clearInterval(invTimerInterval);
                const totalSec = ((Date.now() - invStartTime) / 1000).toFixed(1);

                if (data.status === 'success') {
                    const a = data.analysis;
                    resContainer.classList.remove('hidden');

                    // Update Stepper to Completion
                    updateInvStepState(1, 'done');
                    updateInvStepState(2, 'done');
                    updateInvStepState(3, 'done', `추론 및 구조화 생성 완료 (소요: ${totalSec}s)`);
                    updateInvStepState(4, 'done', '정책 검증 통과 및 인간 승인 큐(HITL) 등록 완료');

                    progBar.className = "bg-gradient-to-r from-emerald-500 to-teal-400 h-2 rounded-full transition-all duration-300 ease-out";
                    progBar.style.width = '100%';
                    progPct.textContent = '100%';
                    progLabel.textContent = `🎉 AI 심층 조사 완료 (총 ${totalSec}초 소요)`;
                    document.getElementById('inv-timer-display').textContent = `${totalSec}s`;
                    viewResultBtn.classList.remove('hidden');
                    document.getElementById('pill-status').textContent = `조사 완료 (${totalSec}s)`;

                    showToastNotification(`사고 [${incidentId}] AI 심층 조사가 완료되었습니다! (${totalSec}s)`, 'success');

                    const isMock = a.model_info.provider?.toLowerCase().includes('mock');
                    const providerTag = isMock ?
                        '<span class="text-[10px] px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/30">모의 분석 기준선 (Mock Baseline)</span>' :
                        `<span class="text-[10px] px-2 py-0.5 rounded bg-purple-500/10 text-purple-300 border border-purple-500/30">${escapeHTML(a.model_info.provider)} / ${escapeHTML(a.model_info.model)}</span>`;

                    resContainer.innerHTML = `
                        <div class="bg-slate-950/60 border border-indigo-900/40 rounded-xl p-4 space-y-3 font-mono text-xs text-slate-300">
                            <div class="flex items-center justify-between border-b border-slate-800 pb-2 flex-wrap gap-2">
                                <span class="font-bold text-indigo-300 flex items-center gap-1.5">
                                    <span>🧠</span> AI Triage & Investigation Report
                                </span>
                                <div class="flex items-center gap-2">
                                    ${providerTag}
                                    <span class="text-[10px] text-slate-400 font-mono">소요 시간: ${a.model_info.orchestrator_latency_ms}ms (${totalSec}s) | 도구 호출: ${a.model_info.tools_executed}회</span>
                                </div>
                            </div>
                            <div>
                                <p class="text-white font-semibold mb-1">📋 조사 총평 (Executive Summary):</p>
                                <p class="text-slate-300 text-xs leading-relaxed">${escapeHTML(a.summary || a.executive_summary || '조사 완료')}</p>
                            </div>
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
                                <div class="bg-slate-900/70 p-3 rounded-lg border border-slate-800">
                                    <p class="text-cyan-400 font-semibold mb-1.5 flex items-center gap-1">
                                        <span>🔍</span> 확인된 객관적 사실 (Observed Facts):
                                    </p>
                                    <ul class="list-disc list-inside space-y-1 text-slate-300 text-[11px]">
                                        ${(a.observed_facts || []).map(f => `<li>${escapeHTML(f)}</li>`).join('')}
                                    </ul>
                                </div>
                                <div class="bg-slate-900/70 p-3 rounded-lg border border-slate-800">
                                    <p class="text-amber-400 font-semibold mb-1.5 flex items-center gap-1">
                                        <span>⚠️</span> 미확인 사항 (Unknowns - 추가 점검 권고):
                                    </p>
                                    <ul class="list-disc list-inside space-y-1 text-slate-300 text-[11px]">
                                        ${(a.unknowns || []).map(u => `<li>${escapeHTML(u)}</li>`).join('')}
                                    </ul>
                                </div>
                            </div>
                            <div class="flex flex-wrap gap-2 pt-2 items-center">
                                <span class="text-slate-400 font-semibold">ATT&CK 기법:</span>
                                ${(a.attack_mapping || a.attack_techniques || []).map(t => `<span class="px-2 py-0.5 rounded bg-indigo-950/60 text-indigo-300 border border-indigo-700/50 text-[10px]">${t.technique_id} - ${escapeHTML(t.technique_name || t.name)} (${t.confidence})</span>`).join('')}
                            </div>
                            ${(a.knowledge_refs || a.citations || []).length ? `
                            <div class="pt-1 text-[11px] text-slate-400">
                                <span class="text-cyan-400 font-semibold">참조 플레이북:</span> ${(a.knowledge_refs || a.citations).map(c => `${escapeHTML(c.document_title)} (유사도: ${c.relevance_score})`).join(', ')}
                            </div>` : ''}
                        </div>
                    `;

                    // Refresh proposals to reflect new items
                    const propRes = await fetch('/api/action-proposals');
                    const proposals = await propRes.json();
                    renderProposals(proposals);
                    document.getElementById('metric-approvals').textContent = proposals.filter(p => p.status === 'PENDING').length;
                } else {
                    updateInvStepState(3, 'error', '추론 실패 또는 모델 응답 거부');
                    progBar.className = "bg-red-500 h-2 rounded-full";
                    progLabel.textContent = `오류: ${data.error || 'AI 분석 실패'}`;
                    showToastNotification(`AI 조사 실패: ${data.error || 'Unknown error'}`, 'error');
                }
            } catch (err) {
                clearInterval(invTimerInterval);
                updateInvStepState(3, 'error', '타임아웃 또는 네트워크 연결 오류');
                progBar.className = "bg-red-500 h-2 rounded-full";
                progLabel.textContent = `오류: 타임아웃 또는 서버 응답 없음 (${err.message})`;
                showToastNotification(`AI 조사 실패: ${err.message || err}`, 'error');
            } finally {
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = '<span>🤖</span> AI 재조사';
                }
            }
        }

        function renderProposals(proposals) {
            const tbody = document.getElementById('approvals-tbody');
            if (!proposals || !proposals.length) {
                tbody.innerHTML = '<tr><td colspan="7" class="py-6 text-center text-slate-500 font-mono text-xs">대기 중인 대응 조치 제안이 없습니다.</td></tr>';
                return;
            }
            tbody.innerHTML = proposals.map(p => {
                const act = p.proposed_action;
                const pol = p.policy_validation;
                const polBadge = getLocalizedPolicyVerdict(pol.verdict);

                let statusBadge = '';
                if (p.status === 'PENDING') statusBadge = '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30 animate-pulse">승인 대기 (PENDING)</span>';
                else if (p.status === 'APPROVED') statusBadge = '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-500/20 text-blue-400 border border-blue-500/30">승인됨 (APPROVED)</span>';
                else if (p.status === 'EXECUTED') statusBadge = '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-green-500/20 text-green-400 border border-green-500/30">모의 실행 완료 (EXECUTED)</span>';
                else if (p.status === 'REJECTED') statusBadge = '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-red-500/20 text-red-400 border border-red-500/30">반려됨 (REJECTED)</span>';
                else statusBadge = `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-400">${p.status}</span>`;

                let actionBtns = '';
                if (p.status === 'PENDING') {
                    actionBtns = `
                        <div class="flex items-center justify-center gap-1.5">
                            <button onclick="approveAction('${p.approval_id}')" ${!pol.is_valid ? 'disabled title="정책 위반 조치는 승인 불가 (게이트웨이/SIEM 보호)"' : ''} class="px-2.5 py-1 text-[11px] font-bold ${pol.is_valid ? 'bg-emerald-600 hover:bg-emerald-500 text-white' : 'bg-slate-700 text-slate-500 cursor-not-allowed'} rounded transition">
                                ✅ 모의 실행 승인 (Dry-Run)
                            </button>
                            <button onclick="rejectAction('${p.approval_id}')" class="px-2 py-1 text-[11px] font-bold bg-red-600 hover:bg-red-500 text-white rounded transition">
                                ❌ 반려
                            </button>
                        </div>
                    `;
                } else if (p.execution_output) {
                    actionBtns = `
                        <div class="text-center">
                            <button onclick="showExecutionOutput('${p.approval_id}')" class="px-2.5 py-1 text-[11px] font-semibold bg-slate-800 hover:bg-slate-700 text-cyan-400 border border-cyan-800 rounded transition">
                                📜 실행 증적 확인
                            </button>
                        </div>
                    `;
                } else {
                    actionBtns = `<span class="text-slate-500 text-center block">-</span>`;
                }

                const actionLabel = localizationDict?.action_types?.[act.action_type] || act.action_type;

                return `
                    <tr class="hover:bg-slate-800/30 transition">
                        <td class="py-2.5 px-3 font-semibold text-purple-300 font-mono">${escapeHTML(p.approval_id)}</td>
                        <td class="py-2.5 px-3 text-slate-400 font-mono">${escapeHTML(p.incident_id)}</td>
                        <td class="py-2.5 px-3">
                            <span class="font-bold text-white">${escapeHTML(actionLabel)}</span>
                            <span class="text-red-400 ml-1 font-mono font-bold">(${escapeHTML(act.target)})</span>
                        </td>
                        <td class="py-2.5 px-3">${polBadge}</td>
                        <td class="py-2.5 px-3 font-mono text-[11px] text-slate-300">
                            <button onclick="showRulePreview('${p.approval_id}')" class="text-cyan-400 hover:underline">
                                ${escapeHTML(act.rule_syntax_preview.substring(0, 34))}...
                            </button>
                        </td>
                        <td class="py-2.5 px-3">${statusBadge}</td>
                        <td class="py-2.5 px-3">${actionBtns}</td>
                    </tr>
                `;
            }).join('');
        }

        async function approveAction(approvalId) {
            if (!confirm(`[주의: 모의 실행 안내]\n조치 '${approvalId}'를 승인하시겠습니까?\n현재 모드는 DRY_RUN으로 실제 호스트 방화벽 규칙을 변경하지 않고 시뮬레이션 구문을 안전하게 검증합니다.`)) return;
            try {
                const res = await fetch(`/api/action-proposals/${approvalId}/approve`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ reviewer: 'soc-analyst-console', notes: 'Console analyst approved dry-run simulation', auto_execute: true })
                });
                const data = await res.json();
                if (data.status === 'success') {
                    showModal(`조치 승인 및 Dry-Run 모의 실행 증적 (${approvalId})`, `<pre class="text-xs font-mono text-cyan-300 bg-slate-950 p-4 rounded-xl overflow-x-auto whitespace-pre-wrap">${escapeHTML(data.execution_output || 'Dry-run executed successfully.')}</pre>`);
                    refreshData();
                } else {
                    alert('승인 실패: ' + (data.error || 'Unknown error'));
                }
            } catch (e) {
                console.error(e);
                alert('승인 요청 실패');
            }
        }

        async function rejectAction(approvalId) {
            const reason = prompt('반려 사유를 입력하세요 (선택):', '분석가 판단: 오탐 의심 또는 조치 불필요');
            if (reason === null) return;
            try {
                const res = await fetch(`/api/action-proposals/${approvalId}/reject`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ reviewer: 'soc-analyst-console', notes: reason })
                });
                const data = await res.json();
                if (data.status === 'success') {
                    refreshData();
                } else {
                    alert('반려 처리 실패: ' + (data.error || 'Unknown error'));
                }
            } catch (e) {
                console.error(e);
                alert('반려 요청 실패');
            }
        }

        async function showRulePreview(approvalId) {
            try {
                const res = await fetch(`/api/action-proposals/${approvalId}`);
                const data = await res.json();
                const content = `
                    <div class="space-y-3">
                        <p class="text-xs text-slate-300 font-medium">제안된 방화벽 규칙 구문 (nftables / iptables 프리뷰):</p>
                        <pre class="text-xs font-mono text-cyan-300 bg-slate-950 p-4 rounded-xl overflow-x-auto whitespace-pre-wrap">${escapeHTML(data.proposed_action.rule_syntax_preview)}</pre>
                        <p class="text-[11px] text-slate-500 font-mono">격리 유지 권고 시간: ${data.proposed_action.duration_minutes}분 | 실행 모드: DRY_RUN</p>
                    </div>
                `;
                showModal(`규칙 구문 프리뷰 - ${approvalId}`, content);
            } catch (e) {
                console.error(e);
            }
        }

        async function showExecutionOutput(approvalId) {
            try {
                const res = await fetch(`/api/action-proposals/${approvalId}`);
                const data = await res.json();
                const content = `<pre class="text-xs font-mono text-emerald-300 bg-slate-950 p-4 rounded-xl overflow-x-auto whitespace-pre-wrap">${escapeHTML(data.execution_output || '실행 증적 정보 없음')}</pre>`;
                showModal(`실행 증적 감사 기록 (Audit Trail) - ${approvalId}`, content);
            } catch (e) {
                console.error(e);
            }
        }

        function filterAlerts() {
            const query = (document.getElementById('alert-search-input')?.value || '').toLowerCase();
            const sevFilter = document.getElementById('alert-severity-select')?.value || 'ALL';

            const filtered = rawAlertsCache.filter(a => {
                const matchSev = (sevFilter === 'ALL') || (a.severity === sevFilter);
                if (!matchSev) return false;
                if (!query) return true;

                const matchSig = a.signature.toLowerCase().includes(query);
                const matchSrc = a.src_ip.toLowerCase().includes(query);
                const matchDst = a.dst_ip.toLowerCase().includes(query);
                const matchSid = String(a.sid).includes(query);
                return matchSig || matchSrc || matchDst || matchSid;
            });

            renderAlerts(filtered);
        }

        function renderAlerts(alerts) {
            const tbody = document.getElementById('alerts-tbody');
            if (!alerts || !alerts.length) {
                tbody.innerHTML = '<tr><td colspan="8" class="py-8 text-center text-slate-500 font-mono text-xs">일치하는 경보 로그가 없습니다.</td></tr>';
                return;
            }

            tbody.innerHTML = alerts.map((a, idx) => {
                const sevBadge = getLocalizedSeverity(a.severity);
                const engBadge = a.engine === 'SURICATA' ? 'text-cyan-400' : 'text-orange-400';
                const timeKST = formatKST(a.timestamp);
                const localizedSig = getLocalizedSignature(a.signature);
                const mitreText = a.mitre_technique ? (localizationDict?.mitre_techniques?.[a.mitre_technique]?.name_ko ? `${a.mitre_technique} (${localizationDict.mitre_techniques[a.mitre_technique].name_ko})` : a.mitre_technique) : '-';

                return `
                    <tr class="hover:bg-slate-800/30 transition text-xs">
                        <td class="py-2.5 px-3 text-slate-400 font-mono whitespace-nowrap" title="UTC: ${escapeHTML(a.timestamp)}">
                            ${timeKST}
                        </td>
                        <td class="py-2.5 px-3 font-bold ${engBadge} whitespace-nowrap">${escapeHTML(a.engine)}</td>
                        <td class="py-2.5 px-3 whitespace-nowrap">${sevBadge}</td>
                        <td class="py-2.5 px-3 max-w-xs">${localizedSig}</td>
                        <td class="py-2.5 px-3 text-red-300 font-mono whitespace-nowrap font-semibold">
                            ${escapeHTML(a.src_ip)}:${a.src_port || '-'}
                        </td>
                        <td class="py-2.5 px-3 text-blue-300 font-mono whitespace-nowrap font-semibold">
                            ${escapeHTML(a.dst_ip)}:${a.dst_port || '-'}
                        </td>
                        <td class="py-2.5 px-3 text-purple-300 font-mono whitespace-nowrap">${escapeHTML(mitreText)}</td>
                        <td class="py-2.5 px-3 text-center whitespace-nowrap">
                            <div class="flex items-center justify-center gap-1">
                                <button onclick="interpretAlert('${escapeHTML(a.signature)}', '${escapeHTML(a.category)}', '${escapeHTML(a.severity)}', '${escapeHTML(a.mitre_technique || '')}')" class="px-2 py-0.5 text-[10px] font-semibold bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-slate-700 rounded transition" title="한국어 상세 해석">
                                    📖 해석
                                </button>
                                <button onclick="viewRawAlertDetails(${idx})" class="px-2 py-0.5 text-[10px] font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 rounded transition" title="증적 및 원본 패킷 정보 열람">
                                    🔍 증적
                                </button>
                            </div>
                        </td>
                    </tr>
                `;
            }).join('');
        }

        function viewRawAlertDetails(alertIndex) {
            const a = rawAlertsCache[alertIndex];
            if (!a) return;

            const content = `
                <div class="space-y-3 font-mono text-xs">
                    <div class="bg-slate-950 p-3 rounded-lg border border-slate-800 space-y-1">
                        <div><span class="text-cyan-400 font-semibold">시그니처:</span> ${escapeHTML(a.signature)}</div>
                        <div><span class="text-slate-400">규칙 식별자 (SID / GID / Rev):</span> ${a.sid} / ${a.gid} / rev ${a.rev}</div>
                        <div><span class="text-slate-400">이벤트 시각:</span> ${formatKST(a.timestamp)} (UTC: ${escapeHTML(a.timestamp)})</div>
                        <div><span class="text-slate-400">출발지:</span> ${escapeHTML(a.src_ip)}:${a.src_port || '-'} ➔ <span class="text-slate-400">목적지:</span> ${escapeHTML(a.dst_ip)}:${a.dst_port || '-'} (${escapeHTML(a.protocol)})</div>
                        <div><span class="text-slate-400">커뮤니티 ID:</span> ${escapeHTML(a.community_id || '-')}</div>
                    </div>

                    ${a.http_hostname || a.http_uri ? `
                    <div class="bg-slate-950 p-3 rounded-lg border border-slate-800 space-y-1">
                        <div class="text-cyan-400 font-semibold mb-1">🌐 HTTP 트래픽 메타데이터:</div>
                        <div><span class="text-slate-400">호스트:</span> ${escapeHTML(a.http_hostname || '-')}</div>
                        <div><span class="text-slate-400">요청 URI:</span> <span class="text-red-300 break-all">${escapeHTML(a.http_uri || '-')}</span></div>
                        <div><span class="text-slate-400">User-Agent:</span> ${escapeHTML(a.http_user_agent || '-')}</div>
                    </div>` : ''}

                    <div class="bg-slate-950 p-3 rounded-lg border border-slate-800">
                        <div class="text-cyan-400 font-semibold mb-1">📦 원본 JSON 로우 데이터 (Raw Evidence):</div>
                        <pre class="text-[11px] text-slate-300 overflow-x-auto whitespace-pre-wrap max-h-48">${escapeHTML(JSON.stringify(a.raw_data || a, null, 2))}</pre>
                    </div>
                </div>
            `;
            showModal(`증적 및 원본 패킷 정보 - SID ${a.sid}`, content);
        }

        function openInterpretationModal(title, data) {
            const checksList = (data.recommended_checks || []).map(c => `<li>${escapeHTML(c)}</li>`).join('');
            const content = `
                <div class="space-y-4 text-xs">
                    <div class="p-3 rounded-xl bg-slate-950 border border-cyan-900/50">
                        <h5 class="text-sm font-bold text-white mb-1">${escapeHTML(data.korean_title)}</h5>
                        <p class="text-cyan-300">${escapeHTML(data.plain_korean_summary)}</p>
                    </div>

                    <div class="bg-slate-950 p-3.5 rounded-xl border border-slate-800 space-y-1.5">
                        <div class="text-slate-400 font-semibold">🔍 보안 분석적 의미:</div>
                        <p class="text-slate-200 leading-relaxed">${escapeHTML(data.security_meaning)}</p>
                    </div>

                    <div class="bg-slate-950 p-3.5 rounded-xl border border-amber-900/40 space-y-1.5">
                        <div class="text-amber-400 font-semibold flex items-center gap-1">
                            <span>⚠️</span> 침해 성공 여부 판정 기준:
                        </div>
                        <p class="text-slate-300 text-xs">${escapeHTML(data.compromise_status)}</p>
                    </div>

                    <div class="bg-slate-950 p-3.5 rounded-xl border border-slate-800 space-y-1.5">
                        <div class="text-emerald-400 font-semibold flex items-center gap-1">
                            <span>📋</span> 분석가 필수 추가 점검 항목 (Checklist):
                        </div>
                        <ul class="list-disc list-inside space-y-1 text-slate-300 text-[11px]">
                            ${checksList}
                        </ul>
                    </div>
                </div>
            `;
            showModal(title, content);
        }

        function showModal(title, htmlBody) {
            document.getElementById('modalTitle').textContent = title;
            document.getElementById('modalBody').innerHTML = htmlBody;
            document.getElementById('generalModal').classList.remove('hidden');
        }

        function closeModal() {
            document.getElementById('generalModal').classList.add('hidden');
        }

        // Initialize view mode and refresh loop
        setViewMode(currentViewMode);
        refreshData();
        setInterval(refreshData, 3000);
    </script>
</body>
</html>
    """
