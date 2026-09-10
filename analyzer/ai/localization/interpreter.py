"""
Security Event Korean Interpreter & Semantic Enrichment Service.
Translates complex English security signatures and incidents into plain Korean,
clearly distinguishing between 'Detection' and 'Confirmed Compromise'.
Maintains an in-memory SHA-256 cache to guarantee instant response and zero redundant overhead.
"""

import hashlib
from datetime import UTC, datetime
from typing import Any

from analyzer.ai.localization.korean_dict import (
    ATTACK_STAGE_MAP,
    MITRE_TECHNIQUE_MAP,
    SEVERITY_MAP,
    SIGNATURE_MAP,
)


class InterpretationCache:
    def __init__(self, max_size: int = 500):
        self._cache: dict[str, dict[str, Any]] = {}
        self.max_size = max_size

    def get(self, key: str) -> dict[str, Any] | None:
        return self._cache.get(key)

    def set(self, key: str, value: dict[str, Any]) -> None:
        if len(self._cache) >= self.max_size:
            # Simple eviction of oldest item
            first_key = next(iter(self._cache))
            del self._cache[first_key]
        self._cache[key] = value

    def clear(self) -> None:
        self._cache.clear()


class SecurityEventInterpreter:
    def __init__(self):
        self.cache = InterpretationCache()

    def _generate_cache_key(self, raw_text: str, context_type: str) -> str:
        content = f"{context_type}::{raw_text.strip()}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def interpret_alert(self, signature: str, category: str = "", severity: str = "MEDIUM", mitre_id: str | None = None) -> dict[str, Any]:
        cache_key = self._generate_cache_key(signature, "alert")
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        sig_info = SIGNATURE_MAP.get(signature)
        sev_info = SEVERITY_MAP.get(severity.upper(), SEVERITY_MAP["MEDIUM"])
        mitre_info = MITRE_TECHNIQUE_MAP.get(mitre_id) if mitre_id else None

        if sig_info:
            korean_title = sig_info["ko_title"]
            security_meaning = sig_info["explanation"]
            checks = [sig_info["investigation_guide"]]
        else:
            # Generic fallback interpretation based on keywords
            sig_upper = signature.upper()
            if "SCAN" in sig_upper or "RECON" in sig_upper:
                korean_title = f"네트워크 정찰 및 스캔 활동 탐지 ({signature})"
                security_meaning = "공격자가 내부망의 자산이나 열린 포트를 탐색하기 위한 사전 정찰 트래픽입니다."
                checks = ["출발지 IP의 과거 스캔 이력 및 방화벽 차단 여부 확인"]
            elif "SQL" in sig_upper or "INJECTION" in sig_upper:
                korean_title = f"웹 취약점(인젝션) 공격 시도 탐지 ({signature})"
                security_meaning = "웹 애플리케이션의 데이터베이스 질의를 비인가 조작하려는 공격 패턴입니다."
                checks = ["웹 서버의 실제 HTTP 응답 코드(200 OK vs 403/500) 및 페이로드 분석"]
            elif "BRUTE" in sig_upper or "AUTH" in sig_upper or "SSH" in sig_upper:
                korean_title = f"인증 무차별 대입 공격(Brute Force) 탐지 ({signature})"
                security_meaning = "다수의 계정/비밀번호 조합을 대입하여 인증을 우회하려는 시도입니다."
                checks = ["인증 서버 로그에서 실제 로그인 성공(Accepted) 여부 점검"]
            elif "SHELL" in sig_upper or "MALWARE" in sig_upper or "TROJAN" in sig_upper:
                korean_title = f"악성코드 / 리버스 셸(C2) 통신 의심 탐지 ({signature})"
                security_meaning = "공격자가 타깃 호스트의 제어권을 획득하여 역방향 통신을 맺으려는 고위험 징후입니다."
                checks = ["해당 호스트의 프로세스 목록 및 아웃바운드 네트워크 연결 즉시 확인"]
            else:
                korean_title = f"보안 경보 이벤트: {signature}"
                security_meaning = f"네트워크 침입탐지 규칙 '{signature}'에 부합하는 패킷이 감지되었습니다."
                checks = ["패킷 페이로드 및 송수신 호스트의 정상 업무 트래픽 여부 대조"]

        # Add MITRE context if known
        if mitre_info:
            checks.append(f"관련 ATT&CK 기법: {mitre_id} ({mitre_info['name_ko']}) - {mitre_info['desc']}")

        result = {
            "source_signature": signature,
            "korean_title": korean_title,
            "plain_korean_summary": f"[{sev_info['ko']}] {korean_title}",
            "security_meaning": security_meaning,
            "compromise_status": "경보 발생 상태 (공격의 침해 성공 여부는 응답 로그 추가 검증 필요)",
            "recommended_checks": checks,
            "severity_ko": sev_info["ko"],
            "severity_desc": sev_info["desc"],
            "generated_at": datetime.now(UTC).isoformat(),
        }

        self.cache.set(cache_key, result)
        return result

    def interpret_incident(self, incident: dict[str, Any]) -> dict[str, Any]:
        inc_id = incident.get("incident_id", "UNKNOWN-INC")
        cache_key = self._generate_cache_key(inc_id, "incident")
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        src_ip = incident.get("src_ip", "Unknown")
        target_ips = incident.get("target_ips", [])
        attack_stages = incident.get("attack_stages", [])
        highest_sev = incident.get("highest_severity", "HIGH")

        stages_ko = []
        for s in attack_stages:
            st_info = ATTACK_STAGE_MAP.get(s)
            stages_ko.append(st_info["ko"] if st_info else s)

        sev_info = SEVERITY_MAP.get(highest_sev, SEVERITY_MAP["HIGH"])

        summary = (
            f"공격자 IP '{src_ip}'가 내부 자산({', '.join(target_ips)})을 대상으로 "
            f"다단계 복합 침해 공격을 수행 중입니다. "
            f"진행 단계: {' -> '.join(stages_ko)}."
        )

        checks = [
            f"공격자 {src_ip}에 대한 방화벽 인바운드 차단 조치 검토",
            f"공격 대상 자산({', '.join(target_ips)})의 시스템 침해 지표(IoC) 및 프로세스 점검",
            "동일 서브넷 내부로의 횡적 이동(Lateral Movement) 시도 여부 모니터링",
        ]

        result = {
            "incident_id": inc_id,
            "korean_title": f"다단계 복합 침해사고 ({src_ip} -> {len(target_ips)}개 호스트)",
            "plain_korean_summary": summary,
            "attack_stages_ko": stages_ko,
            "highest_severity_ko": sev_info["ko"],
            "security_meaning": (
                "단발성 경보가 아닌, 정찰부터 초기 침투 및 권한 획득/C2로 이어지는 "
                "일관된 사이버 킬체인(Cyber Kill Chain) 공격 흐름이 상관분석 엔진에 의해 입증되었습니다."
            ),
            "compromise_status": (
                "상관분석 입증 완료: 다단계 공격 흐름이 확인되었으며, 후속 단계(C2/리버스 셸) 포함 시 침해 확정 가능성 높음."
            ),
            "recommended_checks": checks,
            "generated_at": datetime.now(UTC).isoformat(),
        }

        self.cache.set(cache_key, result)
        return result
