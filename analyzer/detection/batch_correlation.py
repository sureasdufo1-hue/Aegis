"""
AegisAI Long-Term Batch Correlation Engine (Resolves RSK-001)
Extends detection beyond short sliding windows (15-30m) to uncover
Low-and-Slow, multi-hour advanced persistent campaigns across up to 24 hours.
"""

from collections import defaultdict
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from pydantic import BaseModel, Field

from analyzer.models import NormalizedAlert, Severity
from analyzer.detection.correlation_engine import CorrelationEngine


class AttackPatternType(StrEnum):
    LOW_AND_SLOW = "LOW_AND_SLOW"
    MULTI_STAGE_PROGRESSION = "MULTI_STAGE_PROGRESSION"
    DISTRIBUTED_PERSISTENT = "DISTRIBUTED_PERSISTENT"
    RAPID_MULTI_STAGE = "RAPID_MULTI_STAGE"


class BatchCorrelatedCampaign(BaseModel):
    campaign_id: str
    attacker_ip: str
    targeted_ips: list[str]
    first_activity: datetime
    last_activity: datetime
    dwell_time_hours: float
    total_alerts: int
    pattern_type: AttackPatternType
    stages_detected: list[str]
    mitre_techniques: list[str]
    alerts: list[NormalizedAlert]
    highest_severity: Severity
    is_low_and_slow: bool
    verdict: str
    recommended_playbook: str
    remediation_priority: str = Field(default="P1-HIGH")


class BatchCorrelationEngine:
    """
    Batch analytics engine evaluating alert histories across 24 hours to correlate
    temporal anomalies, slow scanning, multi-stage persistence, and stealthy lateral movement.
    """

    def __init__(
        self,
        lookback_hours: int = 24,
        min_stage_count: int = 2,
        low_and_slow_threshold_minutes: float = 30.0,
    ):
        self.lookback = timedelta(hours=lookback_hours)
        self.min_stage_count = min_stage_count
        self.low_and_slow_threshold_minutes = low_and_slow_threshold_minutes
        self._classifier = CorrelationEngine(window_minutes=30)

    def classify_stage(self, alert: NormalizedAlert) -> str:
        return self._classifier.classify_stage(alert)

    def analyze_alert_batch(
        self,
        alerts: list[NormalizedAlert],
        reference_time: datetime | None = None,
    ) -> list[BatchCorrelatedCampaign]:
        if not alerts:
            return []

        ref_time = reference_time or max(a.timestamp for a in alerts)
        cutoff_time = ref_time - self.lookback

        # 1. Filter alerts within the lookback window
        window_alerts = [a for a in alerts if a.timestamp >= cutoff_time]
        if not window_alerts:
            return []

        # 2. Group alerts by attacker IP
        ip_groups: dict[str, list[NormalizedAlert]] = defaultdict(list)
        for a in window_alerts:
            ip_groups[a.src_ip].append(a)

        campaigns: list[BatchCorrelatedCampaign] = []

        # 3. Analyze each attacker session
        for attacker_ip, group in ip_groups.items():
            # Sort chronologically
            group.sort(key=lambda x: x.timestamp)
            first_time = group[0].timestamp
            last_time = group[-1].timestamp
            dwell_seconds = max(0.0, (last_time - first_time).total_seconds())
            dwell_hours = round(dwell_seconds / 3600.0, 2)

            # Classify distinct actionable stages
            stage_map: dict[str, list[NormalizedAlert]] = defaultdict(list)
            for a in group:
                st = self.classify_stage(a)
                if st not in ["Diagnostic / Telemetry", "Generic Security Activity"]:
                    stage_map[st].append(a)

            unique_stages = sorted(stage_map.keys())

            # Check if alert qualifies as campaign:
            # - At least 2 actionable kill chain stages OR
            # - Dwell time > 1 hour with multiple distinct target ports or techniques
            has_multi_stage = len(unique_stages) >= self.min_stage_count
            has_long_dwell = dwell_hours >= 1.0 and len(group) >= 3

            if not (has_multi_stage or has_long_dwell):
                continue

            # Determine Low-and-Slow characteristics:
            # Low-and-Slow: Intervals between alerts average >= low_and_slow_threshold_minutes
            # OR total dwell time >= 2 hours with low alert frequency (< 10 alerts per hour)
            intervals_min = []
            for i in range(1, len(group)):
                diff_m = (group[i].timestamp - group[i - 1].timestamp).total_seconds() / 60.0
                intervals_min.append(diff_m)

            avg_interval = sum(intervals_min) / len(intervals_min) if intervals_min else 0.0
            is_low_and_slow = (
                avg_interval >= self.low_and_slow_threshold_minutes or
                (dwell_hours >= 2.0 and (len(group) / max(dwell_hours, 1.0)) <= 10.0)
            )

            # Assign Pattern Type
            if is_low_and_slow:
                pattern = AttackPatternType.LOW_AND_SLOW
            elif has_multi_stage and dwell_hours <= 0.5:
                pattern = AttackPatternType.RAPID_MULTI_STAGE
            elif has_multi_stage:
                pattern = AttackPatternType.MULTI_STAGE_PROGRESSION
            else:
                pattern = AttackPatternType.DISTRIBUTED_PERSISTENT

            # Extract distinct MITRE techniques
            mitre_set = sorted(set(a.mitre_technique for a in group if a.mitre_technique))

            # Highest severity
            severities = [a.severity for a in group]
            if Severity.CRITICAL in severities:
                highest_sev = Severity.CRITICAL
                priority = "P0-CRITICAL"
            elif Severity.HIGH in severities:
                highest_sev = Severity.HIGH
                priority = "P1-HIGH"
            elif Severity.MEDIUM in severities:
                highest_sev = Severity.MEDIUM
                priority = "P2-MEDIUM"
            else:
                highest_sev = Severity.LOW
                priority = "P3-LOW"

            targeted_ips = sorted(set(a.dst_ip for a in group))

            # Recommended Playbook
            if any("3. Command & Control" in s for s in unique_stages) or any("4. Exfiltration" in s for s in unique_stages):
                playbook = "playbooks/04_malware_c2_investigation.md"
            elif any("2. Initial Access" in s for s in unique_stages):
                if any("SSH" in a.signature.upper() or "BRUTE" in a.signature.upper() for a in group):
                    playbook = "playbooks/05_ssh_brute_force_investigation.md"
                else:
                    playbook = "playbooks/03_web_attack_investigation.md"
            else:
                playbook = "playbooks/01_port_scan_investigation.md"

            speed_desc = "Low-and-Slow Stealth Attack" if is_low_and_slow else "Multi-Stage Attack Progression"
            verdict = (
                f"{speed_desc} identified over {dwell_hours:.1f}h dwell time. "
                f"Stages: {' -> '.join(unique_stages) if unique_stages else 'Persistent Probing'} "
                f"across {len(targeted_ips)} target host(s) ({len(group)} alerts correlated)."
            )

            campaign_id = f"CMP-{attacker_ip}-{int(first_time.timestamp())}"
            campaign = BatchCorrelatedCampaign(
                campaign_id=campaign_id,
                attacker_ip=attacker_ip,
                targeted_ips=targeted_ips,
                first_activity=first_time,
                last_activity=last_time,
                dwell_time_hours=dwell_hours,
                total_alerts=len(group),
                pattern_type=pattern,
                stages_detected=unique_stages,
                mitre_techniques=mitre_set,
                alerts=group,
                highest_severity=highest_sev,
                is_low_and_slow=is_low_and_slow,
                verdict=verdict,
                recommended_playbook=playbook,
                remediation_priority=priority,
            )
            campaigns.append(campaign)

        # Sort campaigns by severity then dwell time
        campaigns.sort(key=lambda c: (c.highest_severity == Severity.CRITICAL, c.dwell_time_hours), reverse=True)
        return campaigns
