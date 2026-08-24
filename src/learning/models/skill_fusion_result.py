from __future__ import annotations

from dataclasses import dataclass

from src.learning.models.skill_level import SkillLevel
from src.learning.models.skill_signal import SkillSignal


@dataclass(frozen=True)
class SkillFusionResult:
    """Resultado da fusão entre assessment oficial e evidências históricas."""

    skill_id: str
    skill_label: str

    baseline_available: bool
    baseline_level: SkillLevel | None
    baseline_score: float | None
    baseline_confidence: float | None

    fused_level: SkillLevel | None
    fused_score: float | None
    fused_confidence: float | None

    decision: str
    supporting_signals: tuple[SkillSignal, ...]
    evidence_ids: tuple[str, ...]
    interpretation: str
    limitations: tuple[str, ...]
