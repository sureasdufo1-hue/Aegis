"""
SOC Detection & Monitoring Lab - Detection Quality & Performance Metrics
Reference: LLD v1.0, AGENTS.md Section 17 & 21
"""

from typing import Any
from pydantic import BaseModel, Field


class ConfusionMatrix(BaseModel):
    tp: int = Field(default=0, description="True Positives (Correct Alert on Attack)")
    fp: int = Field(default=0, description="False Positives (Erroneous Alert on Normal Traffic)")
    tn: int = Field(default=0, description="True Negatives (No Alert on Normal Traffic)")
    fn: int = Field(default=0, description="False Negatives (Missed Detection on Attack)")

    @property
    def total(self) -> int:
        return self.tp + self.fp + self.tn + self.fn

    @property
    def precision(self) -> float:
        denom = self.tp + self.fp
        return (self.tp / denom) if denom > 0 else 0.0

    @property
    def recall(self) -> float:
        denom = self.tp + self.fn
        return (self.tp / denom) if denom > 0 else 0.0

    @property
    def f1_score(self) -> float:
        p, r = self.precision, self.recall
        return (2 * p * r / (p + r)) if (p + r) > 0 else 0.0

    @property
    def fpr(self) -> float:
        denom = self.fp + self.tn
        return (self.fp / denom) if denom > 0 else 0.0

    @property
    def fnr(self) -> float:
        denom = self.fn + self.tp
        return (self.fn / denom) if denom > 0 else 0.0

    @property
    def accuracy(self) -> float:
        return ((self.tp + self.tn) / self.total) if self.total > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "TP": self.tp,
            "FP": self.fp,
            "TN": self.tn,
            "FN": self.fn,
            "Total": self.total,
            "Precision": round(self.precision * 100, 2),
            "Recall": round(self.recall * 100, 2),
            "F1_Score": round(self.f1_score * 100, 2),
            "FPR": round(self.fpr * 100, 2),
            "FNR": round(self.fnr * 100, 2),
            "Accuracy": round(self.accuracy * 100, 2),
        }
