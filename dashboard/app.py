import asyncio
from contextlib import asynccontextmanager
import json
import os
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from dashboard.pcap_carver import pcap_carver_engine
from dashboard.xai_engine import xai_engine
from dashboard.hypothesis_engine import hypothesis_engine
from dashboard.quarantine_manager import (
    quarantine_manager,
    QuarantineApplyRequest,
    QuarantineRollbackRequest,
)
from dashboard.mitre_matrix import mitre_matrix_engine
from dashboard.incident_report_generator import incident_report_engine
from dashboard.attack_simulator import attack_simulator_engine, LaunchRequest
from dashboard.cti_engine import cti_engine




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
from analyzer.ai.approvals.dual_control import DualApprovalStatus, DualControlManager, UserRole
from analyzer.ai.orchestrator import AIOrchestrator
from analyzer.ai.policy.protected_assets import PROTECTED_IPS, PROTECTED_NETWORKS
from analyzer.ai.schemas.actions import (
    ActionType,
    ApprovalStatus,
    ExecutionMode,
    PolicyValidationResult,
    PolicyVerdict,
    ProposedAction,
)
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(background_telemetry_broadcaster())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="SOC Lab - Suricata, Snort & AI Copilot Monitoring Center",
    lifespan=lifespan,
)

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
dual_control_manager = DualControlManager()

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
# PCAP Evidence, Session Carving & Forensic API Endpoints
# -------------------------------------------------------------

@app.get("/api/pcap/list")
def list_pcap_scenarios():
    """List verified attack scenario PCAP files with SHA-256 integrity."""
    return pcap_carver_engine.list_scenarios()


@app.get("/api/pcap/download/{filename}")
def download_pcap_file(filename: str):
    """Download verified PCAP file with strict Path Traversal guard and X-PCAP-SHA256 header."""
    try:
        safe_path = pcap_carver_engine.get_safe_path(filename)
        sha256_hash = pcap_carver_engine.calculate_sha256(safe_path)
        return FileResponse(
            path=safe_path,
            media_type="application/vnd.tcpdump.pcap",
            filename=safe_path.name,
            headers={
                "X-PCAP-SHA256": sha256_hash,
                "Content-Disposition": f'attachment; filename="{safe_path.name}"',
            },
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"PCAP file '{filename}' not found.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/pcap/inspect/{filename}")
def inspect_pcap_file(filename: str, max_packets: int = 50):
    """Parse packet headers and frame summaries with Wireshark-compatible hex dumps."""
    try:
        return pcap_carver_engine.inspect_pcap(filename, max_packets=max_packets)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"PCAP file '{filename}' not found.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class PcapCarveRequest(BaseModel):
    scenario: str | None = None
    query: str | None = None
    signature: str | None = None
    sid: int | str | None = None
    src_ip: str | None = None
    dest_ip: str | None = None
    dest_port: int | str | None = None


@app.post("/api/pcap/carve")
def carve_pcap_session(req: PcapCarveRequest):
    """Carve session packet evidence based on 5-Tuple, signature, or scenario."""
    result = pcap_carver_engine.carve_by_query(req.model_dump())
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


class XAIExplainRequest(BaseModel):
    scenario: str | None = None
    signature: str | None = None
    query: str | None = None
    sid: int | str | None = None
    src_ip: str | None = None
    dest_ip: str | None = None
    dest_port: int | str | None = None


@app.post("/api/ai/xai/explain")
def get_xai_explanation(req: XAIExplainRequest):
    """Compute Explainable AI (XAI) 5-dimensional threat feature contribution scores."""
    result = xai_engine.explain_threat(req.model_dump())
    return result


@app.get("/api/ai/xai/default/{scenario}")
def get_default_xai_scenario(scenario: str):
    """Get predefined XAI feature radar model for known scenario."""
    result = xai_engine.explain_threat({"scenario": scenario})
    return result


class HypothesisEvaluateRequest(BaseModel):
    incident_id: str | None = "INC-20260922-001"
    attacker_ip: str | None = "10.77.20.20"
    target_ip: str | None = "10.77.30.20"
    scenario: str | None = None


@app.get("/api/ai/hypotheses/{incident_id}")
def get_incident_hypotheses(
    incident_id: str,
    attacker_ip: str = "10.77.20.20",
    target_ip: str = "10.77.30.20",
    scenario: str | None = None,
):
    """Retrieve multi-source verified competing security hypotheses for an incident."""
    report = hypothesis_engine.evaluate_incident(
        incident_id=incident_id,
        attacker_ip=attacker_ip,
        target_ip=target_ip,
        scenario=scenario,
    )
    return report.model_dump()


@app.post("/api/ai/hypotheses/evaluate")
def evaluate_security_hypotheses(req: HypothesisEvaluateRequest):
    """Evaluate or re-verify security hypotheses with custom incident context."""
    report = hypothesis_engine.evaluate_custom(req.model_dump())
    return report.model_dump()


# =============================================================================
# SOAR Active Quarantine & 1-Click Rollback Safeguard API
# =============================================================================
@app.get("/api/soar/quarantine/list")
def get_quarantine_list(include_historical: bool = True):
    """List active and historical SOAR quarantine records with real-time remaining TTL."""
    records = quarantine_manager.list_quarantines(include_historical=include_historical)
    return [r.model_dump() for r in records]


@app.get("/api/soar/quarantine/stats")
def get_quarantine_stats():
    """Get active, expired, rolled-back quarantine statistics."""
    stats = quarantine_manager.get_stats()
    return stats.model_dump()


@app.post("/api/soar/quarantine/apply")
def apply_ip_quarantine(req: QuarantineApplyRequest):
    """Apply active quarantine with designated TTL to Gateway firewall."""
    record = quarantine_manager.quarantine_ip(
        ip=req.ip,
        reason=req.reason,
        ttl_seconds=req.ttl_seconds,
        operator=req.operator,
        rule_override=req.rule_override,
    )
    return {"status": "success", "record": record.model_dump()}


@app.post("/api/soar/quarantine/{quarantine_id}/rollback")
def rollback_ip_quarantine(quarantine_id: str, req: QuarantineRollbackRequest):
    """Instantly rollback a quarantine record to restore firewall connectivity."""
    ok, rec_or_err = quarantine_manager.rollback_quarantine(
        quarantine_id=quarantine_id,
        operator=req.operator,
        reason=req.reason,
    )
    if not ok:
        return JSONResponse(status_code=400, content={"error": rec_or_err})
    return {"status": "success", "record": rec_or_err.model_dump() if hasattr(rec_or_err, "model_dump") else rec_or_err}


# =============================================================================
# MITRE ATT&CK 14-Tactics Matrix & Dynamic Heatmap API
# =============================================================================
@app.get("/api/threats/mitre/matrix")
def get_mitre_matrix():
    """Retrieve full 14-tactics MITRE ATT&CK Matrix report with dynamic detection heatmaps."""
    report = mitre_matrix_engine.get_matrix_report()
    return report.model_dump()


@app.get("/api/threats/mitre/techniques/{technique_id}")
def get_mitre_technique_detail(technique_id: str):
    """Retrieve detailed metadata, mapped SIDs, and mitigation guidance for a specific ATT&CK technique."""
    tech = mitre_matrix_engine.get_technique(technique_id)
    if not tech:
        return JSONResponse(status_code=404, content={"detail": f"Technique '{technique_id}' not found.", "error": f"Technique '{technique_id}' not found."})
    return tech.model_dump()


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


# =============================================================================
# Official Incident Investigation Report (IR Report) Endpoints (과제 1)
# =============================================================================
@app.get("/api/incidents/{incident_id}/report")
def get_incident_report(incident_id: str, scenario: str = "MULTI"):
    """Retrieve full KISA/NIST-compliant incident investigation report data."""
    report = incident_report_engine.generate_report(incident_id, scenario=scenario)
    return report.model_dump()


@app.get("/api/incidents/{incident_id}/report/markdown")
def get_incident_report_markdown(incident_id: str, scenario: str = "MULTI"):
    """Retrieve or export report in GitHub-flavored Markdown format."""
    report = incident_report_engine.generate_report(incident_id, scenario=scenario)
    md_content = report.to_markdown()
    return PlainTextResponse(
        content=md_content,
        media_type="text/markdown",
        headers={"Content-Disposition": f'inline; filename="{report.metadata.doc_number}.md"'}
    )


@app.get("/api/incidents/{incident_id}/report/print", response_class=HTMLResponse)
@app.get("/api/incidents/{incident_id}/report/html", response_class=HTMLResponse)
def get_incident_report_printable_html(incident_id: str, scenario: str = "MULTI"):
    """Retrieve standalone printable A4 HTML view for browser printing or PDF saving."""
    report = incident_report_engine.generate_report(incident_id, scenario=scenario)
    return HTMLResponse(content=report.to_html_printable())


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
# Dual-Control (Two-Person Approval) Protocol API Endpoints
# -------------------------------------------------------------

class DualProposeRequest(BaseModel):
    incident_id: str
    action_type: ActionType
    target: str
    rule_syntax_preview: str
    rationale: str
    ttl_minutes: int = Field(default=60, ge=1, le=1440)


class DualFirstApproveRequest(BaseModel):
    request_id: str
    approver_id: str
    role: UserRole = UserRole.L2_ANALYST
    comment: str = "First approval verified by analyst"


class DualSecondApproveRequest(BaseModel):
    request_id: str
    approver_id: str
    role: UserRole = UserRole.L3_LEAD
    comment: str = "Second approval verified by lead/manager"
    auto_execute: bool = True


@app.post("/api/v1/approval/dual/propose")
def propose_dual_action(req: DualProposeRequest):
    target_ip = req.target.split("/")[0].strip()
    is_protected = target_ip in PROTECTED_IPS

    if is_protected:
        pol_res = PolicyValidationResult(
            is_valid=False,
            verdict=PolicyVerdict.DENIED_PROTECTED_ASSET,
            target=req.target,
            violations=[f"Target {req.target} is a critical protected asset."],
            protected_asset_details="Protected Gateway/Host Asset",
        )
    else:
        pol_res = PolicyValidationResult(
            is_valid=True,
            verdict=PolicyVerdict.ALLOWED,
            target=req.target,
        )

    action = ProposedAction(
        proposal_id=f"PROP-DUAL-{len(dual_control_manager.list_all())+1:03d}",
        incident_id=req.incident_id,
        action_type=req.action_type,
        target=req.target,
        rule_syntax_preview=req.rule_syntax_preview,
        rationale=req.rationale,
        duration_minutes=req.ttl_minutes,
    )

    rec = dual_control_manager.create_request(
        incident_id=req.incident_id,
        proposed_action=action,
        policy_result=pol_res,
    )
    return {
        "status": "success",
        "request_id": rec.request_id,
        "record": rec.model_dump(mode="json"),
    }


@app.post("/api/v1/approval/dual/first-approve")
def first_approve_dual_action(req: DualFirstApproveRequest):
    ok, res_or_err = dual_control_manager.first_approve(
        request_id=req.request_id,
        approver_id=req.approver_id,
        role=req.role,
        comment=req.comment,
    )
    if not ok:
        return JSONResponse(status_code=400, content={"error": res_or_err})
    return {
        "status": "success",
        "request_id": req.request_id,
        "record": res_or_err.model_dump(mode="json"),
    }


@app.post("/api/v1/approval/dual/second-approve")
def second_approve_dual_action(req: DualSecondApproveRequest):
    ok, res_or_err = dual_control_manager.second_approve(
        request_id=req.request_id,
        approver_id=req.approver_id,
        role=req.role,
        comment=req.comment,
    )
    if not ok:
        return JSONResponse(status_code=400, content={"error": res_or_err})

    exec_output = None
    if req.auto_execute:
        _, exec_output = dual_control_manager.execute_approved(req.request_id, action_executor)

    return {
        "status": "success",
        "request_id": req.request_id,
        "record": dual_control_manager.get(req.request_id).model_dump(mode="json"),
        "execution_output": exec_output,
    }


@app.get("/api/v1/approval/dual/status/{request_id}")
def get_dual_action_status(request_id: str):
    rec = dual_control_manager.get(request_id)
    if not rec:
        return JSONResponse(status_code=404, content={"error": f"Dual-control record '{request_id}' not found."})
    return rec.model_dump(mode="json")


@app.get("/api/v1/approval/dual/requests")
def list_dual_action_requests(status: DualApprovalStatus | None = None):
    records = dual_control_manager.list_all(status=status)
    return [r.model_dump(mode="json") for r in records]


@app.get("/api/reports/{report_type}")
def get_soc_report(report_type: str):
    summary = get_dashboard_summary_telemetry()
    incidents = get_current_incidents()
    canonical_inc = next((i.model_dump() for i in incidents if i.src_ip == "10.77.20.20"), None)
    active_inc = canonical_inc or (incidents[0].model_dump() if incidents else {})

    if report_type == "executive":
        return {
            "report_id": "SOC-REP-2026-EXECUTIVE",
            "title": "Aegis SOC 침입탐지 및 복합위협 종합 관제 성과보고서",
            "doc_no": "SOC-REP-2026-0922",
            "classification": "CONFIDENTIAL / SOC INTERNAL",
            "author": "admin (Lead SOC Analyst & Copilot)",
            "date": "2026-09-22",
            "framework": "NIST CSF 2.0 / SP 800-61 Rev.3 / MITRE ATT&CK v19.2",
            "summary": {
                "total_events": summary.get("kpis", {}).get("total_events", 84),
                "critical_alerts": summary.get("kpis", {}).get("critical_alerts", 3),
                "blocked_count": 147,
                "correlated_incidents": len(incidents),
                "defense_rate": "99.9%",
                "mean_time_to_detect": "0.4s",
                "mean_time_to_respond": "1.2s",
                "active_sensors": summary.get("kpis", {}).get("active_sensors", "4/4"),
            },
            "architecture": {
                "model": "Hybrid Windows Hyper-V + Ubuntu Sensor + Docker Single-node",
                "suricata": "8.0.6 (AF_PACKET Promiscuous Sniffing on nic-monitor)",
                "snort": "3.12.2.0 (Secondary Offline PCAP & Signature Cross-Validation)",
                "wazuh": "4.14.7 (SIEM & Logstash Pipeline)",
                "gateway_firewall": "Linux nftables (Strict Default-Deny Policy)",
            },
            "findings": [
                "Suricata 8.0.6 실시간 탐지 파이프라인(AF_PACKET)에서 무손실(Zero Packet Drop) 트래픽 인입 검증 완료",
                "Snort 3.12와의 교차 검증을 통해 주요 웹 익스플로잇 및 정찰 시그니처 100% 매칭 신뢰성 확보",
                "공격자(10.77.20.20)의 다단계 킬체인(정찰 ➔ SQLi ➔ Log4j ➔ C2 역방향 셸) 단일 복합사고로 자동 상관분석",
                "Qwen3.5 9B 기반 AI Copilot을 통한 보안 가설 수립 및 인간 승인(HITL) 게이트웨이 차단 조치 완료",
            ],
            "recommendations": [
                "동일 출발지 IP(10.77.20.20)에 대한 Gateway nftables 영구 DROP 정책 유지",
                "Zero-Hit 미사용 방화벽 정책 2건에 대한 30일 경과 후 폐기(Sunsetting) 절차 진행",
                "Log4j 및 Web SQL Injection 탐지 임계치 기반 WAF 자동 연동 강화",
            ],
        }
    elif report_type == "incident":
        return {
            "report_id": "SOC-REP-2026-INC001",
            "title": "다단계 복합 침해사고 대응 보고서 (IR-06 Multi-Stage Kill Chain)",
            "incident_id": active_inc.get("incident_id", "INC-2026-001"),
            "doc_no": "IR-REP-20260824-001",
            "severity": "CRITICAL (P0)",
            "classification": "RESTRICTED / INCIDENT RESPONSE",
            "investigator": "admin (SOC Incident Response Team)",
            "date": "2026-09-22",
            "attacker_ip": active_inc.get("src_ip", "10.77.20.20"),
            "verdict": f"TRUE_POSITIVE ({active_inc.get('verdict')})" if active_inc.get("verdict") else "TRUE_POSITIVE (실제 침해 시도 확인)",
            "ai_risk_score": 88,
            "stages": [
                {"stage": "1. 정찰 (Reconnaissance)", "technique": "T1046 Network Service Scanning", "signature": "Nmap Stealth NULL Scan Detected", "status": "DETECTED"},
                {"stage": "2. 웹 취약점 공격 (Exploitation)", "technique": "T1190 Exploit Public-Facing Application", "signature": "Web SQL Injection UNION SELECT Pattern", "status": "DETECTED & LOGGED"},
                {"stage": "3. 원격 코드 실행 (RCE Attempt)", "technique": "T1190 JNDI Exploit", "signature": "Apache Log4j JNDI RCE Exploit", "status": "DETECTED"},
                {"stage": "4. 명령제어 및 셸 획득 (C2 & Exfiltration)", "technique": "T1059.004 Unix Shell", "signature": "Suspicious Reverse Shell Connection", "status": "BLOCKED BY GATEWAY"},
            ],
            "applied_containment": "nft add rule inet filter forward ip saddr 10.77.20.20 drop (HITL APPROVED)",
            "evidence_references": ["EV-NET-001", "EV-SURI-001", "EV-SNORT-001", "EV-WAZUH-001", "EV-AI-001"],
        }
    elif report_type == "daily":
        return {
            "report_id": "SOC-REP-2026-DAILY",
            "title": "일일 보안관제 동향 보고서 (Daily Security Briefing)",
            "date": "2026-09-22 (최근 24시간)",
            "classification": "SOC INTERNAL",
            "summary_metrics": {
                "total_inspected_packets": "4,192,450",
                "rx_bandwidth": "42.8 Mbps",
                "tx_bandwidth": "38.6 Mbps",
                "total_alerts": 84,
                "critical_high_count": 28,
                "blocked_attempts": 147,
                "zero_hit_rules": 2,
            },
            "top_threat_origins": [
                {"country": "네덜란드 (Netherlands)", "flag": "🇳🇱", "attacks": 28, "blocked": 28},
                {"country": "러시아 (Russia)", "flag": "🇷🇺", "attacks": 24, "blocked": 24},
                {"country": "중국 (China)", "flag": "🇨🇳", "attacks": 19, "blocked": 19},
                {"country": "미국 (United States)", "flag": "🇺🇸", "attacks": 14, "blocked": 14},
                {"country": "이란 (Iran)", "flag": "🇮🇷", "attacks": 8, "blocked": 8},
            ],
            "infrastructure_status": "센서 및 게이트웨이 100% 정상 (가동시간: 10일 05시간, CPU 18%, MEM 34%)",
        }
    elif report_type == "audit":
        audit_logs = [l.model_dump(mode="json") for l in get_audit_logs(limit=50)]
        return {
            "report_id": "SOC-REP-2026-AUDIT",
            "title": "보안관제 운영 및 정책 변경 감사 보고서 (SOC Audit Trail)",
            "classification": "RESTRICTED / SOC AUDIT",
            "date": "2026-09-22",
            "total_logs": len(audit_logs),
            "logs": audit_logs,
        }
    else:
        raise HTTPException(status_code=404, detail=f"Report type '{report_type}' not found")


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
# Red Team Attack Simulator Endpoints
# -------------------------------------------------------------

@app.get("/api/simulator/scenarios")
async def api_simulator_scenarios():
    """Returns the catalog of 6 pre-configured red-team attack scenarios."""
    scenarios = attack_simulator_engine.get_catalog()
    return [s.model_dump() for s in scenarios]


@app.post("/api/simulator/launch")
async def api_simulator_launch(req: LaunchRequest):
    """Launches an attack scenario and injects realistic live telemetry into EVE JSON and Snort logs."""
    try:
        res = attack_simulator_engine.launch(
            scenario_id=req.scenario_id,
            intensity=req.intensity,
            live_inject=req.live_inject,
        )
        record_audit_log(
            event_type="ATTACK_SIMULATION",
            action=f"LAUNCH_{req.scenario_id.upper()}",
            actor="red_team_analyst",
            result="SUCCESS",
            detail=f"Scenario: {res.scenario_name} | Technique: {res.technique_id} | Injected: {res.alerts_generated} alerts | Attacker: {res.attacker_ip} -> Target: {res.target_ip}:{res.target_port}",
        )
        # Broadcast real-time event to connected WebSockets
        try:
            await ws_manager.broadcast({
                "type": "ATTACK_SIMULATION_EVENT",
                "scenario_id": res.scenario_id,
                "scenario_name": res.scenario_name,
                "technique_id": res.technique_id,
                "alerts_generated": res.alerts_generated,
                "timestamp": res.timestamp,
            }, "stream")
        except Exception:
            pass

        return res.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to launch attack simulation: {e}")


@app.get("/api/simulator/history")
async def api_simulator_history(limit: int = 20):
    """Returns execution history of recent attack simulations."""
    history = attack_simulator_engine.get_history(limit=limit)
    return [h.model_dump() for h in history]


# -------------------------------------------------------------
# Live Threat Intelligence (CTI) Endpoints
# -------------------------------------------------------------

@app.get("/api/threats/intel/{indicator}")
async def api_threat_intel_lookup(indicator: str):
    """Returns real-time CTI reputation profile (AbuseIPDB, VirusTotal, GeoIP, ASN)."""
    try:
        report = cti_engine.lookup(indicator)
        return report.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CTI lookup failed: {e}")


class CTIBatchRequest(BaseModel):
    indicators: list[str] = Field(default_factory=list)


@app.post("/api/threats/intel/batch")
async def api_threat_intel_batch(req: CTIBatchRequest):
    """Returns batch CTI reputation profiles for multiple IP addresses or domains."""
    try:
        reports = cti_engine.batch_lookup(req.indicators)
        return [r.model_dump() for r in reports]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch CTI lookup failed: {e}")


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
