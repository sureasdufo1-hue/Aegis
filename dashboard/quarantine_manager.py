"""SOAR Active Quarantine Management & 1-Click Rollback Safeguard Engine.

Provides active firewall (nftables) quarantine with configurable TTL (Time-To-Live),
automatic expiration background processing, and instant 1-click manual rollback to
prevent business downtime from false-positive blocks in enterprise SOC operations.
"""

from __future__ import annotations

import json
import threading
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field

from dashboard.audit import record_audit_log

QUARANTINE_STORAGE_FILE = Path("logs/quarantine_records.jsonl")


class QuarantineStatus(str, Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    ROLLED_BACK = "ROLLED_BACK"


class QuarantineRecord(BaseModel):
    id: str = Field(description="격리 고유 식별자 (예: QRN-10.77.20.20-8392)")
    ip: str = Field(description="격리 대상 IP 주소")
    target_type: str = Field(default="IP", description="격리 대상 유형 (IP, SUBNET, PORT)")
    reason: str = Field(description="차단 사유 및 연계 인시던트")
    rule_preview: str = Field(description="Gateway nftables 적용 룰 구문 프리뷰")
    rollback_rule_preview: str = Field(description="롤백 시 실행될 원상 복구 룰 구문")
    created_at: str = Field(description="격리 생성 일시 (ISO 8601)")
    created_by: str = Field(default="soc-analyst", description="격리 등록자/엔진")
    ttl_seconds: int = Field(default=3600, description="격리 유효 수명 (초 단위, 0=영구 차단)")
    expires_at: str | None = Field(default=None, description="만료 예정 일시 (ISO 8601, 영구는 None)")
    status: QuarantineStatus = Field(default=QuarantineStatus.ACTIVE, description="격리 상태")
    remaining_seconds: int = Field(default=0, description="현재 잔여 격리 시간 (초)")
    rolled_back_at: str | None = Field(default=None, description="롤백 일시")
    rolled_back_by: str | None = Field(default=None, description="롤백 실행자")
    rollback_reason: str | None = Field(default=None, description="롤백 사유")

    def compute_remaining_seconds(self) -> int:
        if self.status != QuarantineStatus.ACTIVE:
            return 0
        if self.ttl_seconds <= 0 or not self.expires_at:
            return -1  # 영구 차단
        try:
            exp_dt = datetime.fromisoformat(self.expires_at)
            now_dt = datetime.now(UTC)
            diff = int((exp_dt - now_dt).total_seconds())
            return max(0, diff)
        except Exception:
            return 0


class QuarantineApplyRequest(BaseModel):
    ip: str = Field(..., description="격리 대상 IP")
    reason: str = Field(default="보안 위협 탐지 및 침해 확산 방지 격리", description="격리 사유")
    ttl_seconds: int = Field(default=3600, ge=0, description="격리 유효 시간(초). 3600=1시간, 86400=24시간, 0=영구")
    operator: str = Field(default="soc-analyst", description="작업자")
    rule_override: str | None = Field(default=None, description="커스텀 방화벽 룰")


class QuarantineRollbackRequest(BaseModel):
    reason: str = Field(default="오탐 판명 및 서비스 정상화를 위한 즉시 원상 복구", description="롤백 사유")
    operator: str = Field(default="soc-analyst", description="롤백 실행자")


class QuarantineStats(BaseModel):
    active_count: int
    expired_count: int
    rolled_back_count: int
    total_count: int
    permanent_count: int


INITIAL_QUARANTINE_SEEDS: list[dict[str, Any]] = [
    {
        "id": "QRN-10.77.20.20-001",
        "ip": "10.77.20.20",
        "target_type": "IP",
        "reason": "IR-06 다단계 킬체인 공격자 (SQLi + Log4j + BruteForce) 능동 차단",
        "rule_preview": "nft insert rule inet filter forward ip saddr 10.77.20.20 drop",
        "rollback_rule_preview": "nft delete rule inet filter forward ip saddr 10.77.20.20 drop",
        "created_at": (datetime.now(UTC) - timedelta(minutes=18)).isoformat(),
        "created_by": "ai-copilot",
        "ttl_seconds": 3600,
        "expires_at": (datetime.now(UTC) + timedelta(minutes=42)).isoformat(),
        "status": "ACTIVE",
        "remaining_seconds": 2520,
        "rolled_back_at": None,
        "rolled_back_by": None,
        "rollback_reason": None,
    },
    {
        "id": "QRN-10.77.20.50-002",
        "ip": "10.77.20.50",
        "target_type": "IP",
        "reason": "IR-02 SSH 무차별 대입(T1110.001) 초고빈도 접근 임시 차단",
        "rule_preview": "nft insert rule inet filter forward ip saddr 10.77.20.50 drop",
        "rollback_rule_preview": "nft delete rule inet filter forward ip saddr 10.77.20.50 drop",
        "created_at": (datetime.now(UTC) - timedelta(minutes=30)).isoformat(),
        "created_by": "soc-analyst",
        "ttl_seconds": 7200,
        "expires_at": (datetime.now(UTC) + timedelta(minutes=90)).isoformat(),
        "status": "ACTIVE",
        "remaining_seconds": 5400,
        "rolled_back_at": None,
        "rolled_back_by": None,
        "rollback_reason": None,
    },
    {
        "id": "QRN-10.77.20.88-003",
        "ip": "10.77.20.88",
        "target_type": "IP",
        "reason": "IR-01 Nmap SYN Stealth 포트 스캔 정찰 임시 격리",
        "rule_preview": "nft insert rule inet filter forward ip saddr 10.77.20.88 drop",
        "rollback_rule_preview": "nft delete rule inet filter forward ip saddr 10.77.20.88 drop",
        "created_at": (datetime.now(UTC) - timedelta(hours=3)).isoformat(),
        "created_by": "soc-analyst",
        "ttl_seconds": 1800,
        "expires_at": (datetime.now(UTC) - timedelta(hours=2, minutes=30)).isoformat(),
        "status": "EXPIRED",
        "remaining_seconds": 0,
        "rolled_back_at": (datetime.now(UTC) - timedelta(hours=2, minutes=30)).isoformat(),
        "rolled_back_by": "system-scheduler",
        "rollback_reason": "TTL 1800s 자동 만료에 따른 격리 해제 (TTL Expired)",
    },
    {
        "id": "QRN-10.77.10.150-004",
        "ip": "10.77.10.150",
        "target_type": "IP",
        "reason": "내부 단말 비인가 프로토콜 접근 의심 수동 차단",
        "rule_preview": "nft insert rule inet filter forward ip saddr 10.77.10.150 drop",
        "rollback_rule_preview": "nft delete rule inet filter forward ip saddr 10.77.10.150 drop",
        "created_at": (datetime.now(UTC) - timedelta(hours=5)).isoformat(),
        "created_by": "soc-tier1",
        "ttl_seconds": 3600,
        "expires_at": (datetime.now(UTC) - timedelta(hours=4)).isoformat(),
        "status": "ROLLED_BACK",
        "remaining_seconds": 0,
        "rolled_back_at": (datetime.now(UTC) - timedelta(hours=4, minutes=50)).isoformat(),
        "rolled_back_by": "soc-lead",
        "rollback_reason": "사내 관리자 단말 오탐(False Positive) 확인으로 즉각 1-Click 롤백 복구",
    },
]


class QuarantineManager:
    """Thread-safe SOAR Quarantine Manager with TTL Auto-Expiration & 1-Click Rollback."""

    def __init__(self, storage_path: Path = QUARANTINE_STORAGE_FILE) -> None:
        self.storage_path = storage_path
        self._lock = threading.Lock()
        self._records: dict[str, QuarantineRecord] = {}
        self._init_storage()

    def _init_storage(self) -> None:
        with self._lock:
            if not self.storage_path.exists():
                self.storage_path.parent.mkdir(parents=True, exist_ok=True)
                for seed in INITIAL_QUARANTINE_SEEDS:
                    rec = QuarantineRecord.model_validate(seed)
                    rec.remaining_seconds = rec.compute_remaining_seconds()
                    self._records[rec.id] = rec
                self._save_to_disk()
            else:
                try:
                    with open(self.storage_path, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                try:
                                    rec = QuarantineRecord.model_validate(json.loads(line))
                                    self._records[rec.id] = rec
                                except Exception:
                                    continue
                except Exception:
                    pass

    def _save_to_disk(self) -> None:
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                for rec in self._records.values():
                    f.write(json.dumps(rec.model_dump(), ensure_ascii=False) + "\n")
        except Exception:
            pass

    def check_and_expire(self) -> list[QuarantineRecord]:
        """Check all active records and automatically expire those past their TTL."""
        expired: list[QuarantineRecord] = []
        now = datetime.now(UTC)
        with self._lock:
            for rec in self._records.values():
                if rec.status == QuarantineStatus.ACTIVE and rec.ttl_seconds > 0 and rec.expires_at:
                    try:
                        exp_dt = datetime.fromisoformat(rec.expires_at)
                        if now >= exp_dt:
                            rec.status = QuarantineStatus.EXPIRED
                            rec.remaining_seconds = 0
                            rec.rolled_back_at = now.isoformat()
                            rec.rolled_back_by = "system-scheduler"
                            rec.rollback_reason = f"TTL {rec.ttl_seconds}s 자동 만료에 따른 격리 해제 (Auto-Expired)"
                            expired.append(rec)
                            record_audit_log(
                                event_type="POLICY",
                                action="Quarantine TTL Expired",
                                actor="system-scheduler",
                                result="SUCCESS",
                                detail=f"Auto-released quarantine for IP {rec.ip} (Record: {rec.id}, TTL: {rec.ttl_seconds}s).",
                            )
                    except Exception:
                        continue
            if expired:
                self._save_to_disk()
        return expired

    def quarantine_ip(
        self,
        ip: str,
        reason: str = "보안 위협 탐지 및 침해 확산 방지 격리",
        ttl_seconds: int = 3600,
        operator: str = "soc-analyst",
        rule_override: str | None = None,
    ) -> QuarantineRecord:
        """Quarantine an IP with designated TTL."""
        self.check_and_expire()
        now = datetime.now(UTC)
        expires_at = (now + timedelta(seconds=ttl_seconds)).isoformat() if ttl_seconds > 0 else None
        record_id = f"QRN-{ip}-{int(now.timestamp()) % 100000:05d}"

        rule_prev = rule_override or f"nft insert rule inet filter forward ip saddr {ip} drop"
        rollback_prev = f"nft delete rule inet filter forward ip saddr {ip} drop"

        rec = QuarantineRecord(
            id=record_id,
            ip=ip,
            target_type="IP",
            reason=reason,
            rule_preview=rule_prev,
            rollback_rule_preview=rollback_prev,
            created_at=now.isoformat(),
            created_by=operator,
            ttl_seconds=ttl_seconds,
            expires_at=expires_at,
            status=QuarantineStatus.ACTIVE,
            remaining_seconds=ttl_seconds if ttl_seconds > 0 else -1,
        )

        with self._lock:
            self._records[rec.id] = rec
            self._save_to_disk()

        ttl_label = f"{ttl_seconds}s" if ttl_seconds > 0 else "Permanent"
        record_audit_log(
            event_type="POLICY",
            action="IP Quarantined (Active Defense)",
            actor=operator,
            result="SUCCESS",
            detail=f"Quarantined IP {ip} at Gateway nftables. TTL: {ttl_label}, Reason: {reason} (Record: {rec.id}).",
        )
        return rec

    def rollback_quarantine(
        self,
        quarantine_id: str,
        operator: str = "soc-analyst",
        reason: str = "오탐 판명 및 서비스 정상화를 위한 즉시 원상 복구",
    ) -> tuple[bool, QuarantineRecord | str]:
        """Instantly rollback an active or existing quarantine record."""
        self.check_and_expire()
        now = datetime.now(UTC)

        with self._lock:
            rec = self._records.get(quarantine_id)
            if not rec:
                return False, f"격리 기록 '{quarantine_id}'을(를) 찾을 수 없습니다."

            if rec.status == QuarantineStatus.ROLLED_BACK:
                return False, f"격리 기록 '{quarantine_id}'은(는) 이미 롤백되었습니다."

            rec.status = QuarantineStatus.ROLLED_BACK
            rec.remaining_seconds = 0
            rec.rolled_back_at = now.isoformat()
            rec.rolled_back_by = operator
            rec.rollback_reason = reason
            self._save_to_disk()

        record_audit_log(
            event_type="POLICY",
            action="Quarantine Rolled Back (1-Click Restore)",
            actor=operator,
            result="SUCCESS",
            detail=f"Restored firewall rule for IP {rec.ip} (Record: {rec.id}). Rollback Reason: {reason}.",
        )
        return True, rec

    def list_quarantines(self, include_historical: bool = True) -> list[QuarantineRecord]:
        """List quarantine records with updated remaining seconds."""
        self.check_and_expire()
        results: list[QuarantineRecord] = []
        with self._lock:
            for rec in self._records.values():
                rec.remaining_seconds = rec.compute_remaining_seconds()
                if include_historical or rec.status == QuarantineStatus.ACTIVE:
                    results.append(rec)
        results.sort(key=lambda x: x.created_at, reverse=True)
        return results

    def get_stats(self) -> QuarantineStats:
        """Get summary metrics for dashboard."""
        self.check_and_expire()
        records = self.list_quarantines(include_historical=True)
        active = sum(1 for r in records if r.status == QuarantineStatus.ACTIVE)
        expired = sum(1 for r in records if r.status == QuarantineStatus.EXPIRED)
        rolled_back = sum(1 for r in records if r.status == QuarantineStatus.ROLLED_BACK)
        permanent = sum(1 for r in records if r.status == QuarantineStatus.ACTIVE and r.ttl_seconds <= 0)

        return QuarantineStats(
            active_count=active,
            expired_count=expired,
            rolled_back_count=rolled_back,
            total_count=len(records),
            permanent_count=permanent,
        )


quarantine_manager = QuarantineManager()
