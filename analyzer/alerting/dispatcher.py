from __future__ import annotations

import logging
import os
import uuid
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

import httpx
from pydantic import BaseModel, Field

from analyzer.detection.correlation_engine import Incident
from analyzer.models import Severity

logger = logging.getLogger("soc.alerting.dispatcher")


class NotificationChannel(str, Enum):
    SLACK = "slack"
    DISCORD = "discord"
    WEBHOOK = "webhook"


class DispatchStatus(str, Enum):
    SUCCESS = "success"
    THROTTLED = "throttled"
    FAILED = "failed"
    DRY_RUN = "dry_run"
    SUPPRESSED = "suppressed"


class NotificationRecord(BaseModel):
    record_id: str = Field(default_factory=lambda: f"NOTIF-{uuid.uuid4().hex[:8].upper()}")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    incident_id: str
    src_ip: str
    channel: NotificationChannel
    status: DispatchStatus
    details: str
    error_message: str | None = None


class NotificationConfig(BaseModel):
    slack_webhook_url: str | None = None
    discord_webhook_url: str | None = None
    generic_webhook_url: str | None = None
    cooldown_minutes: int = 10
    dashboard_base_url: str = "http://10.77.10.10:8501"
    auto_dispatch: bool = True
    dry_run: bool = False

    @classmethod
    def from_env(cls) -> NotificationConfig:
        return cls(
            slack_webhook_url=os.getenv("AEGIS_SLACK_WEBHOOK_URL") or os.getenv("SLACK_WEBHOOK_URL"),
            discord_webhook_url=os.getenv("AEGIS_DISCORD_WEBHOOK_URL") or os.getenv("DISCORD_WEBHOOK_URL"),
            generic_webhook_url=os.getenv("AEGIS_ALERT_WEBHOOK_URL") or os.getenv("WEBHOOK_URL"),
            cooldown_minutes=int(os.getenv("AEGIS_ALERT_COOLDOWN_MINUTES", "10")),
            dashboard_base_url=os.getenv("AEGIS_DASHBOARD_URL", "http://10.77.10.10:8501"),
            auto_dispatch=os.getenv("AEGIS_AUTO_DISPATCH", "true").lower() in ("true", "1", "yes"),
            dry_run=os.getenv("AEGIS_ALERT_DRY_RUN", "false").lower() in ("true", "1", "yes"),
        )


class NotificationDispatcher:
    """
    SOAR Tier-1 Real-Time Incident Notification Dispatcher.
    Supports Slack Block Kit, Discord Rich Embeds, and Generic JSON Webhook.
    Includes sliding-window throttling, anti-flood deduplication, and firewall command recommendations.
    """

    def __init__(
        self,
        config: NotificationConfig | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.config = config or NotificationConfig.from_env()
        self._custom_client = http_client
        self._cooldown_tracker: dict[str, datetime] = {}
        self._history: list[NotificationRecord] = []

    @property
    def history(self) -> list[NotificationRecord]:
        return list(self._history)

    def _mask_url(self, url: str | None) -> str | None:
        if not url:
            return None
        if len(url) <= 20:
            return "******"
        return f"{url[:12]}...{url[-6:]}"

    def get_masked_config(self) -> dict[str, Any]:
        return {
            "slack_configured": bool(self.config.slack_webhook_url),
            "slack_url_masked": self._mask_url(self.config.slack_webhook_url),
            "discord_configured": bool(self.config.discord_webhook_url),
            "discord_url_masked": self._mask_url(self.config.discord_webhook_url),
            "webhook_configured": bool(self.config.generic_webhook_url),
            "webhook_url_masked": self._mask_url(self.config.generic_webhook_url),
            "cooldown_minutes": self.config.cooldown_minutes,
            "dashboard_base_url": self.config.dashboard_base_url,
            "auto_dispatch": self.config.auto_dispatch,
            "dry_run": self.config.dry_run,
        }

    def is_throttled(self, src_ip: str) -> bool:
        """Checks if alerts from src_ip should be throttled based on cooldown window."""
        now = datetime.now(UTC)
        last_sent = self._cooldown_tracker.get(src_ip)
        if not last_sent:
            return False
        delta = now - last_sent
        return delta < timedelta(minutes=self.config.cooldown_minutes)

    def record_dispatch(self, src_ip: str) -> None:
        """Records timestamp for the IP to enforce cooldown."""
        self._cooldown_tracker[src_ip] = datetime.now(UTC)

    def reset_cooldown(self, src_ip: str | None = None) -> None:
        if src_ip:
            self._cooldown_tracker.pop(src_ip, None)
        else:
            self._cooldown_tracker.clear()

    # ------------------------------------------------------------------
    # Payload Formatters
    # ------------------------------------------------------------------

    def format_slack_payload(self, incident: Incident) -> dict[str, Any]:
        """Formats an Incident into Slack Block Kit specification."""
        sev_color = "🚨 *CRITICAL INCIDENT*" if incident.highest_severity == Severity.CRITICAL else "⚠️ *HIGH SEVERITY ALERT*"
        targets_str = ", ".join(incident.target_ips) if incident.target_ips else "Unknown"
        stages_str = " ➔ ".join(incident.attack_stages) if incident.attack_stages else "Undetermined"
        isolation_cmd = f"nft add element inet filter blocklist {{ {incident.src_ip} }}"
        dashboard_url = f"{self.config.dashboard_base_url}/"

        mitre_list = sorted(list(set(a.mitre_technique for a in incident.alerts if a.mitre_technique)))
        mitre_str = ", ".join(mitre_list) if mitre_list else "T1046, T1190"

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🚨 [AEGIS SOC] 침해사고 긴급 경보 ({incident.highest_severity.value})",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{sev_color}\n*{incident.verdict}*",
                },
            },
            {"type": "divider"},
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Incident ID:*\n`{incident.incident_id}`"},
                    {"type": "mrkdwn", "text": f"*Activity Status:*\n`{incident.activity_status}`"},
                    {"type": "mrkdwn", "text": f"*Attacker IP:*\n`{incident.src_ip}` (Threat Zone)"},
                    {"type": "mrkdwn", "text": f"*Victim Assets:*\n`{targets_str}`"},
                ],
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*MITRE ATT&CK:*\n`{mitre_str}`"},
                    {"type": "mrkdwn", "text": f"*Total Alerts:*\n`{len(incident.alerts)} events`"},
                ],
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Kill Chain Progression:*\n`{stages_str}`",
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*권고 초동 조치 (Gateway Firewall 차단):*\n```{isolation_cmd}```",
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "3D 관제 대시보드 바로가기", "emoji": True},
                        "url": dashboard_url,
                        "style": "danger" if incident.highest_severity == Severity.CRITICAL else "primary",
                    }
                ],
            },
        ]
        return {"blocks": blocks, "text": f"[AEGIS SOC Alert] {incident.incident_id} - {incident.src_ip}"}

    def format_discord_payload(self, incident: Incident) -> dict[str, Any]:
        """Formats an Incident into Discord Rich Embed specification."""
        color = 0xE02424 if incident.highest_severity == Severity.CRITICAL else 0xF59E0B
        targets_str = ", ".join(incident.target_ips) if incident.target_ips else "Unknown"
        stages_str = " ➔ ".join(incident.attack_stages) if incident.attack_stages else "Undetermined"
        isolation_cmd = f"nft add element inet filter blocklist {{ {incident.src_ip} }}"
        dashboard_url = f"{self.config.dashboard_base_url}/"

        mitre_list = sorted(list(set(a.mitre_technique for a in incident.alerts if a.mitre_technique)))
        mitre_str = ", ".join(mitre_list) if mitre_list else "T1046, T1190"

        embed = {
            "title": f"🚨 [AEGIS SOC] 침해사고 긴급 경보 - {incident.incident_id}",
            "description": f"**{incident.verdict}**",
            "url": dashboard_url,
            "color": color,
            "fields": [
                {"name": "공격자 IP", "value": f"`{incident.src_ip}`", "inline": True},
                {"name": "피해 대상 자산", "value": f"`{targets_str}`", "inline": True},
                {"name": "심각도 / 상태", "value": f"**{incident.highest_severity.value}** ({incident.activity_status})", "inline": True},
                {"name": "MITRE ATT&CK", "value": f"`{mitre_str}`", "inline": True},
                {"name": "연관 탐지 건수", "value": f"{len(incident.alerts)} 건", "inline": True},
                {"name": "플레이북", "value": f"`{incident.playbook_ref or 'playbooks/01_triage.md'}`", "inline": True},
                {"name": "킬체인 전개 단계", "value": f"`{stages_str}`", "inline": False},
                {"name": "🛡️ 초동 격리 명령 (NFTables)", "value": f"```{isolation_cmd}```", "inline": False},
            ],
            "footer": {"text": "Aegis SOC Lab • Dual IDS Evidence Pipeline"},
            "timestamp": incident.last_seen.isoformat(),
        }
        return {"embeds": [embed]}

    def format_generic_payload(self, incident: Incident) -> dict[str, Any]:
        """Formats an Incident into standardized JSON Webhook specification."""
        mitre_list = sorted(list(set(a.mitre_technique for a in incident.alerts if a.mitre_technique)))
        return {
            "source": "Aegis-SOC-CorrelationEngine",
            "version": "1.0",
            "event_type": "security_incident",
            "incident": {
                "incident_id": incident.incident_id,
                "src_ip": incident.src_ip,
                "target_ips": incident.target_ips,
                "highest_severity": incident.highest_severity.value,
                "activity_status": incident.activity_status,
                "verdict": incident.verdict,
                "attack_stages": incident.attack_stages,
                "total_alerts": len(incident.alerts),
                "mitre_techniques": mitre_list,
                "playbook": incident.playbook_ref,
                "recommended_action": f"nft add element inet filter blocklist {{ {incident.src_ip} }}",
                "first_seen": incident.start_time.isoformat(),
                "last_seen": incident.last_seen.isoformat(),
            },
            "dispatch_timestamp": datetime.now(UTC).isoformat(),
        }

    # ------------------------------------------------------------------
    # Dispatch Execution Core
    # ------------------------------------------------------------------

    async def _send_http_post(self, url: str, payload: dict[str, Any]) -> tuple[bool, str | None]:
        try:
            if self._custom_client:
                resp = await self._custom_client.post(url, json=payload, timeout=5.0)
                if resp.status_code in (200, 204):
                    return True, None
                return False, f"HTTP {resp.status_code}: {resp.text[:100]}"
            else:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.post(url, json=payload)
                    if resp.status_code in (200, 204):
                        return True, None
                    return False, f"HTTP {resp.status_code}: {resp.text[:100]}"
        except Exception as e:
            return False, str(e)

    async def dispatch_incident(
        self, incident: Incident, force: bool = False
    ) -> dict[str, Any]:
        """
        Dispatches an incident across all configured notification channels.
        Enforces cooldown filtering unless force=True.
        """
        results: dict[str, Any] = {
            "incident_id": incident.incident_id,
            "src_ip": incident.src_ip,
            "dispatched_channels": [],
            "status": "completed",
        }

        # 1. Check if suppressed (e.g. Diagnostic only)
        if all(s == "Diagnostic / Telemetry" for s in incident.attack_stages):
            rec = NotificationRecord(
                incident_id=incident.incident_id,
                src_ip=incident.src_ip,
                channel=NotificationChannel.WEBHOOK,
                status=DispatchStatus.SUPPRESSED,
                details="Suppressed diagnostic telemetry",
            )
            self._history.append(rec)
            results["status"] = "suppressed"
            return results

        # 2. Check Cooldown/Deduplication
        if not force and self.is_throttled(incident.src_ip):
            rec = NotificationRecord(
                incident_id=incident.incident_id,
                src_ip=incident.src_ip,
                channel=NotificationChannel.WEBHOOK,
                status=DispatchStatus.THROTTLED,
                details=f"Suppressed duplicate alert within {self.config.cooldown_minutes}m window",
            )
            self._history.append(rec)
            results["status"] = "throttled"
            return results

        # 3. Dispatch to Slack
        if self.config.slack_webhook_url or self.config.dry_run:
            payload = self.format_slack_payload(incident)
            if self.config.dry_run or not self.config.slack_webhook_url:
                rec = NotificationRecord(
                    incident_id=incident.incident_id,
                    src_ip=incident.src_ip,
                    channel=NotificationChannel.SLACK,
                    status=DispatchStatus.DRY_RUN,
                    details="Dry run dispatch simulated for Slack Block Kit",
                )
            else:
                ok, err = await self._send_http_post(self.config.slack_webhook_url, payload)
                rec = NotificationRecord(
                    incident_id=incident.incident_id,
                    src_ip=incident.src_ip,
                    channel=NotificationChannel.SLACK,
                    status=DispatchStatus.SUCCESS if ok else DispatchStatus.FAILED,
                    details="Slack Block Kit notification dispatched" if ok else "Failed Slack delivery",
                    error_message=err,
                )
            self._history.append(rec)
            results["dispatched_channels"].append({"channel": "slack", "status": rec.status.value})

        # 4. Dispatch to Discord
        if self.config.discord_webhook_url or self.config.dry_run:
            payload = self.format_discord_payload(incident)
            if self.config.dry_run or not self.config.discord_webhook_url:
                rec = NotificationRecord(
                    incident_id=incident.incident_id,
                    src_ip=incident.src_ip,
                    channel=NotificationChannel.DISCORD,
                    status=DispatchStatus.DRY_RUN,
                    details="Dry run dispatch simulated for Discord Embed",
                )
            else:
                ok, err = await self._send_http_post(self.config.discord_webhook_url, payload)
                rec = NotificationRecord(
                    incident_id=incident.incident_id,
                    src_ip=incident.src_ip,
                    channel=NotificationChannel.DISCORD,
                    status=DispatchStatus.SUCCESS if ok else DispatchStatus.FAILED,
                    details="Discord Embed notification dispatched" if ok else "Failed Discord delivery",
                    error_message=err,
                )
            self._history.append(rec)
            results["dispatched_channels"].append({"channel": "discord", "status": rec.status.value})

        # 5. Dispatch to Generic Webhook
        if self.config.generic_webhook_url or self.config.dry_run:
            payload = self.format_generic_payload(incident)
            if self.config.dry_run or not self.config.generic_webhook_url:
                rec = NotificationRecord(
                    incident_id=incident.incident_id,
                    src_ip=incident.src_ip,
                    channel=NotificationChannel.WEBHOOK,
                    status=DispatchStatus.DRY_RUN,
                    details="Dry run dispatch simulated for Generic Webhook JSON",
                )
            else:
                ok, err = await self._send_http_post(self.config.generic_webhook_url, payload)
                rec = NotificationRecord(
                    incident_id=incident.incident_id,
                    src_ip=incident.src_ip,
                    channel=NotificationChannel.WEBHOOK,
                    status=DispatchStatus.SUCCESS if ok else DispatchStatus.FAILED,
                    details="Generic Webhook notification dispatched" if ok else "Failed Webhook delivery",
                    error_message=err,
                )
            self._history.append(rec)
            results["dispatched_channels"].append({"channel": "webhook", "status": rec.status.value})

        # Record dispatch cooldown
        self.record_dispatch(incident.src_ip)
        # Cap history at 100 items
        if len(self._history) > 100:
            self._history = self._history[-100:]

        return results

    async def send_test_notification(self, channel: str | None = None) -> dict[str, Any]:
        """Generates a synthetic high-severity incident and dispatches a test alert."""
        from analyzer.models import EngineType, NormalizedAlert

        now_utc = datetime.now(UTC)
        test_alert = NormalizedAlert(
            id=f"ALERT-TEST-{int(now_utc.timestamp())}",
            timestamp=now_utc,
            engine=EngineType.SURICATA,
            sid=9010001,
            rev=1,
            signature="WEB-ATTACK SQL Injection Attempt Detected (UNION SELECT)",
            category="Web Application Attack",
            severity=Severity.HIGH,
            src_ip="10.77.20.20",
            dst_ip="10.77.30.20",
            src_port=48210,
            dst_port=80,
            protocol="TCP",
            mitre_technique="T1190",
        )

        mock_incident = Incident(
            incident_id=f"INC-TEST-{int(now_utc.timestamp())}",
            src_ip="10.77.20.20",
            target_ips=["10.77.30.20"],
            attack_stages=["1. Reconnaissance", "2. Initial Access / Exploitation"],
            alerts=[test_alert],
            start_time=now_utc,
            last_seen=now_utc,
            highest_severity=Severity.CRITICAL,
            verdict="Test Simulation: Multi-stage SQL Injection and Exploit Activity",
            playbook_ref="playbooks/03_web_attack_investigation.md",
            activity_status="CONFIRMED_COMPROMISE",
        )

        # Force bypass cooldown for manual test
        return await self.dispatch_incident(mock_incident, force=True)
