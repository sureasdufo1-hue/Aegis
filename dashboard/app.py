import asyncio
import json
import os
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
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
from dashboard.audit import get_audit_logs, record_audit_log
from dashboard.telemetry import (
    get_assets_telemetry,
    get_dashboard_summary_telemetry,
    get_network_interfaces_telemetry,
    get_security_policies_telemetry,
    get_sensors_telemetry,
    get_threats_countries_data,
    get_traffic_analysis_data,
    load_normalized_alerts,
)
from dashboard.elk_client import (
    get_elk_cluster_health,
    get_elk_events,
    get_elk_stats,
    get_elk_timeline,
)
from dashboard.websocket_manager import ws_manager

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
        "timestamp": datetime.now(UTC).isoformat(),
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
        "rag_documents_loaded": len({c.file_path for c in orchestrator.retriever.store.chunks}),
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


INDEX_HTML_PATH = Path(__file__).parent / "templates" / "index.html"


@app.get("/", response_class=HTMLResponse)
def index():
    if INDEX_HTML_PATH.exists():
        return HTMLResponse(content=INDEX_HTML_PATH.read_text(encoding="utf-8"))
    raise HTTPException(status_code=500, detail="Dashboard index template not found")


@app.get("/api/dashboard/summary")
def get_dashboard_summary():
    return get_dashboard_summary_telemetry()


@app.get("/api/events")
def get_events(
    limit: int = 50,
    severity: str | None = None,
    engine: str | None = None,
    search: str | None = None,
):
    alerts = load_normalized_alerts()
    if severity and severity.upper() != "ALL":
        alerts = [a for a in alerts if a.severity.value == severity.upper()]
    if engine and engine.upper() != "ALL":
        alerts = [a for a in alerts if a.engine.value == engine.upper()]
    if search:
        s = search.lower()
        alerts = [
            a for a in alerts
            if s in a.signature.lower() or s in a.src_ip.lower() or s in a.dst_ip.lower() or s in str(a.sid)
        ]
    return [a.model_dump() for a in alerts[:limit]]


@app.get("/api/events/{event_id}")
def get_single_event(event_id: str):
    alerts = load_normalized_alerts()
    target = next((a for a in alerts if a.id == event_id), None)
    if not target:
        raise HTTPException(status_code=404, detail=f"Event '{event_id}' not found")
    return target.model_dump()


@app.get("/api/incidents/{incident_id}")
def get_single_incident(incident_id: str):
    incidents = get_current_incidents()
    target = next((i for i in incidents if i.incident_id == incident_id or incident_id.startswith(f"INC-{i.src_ip}")), None)
    if not target:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found")
    return target.model_dump()


@app.get("/api/network/traffic")
def get_network_traffic_endpoint(time_range: str = "1H"):
    return get_traffic_analysis_data(time_range=time_range)


@app.get("/api/network/interfaces")
def get_network_interfaces_endpoint():
    return get_network_interfaces_telemetry()


@app.get("/api/threats/countries")
def get_threats_countries_endpoint():
    return get_threats_countries_data()


@app.get("/api/assets")
def get_assets_endpoint():
    return get_assets_telemetry()


@app.get("/api/sensors")
def get_sensors_endpoint():
    return get_sensors_telemetry()


@app.get("/api/policies")
def get_policies_endpoint():
    return get_security_policies_telemetry()


@app.get("/api/ai/analysis/{event_id}")
def get_event_ai_analysis(event_id: str):
    alerts = load_normalized_alerts()
    target = next((a for a in alerts if a.id == event_id), None)
    if not target:
        raise HTTPException(status_code=404, detail=f"Event '{event_id}' not found")
    interp = interpreter.interpret_alert(
        signature=target.signature,
        category=target.category,
        severity=target.severity.value,
        mitre_id=target.mitre_technique,
    )
    return {
        "event_id": event_id,
        "interpretation": interp,
        "ai_risk_score": 88 if target.severity == Severity.CRITICAL else (65 if target.severity == Severity.HIGH else 35),
        "confidence": 0.92,
        "recommended_action": "BLOCK_IP" if target.severity in (Severity.CRITICAL, Severity.HIGH) else "MONITOR",
        "false_positive_probability": 0.08,
    }


class CreateAuditLogRequest(BaseModel):
    type: str
    action: str
    actor: str = "soc-analyst"
    result: str = "SUCCESS"
    detail: str = ""


@app.get("/api/audit/logs")
def get_audit_logs_endpoint(limit: int = 50):
    return [l.model_dump() for l in get_audit_logs(limit=limit)]


@app.post("/api/audit/logs")
def create_audit_log_endpoint(req: CreateAuditLogRequest):
    rec = record_audit_log(
        event_type=req.type,
        action=req.action,
        actor=req.actor,
        result=req.result,
        detail=req.detail,
    )
    return rec.model_dump()


# -------------------------------------------------------------
# ELK Stack 8.17.3 Integration Endpoints
# -------------------------------------------------------------

@app.get("/api/elk/health")
async def api_elk_health():
    """Returns real-time cluster health for Elasticsearch 8.17.3 and Kibana."""
    return get_elk_cluster_health()


@app.get("/api/elk/events")
async def api_elk_events(limit: int = 50, module: str | None = None, severity: int | None = None):
    """Returns normalized security events from logs-* with optional module and severity filters."""
    return get_elk_events(limit=limit, module=module, severity=severity)


@app.get("/api/elk/timeline/{ip}")
async def api_elk_timeline(ip: str, limit: int = 50):
    """Returns multi-source correlated incident timeline for a specified attacker/victim IP."""
    return get_elk_timeline(ip=ip, limit=limit)


@app.get("/api/elk/stats")
async def api_elk_stats():
    """Returns aggregated security metrics across all 4 telemetry streams."""
    return get_elk_stats()


# -------------------------------------------------------------
# WebSocket Live Streaming Endpoints (Multiplexed & Dedicated)
# -------------------------------------------------------------

@app.websocket("/ws/stream")
async def websocket_stream_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket, "stream")
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "PONG", "timestamp": datetime.now(UTC).isoformat()}))
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, "stream")
    except (RuntimeError, OSError):
        ws_manager.disconnect(websocket, "stream")


@app.websocket("/ws/{channel}")
async def websocket_channel_endpoint(websocket: WebSocket, channel: str):
    await ws_manager.connect(websocket, channel)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "PONG", "channel": channel}))
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, channel)
    except (RuntimeError, OSError):
        ws_manager.disconnect(websocket, channel)


# Background Broadcaster Task
async def background_telemetry_broadcaster():
    while True:
        try:
            await asyncio.sleep(3.0)
            if any(len(conns) > 0 for conns in ws_manager.active_connections.values()):
                summary = get_dashboard_summary_telemetry()
                await ws_manager.broadcast({
                    "type": "TICK",
                    "timestamp": datetime.now(UTC).isoformat(),
                    "kpis": summary["kpis"],
                    "system": summary["system_telemetry"],
                }, "stream")
        except asyncio.CancelledError:
            break
        except (RuntimeError, OSError):
            await asyncio.sleep(1.0)


@app.on_event("startup")
async def on_startup():
    asyncio.create_task(background_telemetry_broadcaster())
