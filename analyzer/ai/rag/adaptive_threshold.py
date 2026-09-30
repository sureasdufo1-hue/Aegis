"""
AegisAI Dynamic Adaptive Similarity Threshold Calculator (Resolves EVAL-GAP-008)
Replaces rigid static thresholds with context-aware, security-tuned thresholding:
- Technical Specificity Adjustments: CVE IDs, MITRE ATT&CK techniques, and high-entropy security keywords.
- Query Ambiguity Dampening: Short/ambiguous queries increase threshold to avoid hallucinated noise.
- Grounded Evidence Range: Bounded [min_threshold, max_threshold] ensuring deterministic retrieval.
"""

import re
from pydantic import BaseModel, Field

from analyzer.ai.rag.knowledge_store import KnowledgeChunk


# High-signal security jargon that warrants lower technical threshold to capture exact domain playbooks
SECURITY_JARGON_KEYWORDS = {
    "sqli", "xss", "log4j", "traversal", "bruteforce", "c2", "beacon",
    "meterpreter", "cobaltstrike", "mimikatz", "exfiltration", "synflood",
    "dirbuster", "nmap", "portscan", "ransomware", "backdoor", "webshell"
}


class QueryProfile(BaseModel):
    query: str
    word_count: int
    has_cve: bool
    cve_ids: list[str] = Field(default_factory=list)
    has_mitre: bool
    mitre_techniques: list[str] = Field(default_factory=list)
    has_jargon: bool
    detected_jargon: list[str] = Field(default_factory=list)
    is_short: bool
    is_long: bool


class AdaptiveThresholdResult(BaseModel):
    effective_threshold: float
    base_threshold: float
    adjustments: list[str] = Field(default_factory=list)
    query_profile: QueryProfile


class AdaptiveThresholdCalculator:
    """
    Computes an adaptive relevance threshold tailored to security query characteristics.
    """

    def __init__(
        self,
        base_threshold: float = 0.50,
        min_threshold: float = 0.20,
        max_threshold: float = 0.85,
    ):
        self.base_threshold = base_threshold
        self.min_threshold = min_threshold
        self.max_threshold = max_threshold

    def analyze_query(self, query: str) -> QueryProfile:
        q_lower = query.lower()
        words = re.findall(r"\b[A-Za-z0-9_-]{2,}\b", query)
        
        # CVE Detection (e.g. CVE-2021-44228)
        cves = re.findall(r"\bCVE-\d{4}-\d+\b", query, re.IGNORECASE)
        
        # MITRE ATT&CK Technique Detection (e.g. T1046, T1059.001)
        mitres = re.findall(r"\bT\d{4}(?:\.\d{3})?\b", query, re.IGNORECASE)

        # Security Jargon Detection
        jargon = [k for k in SECURITY_JARGON_KEYWORDS if k in q_lower or any(k in w.lower() for w in words)]

        word_count = len(words)
        is_short = word_count <= 2
        is_long = word_count >= 8

        return QueryProfile(
            query=query,
            word_count=word_count,
            has_cve=bool(cves),
            cve_ids=cves,
            has_mitre=bool(mitres),
            mitre_techniques=mitres,
            has_jargon=bool(jargon),
            detected_jargon=jargon,
            is_short=is_short,
            is_long=is_long,
        )

    def calculate(self, query: str) -> AdaptiveThresholdResult:
        profile = self.analyze_query(query)
        threshold = self.base_threshold
        adjustments: list[str] = []

        # 1. Exact CVE penalty deduction: High-precision indicator -> Lower threshold by 0.15
        if profile.has_cve:
            threshold -= 0.15
            adjustments.append(f"CVE Detected ({', '.join(profile.cve_ids)}): -0.15")

        # 2. MITRE Technique deduction: Standardized taxonomy -> Lower threshold by 0.10
        if profile.has_mitre:
            threshold -= 0.10
            adjustments.append(f"MITRE ATT&CK Detected ({', '.join(profile.mitre_techniques)}): -0.10")

        # 3. Security Jargon deduction -> Lower threshold by 0.05
        if profile.has_jargon:
            threshold -= 0.05
            adjustments.append(f"Security Jargon Detected ({', '.join(profile.detected_jargon)}): -0.05")

        # 4. Short Query Ambiguity Guard: Short queries (< 3 words) increase threshold by +0.10 to prevent broad noise
        if profile.is_short:
            threshold += 0.10
            adjustments.append("Short/Ambiguous Query Guard: +0.10")

        # 5. Long Specific Query adjustment: Detailed alerts with multiple tokens lower threshold slightly
        elif profile.is_long:
            threshold -= 0.05
            adjustments.append("Multi-token Context Query: -0.05")

        # Clamp within safety boundaries
        bounded_threshold = round(max(self.min_threshold, min(self.max_threshold, threshold)), 3)

        return AdaptiveThresholdResult(
            effective_threshold=bounded_threshold,
            base_threshold=self.base_threshold,
            adjustments=adjustments,
            query_profile=profile,
        )

    def filter_and_rank(
        self,
        query: str,
        scored_chunks: list[tuple[KnowledgeChunk, float]],
        top_k: int = 3,
    ) -> tuple[list[tuple[KnowledgeChunk, float]], AdaptiveThresholdResult]:
        calc_result = self.calculate(query)
        cutoff = calc_result.effective_threshold

        accepted = [(chunk, score) for chunk, score in scored_chunks if score >= cutoff]
        accepted.sort(key=lambda x: x[1], reverse=True)
        return accepted[:top_k], calc_result
