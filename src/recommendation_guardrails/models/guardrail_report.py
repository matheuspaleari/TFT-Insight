from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class GuardrailSeverity(str, Enum):
    BLOCK = "BLOCK"
    WARNING = "WARNING"
    INFO = "INFO"

@dataclass(frozen=True)
class GuardrailFinding:
    rule_id: str
    severity: GuardrailSeverity
    message: str
    field: str | None = None
    excerpt: str | None = None

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "severity": self.severity.value,
            "message": self.message,
            "field": self.field,
            "excerpt": self.excerpt,
        }

@dataclass(frozen=True)
class GuardrailReport:
    passed: bool
    findings: tuple[GuardrailFinding, ...] = field(default_factory=tuple)
    blocked_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    changes_learning_priority: bool = False
    changes_mission: bool = False
    changes_difficulty: bool = False
    changes_evidence_class: bool = False
    counts_as_mission_evidence: bool = False
    predicts_rank_up: bool = False

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "findings": [item.to_dict() for item in self.findings],
            "blocked_count": self.blocked_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "changes_learning_priority": self.changes_learning_priority,
            "changes_mission": self.changes_mission,
            "changes_difficulty": self.changes_difficulty,
            "changes_evidence_class": self.changes_evidence_class,
            "counts_as_mission_evidence": self.counts_as_mission_evidence,
            "predicts_rank_up": self.predicts_rank_up,
        }
